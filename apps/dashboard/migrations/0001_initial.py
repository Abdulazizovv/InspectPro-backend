from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("inspection_price", models.DecimalField(decimal_places=2, default=200000, max_digits=12, verbose_name="Ko'rik narxi (so'm)")),
            ],
            options={
                "verbose_name": "Sayt sozlamalari",
                "verbose_name_plural": "Sayt sozlamalari",
                "db_table": "dashboard_sitesettings",
            },
        ),
    ]
