"""Posting dan persetujuan gaji per periode: pratinjau, proses massal, SoD, kasbon, dan slip yang gagal."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import TrJurnal
from operations.models import GajiPegawai, Pegawai, PinjamanPegawai
from operations.test_tp_batch import _coa


class GajiPeriodeTests(APITestCase):
    def setUp(self):
        self.keuangan, self.kepsek = (get_user_model().objects.create_user(n) for n in ("keu-gp", "kepsek-gp"))
        self.keuangan.groups.add(Group.objects.get(name="Finance"))
        self.kepsek.groups.add(Group.objects.get(name="SchoolPrincipal"))
        for kode, nama, pos in (("112", "Kas di Bank", "D"), ("114", "Piutang Karyawan (Kasbon)", "D"),
                                ("211", "Utang potongan", "K"), ("5301", "Beban Gaji", "D")):
            _coa(kode, nama, pos)
        self.pegawai = [Pegawai.objects.create(nama=f"Pegawai {i}", status="aktif") for i in range(3)]
        PinjamanPegawai.objects.create(pegawai=self.pegawai[0], tanggal_pinjaman=date(2026, 12, 1), jumlah_pinjaman=Decimal("300"),
                                       tenor_bulan=3, angsuran_per_bulan=Decimal("100"), is_legacy=True)
        for p in self.pegawai:
            self.client.force_authenticate(self.keuangan)
            res = self.client.post("/api/v1/gaji/", {"pegawai": p.pk, "periode_bulan": 1, "periode_tahun": 2027,
                                                     "gaji_pokok": "1000", "potongan_asuransi": "10"}, format="json")
            self.assertEqual(res.status_code, 201, res.data)
        # Slip periode lain tidak boleh ikut.
        GajiPegawai.objects.create(pegawai=self.pegawai[1], periode_bulan=2, periode_tahun=2027, gaji_pokok=Decimal("1000"))

    def periode(self, user, aksi, simpan):
        self.client.force_authenticate(user)
        return self.client.post(f"/api/v1/gaji/{aksi}/", {"periode_bulan": 1, "periode_tahun": 2027, "simpan": simpan}, format="json")

    def test_pratinjau_posting_lalu_setujui_semua(self):
        pv = self.periode(self.keuangan, "posting-periode", False)
        self.assertEqual(pv.status_code, 200, pv.data)
        self.assertEqual((pv.data["jumlah"], pv.data["berhasil"], pv.data["disimpan"]), (3, 0, False))
        self.assertEqual(pv.data["total_netto"], "2870.00")  # 3 x (1000 - 10) - kasbon 100
        self.assertFalse(TrJurnal.objects.exists())

        res = self.periode(self.keuangan, "posting-periode", True)
        self.assertEqual((res.data["berhasil"], res.data["gagal"]), (3, 0))
        self.assertEqual(set(TrJurnal.objects.values_list("status", flat=True)), {"PENDING"})
        self.assertTrue(all(j.submitted_by_id == self.keuangan.pk for j in TrJurnal.objects.all()))
        self.assertEqual(self.periode(self.keuangan, "posting-periode", False).data["jumlah"], 0)
        self.assertIsNone(GajiPegawai.objects.get(periode_bulan=2).jurnal_id)

        self.assertEqual(self.periode(self.keuangan, "setujui-periode", True).status_code, 403)
        ok = self.periode(self.kepsek, "setujui-periode", True)
        self.assertEqual((ok.data["jumlah"], ok.data["berhasil"], ok.data["gagal"]), (3, 3, 0))
        self.assertEqual(set(TrJurnal.objects.values_list("status", flat=True)), {"POSTED"})
        self.assertEqual(PinjamanPegawai.objects.get().sudah_terbayar, Decimal("100"))
        self.assertEqual(self.periode(self.kepsek, "setujui-periode", False).data["jumlah"], 0)

    def test_kepsek_tidak_bisa_posting_dan_jurnal_buatannya_sendiri_gagal_per_slip(self):
        self.assertEqual(self.periode(self.kepsek, "posting-periode", True).status_code, 403)
        self.periode(self.keuangan, "posting-periode", True)
        TrJurnal.objects.filter(pk=GajiPegawai.objects.filter(pegawai=self.pegawai[2]).get().jurnal_id).update(created_by=self.kepsek)
        res = self.periode(self.kepsek, "setujui-periode", True)
        self.assertEqual((res.data["berhasil"], res.data["gagal"]), (2, 1))
        gagal = [h for h in res.data["hasil"] if h["status"] == "gagal"][0]
        self.assertIn("SoD", gagal["pesan"])
        self.assertEqual(sorted(TrJurnal.objects.values_list("status", flat=True)), ["PENDING", "POSTED", "POSTED"])

    def test_slip_menampilkan_status_jurnal(self):
        self.periode(self.keuangan, "posting-periode", True)
        self.client.force_authenticate(self.kepsek)
        rows = self.client.get("/api/v1/gaji/?page_size=50").data["results"]
        self.assertEqual(sorted(r["jurnal_status"] or "-" for r in rows), ["-", "PENDING", "PENDING", "PENDING"])
