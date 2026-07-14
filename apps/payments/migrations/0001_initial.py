import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial"),
        ("vehicles", "0001_initial"),
        ("inspections", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqti")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="O'chirilgan vaqti")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Summa")),
                ("payment_date", models.DateField(verbose_name="To'lov sanasi")),
                ("payment_method", models.CharField(
                    choices=[("cash", "Naqd"), ("card", "Karta"), ("transfer", "O'tkazma")],
                    default="cash",
                    max_length=20,
                    verbose_name="To'lov usuli",
                )),
                ("status", models.CharField(
                    choices=[("pending", "Kutilmoqda"), ("paid", "To'landi"), ("cancelled", "Bekor qilindi")],
                    default="pending",
                    max_length=20,
                    verbose_name="Holat",
                )),
                ("notes", models.TextField(blank=True, verbose_name="Izohlar")),
                ("client", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="payments",
                    to="clients.client",
                    verbose_name="Mijoz",
                )),
                ("vehicle", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="payments",
                    to="vehicles.vehicle",
                    verbose_name="Avtomobil",
                )),
                ("inspection", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="payments",
                    to="inspections.inspection",
                    verbose_name="Ko'rik",
                )),
                ("created_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_payments",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="Qo'shgan xodim",
                )),
            ],
            options={
                "verbose_name": "To'lov",
                "verbose_name_plural": "To'lovlar",
                "db_table": "payments_payment",
                "ordering": ["-payment_date", "-created_at"],
                "abstract": False,
                "get_latest_by": "created_at",
            },
        ),
    ]
