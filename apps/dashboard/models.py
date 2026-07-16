from django.db import models


class SiteSettings(models.Model):
    inspection_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=200000,
        verbose_name="Ko'rik narxi (so'm)",
    )
    branch = models.OneToOneField(
        "branches.Branch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="settings",
        verbose_name="Filial",
        help_text="Null = global sozlamalar (super_admin uchun)",
    )
    auto_sms_hour = models.PositiveSmallIntegerField(
        default=9,
        verbose_name="Avtomatik SMS soati (0-23)",
    )
    auto_sms_minute = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Avtomatik SMS daqiqasi (0-59)",
    )
    auto_sms_enabled = models.BooleanField(
        default=True,
        verbose_name="Avtomatik SMS yoqilgan",
    )

    class Meta:
        db_table = "dashboard_sitesettings"
        verbose_name = "Sayt sozlamalari"
        verbose_name_plural = "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        # Agar branch yo'q bo'lsa (global settings) — singleton (pk=1)
        if self.branch_id is None and not self.pk:
            self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Global (branch=None) settings — singleton."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"inspection_price": 200000})
        return obj

    @classmethod
    def get_for_branch(cls, branch):
        """Filialga tegishli settings. Agar yo'q bo'lsa yangi yaratadi."""
        obj, _ = cls.objects.get_or_create(branch=branch)
        return obj
