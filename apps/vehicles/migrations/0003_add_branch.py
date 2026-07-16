import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0002_alter_vehicle_options_and_more"),
        ("branches", "0001_initial"),
    ]

    operations = [
        # Eski global unique constraint olib tashlanadi
        migrations.RemoveConstraint(
            model_name="vehicle",
            name="unique_active_vehicle_plate",
        ),
        # branch FK qo'shiladi
        migrations.AddField(
            model_name="vehicle",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vehicles",
                to="branches.branch",
                verbose_name="Filial",
            ),
        ),
        # Yangi filial + plate_number unique constraint
        migrations.AddConstraint(
            model_name="vehicle",
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=["branch", "plate_number"],
                name="unique_active_vehicle_plate_per_branch",
            ),
        ),
    ]
