"""Daftar harga TA 2026/27 (dikonfirmasi sekolah 2/11/2026): Kegiatan TK baru, Seragam TK dan PG.

Hanya baris yang masih bernilai lama yang diubah, supaya isian manual lewat admin tidak tertimpa.
Tagihan yang sudah dibuat tidak berubah; nilai ini dipakai untuk tagihan dan prefill berikutnya.
"""

from decimal import Decimal

from django.db import migrations

# (kode, jenjang, tipe_siswa, tahun_ke, nominal lama, nominal baru)
HARGA = [
    ("KEGIATAN", "RA", "baru", 1, "4500000", "5000000"),
    ("SERAGAM", "RA", "baru", 1, "400000", "500000"),
    ("SERAGAM", "PG", "baru", 1, "200000", "250000"),
]


def _ubah(apps, dari, ke):
    KomponenBiayaTemplate = apps.get_model("operations", "KomponenBiayaTemplate")
    for kode, jenjang, tipe, tahun_ke, lama, baru in HARGA:
        nilai = {"lama": lama, "baru": baru}
        KomponenBiayaTemplate.objects.filter(
            kode=kode, jenjang=jenjang, tipe_siswa=tipe, tahun_ke=tahun_ke, nominal=Decimal(nilai[dari]),
        ).update(nominal=Decimal(nilai[ke]))


def maju(apps, schema_editor):
    _ubah(apps, "lama", "baru")


def mundur(apps, schema_editor):
    _ubah(apps, "baru", "lama")


class Migration(migrations.Migration):

    dependencies = [("operations", "0020_seed_kode_pengeluaran")]

    operations = [migrations.RunPython(maju, mundur)]
