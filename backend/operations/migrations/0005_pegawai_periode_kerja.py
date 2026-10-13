from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0004_tagihandetail_kategori_keterangan"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalpegawai",
            name="tanggal_mulai_kerja",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="historicalpegawai",
            name="tanggal_selesai_kerja",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pegawai",
            name="tanggal_mulai_kerja",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pegawai",
            name="tanggal_selesai_kerja",
            field=models.DateField(blank=True, null=True),
        ),
    ]
