import logging
from datetime import date, timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_reminder(self, reminder_id: str):
    from .models import SmsReminder
    from .providers import get_sms_provider

    try:
        reminder = SmsReminder.objects.get(id=reminder_id)
    except SmsReminder.DoesNotExist:
        logger.warning("SmsReminder %s not found", reminder_id)
        return

    if reminder.status == SmsReminder.Status.SENT:
        return

    provider = get_sms_provider()
    try:
        result = provider.send(phone=reminder.phone, message=reminder.message)
        message_id = result.get("message_id", "") if isinstance(result, dict) else ""
        reminder.status = SmsReminder.Status.SENT
        reminder.sent_at = timezone.now()
        reminder.infinireach_message_id = message_id
        reminder.error_message = ""
        reminder.save(update_fields=["status", "sent_at", "infinireach_message_id", "error_message", "updated_at"])
        logger.info("SMS sent for reminder %s: %s", reminder_id, result)
    except Exception as exc:
        reminder.status = SmsReminder.Status.FAILED
        reminder.error_message = str(exc)
        reminder.save(update_fields=["status", "error_message", "updated_at"])
        logger.error("SMS failed for reminder %s: %s", reminder_id, exc)
        raise self.retry(exc=exc)


@shared_task
def schedule_expiry_reminders():
    """
    Runs daily at 09:00. Creates pending reminders for vehicles whose
    ko'rik muddati (expiry_date) or gas_cylinder_expiry_date is 30, 14, or 7 days away.
    Skips vehicles that already have a pending/sent reminder for that vehicle+inspection_type+date.
    """
    from .models import SmsReminder, SmsTemplate
    from apps.vehicles.models import Vehicle

    today = date.today()
    notify_days = [30, 14, 7]
    created_count = 0

    GAS_ENGINE_TYPES = ("metan", "propan")

    def _get_template(days_ahead, inspection_type_value):
        """Ko'rik turiga mos shablon topish: exact match yoki any"""
        template = SmsTemplate.objects.filter(
            days_before=days_ahead,
            inspection_type=inspection_type_value,
            is_active=True,
            deleted_at__isnull=True,
        ).first()
        if not template:
            template = SmsTemplate.objects.filter(
                days_before=days_ahead,
                inspection_type="any",
                is_active=True,
                deleted_at__isnull=True,
            ).first()
        return template

    def _create_reminder(vehicle, phone, days_ahead, target_date, inspection_type_value, default_msg):
        already_scheduled = SmsReminder.objects.filter(
            vehicle=vehicle,
            inspection_type=inspection_type_value,
            scheduled_date=today,
            status__in=[SmsReminder.Status.PENDING, SmsReminder.Status.SENT],
            trigger_type=SmsReminder.TriggerType.AUTO,
        ).exists()

        if already_scheduled:
            return 0

        template = _get_template(days_ahead, inspection_type_value)

        if template:
            message = template.render(
                client_name=vehicle.client.full_name,
                plate_number=vehicle.plate_number,
                brand=vehicle.brand,
                model=vehicle.model,
                expiry_date=target_date.strftime("%d.%m.%Y"),
                days_left=days_ahead,
            )
        else:
            message = default_msg

        reminder = SmsReminder.objects.create(
            vehicle=vehicle,
            phone=phone,
            message=message,
            scheduled_date=today,
            trigger_type=SmsReminder.TriggerType.AUTO,
            inspection_type=inspection_type_value,
            branch=vehicle.branch,
        )
        send_sms_reminder.delay(str(reminder.id))
        return 1

    for days_ahead in notify_days:
        target_date = today + timedelta(days=days_ahead)

        # 1. Texnik ko'rik uchun eslatmalar
        tech_vehicles = Vehicle.objects.active().filter(
            expiry_date=target_date,
            is_active=True,
        ).select_related("client")

        for vehicle in tech_vehicles:
            phone = vehicle.client.phone
            if not phone:
                continue
            default_msg = (
                f"Hurmatli {vehicle.client.full_name}! "
                f"{vehicle.brand} {vehicle.model} ({vehicle.plate_number}) "
                f"avtomobilingizning texnik ko'rik muddati {days_ahead} kundan so'ng "
                f"({target_date.strftime('%d.%m.%Y')}) tugaydi. "
                f"Iltimos, o'z vaqtida ko'rikdan o'ting."
            )
            created_count += _create_reminder(
                vehicle, phone, days_ahead, target_date, "technical", default_msg
            )

        # 2. Gaz ballon akt uchun eslatmalar (faqat metan/propan)
        gas_vehicles = Vehicle.objects.active().filter(
            gas_cylinder_expiry_date=target_date,
            engine_type__in=GAS_ENGINE_TYPES,
            is_active=True,
        ).select_related("client")

        for vehicle in gas_vehicles:
            phone = vehicle.client.phone
            if not phone:
                continue
            default_msg = (
                f"Hurmatli {vehicle.client.full_name}! "
                f"{vehicle.brand} {vehicle.model} ({vehicle.plate_number}) "
                f"avtomobilingizning gaz ballon akti {days_ahead} kundan so'ng "
                f"({target_date.strftime('%d.%m.%Y')}) tugaydi. "
                f"Iltimos, o'z vaqtida yangilab oling."
            )
            created_count += _create_reminder(
                vehicle, phone, days_ahead, target_date, "gas_cylinder", default_msg
            )

    logger.info("schedule_expiry_reminders: created %d reminders", created_count)
    return created_count


