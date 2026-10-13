"""Tests legacy CSV import parsers."""

from pathlib import Path

from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from operations.services.legacy_import.absensi_csv import parse_absensi_csv

LEGACY_DIR = Path(__file__).resolve().parents[2] / "legacy-data"


class AbsensiCsvParserTests(SimpleTestCase):
    def test_parse_juli_2024_tk_a(self):
        path = LEGACY_DIR / "Absen siswa (3).xlsx - TK A.csv"
        if not path.is_file():
            self.skipTest("legacy-data not present")

        rows = parse_absensi_csv(path, target_bulan=7, target_tahun=2024)
        self.assertGreater(len(rows), 10)

        adzkiya = next(r for r in rows if "Adzkiya" in r.nama)
        self.assertTrue(adzkiya.catering_enrolled)
        self.assertEqual(len(adzkiya.days), 2)
        self.assertEqual(adzkiya.days[0].catering_amount, 20)

    def test_parse_agustus_2024_has_many_days(self):
        path = LEGACY_DIR / "Absen siswa (3).xlsx - TK A.csv"
        if not path.is_file():
            self.skipTest("legacy-data not present")

        rows = parse_absensi_csv(path, target_bulan=8, target_tahun=2024)
        ahsan = next(r for r in rows if "Ahsan Ghibran" in r.nama)
        self.assertGreater(len(ahsan.days), 10)
        amounts = {d.catering_amount for d in ahsan.days}
        self.assertIn(20, amounts)
        self.assertIn(10, amounts)


class JemputCsvParserTests(SimpleTestCase):
    def test_parse_juni_2024(self):
        path = LEGACY_DIR / "Absen Jemputan 2023-2024 (version 1) (2).xlsx - Juni 24.csv"
        if not path.is_file():
            self.skipTest("legacy-data not present")

        from operations.services.legacy_import.jemput_csv import parse_jemput_csv

        rows = parse_jemput_csv(path, target_bulan=6, target_tahun=2024)
        self.assertGreater(len(rows), 10)
        kekey = next(r for r in rows if r.nama.lower() == "kekey")
        self.assertEqual(kekey.tarif_per_trip, Decimal("23000"))
        self.assertGreater(len(kekey.days), 5)
