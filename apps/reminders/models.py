from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.vehicles.models import Vehicle


class SmsTemplate(BaseModel):
    class InspectionType(models.TextChoices):
        TECHNICAL = "technical", "Texnik ko'rik"
        GAS_CYLINDER = "gas_cylinder", "Gaz ballon akt"
        ANY = "any", "Har ikkisi"

    name = models.CharField(max_length=100, unique=True, verbose_name="Shablon nomi")
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

    def __str__(self) -> str:
        return self.name

    def render(self, **kwargs) -> str:
        try:
            return self.body.format(**kwargs)
        except KeyError:
            return self.body


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
        return f"{self.vehicle.plate_number} → {self.phone} ({self.get_status_display()})"
