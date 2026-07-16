from datetime import timedelta

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.utils import timezone

from apps.common.mixins import BranchScopedQuerysetMixin
from apps.common.activity import log_activity
from apps.accounts.models import ActivityLog
from .filters import SmsReminderFilter
from .models import SmsReminder, SmsTemplate
from .serializers import (
    SmsReminderDetailSerializer,
    SmsReminderListSerializer,
    SmsReminderWriteSerializer,
    SmsTemplateSerializer,
)
from .tasks import schedule_expiry_reminders, send_sms_reminder
from apps.vehicles.models import Vehicle


@extend_schema_view(
    list=extend_schema(summary="SMS shablonlar ro'yxati", tags=["Reminders"]),
    retrieve=extend_schema(summary="SMS shablon ma'lumotlari", tags=["Reminders"]),
    create=extend_schema(summary="Yangi SMS shablon qo'shish", tags=["Reminders"]),
    update=extend_schema(summary="SMS shablonni yangilash", tags=["Reminders"]),
    partial_update=extend_schema(summary="SMS shablonni qisman yangilash", tags=["Reminders"]),
    destroy=extend_schema(summary="SMS shablonni o'chirish", tags=["Reminders"]),
)
class SmsTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SmsTemplateSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "body"]
    ordering_fields = ["days_before", "name", "created_at"]
    ordering = ["days_before", "name"]

    def get_queryset(self):
        return SmsTemplate.objects.active()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(summary="SMS eslatmalar ro'yxati", tags=["Reminders"]),
    retrieve=extend_schema(summary="SMS eslatma ma'lumotlari", tags=["Reminders"]),
    create=extend_schema(summary="Yangi SMS eslatma qo'shish", tags=["Reminders"]),
    update=extend_schema(summary="SMS eslatmani yangilash", tags=["Reminders"]),
    partial_update=extend_schema(summary="SMS eslatmani qisman yangilash", tags=["Reminders"]),
    destroy=extend_schema(summary="SMS eslatmani o'chirish", tags=["Reminders"]),
)
class SmsReminderViewSet(BranchScopedQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SmsReminderFilter
    search_fields = ["vehicle__plate_number", "vehicle__client__full_name", "phone"]
    ordering_fields = ["scheduled_date", "sent_at", "status", "created_at"]
    ordering = ["-scheduled_date"]

    def get_queryset(self):
        qs = SmsReminder.objects.active().select_related(
            "vehicle", "vehicle__client", "created_by", "branch"
        )
        return self._apply_branch_filter(qs)

    def get_serializer_class(self):
        if self.action == "list":
            return SmsReminderListSerializer
        if self.action in ("create", "update", "partial_update"):
            return SmsReminderWriteSerializer
        return SmsReminderDetailSerializer

    def perform_create(self, serializer):
        user = self.request.user
        branch = getattr(user, "branch", None)
        if user.role == "super_admin":
            branch_id = self.request.data.get("branch") or self.request.query_params.get("branch")
            if branch_id:
                from apps.branches.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    pass
        instance = serializer.save(branch=branch, created_by=user)
        if instance.trigger_type == "manual":
            log_activity(
                user,
                ActivityLog.Action.SMS_SENT_MANUAL,
                instance,
                self.request,
                metadata={"phone": instance.phone or "", "message": (instance.message or "")[:100]},
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="SMS eslatmani hozir yuborish", tags=["Reminders"])
    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        reminder = self.get_object()
        if reminder.status == SmsReminder.Status.SENT:
            return Response(
                {"detail": "Bu eslatma allaqachon yuborilgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reminder.status = SmsReminder.Status.PENDING
        reminder.error_message = ""
        reminder.save(update_fields=["status", "error_message", "updated_at"])
        send_sms_reminder.delay(str(reminder.id))
        return Response({"detail": "SMS yuborish navbatga qo'yildi."})

    @extend_schema(summary="Muddati tugayotgan avtomobillar uchun avtomatik eslatmalar", tags=["Reminders"])
    @action(detail=False, methods=["post"])
    def schedule_auto(self, request):
        task = schedule_expiry_reminders.delay()
        return Response({"detail": "Avtomatik rejalashtirish navbatga qo'yildi.", "task_id": task.id})

    @extend_schema(summary="Texnik ko'rik va gaz ballon muddati yaqinlashayotgan avtomobillar", tags=["Reminders"])
    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        from django.db.models import Q
        today = timezone.now().date()
        end_date = today + timedelta(days=30)

        user = request.user
        branch_filter = {} if user.role == "super_admin" else {"branch": user.branch}
        branch_id = request.query_params.get("branch")
        if user.role == "super_admin" and branch_id:
            branch_filter = {"branch_id": branch_id}

        # Texnik ko'rik muddati yaqinlashayotgan avtomobillar
        tech_vehicles = Vehicle.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=end_date,
            deleted_at__isnull=True,
            is_active=True,
            **branch_filter,
        ).select_related("client").order_by("expiry_date")

        # Gaz ballon muddati yaqinlashayotgan avtomobillar (faqat metan/propan)
        gas_vehicles = Vehicle.objects.filter(
            gas_cylinder_expiry_date__gte=today,
            gas_cylinder_expiry_date__lte=end_date,
            engine_type__in=["metan", "propan"],
            deleted_at__isnull=True,
            is_active=True,
            **branch_filter,
        ).select_related("client").order_by("gas_cylinder_expiry_date")

        result = []

        for v in tech_vehicles:
            days_left = (v.expiry_date - today).days
            existing = SmsReminder.objects.filter(
                vehicle=v,
                inspection_type="technical",
                status__in=[SmsReminder.Status.PENDING, SmsReminder.Status.SENT],
                deleted_at__isnull=True,
            ).order_by("-created_at").first()

            result.append({
                "vehicle_id": str(v.id),
                "plate_number": v.plate_number,
                "brand": v.brand,
                "model": v.model,
                "expiry_date": v.expiry_date.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "inspection_type": "technical",
                "client_name": v.client.full_name if v.client else "",
                "client_phone": v.client.phone if v.client else "",
                "existing_reminder": {
                    "id": str(existing.id),
                    "status": existing.status,
                } if existing else None,
            })

        for v in gas_vehicles:
            days_left = (v.gas_cylinder_expiry_date - today).days
            existing = SmsReminder.objects.filter(
                vehicle=v,
                inspection_type="gas_cylinder",
                status__in=[SmsReminder.Status.PENDING, SmsReminder.Status.SENT],
                deleted_at__isnull=True,
            ).order_by("-created_at").first()

            result.append({
                "vehicle_id": str(v.id),
                "plate_number": v.plate_number,
                "brand": v.brand,
                "model": v.model,
                "expiry_date": v.gas_cylinder_expiry_date.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "inspection_type": "gas_cylinder",
                "client_name": v.client.full_name if v.client else "",
                "client_phone": v.client.phone if v.client else "",
                "existing_reminder": {
                    "id": str(existing.id),
                    "status": existing.status,
                } if existing else None,
            })

        # days_left bo'yicha tartiblash
        result.sort(key=lambda x: x["days_left"])
        return Response(result)

    @extend_schema(summary="Kelayotgan avtomatik SMS jadvali", tags=["Reminders"])
    @action(detail=False, methods=["get"])
    def schedule_preview(self, request):
        """
        Keyingi 30 kun ichida avtomatik SMS borishi rejalashtirilgan avtomobillar.
        7, 14, 30 kun oldin eslatma boradi.
        """
        today = timezone.now().date()
        notify_days = [7, 14, 30]
        GAS_ENGINE_TYPES = ("metan", "propan")

        user = request.user
        branch_filter = {} if user.role == "super_admin" else {"branch": user.branch}
        branch_id = request.query_params.get("branch")
        if user.role == "super_admin" and branch_id:
            branch_filter = {"branch_id": branch_id}

        groups = []

        for days_ahead in notify_days:
            date_from = today + timedelta(days=days_ahead)
            date_to = today + timedelta(days=days_ahead + 30)

            # Texnik ko'rik
            tech_vehicles = Vehicle.objects.filter(
                expiry_date__gte=date_from,
                expiry_date__lte=date_to,
                is_active=True,
                deleted_at__isnull=True,
                **branch_filter,
            ).select_related("client").order_by("expiry_date")

            for v in tech_vehicles:
                if not v.client or not v.client.phone:
                    continue
                sms_date = v.expiry_date - timedelta(days=days_ahead)
                already = SmsReminder.objects.filter(
                    vehicle=v, inspection_type="technical",
                    scheduled_date=sms_date,
                    status__in=["pending", "sent"],
                    trigger_type="auto",
                    deleted_at__isnull=True,
                ).exists()
                groups.append({
                    "sms_date": sms_date.strftime("%Y-%m-%d"),
                    "days_before_expiry": days_ahead,
                    "vehicle_id": str(v.id),
                    "plate_number": v.plate_number,
                    "brand": v.brand,
                    "model": v.model,
                    "client_name": v.client.full_name,
                    "inspection_type": "technical",
                    "expiry_date": v.expiry_date.strftime("%Y-%m-%d"),
                    "already_scheduled": already,
                })

            # Gaz ballon
            gas_vehicles = Vehicle.objects.filter(
                gas_cylinder_expiry_date__gte=date_from,
                gas_cylinder_expiry_date__lte=date_to,
                engine_type__in=GAS_ENGINE_TYPES,
                is_active=True,
                deleted_at__isnull=True,
                **branch_filter,
            ).select_related("client").order_by("gas_cylinder_expiry_date")

            for v in gas_vehicles:
                if not v.client or not v.client.phone:
                    continue
                sms_date = v.gas_cylinder_expiry_date - timedelta(days=days_ahead)
                already = SmsReminder.objects.filter(
                    vehicle=v, inspection_type="gas_cylinder",
                    scheduled_date=sms_date,
                    status__in=["pending", "sent"],
                    trigger_type="auto",
                    deleted_at__isnull=True,
                ).exists()
                groups.append({
                    "sms_date": sms_date.strftime("%Y-%m-%d"),
                    "days_before_expiry": days_ahead,
                    "vehicle_id": str(v.id),
                    "plate_number": v.plate_number,
                    "brand": v.brand,
                    "model": v.model,
                    "client_name": v.client.full_name,
                    "inspection_type": "gas_cylinder",
                    "expiry_date": v.gas_cylinder_expiry_date.strftime("%Y-%m-%d"),
                    "already_scheduled": already,
                })

        groups.sort(key=lambda x: x["sms_date"])
        return Response(groups)

    @extend_schema(summary="SMS eslatmalar oylik statistikasi (global)", tags=["Reminders"])
    @action(detail=False, methods=["get"])
    def stats(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Global limit — barcha filiallar bo'yicha umumiy hisob
        month_sent = SmsReminder.objects.filter(
            status=SmsReminder.Status.SENT,
            sent_at__gte=month_start,
            deleted_at__isnull=True,
        ).count()

        total_pending = SmsReminder.objects.filter(
            status=SmsReminder.Status.PENDING,
            deleted_at__isnull=True,
        ).count()

        total_failed = SmsReminder.objects.filter(
            status=SmsReminder.Status.FAILED,
            deleted_at__isnull=True,
        ).count()

        return Response({
            "month_sent": month_sent,
            "month_limit": 100,
            "total_pending": total_pending,
            "total_failed": total_failed,
        })
