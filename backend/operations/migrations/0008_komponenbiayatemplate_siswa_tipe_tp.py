from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0007_tarifkatering_jumat"),
    ]

    operations = [
        migrations.AddField(
            model_name="siswa",
            name="tipe_tp",
            field=models.CharField(
                choices=[("baru", "Siswa Baru"), ("lama", "Daftar Ulang")],
                default="baru",
                help_text="Status TP untuk komponen biaya tahunan (baru vs daftar ulang).",
                max_length=5,
            ),
        ),
        migrations.AddField(
            model_name="historicalsiswa",
            name="tipe_tp",
            field=models.CharField(
                choices=[("baru", "Siswa Baru"), ("lama", "Daftar Ulang")],
                default="baru",
                help_text="Status TP untuk komponen biaya tahunan (baru vs daftar ulang).",
                max_length=5,
            ),
        ),
        migrations.CreateModel(
            name="KomponenBiayaTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kode", models.CharField(max_length=40)),
                ("nama", models.CharField(max_length=120)),
                ("jenjang", models.CharField(choices=[("PG", "Playgroup"), ("RA", "RA / TK")], max_length=5)),
                (
                    "tipe_siswa",
                    models.CharField(
                        choices=[("baru", "Siswa Baru"), ("lama", "Daftar Ulang"), ("all", "Semua")],
                        default="all",
                        max_length=5,
                    ),
                ),
                (
                    "tahun_ke",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="Tahun pendidikan RA (1=tahun pertama, 2=naik/mengulang).",
                    ),
                ),
                (
                    "bulan_tagih",
                    models.PositiveSmallIntegerField(
                        default=7,
                        help_text="Bulan tagihan komponen tahunan (default Juli awal TP).",
                    ),
                ),
                ("nominal", models.DecimalField(decimal_places=2, max_digits=18)),
                ("urutan", models.PositiveSmallIntegerField(default=0)),
                ("aktif", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["jenjang", "tahun_ke", "urutan", "kode"],
                "unique_together": {("kode", "jenjang", "tipe_siswa", "tahun_ke")},
            },
        ),
    ]
