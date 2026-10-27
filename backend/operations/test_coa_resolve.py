"""Test resolver akun COA Final untuk auto-jurnal payroll."""

from decimal import Decimal

from django.test import TestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan
from operations.models import GajiPegawai, MsPostingRule, Pegawai
from operations.services import post_gaji
from operations.services.coa_resolve import (
    ensure_piutang_karyawan,
    resolve_system_account,
    seed_system_posting_rules,
)


def _coa_final_fixture():
    g1, _ = MsGolongan.objects.get_or_create(kode_golongan="1", defaults={"nama_golongan": "ASET"})
    g2, _ = MsGolongan.objects.get_or_create(kode_golongan="2", defaults={"nama_golongan": "LIABILITAS"})
    sg11, _ = MsSubGolongan.objects.get_or_create(
        kode_sub="11", defaults={"golongan": g1, "nama_sub": "ASET LANCAR"},
    )
    sg21, _ = MsSubGolongan.objects.get_or_create(
        kode_sub="21", defaults={"golongan": g2, "nama_sub": "LIABILITAS JANGKA PENDEK"},
    )
    g5, _ = MsGolongan.objects.get_or_create(kode_golongan="5", defaults={"nama_golongan": "BEBAN"})
    sg53, _ = MsSubGolongan.objects.get_or_create(
        kode_sub="53", defaults={"golongan": g5, "nama_sub": "BEBAN KEPEGAWAIAN"},
    )

    g4, _ = MsGolongan.objects.get_or_create(kode_golongan="4", defaults={"nama_golongan": "PENDAPATAN"})
    sg41, _ = MsSubGolongan.objects.get_or_create(
        kode_sub="41", defaults={"golongan": g4, "nama_sub": "PENDAPATAN USAHA"},
    )
    for kode, nama in [
        ("411", "SPP"),
        ("412", "Uang Masuk"),
        ("415", "Pendapatan Formulir"),
        ("416", "Pendapatan Sit In"),
        ("417", "Pendapatan Lain-lain"),
    ]:
        MsCoa.objects.get_or_create(
            kode_akun=kode,
            defaults={"sub_golongan": sg41, "nama_akun": nama, "posisi_normal": "K"},
        )

    for kode, nama, sub, pos in [
        ("111", "Kas di Tangan", sg11, "D"),
        ("112", "Kas di Bank", sg11, "D"),
        ("211", "Utang Gaji Pegawai", sg21, "K"),
        ("5301", "Beban Gaji Pegawai", sg53, "D"),
    ]:
        MsCoa.objects.get_or_create(
            kode_akun=kode,
            defaults={"sub_golongan": sub, "nama_akun": nama, "posisi_normal": pos},
        )


class CoaResolveTests(TestCase):
    def setUp(self):
        _coa_final_fixture()

    def test_ensure_piutang_karyawan_creates_114(self):
        kode = ensure_piutang_karyawan()
        self.assertEqual(kode, "114")
        self.assertTrue(MsCoa.objects.filter(kode_akun="114").exists())

    def test_legacy_1103_perlengkapan_tidak_dipakai_untuk_kasbon(self):
        sub = MsSubGolongan.objects.get(kode_sub="11")
        MsCoa.objects.create(
            kode_akun="1103", sub_golongan=sub, nama_akun="Perlengkapan Sekolah", posisi_normal="D",
        )
        MsPostingRule.objects.create(
            event_code="SISTEM", komponen="PIUTANG_KARYAWAN",
            akun_debit_id="111", akun_kredit_id="1103", aktif=True,
        )

        self.assertEqual(resolve_system_account("PIUTANG_KARYAWAN"), "114")
        seed_system_posting_rules()
        rule = MsPostingRule.objects.get(event_code="SISTEM", komponen="PIUTANG_KARYAWAN")
        self.assertEqual(rule.akun_kredit_id, "114")

    def test_resolve_system_account_coa_final(self):
        seed_system_posting_rules()
        self.assertIn(resolve_system_account("KAS"), ("111", "112"))
        self.assertEqual(resolve_system_account("BEBAN_GAJI"), "5301")
        self.assertEqual(resolve_system_account("UTANG_ASURANSI"), "211")

    def test_post_gaji_coa_final(self):
        seed_system_posting_rules()
        pegawai = Pegawai.objects.create(nama="Guru COA Final")
        gaji = GajiPegawai.objects.create(
            pegawai=pegawai,
            periode_bulan=4,
            periode_tahun=2025,
            gaji_pokok=Decimal("3000000"),
            potongan_pinjaman=Decimal("100000"),
        )
        jurnal = post_gaji(gaji)
        kodes = {d.kode_akun_id for d in jurnal.detail.all()}
        self.assertIn("5301", kodes)
        self.assertTrue(kodes & {"111", "112"}, f"kas tidak ditemukan: {kodes}")
        self.assertIn("114", kodes)

    def test_stale_posting_rule_ignored_when_akun_missing(self):
        MsPostingRule.objects.create(
            event_code="SISTEM",
            komponen="BEBAN_GAJI",
            akun_debit_id="111",
            akun_kredit_id="9999",
            aktif=True,
        )
        self.assertEqual(resolve_system_account("BEBAN_GAJI"), "5301")

    def test_seed_tagihan_per_komponen_coa_final(self):
        seed_system_posting_rules()
        spp = MsPostingRule.objects.get(event_code="TAGIHAN", komponen="SPP")
        self.assertEqual(spp.akun_kredit_id, "411")
        sitin = MsPostingRule.objects.get(event_code="REGISTRASI", komponen="SITIN")
        self.assertEqual(sitin.akun_kredit_id, "416")
        daftar = MsPostingRule.objects.get(event_code="REGISTRASI", komponen="PENDAFTARAN")
        self.assertEqual(daftar.akun_kredit_id, "415")

    def test_resolve_komponen_tanpa_posting_rule(self):
        from operations.services.coa_resolve import resolve_komponen_pendapatan

        MsPostingRule.objects.filter(event_code="TAGIHAN", komponen="SPP").delete()
        self.assertEqual(resolve_komponen_pendapatan("SPP"), "411")

    def test_resolve_registrasi_tanpa_posting_rule(self):
        from operations.services.coa_resolve import resolve_komponen_pendapatan

        MsPostingRule.objects.filter(event_code="REGISTRASI").delete()
        self.assertEqual(resolve_komponen_pendapatan("SITIN", event_code="REGISTRASI"), "416")
        self.assertEqual(resolve_komponen_pendapatan("PENDAFTARAN", event_code="REGISTRASI"), "415")
