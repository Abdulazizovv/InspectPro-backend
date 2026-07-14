import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("vehicles", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Inspection",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("inspection_date", models.DateField(verbose_name="Ko'rik sanasi")),
                ("expiry_date", models.DateField(blank=True, null=True, verbose_name="Yangi muddat")),
                ("status", models.CharField(
                    choices=[
                        ("scheduled", "Rejalashtirilgan"),
                        ("passed", "O'tdi"),
                        ("failed", "O'tmadi"),
                    ],
                    default="scheduled",
                    max_length=20,
                    verbose_name="Holat",
                )),
                ("notes", models.TextField(blank=True, verbose_name="Izohlar")),
                ("vehicle", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="inspections",
                    to="vehicles.vehicle",
                    verbose_name="Avtomobil",
                )),
                ("inspector", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="inspected",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="Tekshiruvchi",
                )),
                ("created_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_inspections",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="Qo'shgan xodim",
                )),
            ],
            options={
                "verbose_name": "Ko'rik",
                "verbose_name_plural": "Ko'riklar",
                "db_table": "inspections_inspection",
                "ordering": ["-inspection_date", "-created_at"],
                "abstract": False,
                "get_latest_by": "created_at",
            },
        ),
    ]
