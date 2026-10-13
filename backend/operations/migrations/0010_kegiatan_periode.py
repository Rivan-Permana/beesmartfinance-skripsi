from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounting", "0001_initial"),
        ("operations", "0009_kafalah_payroll_anggaran"),
    ]

    operations = [
        migrations.AddField(
            model_name="kegiatan",
            name="periode",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=models.SET_NULL,
                related_name="kegiatan",
                to="accounting.msperiodeakuntansi",
            ),
        ),
        migrations.AddField(
            model_name="historicalkegiatan",
            name="periode",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=models.SET_NULL,
                related_name="+",
                to="accounting.msperiodeakuntansi",
            ),
        ),
    ]
