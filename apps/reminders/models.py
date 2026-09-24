from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.vehicles.models import Vehicle


# Canonical placeholders are shown in the UI.  The short names remain for
# compatibility with templates that users created before the standardisation.
SMS_TEMPLATE_VARIABLES = frozenset({
    "client_name", "plate_number", "brand", "model", "expiry_date", "days_left",
    "name", "full_name", "client", "plate", "car_number", "days", "date",
    "next_inspection_date",
})


class _TemplateValues(dict):
    """Keep an unknown placeholder visible instead of discarding the whole SMS."""

    def __missing__(self, key):
        return "{" + key + "}"


class SmsTemplate(BaseModel):
    class InspectionType(models.TextChoices):
        TECHNICAL = "technical", "Texnik ko'rik"
        GAS_CYLINDER = "gas_cylinder", "Gaz ballon akt"
        ANY = "any", "Har ikkisi"

    name = models.CharField(max_length=100, verbose_name="Shablon nomi")
    body = models.TextField(verbose_name="Xabar matni")
    days_before = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Necha kun oldin (avtomatik uchun)",
        help_text="Null = faqat qo'lda ishlatiladi. 7/14/30 = avtomatik eslatma uchun.",
    )
    inspection_type = models.CharField(
        max_length=20,
        choices=InspectionType.choices,
        default=InspectionType.ANY,
        verbose_name="Ko'rik turi",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sms_templates",
        verbose_name="Filial",
        help_text="Null = global shablon (barcha filiallar uchun)",
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        db_table = "reminders_smstemplate"
        verbose_name = "SMS Shablon"
        verbose_name_plural = "SMS Shablonlar"
        ordering = ["days_before", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_smstemplate_branch_name",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def render(self, **kwargs) -> str:
        # Normalize all values to str before formatting
        for k, v in list(kwargs.items()):
            kwargs[k] = str(v) if v is not None else ""
        # Support aliases so templates work regardless of key name used
        cn = kwargs.get("client_name", "")
        kwargs.setdefault("name", cn)
        kwargs.setdefault("full_name", cn)
        kwargs.setdefault("client", cn)
        pn = kwargs.get("plate_number", "")
        kwargs.setdefault("plate", pn)
        kwargs.setdefault("car_number", pn)
        dl = kwargs.get("days_left", "")
        kwargs.setdefault("days", dl)
        ed = kwargs.get("expiry_date", "")
        kwargs.setdefault("date", ed)
        kwargs.setdefault("next_inspection_date", ed)
        return self.body.format_map(_TemplateValues(kwargs))


class SmsReminder(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        SENT = "sent", "Yuborildi"
        FAILED = "failed", "Xatolik"
        CANCELLED = "cancelled", "Bekor qilindi"

    class TriggerType(models.TextChoices):
        MANUAL = "manual", "Qo'lda"
        AUTO = "auto", "Avtomatik"

    class InspectionType(models.TextChoices):
        TECHNICAL = "technical", "Texnik ko'rik"
        GAS_CYLINDER = "gas_cylinder", "Gaz ballon akt"

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sms_reminders",
        verbose_name="Avtomobil",
    )
    phone = models.CharField(max_length=20, verbose_name="Telefon raqami")
    message = models.TextField(verbose_name="Xabar matni")
    scheduled_date = models.DateField(verbose_name="Rejalashtirilgan sana")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Yuborilgan vaqt")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Holat",
    )
    trigger_type = models.CharField(
        max_length=10,
        choices=TriggerType.choices,
        default=TriggerType.MANUAL,
        verbose_name="Tur",
    )
    inspection_type = models.CharField(
        max_length=20,
        choices=InspectionType.choices,
        default=InspectionType.TECHNICAL,
        verbose_name="Ko'rik turi",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sms_reminders",
        verbose_name="Filial",
    )
    error_message = models.TextField(blank=True, verbose_name="Xato xabari")
    infinireach_message_id = models.CharField(
        max_length=100, blank=True, default="", verbose_name="InfiniReach Message ID"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_reminders",
        verbose_name="Qo'shgan xodim",
    )

    class Meta:
        db_table = "reminders_smsreminder"
        verbose_name = "SMS Eslatma"
        verbose_name_plural = "SMS Eslatmalar"
        ordering = ["-scheduled_date", "-created_at"]

    def __str__(self) -> str:
        plate = self.vehicle.plate_number if self.vehicle else "—"
        return f"{plate} → {self.phone} ({self.get_status_display()})"
