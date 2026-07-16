import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reminders", "0003_smsreminder_infinireach_message_id_and_more"),
        ("branches", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="smsreminder",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sms_reminders",
                to="branches.branch",
                verbose_name="Filial",
            ),
        ),
        migrations.AddField(
            model_name="smstemplate",
            name="branch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sms_templates",
                to="branches.branch",
                verbose_name="Filial",
                help_text="Null = global shablon (barcha filiallar uchun)",
            ),
        ),
    ]
