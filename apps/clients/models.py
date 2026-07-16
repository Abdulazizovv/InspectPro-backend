from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Client(BaseModel):
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism")
    phone = models.CharField(max_length=20, verbose_name="Telefon raqam")
    passport = models.CharField(max_length=50, blank=True, verbose_name="Pasport seriyasi")
    address = models.TextField(blank=True, verbose_name="Manzil")
    notes = models.TextField(blank=True, verbose_name="Izohlar")
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="clients",
        verbose_name="Filial",
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_clients",
        verbose_name="Qo'shgan xodim",
    )

    class Meta:
        db_table = "clients_client"
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"
        ordering = ["-created_at"]
        constraints = [
            # Bir xil telefon raqam faqat aktiv mijozlarda unique bo'lishi kerak
            models.UniqueConstraint(
                fields=["phone"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_client_phone",
            )
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone})"

    @property
    def vehicle_count(self) -> int:
        try:
            return self.vehicles.filter(deleted_at__isnull=True).count()
        except AttributeError:
            return 0
