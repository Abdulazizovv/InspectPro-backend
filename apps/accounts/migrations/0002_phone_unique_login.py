from django.db import migrations, models


def assign_temp_phones(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    counter = 900_000_000
    for user in User.objects.filter(phone=""):
        user.phone = f"+998{counter}"
        user.save(update_fields=["phone"])
        counter += 1


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        # 1. Mavjud bo'sh phone'larga vaqtinchalik unique raqam berish
        migrations.RunPython(assign_temp_phones, migrations.RunPython.noop),
        # 2. phone → unique=True, blank=False
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(max_length=20, unique=True, verbose_name="Telefon"),
        ),
    ]
