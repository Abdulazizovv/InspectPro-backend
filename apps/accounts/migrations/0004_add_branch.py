import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_role_update"),
        ("branches", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="users",
                to="branches.branch",
                verbose_name="Filial",
            ),
        ),
    ]
