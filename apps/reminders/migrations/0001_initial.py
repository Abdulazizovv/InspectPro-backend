import uuid
import django.db.models.deletion
import django.utils.timezone
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
            name="SmsReminder",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("phone", models.CharField(max_length=20, verbose_name="Telefon raqami")),
                ("message", models.TextField(verbose_name="Xabar matni")),
                ("scheduled_date", models.DateField(verbose_name="Rejalashtirilgan sana")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="Yuborilgan vaqt")),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Kutilmoqda"),
                        ("sent", "Yuborildi"),
                        ("failed", "Xatolik"),
                        ("cancelled", "Bekor qilindi"),
                    ],
                    default="pending",
                    max_length=20,
                    verbose_name="Holat",
                )),
                ("trigger_type", models.CharField(
                    choices=[("manual", "Qo'lda"), ("auto", "Avtomatik")],
                    default="manual",
                    max_length=10,
                    verbose_name="Tur",
                )),
                ("error_message", models.TextField(blank=True, verbose_name="Xato xabari")),
                ("created_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_reminders",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="Qo'shgan xodim",
                )),
                ("vehicle", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="sms_reminders",
                    to="vehicles.vehicle",
                    verbose_name="Avtomobil",
                )),
            ],
            options={
                "verbose_name": "SMS Eslatma",
                "verbose_name_plural": "SMS Eslatmalar",
                "db_table": "reminders_smsreminder",
                "ordering": ["-scheduled_date", "-created_at"],
                "abstract": False,
            },
        ),
    ]
