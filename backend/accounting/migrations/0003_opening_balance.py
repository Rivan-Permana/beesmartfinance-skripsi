from pathlib import Path

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounting", "0002_user_fk")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    (Path(__file__).resolve().parents[3] / "database/schemas/04_opening_balance.sql").read_text(),
                ),
            ],
            state_operations=[
                migrations.AddField("mscoa", "saldo_awal", models.DecimalField(max_digits=18, decimal_places=2, default=0)),
                migrations.AddField("mscoa", "tanggal_saldo_awal", models.DateField(blank=True, null=True)),
            ],
        ),
    ]
