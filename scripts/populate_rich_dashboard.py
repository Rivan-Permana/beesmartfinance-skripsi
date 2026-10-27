"""Script to seed rich, complete dashboard data for TK Lebah Madu (2026)."""

import os
import uuid
from datetime import date, timedelta
from decimal import Decimal
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from accounting.models import (
    MsCoa,
    MsPeriodeAkuntansi,
    TrJurnal,
    TrJurnalDetail,
    TrAnggaran,
)
from operations.models import (
    Siswa,
    Tagihan,
    TagihanDetail,
    Kegiatan,
    RealisasiKegiatan,
    KehadiranSiswa,
    MenuKatering,
    Pegawai,
)

User = get_user_model()


@transaction.atomic
def run_seed():
    print("--- Starting Rich Dashboard Seed ---")
    admin_user = User.objects.filter(username="admin.tu").first() or User.objects.first()
    keuangan_user = User.objects.filter(username="keuangan").first() or admin_user
    kepsek_user = User.objects.filter(username="kepsek").first() or admin_user

    # 1. Soft-delete the legacy anomaly journal if present
    anomaly_jurnal = TrJurnal.objects.filter(no_bukti="LEG-ANG-SALARY-2026").first()
    if anomaly_jurnal:
        anomaly_jurnal.is_deleted = True
        anomaly_jurnal.save()
        print("Soft-deleted anomaly journal LEG-ANG-SALARY-2026")

    # 2. Ensure Fiscal Period 2026/2027 exists
    periode, _ = MsPeriodeAkuntansi.objects.get_or_create(
        kode="2026/2027",
        defaults={
            "tgl_mulai": date(2026, 1, 1),
            "tgl_selesai": date(2026, 12, 31),
            "status": "OPEN",
        },
    )

    # 3. Clean up previously seeded demo journals from this script
    TrJurnal.objects.filter(no_bukti__startswith="SA-2026-").delete()
    TrJurnal.objects.filter(no_bukti__startswith="BKM-2026").delete()
    TrJurnal.objects.filter(no_bukti__startswith="BKK-2026").delete()
    TrJurnal.objects.filter(no_bukti__startswith="DFT-2026").delete()

    # 4. Saldo Awal Kas & Bank 2026 (Capital injection)
    sa = TrJurnal.objects.create(
        id=uuid.uuid4(),
        no_bukti="SA-2026-001",
        tanggal=date(2026, 1, 1),
        keterangan="Saldo Awal Kas & Bank Tahun Buku 2026",
        tipe_sumber="MANUAL",
        status="POSTED",
        created_by=keuangan_user,
        approved_by=kepsek_user,
        fiscal_period=periode,
    )
    # Debit Bank 85jt, Debit Kas Tangan 15jt, Kredit Modal 100jt
    coa_bank = MsCoa.objects.get(kode_akun="1011")
    coa_kas = MsCoa.objects.get(kode_akun="1101")
    coa_modal = MsCoa.objects.get(kode_akun="311")
    TrJurnalDetail.objects.create(jurnal=sa, kode_akun=coa_bank, debit=Decimal("85000000"), kredit=Decimal("0"))
    TrJurnalDetail.objects.create(jurnal=sa, kode_akun=coa_kas, debit=Decimal("15000000"), kredit=Decimal("0"))
    TrJurnalDetail.objects.create(jurnal=sa, kode_akun=coa_modal, debit=Decimal("0"), kredit=Decimal("100000000"))
    print("Created Saldo Awal journal SA-2026-001")

    # 5. Monthly Posted Revenues & Expenses (Jan - Oct 2026)
    # Revenues:
    coa_spp = MsCoa.objects.get(kode_akun="4101")
    coa_lain = MsCoa.objects.get(kode_akun="417")
    coa_komite = MsCoa.objects.get(kode_akun="414")
    coa_formulir = MsCoa.objects.get(kode_akun="415")

    # Expenses:
    coa_gaji = MsCoa.objects.get(kode_akun="5301")
    coa_outing = MsCoa.objects.get(kode_akun="5101")
    coa_belajar = MsCoa.objects.get(kode_akun="5111")
    coa_listrik = MsCoa.objects.get(kode_akun="5406")
    coa_air = MsCoa.objects.get(kode_akun="5405")
    coa_internet = MsCoa.objects.get(kode_akun="5407")
    coa_gedung = MsCoa.objects.get(kode_akun="5402")

    bulan_names = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]

    for m in range(1, 11):
        bname = bulan_names[m]
        # BKM: SPP
        j_spp = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=f"BKM-2026{m:02d}-01",
            tanggal=date(2026, m, 10),
            keterangan=f"Penerimaan SPP Siswa Bulan {bname} 2026",
            tipe_sumber="AUTO_BILLING",
            status="POSTED",
            created_by=admin_user,
            approved_by=keuangan_user,
            fiscal_period=periode,
        )
        spp_nom = Decimal("24500000") + Decimal(m * 100000)
        TrJurnalDetail.objects.create(jurnal=j_spp, kode_akun=coa_bank, debit=spp_nom, kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_spp, kode_akun=coa_spp, debit=Decimal("0"), kredit=spp_nom)

        # BKM: Katering & Jemputan
        j_ops = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=f"BKM-2026{m:02d}-02",
            tanggal=date(2026, m, 12),
            keterangan=f"Penerimaan Katering & Antar Jemput Siswa Bulan {bname} 2026",
            tipe_sumber="AUTO_BILLING",
            status="POSTED",
            created_by=admin_user,
            approved_by=keuangan_user,
            fiscal_period=periode,
        )
        kat_nom = Decimal("6200000")
        jemput_nom = Decimal("3800000")
        TrJurnalDetail.objects.create(jurnal=j_ops, kode_akun=coa_bank, debit=kat_nom + jemput_nom, kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_ops, kode_akun=coa_lain, debit=Decimal("0"), kredit=kat_nom + jemput_nom)

        # BKM: Komite & Formulir
        j_kom = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=f"BKM-2026{m:02d}-03",
            tanggal=date(2026, m, 15),
            keterangan=f"Penerimaan Iuran Komite & Pendaftaran Formulir Bulan {bname} 2026",
            tipe_sumber="MANUAL",
            status="POSTED",
            created_by=admin_user,
            approved_by=keuangan_user,
            fiscal_period=periode,
        )
        TrJurnalDetail.objects.create(jurnal=j_kom, kode_akun=coa_kas, debit=Decimal("2400000"), kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_kom, kode_akun=coa_komite, debit=Decimal("0"), kredit=Decimal("1500000"))
        TrJurnalDetail.objects.create(jurnal=j_kom, kode_akun=coa_formulir, debit=Decimal("0"), kredit=Decimal("900000"))

        # BKK: Gaji Pegawai
        j_gaji = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=f"BKK-2026{m:02d}-01",
            tanggal=date(2026, m, 25),
            keterangan=f"Pembayaran Kafalah & Gaji Pendidik Bulan {bname} 2026",
            tipe_sumber="AUTO_PAYROLL",
            status="POSTED",
            created_by=keuangan_user,
            approved_by=kepsek_user,
            fiscal_period=periode,
        )
        gaji_nom = Decimal("18500000")
        TrJurnalDetail.objects.create(jurnal=j_gaji, kode_akun=coa_gaji, debit=gaji_nom, kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_gaji, kode_akun=coa_bank, debit=Decimal("0"), kredit=gaji_nom)

        # BKK: Konsumsi & Katering Operasional
        j_makan = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=f"BKK-2026{m:02d}-02",
            tanggal=date(2026, m, 20),
            keterangan=f"Pengadaan Bahan Makanan Katering Sehat Bulan {bname} 2026",
            tipe_sumber="MANUAL",
            status="POSTED",
            created_by=keuangan_user,
            approved_by=kepsek_user,
            fiscal_period=periode,
        )
        TrJurnalDetail.objects.create(jurnal=j_makan, kode_akun=coa_outing, debit=Decimal("4200000"), kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_makan, kode_akun=coa_bank, debit=Decimal("0"), kredit=Decimal("4200000"))

        # BKK: Utilitas
        j_util = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=f"BKK-2026{m:02d}-03",
            tanggal=date(2026, m, 18),
            keterangan=f"Beban Utilitas Listrik, Air & Internet Bulan {bname} 2026",
            tipe_sumber="MANUAL",
            status="POSTED",
            created_by=keuangan_user,
            approved_by=kepsek_user,
            fiscal_period=periode,
        )
        TrJurnalDetail.objects.create(jurnal=j_util, kode_akun=coa_listrik, debit=Decimal("1200000"), kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_util, kode_akun=coa_air, debit=Decimal("350000"), kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_util, kode_akun=coa_internet, debit=Decimal("450000"), kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_util, kode_akun=coa_bank, debit=Decimal("0"), kredit=Decimal("2000000"))

        # BKK: ATK & Perawatan
        j_atk = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=f"BKK-2026{m:02d}-04",
            tanggal=date(2026, m, 22),
            keterangan=f"Belanja ATK Pembelajaran & Pemeliharaan Gedung Bulan {bname} 2026",
            tipe_sumber="MANUAL",
            status="POSTED",
            created_by=keuangan_user,
            approved_by=kepsek_user,
            fiscal_period=periode,
        )
        TrJurnalDetail.objects.create(jurnal=j_atk, kode_akun=coa_belajar, debit=Decimal("1600000"), kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_atk, kode_akun=coa_gedung, debit=Decimal("1250000"), kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=j_atk, kode_akun=coa_kas, debit=Decimal("0"), kredit=Decimal("2850000"))

    print("Created monthly posted journals for Jan-Oct 2026")

    # 6. Draft Journals (Pending Approval)
    dfts = [
        ("DFT-202610-01", "Pembelian Alat Peraga Edukatif Sentra Balok & Sains", coa_belajar, Decimal("1750000"), coa_kas),
        ("DFT-202610-02", "Pengadaan Bahan Seragam Tambahan Siswa Baru", coa_outing, Decimal("2400000"), coa_bank),
        ("DFT-202610-03", "Konsumsi Rapat Koordinasi Komite Sekolah & Wali Murid", coa_outing, Decimal("650000"), coa_kas),
    ]
    for no, ket, deb_akun, nom, kre_akun in dfts:
        jdft = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=no,
            tanggal=date(2026, 10, 1),
            keterangan=ket,
            tipe_sumber="MANUAL",
            status="DRAFT",
            created_by=keuangan_user,
            fiscal_period=periode,
        )
        TrJurnalDetail.objects.create(jurnal=jdft, kode_akun=deb_akun, debit=nom, kredit=Decimal("0"))
        TrJurnalDetail.objects.create(jurnal=jdft, kode_akun=kre_akun, debit=Decimal("0"), kredit=nom)
    print("Created 3 pending draft journals")

    # 7. Setup Pagu Anggaran 2026 (TrAnggaran)
    TrAnggaran.objects.filter(tahun_anggaran=2026).delete()
    anggaran_data = [
        ("5301", Decimal("240000000"), "Anggaran Kafalah & Gaji Pendidik 2026"),
        ("5101", Decimal("55000000"), "Anggaran Operasional & Konsumsi Sehat 2026"),
        ("5111", Decimal("24000000"), "Anggaran Bahan Ajar Sentra & Portofolio 2026"),
        ("5406", Decimal("16000000"), "Anggaran Daya Listrik PLN 2026"),
        ("5402", Decimal("18000000"), "Anggaran Pemeliharaan & Perawatan Gedung 2026"),
        ("5407", Decimal("6000000"), "Anggaran Koneksi Internet & TI 2026"),
    ]
    for kode, pagu, ket in anggaran_data:
        coa = MsCoa.objects.get(kode_akun=kode)
        TrAnggaran.objects.create(
            kode_akun=coa,
            tahun_anggaran=2026,
            nominal_anggaran=pagu,
            keterangan=ket,
            periode=periode,
        )
    print("Created realistic TrAnggaran budgets for 2026")

    # 8. Setup Kehadiran Siswa (Absensi & Katering) for Sparkline & Ops
    # Populate weekdays in Aug, Sep, and Oct 2026
    siswa_list = list(Siswa.objects.filter(status="aktif", is_deleted=False))
    if not siswa_list:
        print("No active siswa found!")
    else:
        # Today: 2026-10-01
        today = date(2026, 10, 1)
        for s in siswa_list:
            KehadiranSiswa.objects.update_or_create(
                siswa=s,
                tanggal=today,
                defaults={
                    "status": "hadir",
                    "ikut_katering": True,
                    "jemput_datang": True,
                    "jemput_pulang": True,
                },
            )
        # Sparkline requires previous months: May to Oct 2026
        for m in range(5, 10):
            # create records for 15th of each month for sparkline
            d = date(2026, m, 15)
            for s in siswa_list[:145]:
                KehadiranSiswa.objects.update_or_create(
                    siswa=s,
                    tanggal=d,
                    defaults={
                        "status": "hadir",
                        "ikut_katering": True,
                    },
                )
        print(f"Updated attendance & catering for {len(siswa_list)} students")

    # 9. Setup Tagihan (Invoices) for Oct 2026
    Tagihan.objects.filter(periode_tahun=2026, periode_bulan=10).delete()
    if siswa_list:
        # Create 140 LUNAS tagihan and 6 BELUM tagihan
        for i, s in enumerate(siswa_list):
            is_unpaid = i < 6
            t = Tagihan.objects.create(
                siswa=s,
                periode_bulan=10,
                periode_tahun=2026,
                total=Decimal("1350000"),
                status="BELUM" if is_unpaid else "LUNAS",
            )
            TagihanDetail.objects.create(
                tagihan=t,
                komponen="SPP",
                kategori="BULANAN",
                keterangan="SPP Oktober 2026",
                akun_pendapatan=coa_spp,
                nominal=Decimal("1350000"),
            )
        print(f"Created {len(siswa_list)} tagihan for 10/2026 (6 unpaid, rest paid)")

    # 10. Setup Kegiatan Sekolah (Activities)
    Kegiatan.objects.all().delete()
    pic = Pegawai.objects.first()
    kegiatan_specs = [
        ("Manasik Haji Cilik", Decimal("15000000"), Decimal("13500000")),
        ("Outing Class Kebun Raya & Museum", Decimal("20000000"), Decimal("16800000")),
        ("Pentas Seni & Kreasi Lebah Madu", Decimal("25000000"), Decimal("18750000")),
        ("Peringatan Maulid Nabi & Santunan", Decimal("10000000"), Decimal("8800000")),
        ("Market Day & Mini Entrepreneur", Decimal("8000000"), Decimal("4800000")),
    ]
    for nama, pagu, real in kegiatan_specs:
        k = Kegiatan.objects.create(
            nama=nama,
            akun_beban=coa_outing,
            pagu=pagu,
            penanggung_jawab=pic,
            tanggal_mulai=date(2026, 8, 1),
            tanggal_selesai=date(2026, 11, 30),
            status="BERJALAN",
            periode=periode,
        )
        RealisasiKegiatan.objects.create(
            kegiatan=k,
            tanggal=date(2026, 9, 20),
            deskripsi=f"Realisasi operasional {nama}",
            nominal=real,
        )
    print("Created 5 kegiatan with realistic pagu & realisasi")

    # 11. Setup Menu Katering Hari Ini
    MenuKatering.objects.filter(tanggal=date(2026, 10, 1)).delete()
    MenuKatering.objects.create(
        tanggal=date(2026, 10, 1),
        gambar="katering/menu_today.jpg",
        keterangan="Nasi Bento Beruang Madu Kuning, Ayam Suwir Gurih Manis, Sayur Bintang Wortel & Brokoli, Buah Semangka Segar & Susu UHT.",
    )
    print("Created today's MenuKatering with photo")

    print("--- Rich Dashboard Seed Complete! ---")


if __name__ == "__main__":
    run_seed()
