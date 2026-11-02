"""Isi awal kode buku kas sekolah. Hanya kode yang artinya jelas yang dipetakan ke akun;
sisanya dibiarkan kosong sampai dikonfirmasi sekolah dan diisi Keuangan lewat halaman COA."""

from django.db import migrations

# (kode, unit, nama, kode_akun atau None)
KODE = [
    ("GJ", "UMUM", "Gaji", "5301"),
    ("MS", "UMUM", "Makan siang guru", "5302"),
    ("ATK", "UMUM", "Alat tulis kantor", "5401"),
    ("PLN", "UMUM", "Listrik", "5406"),
    ("NET", "UMUM", "Internet", "5407"),
    ("PGM", "UMUM", "Pengembangan", None),
    ("SRG", "UMUM", "Seragam", None),
    ("PLT", "UMUM", "Peralatan", None),
    ("PBB", "UMUM", "PBB", None),
    ("GR", "UMUM", "Perlengkapan guru", None),
    ("ASC", "UMUM", "Asuransi", None),
    ("DVD", "UMUM", "", None),
    ("TMB", "UMUM", "", None),
    ("AB3", "TK", "AB3", "5112"),
    ("AB3", "PG", "AB3", "5212"),
    ("AMY", "TK", "Ayah Main Yuk", "5120"),
    ("AMY", "PG", "Ayah Main Yuk", "5220"),
    ("PRT", "TK", "Parenting", "5124"),
    ("PRT", "PG", "Parenting", "5224"),
    ("COOK", "TK", "Fun cooking", "5116"),
    ("COOK", "PG", "Fun cooking", "5216"),
    ("DR", "TK", "Pemeriksaan dokter", "5103"),
    ("DR", "PG", "Pemeriksaan dokter", "5203"),
    ("HOME", "TK", "Home visit", "5110"),
    ("HOME", "PG", "Home visit", "5210"),
    ("SPL", "PG", "Splash day", "5218"),
    ("PNT", "PG", "Panti asuhan", "5206"),
    ("PNT", "TK", "Panti asuhan", None),
    ("STR", "TK", "Sentra", None),
    ("STR", "PG", "Sentra", None),
    ("KEG", "UMUM", "Kegiatan kelas", None),
    ("KLS", "UMUM", "Kelas", None),
    ("MK", "UMUM", "", None),
    ("FUN", "UMUM", "", None),
    ("17AN", "UMUM", "Agustusan", None),
    ("FEST", "UMUM", "Festival budaya", None),
    ("CAMP", "UMUM", "Camping", None),
    ("FEE", "UMUM", "Fee narasumber", None),
    ("TEA", "UMUM", "", None),
    ("MID", "UMUM", "", None),
    ("RNG", "UMUM", "", None),
    ("PBTS", "UMUM", "", None),
    ("MPBS", "UMUM", "", None),
    ("SRV", "UMUM", "Survei", None),
    ("ATB", "UMUM", "", None),
    ("UMMI", "UMUM", "Buku Ummi", None),
]


def isi(apps, schema_editor):
    KodePengeluaran = apps.get_model("operations", "KodePengeluaran")
    MsCoa = apps.get_model("accounting", "MsCoa")
    ada = set(MsCoa.objects.filter(kode_akun__in=[k[3] for k in KODE if k[3]]).values_list("kode_akun", flat=True))
    for kode, unit, nama, akun in KODE:
        KodePengeluaran.objects.get_or_create(
            kode=kode, unit=unit, defaults={"nama": nama, "akun_id": akun if akun in ada else None},
        )


def hapus(apps, schema_editor):
    KodePengeluaran = apps.get_model("operations", "KodePengeluaran")
    for kode, unit, _nama, _akun in KODE:
        KodePengeluaran.objects.filter(kode=kode, unit=unit).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0019_info_jenjang_seragam_kode_pengeluaran"),
        ("accounting", "0003_opening_balance"),
    ]

    operations = [migrations.RunPython(isi, hapus)]
