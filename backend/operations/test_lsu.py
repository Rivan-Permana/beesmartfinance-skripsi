"""Modul LSU: paket 8/16 pertemuan, catatan pertemuan oleh TU, tagihan per paket."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from operations.models import Jenjang, Kelompok, MsPostingRule, PaketLSU, Siswa, Tagihan
from operations.services.billing import catat_saldo_awal_tagihan
from operations.test_tp_batch import _coa


class LsuTests(APITestCase):
    def setUp(self):
        kas = _coa("1101", "KAS", "D")
        _coa("417", "Lain", "K")
        MsPostingRule.objects.create(event_code="TAGIHAN", komponen="LAIN", akun_debit=kas, akun_kredit_id="417")
        kelompok = Kelompok.objects.create(nama="TKA", jenjang=Jenjang.objects.create(kode="TKA", nama="TK A"))
        self.siswa = Siswa.objects.create(nama="Raka", kelompok=kelompok, spp_nominal=1, status="aktif")
        self.users = {}
        for role in ("Administration", "Finance", "SchoolPrincipal", "TeacherInCharge"):
            user = get_user_model().objects.create_user(f"lsu-{role}")
            user.groups.add(Group.objects.get(name=role))
            self.users[role] = user
        self.client.force_authenticate(self.users["Administration"])

    def buat(self, sesi=8, mulai="2027-01-04"):
        return self.client.post("/api/v1/paket-lsu/", {
            "siswa": self.siswa.pk, "jumlah_sesi": sesi, "harga": "1200000", "tanggal_mulai": mulai,
        }, format="json")

    def catat(self, paket_id, tanggal):
        return self.client.post(f"/api/v1/paket-lsu/{paket_id}/pertemuan/", {"tanggal": tanggal}, format="json")

    def test_paket_membuat_tagihan_dan_sesi_dihabiskan(self):
        res = self.buat()
        self.assertEqual(res.status_code, 201, res.data)
        tagihan = Tagihan.objects.get(pk=res.data["tagihan"])
        self.assertEqual((tagihan.jenis, tagihan.periode_bulan, tagihan.total), ("LSU", 1, 1200000))
        self.assertEqual(tagihan.detail.get().akun_pendapatan_id, "417")
        pid = res.data["id"]
        self.assertEqual(self.catat(pid, "2027-01-03").status_code, 400)  # sebelum paket mulai
        for hari in range(4, 12):
            self.assertEqual(self.catat(pid, f"2027-01-{hari:02d}").status_code, 201)
        habis = self.catat(pid, "2027-01-20")
        self.assertEqual(habis.status_code, 400)
        self.assertIn("sudah terpakai", str(habis.data))
        self.assertEqual(self.client.get(f"/api/v1/paket-lsu/{pid}/").data["sesi_terpakai"], 8)

    def test_paket_baru_ditolak_selama_sesi_lama_tersisa_dan_bulan_sama_boleh(self):
        pid = self.buat().data["id"]
        ditolak = self.buat(sesi=16, mulai="2027-01-25")
        self.assertEqual(ditolak.status_code, 400)
        self.assertIn("masih punya sisa sesi", str(ditolak.data))
        for hari in range(4, 12):
            self.catat(pid, f"2027-01-{hari:02d}")
        self.assertEqual(self.buat(sesi=16, mulai="2027-01-25").status_code, 201)
        self.assertEqual(Tagihan.objects.filter(siswa=self.siswa, jenis="LSU", periode_bulan=1).count(), 2)

    def test_duplikat_tanggal_dan_hapus_pertemuan(self):
        pid = self.buat().data["id"]
        self.catat(pid, "2027-01-05")
        self.assertEqual(self.catat(pid, "2027-01-05").status_code, 400)
        pertemuan_id = PaketLSU.objects.get(pk=pid).pertemuan.get().pk
        res = self.client.delete(f"/api/v1/paket-lsu/{pid}/pertemuan/{pertemuan_id}/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["sesi_terpakai"], 0)

    def test_hapus_paket_hanya_tanpa_pertemuan_dan_penerimaan(self):
        res = self.buat()
        pid, tid = res.data["id"], res.data["tagihan"]
        self.assertEqual(self.client.delete(f"/api/v1/tagihan/{tid}/").status_code, 400)
        catat_saldo_awal_tagihan(Tagihan.objects.get(pk=tid), tanggal=date(2026, 12, 31), nominal=Decimal(1))
        self.assertEqual(self.client.delete(f"/api/v1/paket-lsu/{pid}/").status_code, 400)
        res2 = self.client.post("/api/v1/paket-lsu/", {
            "siswa": Siswa.objects.create(nama="Lain", spp_nominal=1, status="aktif").pk,
            "jumlah_sesi": 16, "harga": "2000000", "tanggal_mulai": "2027-01-04",
        }, format="json")
        self.assertEqual(self.client.delete(f"/api/v1/paket-lsu/{res2.data['id']}/").status_code, 204)
        self.assertFalse(Tagihan.objects.filter(pk=res2.data["tagihan"]).exists())

    def test_validasi_dan_akses(self):
        self.assertEqual(self.buat(sesi=10).status_code, 400)
        pid = self.buat().data["id"]
        for role in ("Finance", "SchoolPrincipal"):
            self.client.force_authenticate(self.users[role])
            self.assertEqual(self.client.get("/api/v1/paket-lsu/").status_code, 200)
            self.assertEqual(self.catat(pid, "2027-01-05").status_code, 403)
        self.client.force_authenticate(self.users["TeacherInCharge"])
        self.assertEqual(self.client.get("/api/v1/paket-lsu/").status_code, 403)
