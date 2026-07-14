import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("brand", models.CharField(max_length=100, verbose_name="Marka")),
                ("model", models.CharField(max_length=100, verbose_name="Model")),
                ("year", models.PositiveSmallIntegerField(verbose_name="Ishlab chiqarilgan yil")),
                ("plate_number", models.CharField(max_length=20, verbose_name="Davlat raqami")),
                ("vin", models.CharField(blank=True, max_length=50, verbose_name="VIN kod")),
                ("color", models.CharField(blank=True, max_length=50, verbose_name="Rang")),
                ("engine_type", models.CharField(
                    choices=[
                        ("gasoline", "Benzin"),
                        ("diesel", "Dizel"),
                        ("electric", "Elektr"),
                        ("hybrid", "Gibrid"),
                        ("gas", "Gaz"),
                    ],
                    default="gasoline",
                    max_length=20,
                    verbose_name="Dvigatel turi",
                )),
                ("last_inspection_date", models.DateField(blank=True, null=True, verbose_name="Oxirgi ko'rik sanasi")),
                ("expiry_date", models.DateField(blank=True, null=True, verbose_name="Ko'rik muddati")),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                ("notes", models.TextField(blank=True, verbose_name="Izohlar")),
                ("client", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="vehicles",
                    to="clients.client",
                    verbose_name="Mijoz",
                )),
                ("created_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_vehicles",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="Qo'shgan xodim",
                )),
            ],
            options={
                "verbose_name": "Avtomobil",
                "verbose_name_plural": "Avtomobillar",
                "db_table": "vehicles_vehicle",
                "ordering": ["-created_at"],
                "abstract": False,
                "get_latest_by": "created_at",
            },
        ),
        migrations.AddConstraint(
            model_name="vehicle",
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=["plate_number"],
                name="unique_active_vehicle_plate",
            ),
        ),
    ]
