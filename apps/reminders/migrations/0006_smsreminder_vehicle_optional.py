import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reminders", "0005_add_branch"),
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="smsreminder",
            name="vehicle",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sms_reminders",
                to="vehicles.vehicle",
                verbose_name="Avtomobil",
            ),
        ),
    ]
