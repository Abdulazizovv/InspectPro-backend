from django.db import models


class SiteSettings(models.Model):
    inspection_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=200000,
        verbose_name="Ko'rik narxi (so'm)",
    )

    class Meta:
        db_table = "dashboard_sitesettings"
        verbose_name = "Sayt sozlamalari"
        verbose_name_plural = "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton — faqat bitta yozuv
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"inspection_price": 200000})
        return obj
