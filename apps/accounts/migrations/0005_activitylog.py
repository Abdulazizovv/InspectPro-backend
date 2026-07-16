import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_add_branch"),
        ("branches", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("action", models.CharField(
                    choices=[
                        ("vehicle_created", "Avtomobil qo'shdi"),
                        ("vehicle_updated", "Avtomobil ma'lumotini o'zgartirdi"),
                        ("vehicle_deleted", "Avtomobilni o'chirdi"),
                        ("client_created", "Mijoz qo'shdi"),
                        ("client_updated", "Mijoz ma'lumotini o'zgartirdi"),
                        ("client_deleted", "Mijozni o'chirdi"),
                        ("inspection_created", "Ko'rik qo'shdi"),
                        ("inspection_updated", "Ko'rik ma'lumotini o'zgartirdi"),
                        ("sms_sent_manual", "Qo'lda SMS jo'natdi"),
                        ("login", "Tizimga kirdi"),
                        ("logout", "Tizimdan chiqdi"),
                    ],
                    max_length=50,
                )),
                ("target_type", models.CharField(blank=True, max_length=50)),
                ("target_id", models.CharField(blank=True, max_length=64)),
                ("target_repr", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("branch", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    to="branches.branch",
                )),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="activities",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "db_table": "accounts_activitylog",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["user", "-created_at"], name="accounts_ac_user_id_idx"),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["branch", "-created_at"], name="accounts_ac_branch_idx"),
        ),
    ]
