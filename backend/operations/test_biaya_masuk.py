"""Biaya masuk siswa (Batch 3 revisi spreadsheet): isian manual, diskon, tagihan, penerimaan sebagian."""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from operations.models import Jenjang, Kelompok, MsPostingRule, PembayaranTagihan, Siswa, Tagihan
from operations.services.billing import build_tagihan_komponen, generate_tagihan
from operations.services.tp_templates import ensure_tp_templates
from operations.test_tp_batch import _coa


class BiayaMasukTests(APITestCase):
    def setUp(self):
        kas = _coa("1101", "KAS", "D")
        for kode, nama in (("411", "SPP"), ("412", "Uang Masuk"), ("413", "Pengembangan"), ("417", "Lain")):
            _coa(kode, nama, "K")
        for komp, akun in (("SPP", "411"), ("UANG_MASUK", "412"), ("PENGEMBANGAN", "413"), ("KEGIATAN", "417"), ("SERAGAM", "417"), ("KOMITE", "417"), ("LAIN", "417")):
            MsPostingRule.objects.create(event_code="TAGIHAN", komponen=komp, akun_debit=kas, akun_kredit_id=akun)
        ensure_tp_templates()
        self.kelompok = Kelompok.objects.create(nama="TKA Melati", jenjang=Jenjang.objects.create(kode="TKA", nama="TK A"))
        self.users = {}
        for role in ("Administration", "Finance", "SchoolPrincipal"):
            user = get_user_model().objects.create_user(f"bm-{role}")
            user.groups.add(Group.objects.get(name=role))
            self.users[role] = user
        self.client.force_authenticate(self.users["Administration"])

    def payload(self, **extra):
        data = {
            "nama": "Ayu", "kelompok": self.kelompok.pk, "spp_nominal": "500000.00", "status": "aktif",
            "uang_masuk": "3200000", "uang_pengembangan": "1650000", "uang_kegiatan": "4500000", "uang_seragam": "400000",
            "diskon_kategori": ["SIB", "PG"], "diskon_nominal": "3500000",
        }
        data.update(extra)
        return data

    def tagihan(self, siswa_id):
        return Tagihan.objects.get(siswa_id=siswa_id, jenis="BIAYA_MASUK")

    def test_simpan_siswa_membuat_tagihan_netto_dengan_diskon_berurutan(self):
        res = self.client.post("/api/v1/siswa/", self.payload(), format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["diskon_kategori"], ["PG", "SIB"])
        tagihan = self.tagihan(res.data["id"])
        rincian = {d.komponen: d for d in tagihan.detail.all()}
        # Diskon 3,5 jt habis di Uang Masuk (3,2 jt) lalu 300 rb dari Pengembangan.
        self.assertNotIn("UANG_MASUK", rincian)
        self.assertEqual(rincian["PENGEMBANGAN"].nominal, Decimal("1350000"))
        self.assertIn("diskon PG, SIB Rp 300.000", rincian["PENGEMBANGAN"].keterangan)
        self.assertEqual(rincian["KEGIATAN"].nominal, Decimal("4500000"))
        self.assertEqual(rincian["PENGEMBANGAN"].akun_pendapatan_id, "413")
        self.assertEqual(tagihan.total, Decimal("6250000"))
        self.assertEqual(res.data["biaya_masuk"]["status"], "BELUM")
        self.assertEqual(res.data["biaya_masuk"]["sisa"], "6250000.00")

    def test_diskon_melebihi_total_ditolak_tanpa_menyimpan_siswa(self):
        res = self.client.post("/api/v1/siswa/", self.payload(diskon_nominal="99999999"), format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("biaya_masuk", res.data)
        self.assertFalse(Siswa.objects.filter(nama="Ayu").exists())

    def test_tagihan_spp_bulan_yang_sama_tetap_bisa_dibuat_dan_komponen_tidak_ganda(self):
        siswa_id = self.client.post("/api/v1/siswa/", self.payload(diskon_nominal="0"), format="json").data["id"]
        biaya = self.tagihan(siswa_id)
        siswa = Siswa.objects.get(pk=siswa_id)
        bulanan = generate_tagihan(siswa, biaya.periode_bulan, biaya.periode_tahun)
        self.assertEqual(bulanan.jenis, "BULANAN")
        # Tagihan Juli berikutnya dalam 12 bulan tidak menagih ulang komponen biaya masuk; Komite tetap.
        bulan_juli = 7
        tahun_juli = biaya.periode_tahun if biaya.periode_bulan <= 7 else biaya.periode_tahun + 1
        lines, _total, _meta = build_tagihan_komponen(siswa, bulan_juli, tahun_juli)
        komponen = {line["komponen"] for line in lines}
        self.assertTrue({"UANG_MASUK", "KEGIATAN", "PENGEMBANGAN", "SERAGAM"}.isdisjoint(komponen))
        self.assertIn("KOMITE", komponen)

    def test_komponen_yang_sudah_ditagih_bulanan_ditolak(self):
        kosong = {f: None for f in ("uang_masuk", "uang_pengembangan", "uang_kegiatan", "uang_seragam")}
        siswa_id = self.client.post("/api/v1/siswa/", self.payload(**kosong, diskon_nominal="0", diskon_kategori=[]), format="json").data["id"]
        juli = generate_tagihan(Siswa.objects.get(pk=siswa_id), 7, 2026)
        self.assertTrue(juli.detail.filter(komponen="UANG_MASUK").exists())
        with patch("operations.services.biaya_masuk.timezone.localdate", return_value=date(2026, 10, 28)):
            res = self.client.patch(f"/api/v1/siswa/{siswa_id}/", {"uang_masuk": "3200000"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Uang Masuk sudah ditagih di tagihan 7/2026", res.data["biaya_masuk"])
        self.assertFalse(Tagihan.objects.filter(siswa_id=siswa_id, jenis="BIAYA_MASUK").exists())
        self.assertIsNone(Siswa.objects.get(pk=siswa_id).uang_masuk)

    def test_bayar_sebagian_lalu_nominal_terbayar_terkunci(self):
        siswa_id = self.client.post("/api/v1/siswa/", self.payload(diskon_nominal="0"), format="json").data["id"]
        tagihan = self.tagihan(siswa_id)
        uang_masuk = tagihan.detail.get(komponen="UANG_MASUK")
        bayar = self.client.post(f"/api/v1/tagihan/{tagihan.pk}/bayar/", {
            "tanggal": "2026-10-28", "no_bukti": "BM-1", "nominal": "1000000", "akun_kas": "1101",
            "request_id": str(uuid.uuid4()), "alokasi": [{"detail": uang_masuk.pk, "nominal": "1000000"}],
        }, format="json")
        self.assertEqual(bayar.status_code, 200, bayar.data)
        self.assertEqual(bayar.data["tagihan"]["status"], "SEBAGIAN")
        self.assertEqual(PembayaranTagihan.objects.get().jurnal.status, "DRAFT")
        ditolak = self.client.patch(f"/api/v1/siswa/{siswa_id}/", {"uang_masuk": "3000000"}, format="json")
        self.assertEqual(ditolak.status_code, 400)
        self.assertIn("Uang Masuk sudah ada penerimaan", ditolak.data["biaya_masuk"])
        self.assertEqual(Siswa.objects.get(pk=siswa_id).uang_masuk, Decimal("3200000"))
        # Komponen lain yang belum dibayar masih boleh diubah.
        ubah = self.client.patch(f"/api/v1/siswa/{siswa_id}/", {"uang_seragam": "350000"}, format="json")
        self.assertEqual(ubah.status_code, 200, ubah.data)
        tagihan.refresh_from_db()
        self.assertEqual(tagihan.total, Decimal("9700000"))
        self.assertEqual(ubah.data["biaya_masuk"]["sisa"], "8700000.00")
        self.assertEqual(self.client.patch(f"/api/v1/tagihan/{tagihan.pk}/", {"periode_bulan": 1}, format="json").status_code, 400)

    def test_mengosongkan_biaya_masuk_menghapus_tagihan_tanpa_pembayaran(self):
        siswa_id = self.client.post("/api/v1/siswa/", self.payload(diskon_nominal="0"), format="json").data["id"]
        kosong = {f: None for f in ("uang_masuk", "uang_pengembangan", "uang_kegiatan", "uang_seragam")}
        res = self.client.patch(f"/api/v1/siswa/{siswa_id}/", kosong, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIsNone(res.data["biaya_masuk"])
        self.assertFalse(Tagihan.objects.filter(siswa_id=siswa_id, jenis="BIAYA_MASUK").exists())

    def test_akses_dan_default_daftar_harga(self):
        default = self.client.get(f"/api/v1/siswa/biaya-masuk-default/?kelompok={self.kelompok.pk}&tipe_tp=baru")
        self.assertEqual(default.status_code, 200)
        self.assertEqual(default.data["uang_masuk"], "3200000.00")
        for role in ("Finance", "SchoolPrincipal"):
            self.client.force_authenticate(self.users[role])
            self.assertEqual(self.client.post("/api/v1/siswa/", self.payload(), format="json").status_code, 403)
        self.client.force_authenticate(self.users["Finance"])
        self.assertEqual(self.client.get("/api/v1/siswa/").status_code, 200)

