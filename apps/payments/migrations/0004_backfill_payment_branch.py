from django.db import migrations


def backfill_payment_branch(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    Branch = apps.get_model("branches", "Branch")

    default_branch = None

    for payment in Payment.objects.filter(branch__isnull=True).select_related("client"):
        branch = getattr(payment.client, "branch_id", None) and payment.client.branch
        if branch is None:
            if default_branch is None:
                default_branch, _ = Branch.objects.get_or_create(
                    code="MAIN",
                    defaults={"name": "Bosh filial", "is_active": True},
                )
            branch = default_branch
        payment.branch = branch
        payment.save(update_fields=["branch"])


def reverse_backfill(apps, schema_editor):
    # Orqaga qaytarishning ma'nosi yo'q — branch qiymatini tozalab qo'ymaymiz,
    # chunki bu ma'lumot yo'qotilishiga olib keladi.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("branches", "0002_default_branch_data"),
        ("payments", "0003_payment_branch"),
    ]

    operations = [
        migrations.RunPython(backfill_payment_branch, reverse_backfill),
    ]
