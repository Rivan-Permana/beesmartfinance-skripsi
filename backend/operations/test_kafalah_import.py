"""Test parser & import KAFALAH / anggaran legacy."""

from decimal import Decimal
from pathlib import Path

from django.test import TestCase

from operations.models import GajiPegawai, Pegawai, PinjamanPegawai
from operations.services.legacy_import.anggaran_csv import parse_anggaran_csv
from operations.services.legacy_import.kafalah_csv import (
    parse_absen,
    parse_idr,
    parse_pinjaman,
    parse_salary_table,
)
from operations.services.payroll import apply_potongan_pinjaman, post_gaji
from operations.services.payroll_kafalah import import_kafalah_payroll

REPO = Path(__file__).resolve().parents[2]
LEGACY = REPO / "legacy-data"


class KafalahParserTests(TestCase):
    def test_parse_idr_indonesia(self):
        self.assertEqual(parse_idr("  3.500.000,00 "), Decimal("3500000"))

    def test_salary_table_ali(self):
        rows = parse_salary_table(LEGACY / "KAFALAH APRIL '2025.xlsx - Salary Table.csv")
        ali = next(r for r in rows if "Ali Suryadi" in r.nama)
        self.assertEqual(ali.gaji_pokok, Decimal("3500000"))
        self.assertEqual(ali.tarif_uang_makan, Decimal("3000"))
        self.assertEqual(ali.tarif_transport, Decimal("17000"))

    def test_absen_total_hari(self):
        rows = parse_absen(LEGACY / "KAFALAH APRIL '2025.xlsx - Absen.csv")
        ali = next(r for r in rows if "Ali Suryadi" in r.nama)
        self.assertEqual(ali.hari_hadir, 11)

    def test_pinjaman_ali_potong(self):
        rows = parse_pinjaman(LEGACY / "KAFALAH APRIL '2025.xlsx - Pinjaman.csv")
        ali = next(r for r in rows if "Ali Suryadi" in r.nama)
        self.assertEqual(ali.potongan_bulan, Decimal("100000"))
        self.assertEqual(ali.sisa_balance, Decimal("100000"))


class KafalahImportTests(TestCase):
    def test_import_creates_gaji_dengan_potongan(self):
        stats = import_kafalah_payroll(legacy_dir=LEGACY, dry_run=False)
        self.assertGreaterEqual(stats["gaji_upserted"], 30)
        ali = Pegawai.objects.get(nip="KAF-001")
        gaji = GajiPegawai.objects.get(pegawai=ali, periode_bulan=4, periode_tahun=2025)
        self.assertEqual(gaji.hari_hadir, 11)
        self.assertEqual(gaji.uang_makan, Decimal("33000"))
        self.assertEqual(gaji.transport, Decimal("187000"))
        self.assertEqual(gaji.potongan_pinjaman, Decimal("100000"))
        self.assertEqual(gaji.total_netto, Decimal("7160000"))


