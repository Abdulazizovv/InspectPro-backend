import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("full_name", models.CharField(max_length=255, verbose_name="To'liq ism")),
                ("phone", models.CharField(max_length=20, verbose_name="Telefon raqam")),
                ("passport", models.CharField(blank=True, max_length=50, verbose_name="Pasport seriyasi")),
                ("address", models.TextField(blank=True, verbose_name="Manzil")),
                ("notes", models.TextField(blank=True, verbose_name="Izohlar")),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                ("created_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_clients",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="Qo'shgan xodim",
                )),
            ],
            options={
                "verbose_name": "Mijoz",
                "verbose_name_plural": "Mijozlar",
                "db_table": "clients_client",
                "ordering": ["-created_at"],
                "abstract": False,
                "get_latest_by": "created_at",
            },
        ),
        migrations.AddConstraint(
            model_name="client",
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=["phone"],
                name="unique_active_client_phone",
            ),
        ),
    ]
