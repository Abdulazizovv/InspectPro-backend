from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Branch(BaseModel):
    name = models.CharField(max_length=200, verbose_name="Filial nomi")
    code = models.CharField(max_length=20, unique=True, verbose_name="Kod")
    address = models.TextField(blank=True, verbose_name="Manzil")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_branches",
        verbose_name="Yaratgan xodim",
    )

    class Meta:
        db_table = "branches_branch"
        verbose_name = "Filial"
        verbose_name_plural = "Filiallar"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.code:
            import uuid
            self.code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def employees_count(self) -> int:
        return self.users.filter(is_active=True).count()

    @property
    def clients_count(self) -> int:
        return self.clients.filter(deleted_at__isnull=True).count()
