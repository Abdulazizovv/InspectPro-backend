import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reminders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SmsTemplate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Shablon nomi")),
                ("body", models.TextField(verbose_name="Xabar matni")),
                ("days_before", models.PositiveIntegerField(
                    blank=True, null=True,
                    verbose_name="Necha kun oldin (avtomatik uchun)",
                    help_text="Null = faqat qo'lda ishlatiladi. 7/14/30 = avtomatik eslatma uchun.",
                )),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
            ],
            options={
                "verbose_name": "SMS Shablon",
                "verbose_name_plural": "SMS Shablonlar",
                "db_table": "reminders_smstemplate",
                "ordering": ["days_before", "name"],
                "abstract": False,
            },
        ),
    ]
