import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inspections", "0003_alter_inspection_options_inspection_inspection_type"),
        ("branches", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inspection",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inspections",
                to="branches.branch",
                verbose_name="Filial",
            ),
        ),
    ]
