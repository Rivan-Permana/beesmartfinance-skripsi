from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0006_tarifkatering"),
    ]

    operations = [
        migrations.AddField(
            model_name="tarifkatering",
            name="tarif_jumat",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("10000"),
                max_digits=18,
            ),
        ),
        migrations.AlterField(
            model_name="tarifkatering",
            name="tarif_harian",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Tarif Senin–Kamis (makan siang).",
                max_digits=18,
            ),
        ),
    ]
