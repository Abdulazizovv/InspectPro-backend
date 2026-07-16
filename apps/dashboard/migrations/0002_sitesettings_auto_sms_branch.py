from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("branches", "0001_initial"),
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="branch",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="settings",
                to="branches.branch",
                verbose_name="Filial",
                help_text="Null = global sozlamalar (super_admin uchun)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="auto_sms_hour",
            field=models.PositiveSmallIntegerField(default=9, verbose_name="Avtomatik SMS soati (0-23)"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="auto_sms_minute",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="Avtomatik SMS daqiqasi (0-59)"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="auto_sms_enabled",
            field=models.BooleanField(default=True, verbose_name="Avtomatik SMS yoqilgan"),
        ),
    ]
