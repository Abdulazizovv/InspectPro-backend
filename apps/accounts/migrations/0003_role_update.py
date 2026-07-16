from django.db import migrations, models


def migrate_roles_forward(apps, schema_editor):
    """
    admin     → super_admin
    manager   → branch_admin
    operator  → operator (o'zgarmaydi)
    """
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="admin").update(role="super_admin")
    User.objects.filter(role="manager").update(role="branch_admin")


def migrate_roles_backward(apps, schema_editor):
    """
    super_admin  → admin
    branch_admin → manager
    """
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="super_admin").update(role="admin")
    User.objects.filter(role="branch_admin").update(role="manager")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_phone_unique_login"),
    ]

    operations = [
        # 1. Avval mavjud qiymatlarni yangilash (choices'dan oldin)
        migrations.RunPython(migrate_roles_forward, migrate_roles_backward),
        # 2. CharField choices'ni yangilash
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("super_admin", "Super Admin"),
                    ("branch_admin", "Filial Admini"),
                    ("operator", "Operator"),
                ],
                default="operator",
                max_length=20,
                verbose_name="Rol",
            ),
        ),
    ]
