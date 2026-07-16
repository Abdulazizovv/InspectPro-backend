import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Branch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("name", models.CharField(max_length=200, verbose_name="Filial nomi")),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="Kod")),
                ("address", models.TextField(blank=True, verbose_name="Manzil")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="Telefon")),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_branches",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Yaratgan xodim",
                    ),
                ),
            ],
            options={
                "verbose_name": "Filial",
                "verbose_name_plural": "Filiallar",
                "db_table": "branches_branch",
                "ordering": ["name"],
            },
        ),
    ]
