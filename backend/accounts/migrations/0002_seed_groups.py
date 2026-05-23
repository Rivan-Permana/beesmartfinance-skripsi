from django.db import migrations

ROLES = ["Finance", "SchoolPrincipal", "Administration", "TeacherInCharge"]


def seed_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nama in ROLES:
        Group.objects.get_or_create(name=nama)


def unseed_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=ROLES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(seed_groups, unseed_groups),
    ]
