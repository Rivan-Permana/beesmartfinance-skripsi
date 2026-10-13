"""Test export CSV layout legacy."""

from decimal import Decimal
from pathlib import Path

from django.test import TestCase

from operations.services.legacy_export import (
    export_laporan_jemput_legacy,
    export_laporan_katering_legacy,
    katering_total_system,
)

REPO = Path(__file__).resolve().parents[2]
LEGACY = REPO / "legacy-data"


class LegacyExportTests(TestCase):
    def test_katering_csv_header_legacy(self):
        csv_text = export_laporan_katering_legacy(7, 2025)
        self.assertIn("LAPORAN CATERING TK LEBAH MADU", csv_text)
        self.assertIn("July-2025", csv_text)
        self.assertIn("No.,Nama, Nominal", csv_text)

    def test_jemput_csv_header(self):
        csv_text = export_laporan_jemput_legacy(6, 2026)
        self.assertIn("LAPORAN JEMPUTAN", csv_text)
        self.assertIn("Trip", csv_text)

    def test_katering_total_non_negative(self):
        self.assertGreaterEqual(katering_total_system(1, 2026), Decimal(0))


class ValidateLegacyParserTests(TestCase):
    def test_parse_legacy_laporan_total(self):
        from accounts.management.commands.validate_legacy import _legacy_katering_total

        parsed = _legacy_katering_total(LEGACY / "Absen siswa (3).xlsx - laporan katering.csv")
        self.assertIsNotNone(parsed)
        bulan, tahun, total = parsed
        self.assertEqual(bulan, 7)
        self.assertEqual(tahun, 2024)
        self.assertGreater(total, Decimal("1000000"))
