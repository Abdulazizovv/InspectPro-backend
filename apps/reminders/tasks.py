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


GAS_ENGINE_TYPES = ("metan", "propan")
NOTIFY_DAYS = [30, 14, 7]


def _get_expiry_template(days_ahead, inspection_type_value, branch):
    """Return the most specific active template available to a branch.

    A branch template must take precedence over a global fallback.  Without
    this scope, the first matching template from another branch could be used
    for an automatic SMS.
    """
    from .models import SmsTemplate

    base_filters = {
        "days_before": days_ahead,
        "is_active": True,
        "deleted_at__isnull": True,
    }
    for template_branch in (branch, None):
        template = SmsTemplate.objects.filter(
            **base_filters,
            branch=template_branch,
            inspection_type=inspection_type_value,
        ).first()
        if template:
            return template
    for template_branch in (branch, None):
        template = SmsTemplate.objects.filter(
            **base_filters,
            branch=template_branch,
            inspection_type="any",
        ).first()
        if template:
            return template
    return None


def _create_expiry_reminder(vehicle, phone, days_ahead, target_date, inspection_type_value, default_msg, today):
    """
    Bitta avtomobil uchun SmsReminder yaratadi (agar shu vehicle+inspection_type uchun
    bugungi kunga allaqachon pending/sent AUTO reminder bo'lmasa). Yaratilgan bo'lsa 1,
    aks holda 0 qaytaradi.
    """
    from .models import SmsReminder

    already_scheduled = SmsReminder.objects.filter(
        vehicle=vehicle,
        inspection_type=inspection_type_value,
        scheduled_date=today,
        status__in=[SmsReminder.Status.PENDING, SmsReminder.Status.SENT],
        trigger_type=SmsReminder.TriggerType.AUTO,
    ).exists()

    if already_scheduled:
        return 0

    template = _get_expiry_template(days_ahead, inspection_type_value, vehicle.branch)

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


def _process_expiry_reminders(branch=None):
    """
    Texnik ko'rik (expiry_date) va gaz ballon akt (gas_cylinder_expiry_date) muddati
    30/14/7 kun qolgan avtomobillar uchun SmsReminder yaratadi va yuborishga navbatga qo'yadi.

    `branch` berilsa — faqat shu filialning avtomobillari qamrab olinadi (filial o'z
    auto_sms_hour vaqtida SMS yuborishi uchun). `branch=None` bo'lsa — barcha filiallar
    (orqaga moslik / qo'lda umumiy chaqiruv uchun, beat jadvalida endi ishlatilmaydi).

    Dedup: har bir vehicle+inspection_type uchun bugungi kunga (scheduled_date=today)
    AUTO turidagi pending/sent reminder mavjud bo'lsa, qayta yaratilmaydi. Bitta vehicle'ning
    expiry_date/gas_cylinder_expiry_date qiymati bitta sana bo'lgani uchun, [30, 14, 7]
    tsiklidagi faqat bitta iteratsiya shu vehicle'ga mos keladi — shuning uchun bu dedup
    bir necha marta chaqirilsa ham (masalan bir kunda bir nechta filial tekshiruvi yoki
    task qayta ishga tushishi) xavfsiz.
    """
    from apps.vehicles.models import Vehicle

    today = date.today()
    created_count = 0

    for days_ahead in NOTIFY_DAYS:
        target_date = today + timedelta(days=days_ahead)

        # 1. Texnik ko'rik uchun eslatmalar
        tech_qs = Vehicle.objects.active().filter(
            expiry_date=target_date,
            is_active=True,
        )
        if branch is not None:
            tech_qs = tech_qs.filter(branch=branch)

        for vehicle in tech_qs.select_related("client"):
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
            created_count += _create_expiry_reminder(
                vehicle, phone, days_ahead, target_date, "technical", default_msg, today
            )

        # 2. Gaz ballon akt uchun eslatmalar (faqat metan/propan)
        gas_qs = Vehicle.objects.active().filter(
            gas_cylinder_expiry_date=target_date,
            engine_type__in=GAS_ENGINE_TYPES,
            is_active=True,
        )
        if branch is not None:
            gas_qs = gas_qs.filter(branch=branch)

        for vehicle in gas_qs.select_related("client"):
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
            created_count += _create_expiry_reminder(
                vehicle, phone, days_ahead, target_date, "gas_cylinder", default_msg, today
            )

    return created_count


@shared_task
def schedule_expiry_reminders():
    """
    BARCHA filiallar uchun expiry reminder yaratadi (global, filial soatlarini hisobga
    olmaydi). Celery beat jadvalidan OLIB TASHLANGAN — endi har filial o'z auto_sms_hour
    vaqtida SMS olishi uchun `check_and_send_auto_sms` / `send_expiry_reminders_for_branch`
    ishlatiladi. Bu funksiya faqat qo'lda chaqirish (masalan management command yoki shell)
    uchun qoldirilgan.
    """
    created_count = _process_expiry_reminders(branch=None)
    logger.info("schedule_expiry_reminders: created %d reminders", created_count)
    return created_count


@shared_task
def check_and_send_auto_sms():
    """Run every minute and dispatch each branch at its configured local time."""
    from apps.dashboard.models import SiteSettings
    from apps.branches.models import Branch

    now = timezone.localtime()

    for branch in Branch.objects.filter(is_active=True):
        try:
            settings_obj = SiteSettings.get_for_branch(branch)
            if not settings_obj.auto_sms_enabled:
                continue
            if (
                settings_obj.auto_sms_hour == now.hour
                and settings_obj.auto_sms_minute == now.minute
            ):
                send_expiry_reminders_for_branch.delay(str(branch.id))
                logger.info("Triggered auto SMS for branch %s at %02d:%02d", branch.id, now.hour, now.minute)
        except Exception as e:
            logger.error("Auto SMS check error for branch %s: %s", branch.id, e)


@shared_task
def send_expiry_reminders_for_branch(branch_id: str):
    """
    Bitta filial uchun expiry reminder'larni (texnik ko'rik + gaz ballon akt) yaratib
    yuboradi. `check_and_send_auto_sms` tomonidan filial o'zining auto_sms_hour vaqtida
    chaqiriladi. Umumiy mantiq `_process_expiry_reminders`da (SmsTemplate.render() orqali).
    """
    from apps.branches.models import Branch

    try:
        branch = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        logger.warning("Branch %s not found for auto SMS", branch_id)
        return

    created_count = _process_expiry_reminders(branch=branch)
    logger.info(
        "send_expiry_reminders_for_branch: created %d reminders for branch %s",
        created_count, branch_id,
    )
    return created_count
