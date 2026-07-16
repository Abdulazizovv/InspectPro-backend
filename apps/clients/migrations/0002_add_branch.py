import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0001_initial"),
        ("branches", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="clients",
                to="branches.branch",
                verbose_name="Filial",
            ),
        ),
    ]
