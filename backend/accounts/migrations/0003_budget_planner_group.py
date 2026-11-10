from django.db import migrations

ROLE = "BudgetPlanner"


def seed(apps, schema_editor):
    apps.get_model("auth", "Group").objects.get_or_create(name=ROLE)


def unseed(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name=ROLE).delete()


class Migration(migrations.Migration):
    """Penyusun anggaran: tulis anggaran bulanan, baca realisasi; tanpa jurnal dan pembayaran."""

    dependencies = [("accounts", "0002_seed_groups")]

    operations = [migrations.RunPython(seed, unseed)]
