from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inspections", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="inspection",
            name="amount",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Ko'rik narxi (so'm)"),
        ),
    ]
