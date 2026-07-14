from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.clients.models import Client


class Vehicle(BaseModel):
    class EngineType(models.TextChoices):
        GASOLINE = "gasoline", "Benzin"
        DIESEL = "diesel", "Dizel"
        ELECTRIC = "electric", "Elektr"
        HYBRID = "hybrid", "Gibrid"
        GAS = "gas", "Gaz"
        METHANE = "metan", "Metan (CNG)"
        PROPANE = "propan", "Propan (LPG)"

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="Mijoz",
    )
    brand = models.CharField(max_length=100, verbose_name="Marka")
    model = models.CharField(max_length=100, verbose_name="Model")
    year = models.PositiveSmallIntegerField(verbose_name="Ishlab chiqarilgan yil")
    plate_number = models.CharField(max_length=20, verbose_name="Davlat raqami")
    vin = models.CharField(max_length=50, blank=True, verbose_name="VIN kod")
    color = models.CharField(max_length=50, blank=True, verbose_name="Rang")
    engine_type = models.CharField(
        max_length=20,
        choices=EngineType.choices,
        default=EngineType.GASOLINE,
        verbose_name="Dvigatel turi",
    )
    last_inspection_date = models.DateField(null=True, blank=True, verbose_name="Oxirgi ko'rik sanasi")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Ko'rik muddati")
    gas_cylinder_expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name="Gaz ballon akt muddati",
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    notes = models.TextField(blank=True, verbose_name="Izohlar")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_vehicles",
        verbose_name="Qo'shgan xodim",
    )

    class Meta:
        db_table = "vehicles_vehicle"
        verbose_name = "Avtomobil"
        verbose_name_plural = "Avtomobillar"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["plate_number"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_vehicle_plate",
            )
        ]

    def __str__(self) -> str:
        return f"{self.brand} {self.model} ({self.plate_number})"

    @property
    def display_name(self) -> str:
        return f"{self.brand} {self.model} {self.year}"