@shared_task
def check_and_send_auto_sms():
    """Har soatda 05 daqiqada ishlaydi. Har filialning auto_sms vaqtini tekshirib, o'z vaqtida reminder'larni yuboradi."""
    from apps.dashboard.models import SiteSettings
    from apps.branches.models import Branch

    now = timezone.localtime()

    for branch in Branch.objects.filter(is_active=True):
        try:
            settings_obj = SiteSettings.get_for_branch(branch)
            if not settings_obj.auto_sms_enabled:
                continue
            # Soat mos keladi va hozir shu soatning birinchi 10 daqiqasidamiz
            if settings_obj.auto_sms_hour == now.hour and now.minute < 10:
                send_expiry_reminders_for_branch.delay(str(branch.id))
                logger.info("Triggered auto SMS for branch %s at %02d:%02d", branch.id, now.hour, now.minute)
        except Exception as e:
            logger.error("Auto SMS check error for branch %s: %s", branch.id, e)


@shared_task
def send_expiry_reminders_for_branch(branch_id: str):
    """Bitta filial uchun expiry reminder'larni yaratib yuboradi."""
    from apps.branches.models import Branch
    from apps.vehicles.models import Vehicle
    from apps.reminders.models import SmsReminder, SmsTemplate

    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        logger.warning("Branch %s not found for auto SMS", branch_id)
        return

    today = timezone.now().date()

    for days in [7, 14, 30]:
        target_date = today + timedelta(days=days)
        vehicles = Vehicle.objects.filter(
            branch=branch,
            is_active=True,
            next_inspection_date=target_date,
        ).select_related("client")

        for vehicle in vehicles:
            if not vehicle.client or not vehicle.client.phone:
                continue

            # Takroriy yuborishni oldini olish
            already_sent = SmsReminder.objects.filter(
                vehicle=vehicle,
                trigger_type=SmsReminder.TriggerType.AUTO,
                scheduled_date=today,
                status__in=[SmsReminder.Status.PENDING, SmsReminder.Status.SENT],
            ).exists()
            if already_sent:
                continue

            template = (
                SmsTemplate.objects.filter(branch=branch, is_active=True, deleted_at__isnull=True).first()
                or SmsTemplate.objects.filter(branch__isnull=True, is_active=True, deleted_at__isnull=True).first()
            )
            if not template:
                continue

            try:
                message = template.body.format(
                    name=vehicle.client.full_name or "",
                    plate=vehicle.plate_number or "",
                    days=days,
                )
            except (KeyError, ValueError):
                message = template.body

            reminder = SmsReminder.objects.create(
                vehicle=vehicle,
                branch=branch,
                phone=vehicle.client.phone,
                message=message,
                scheduled_date=today,
                trigger_type=SmsReminder.TriggerType.AUTO,
                inspection_type=SmsReminder.InspectionType.TECHNICAL,
                status=SmsReminder.Status.PENDING,
            )
            # Mavjud send_sms_reminder taskin ishlatamiz
            send_sms_reminder.delay(str(reminder.id))

    logger.info("send_expiry_reminders_for_branch: done for branch %s", branch_id)