class PotongPinjamanTests(TestCase):
    def setUp(self):
        from accounting.models import MsCoa, MsGolongan, MsSubGolongan

        def _coa(kode, nama, posisi):
            g, _ = MsGolongan.objects.get_or_create(
                kode_golongan=kode[0], defaults={"nama_golongan": "G" + kode[0]}
            )
            sg, _ = MsSubGolongan.objects.get_or_create(
                kode_sub=kode[:2], defaults={"golongan": g, "nama_sub": "SG"}
            )
            return MsCoa.objects.create(
                kode_akun=kode, sub_golongan=sg, nama_akun=nama, posisi_normal=posisi
            )

        _coa("1101", "KAS", "D")
        _coa("1103", "PIUTANG", "D")
        _coa("2101", "UTANG ASURANSI", "K")
        _coa("5201", "BEBAN GAJI", "D")
        self.pegawai = Pegawai.objects.create(nama="Test", nip="T-1")
        PinjamanPegawai.objects.create(
            pegawai=self.pegawai,
            tanggal_pinjaman="2025-04-01",
            jumlah_pinjaman=Decimal("500000"),
            angsuran_per_bulan=Decimal("100000"),
            is_legacy=True,
        )

    def _gaji(self, bulan=4):
        return GajiPegawai.objects.create(
            pegawai=self.pegawai, periode_bulan=bulan, periode_tahun=2025,
            gaji_pokok=Decimal("2000000"),
        )

    def test_kasbon_belum_dicairkan_tidak_dipotong(self):
        PinjamanPegawai.objects.create(
            pegawai=self.pegawai, tanggal_pinjaman="2025-04-02",
            jumlah_pinjaman=Decimal("300000"), angsuran_per_bulan=Decimal("300000"),
        )
        self.assertEqual(apply_potongan_pinjaman(self._gaji()), Decimal("100000"))

    def test_kasbon_dipotong_setelah_pencairan_posted(self):
        from accounting.models import TrJurnal
        from operations.services.payroll import post_pencairan_kasbon

        baru = PinjamanPegawai.objects.create(
            pegawai=self.pegawai, tanggal_pinjaman="2025-04-02",
            jumlah_pinjaman=Decimal("300000"), angsuran_per_bulan=Decimal("300000"),
        )
        jurnal = post_pencairan_kasbon(baru, akun_piutang="1103", akun_kas="1101")
        self.assertEqual(apply_potongan_pinjaman(self._gaji()), Decimal("100000"))
        TrJurnal.objects.filter(pk=jurnal.pk).update(status="POSTED")
        self.assertEqual(apply_potongan_pinjaman(self._gaji(bulan=5)), Decimal("400000"))

    def test_kasbon_legacy_tidak_bisa_dicairkan(self):
        from operations.services.payroll import post_pencairan_kasbon

        with self.assertRaises(ValueError):
            post_pencairan_kasbon(self.pegawai.pinjaman.get(), akun_piutang="1103", akun_kas="1101")

    def test_apply_dan_settle_pinjaman(self):
        gaji = GajiPegawai.objects.create(
            pegawai=self.pegawai, periode_bulan=4, periode_tahun=2025,
            gaji_pokok=Decimal("2000000"),
        )
        apply_potongan_pinjaman(gaji, save=True)
        self.assertEqual(gaji.potongan_pinjaman, Decimal("100000"))
        post_gaji(gaji)
        pinj = self.pegawai.pinjaman.first()
        self.assertEqual(pinj.sudah_terbayar, Decimal("100000"))


class AnggaranParserTests(TestCase):
    def test_parse_anggaran_rows(self):
        rows = parse_anggaran_csv(LEGACY / "realisasi anggaran sekolah.xlsx - Sheet1.csv")
        self.assertEqual(len(rows), 4)
        salary = next(r for r in rows if r.label == "Salary")
        self.assertEqual(salary.pagu, Decimal("1509664000"))
        self.assertIn("5101", salary.coa_candidates)


class AnggaranImportTests(TestCase):
    def setUp(self):
        from accounting.models import MsCoa, MsGolongan, MsSubGolongan

        def _coa(kode, nama, posisi):
            g, _ = MsGolongan.objects.get_or_create(
                kode_golongan=kode[0], defaults={"nama_golongan": "G" + kode[0]}
            )
            sg, _ = MsSubGolongan.objects.get_or_create(
                kode_sub=kode[:2], defaults={"golongan": g, "nama_sub": "SG"}
            )
            return MsCoa.objects.create(
                kode_akun=kode, sub_golongan=sg, nama_akun=nama, posisi_normal=posisi
            )

        _coa("1101", "KAS", "D")
        _coa("5101", "BEBAN GAJI", "D")
        _coa("5102", "BEBAN OPS", "D")
        _coa("51101", "TK OUTING", "D")

    def test_import_legacy_anggaran(self):
        from operations.services.legacy_import.anggaran_import import import_legacy_anggaran

        stats = import_legacy_anggaran(legacy_dir=LEGACY, tahun_anggaran=2026)
        self.assertEqual(stats["anggaran_upserted"], 4)
        self.assertEqual(stats["realisasi_jurnal"], 4)
        self.assertEqual(stats["skipped_no_coa"], 0)
