from pathlib import Path

from django.test import TestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan
from accounting.coa_final_import import import_coa_final
from config.db_errors import humanize_db_error


class CoaFinalImportTests(TestCase):
    def test_import_coa_final_csv(self):
        csv_path = (
            Path(__file__).resolve().parents[2]
            / "legacy-data"
            / "Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv"
        )
        if not csv_path.is_file():
            self.skipTest("COA Final CSV not found")

        stats = import_coa_final(csv_path, replace=True)
        self.assertGreaterEqual(stats["akun_total"], 180)
        self.assertTrue(MsCoa.objects.filter(kode_akun="411").exists())
        self.assertTrue(MsGolongan.objects.filter(kode_golongan="1").exists())
        self.assertTrue(MsSubGolongan.objects.filter(kode_sub="51").exists())


class HumanizeDbErrorTests(TestCase):
    def test_fk_jurnal_detail(self):
        raw = 'update or delete on table "ms_coa" violates foreign key constraint "tr_jurnal_detail_kode_akun_fkey"'
        msg = humanize_db_error(raw)
        self.assertNotIn("violates", msg.lower())
        self.assertIn("jurnal", msg.lower())

    def test_invalid_page(self):
        self.assertIn("Halaman", humanize_db_error("Invalid page."))
