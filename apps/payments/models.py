from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.clients.models import Client
from apps.vehicles.models import Vehicle
from apps.inspections.models import Inspection


class Payment(BaseModel):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Naqd"
        CARD = "card", "Karta"
        TRANSFER = "transfer", "O'tkazma"

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        PAID = "paid", "To'landi"
        CANCELLED = "cancelled", "Bekor qilindi"

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Mijoz",
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Avtomobil",
    )
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Ko'rik",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Summa")
    payment_date = models.DateField(verbose_name="To'lov sanasi")
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name="To'lov usuli",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Holat",
    )
    notes = models.TextField(blank=True, verbose_name="Izohlar")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_payments",
        verbose_name="Qo'shgan xodim",
    )

    class Meta:
        db_table = "payments_payment"
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ["-payment_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.client} — {self.amount} ({self.payment_date})"
