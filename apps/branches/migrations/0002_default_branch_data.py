from django.db import migrations


def create_default_branch(apps, schema_editor):
    Branch = apps.get_model("branches", "Branch")
    User = apps.get_model("accounts", "User")
    Client = apps.get_model("clients", "Client")
    Vehicle = apps.get_model("vehicles", "Vehicle")
    Inspection = apps.get_model("inspections", "Inspection")
    SmsReminder = apps.get_model("reminders", "SmsReminder")

    branch, _ = Branch.objects.get_or_create(
        code="MAIN",
        defaults={"name": "Bosh filial", "is_active": True},
    )

    User.objects.filter(branch__isnull=True).update(branch=branch)
    Client.objects.filter(branch__isnull=True).update(branch=branch)
    Vehicle.objects.filter(branch__isnull=True).update(branch=branch)
    Inspection.objects.filter(branch__isnull=True).update(branch=branch)
    SmsReminder.objects.filter(branch__isnull=True).update(branch=branch)


def reverse_default_branch(apps, schema_editor):
    Branch = apps.get_model("branches", "Branch")
    User = apps.get_model("accounts", "User")
    Client = apps.get_model("clients", "Client")
    Vehicle = apps.get_model("vehicles", "Vehicle")
    Inspection = apps.get_model("inspections", "Inspection")
    SmsReminder = apps.get_model("reminders", "SmsReminder")

    try:
        branch = Branch.objects.get(code="MAIN")
        User.objects.filter(branch=branch).update(branch=None)
        Client.objects.filter(branch=branch).update(branch=None)
        Vehicle.objects.filter(branch=branch).update(branch=None)
        Inspection.objects.filter(branch=branch).update(branch=None)
        SmsReminder.objects.filter(branch=branch).update(branch=None)
        branch.delete()
    except Branch.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("branches", "0001_initial"),
        ("accounts", "0004_add_branch"),
        ("clients", "0002_add_branch"),
        ("vehicles", "0003_add_branch"),
        ("inspections", "0004_add_branch"),
        ("reminders", "0005_add_branch"),
    ]

    operations = [
        migrations.RunPython(create_default_branch, reverse_default_branch),
    ]
