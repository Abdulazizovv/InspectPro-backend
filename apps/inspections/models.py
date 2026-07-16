from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.vehicles.models import Vehicle


class Inspection(BaseModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Rejalashtirilgan"
        PASSED = "passed", "O'tdi"
        FAILED = "failed", "O'tmadi"

    class InspectionType(models.TextChoices):
        TECHNICAL = "technical", "Texnik ko'rik"
        GAS_CYLINDER = "gas_cylinder", "Gaz ballon akt"

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="inspections",
        verbose_name="Avtomobil",
    )
    inspection_type = models.CharField(
        max_length=20,
        choices=InspectionType.choices,
        default=InspectionType.TECHNICAL,
        verbose_name="Ko'rik turi",
    )
    inspection_date = models.DateField(verbose_name="Ko'rik sanasi")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Yangi muddat")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name="Holat",
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspected",
        verbose_name="Tekshiruvchi",
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name="Ko'rik narxi (so'm)",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inspections",
        verbose_name="Filial",
    )
    notes = models.TextField(blank=True, verbose_name="Izohlar")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_inspections",
        verbose_name="Qo'shgan xodim",
    )

    class Meta:
        db_table = "inspections_inspection"
        verbose_name = "Ko'rik"
        verbose_name_plural = "Ko'riklar"
        ordering = ["-inspection_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.vehicle} — {self.inspection_date} ({self.get_status_display()})"
