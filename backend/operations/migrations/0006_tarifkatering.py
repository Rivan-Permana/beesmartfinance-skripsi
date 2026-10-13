from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0005_pegawai_periode_kerja"),
    ]

    operations = [
        migrations.CreateModel(
            name="TarifKatering",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("periode_bulan", models.PositiveSmallIntegerField()),
                ("periode_tahun", models.PositiveSmallIntegerField()),
                ("tarif_harian", models.DecimalField(decimal_places=2, max_digits=18)),
            ],
            options={
                "ordering": ["-periode_tahun", "-periode_bulan"],
                "unique_together": {("periode_bulan", "periode_tahun")},
            },
        ),
    ]
