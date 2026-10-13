from django.db import migrations, models


def set_kategori_from_komponen(apps, schema_editor):
    TagihanDetail = apps.get_model("operations", "TagihanDetail")
    for d in TagihanDetail.objects.all():
        if d.komponen in ("SPP", "KATERING", "JEMPUTAN"):
            d.kategori = "BULANAN"
        else:
            d.kategori = "LAIN"
        if not d.keterangan:
            d.keterangan = d.komponen
        d.save(update_fields=["kategori", "keterangan"])


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0003_historicalkegiatan_historicalpendaftaransiswa_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tagihandetail",
            name="kategori",
            field=models.CharField(
                choices=[
                    ("BULANAN", "Biaya Bulanan"),
                    ("TAHUNAN", "Biaya Tahunan"),
                    ("LAIN", "Lain-lain"),
                ],
                default="BULANAN",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="tagihandetail",
            name="keterangan",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.RunPython(set_kategori_from_komponen, migrations.RunPython.noop),
    ]
