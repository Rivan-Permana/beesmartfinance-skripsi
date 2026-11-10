"""Daftar Pengeluaran (?jenis=keluar): beban 5…, plus kode pengeluaran ke akun non-beban yang dibayar dari kas."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from operations.models import KodePengeluaran
from operations.test_tp_batch import _coa


class PengeluaranFilterTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("keu-filter")
        user.groups.add(Group.objects.get(name="Finance"))
        self.client.force_authenticate(user)
        for kode, nama, pos in (("1101", "Kas", "D"), ("115", "Kas PG", "D"), ("121", "Peralatan", "D"),
                                ("313", "Pembagian Dana ke Yayasan", "K"), ("4101", "SPP", "K"), ("5101", "Beban KBM", "D")):
            _coa(kode, nama, pos)
        KodePengeluaran.objects.update_or_create(kode="DVD", unit="UMUM", defaults={"nama": "Transfer ke yayasan", "akun_id": "313", "aktif": True})

    def jurnal(self, no_bukti, debit, kredit):
        res = self.client.post("/api/v1/jurnal/", {"no_bukti": no_bukti, "tanggal": "2026-11-10", "detail": [
            {"kode_akun": debit, "debit": "100", "kredit": "0"}, {"kode_akun": kredit, "debit": "0", "kredit": "100"}]}, format="json")
        self.assertEqual(res.status_code, 201, res.data)

    def test_keluar_memuat_beban_dan_kode_non_beban_dari_kas(self):
        self.jurnal("BEBAN", "5101", "1101")
        self.jurnal("DVD", "313", "1101")
        self.jurnal("DVD-PG", "313", "115")
        self.jurnal("ALAT", "121", "1101")  # akun 121 belum dipetakan ke kode pengeluaran
        self.jurnal("TRANSFER", "115", "1101")
        self.jurnal("SPP", "1101", "4101")
        self.jurnal("KOREKSI-DVD", "1101", "313")  # pengembalian dari yayasan: kas di debit, bukan pengeluaran
        bukti = sorted(r["no_bukti"] for r in self.client.get("/api/v1/jurnal/?jenis=keluar&page_size=50").data["results"])
        self.assertEqual(bukti, ["BEBAN", "DVD", "DVD-PG"])
        masuk = sorted(r["no_bukti"] for r in self.client.get("/api/v1/jurnal/?jenis=masuk&page_size=50").data["results"])
        self.assertEqual(masuk, ["SPP"])

    def test_kode_tmb_ke_aset_ikut_setelah_dipetakan(self):
        KodePengeluaran.objects.update_or_create(kode="TMB", unit="UMUM", defaults={"nama": "Tambah aset", "akun_id": "121", "aktif": True})
        self.jurnal("ALAT", "121", "1101")
        self.assertEqual(self.client.get("/api/v1/jurnal/?jenis=keluar").data["count"], 1)
