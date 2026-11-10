"""Anggaran bulanan + plafon tahunan, peran penyusun anggaran, dan subtotal laba rugi."""

import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import MsCoa, MsGolongan, MsPeriodeAkuntansi, MsSubGolongan, TrAnggaran, TrJurnal, TrJurnalDetail


def _akun(kode, nama, posisi, sub=None):
    g, _ = MsGolongan.objects.get_or_create(kode_golongan=kode[0], defaults={"nama_golongan": "G" + kode[0]})
    sg, _ = MsSubGolongan.objects.get_or_create(kode_sub=kode[:2], defaults={"golongan": g, "nama_sub": sub or "SG" + kode[:2]})
    return MsCoa.objects.create(kode_akun=kode, sub_golongan=sg, nama_akun=nama, posisi_normal=posisi)


class AnggaranBulananTests(APITestCase):
    def setUp(self):
        self.kas = _akun("111", "Kas", "D")
        self.spp = _akun("411", "SPP", "K", "PENDAPATAN USAHA")
        self.outing = _akun("5101", "TK-Outing", "D", "BEBAN KEGIATAN SEKOLAH - TK")
        self.kbm = _akun("5134", "TK-Kegiatan KBM", "D")
        self.atk = _akun("5401", "Administrasi", "D", "BEBAN OPERASIONAL SEKOLAH")
        self.periode = MsPeriodeAkuntansi.objects.create(kode="2026/2027", tgl_mulai=date(2026, 7, 1), tgl_selesai=date(2027, 6, 30))
        self.users = {}
        for role in ("Finance", "SchoolPrincipal", "BudgetPlanner", "Administration", "TeacherInCharge"):
            user = get_user_model().objects.create_user(f"ang-{role}")
            user.groups.add(Group.objects.get(name=role))
            self.users[role] = user

    def as_(self, role):
        self.client.force_authenticate(self.users[role])

    def jurnal(self, on, akun, nilai):
        j = TrJurnal.objects.create(id=uuid.uuid4(), no_bukti=str(uuid.uuid4()), tanggal=on)
        TrJurnalDetail.objects.create(jurnal=j, kode_akun=akun, debit=nilai, kredit=0)
        TrJurnalDetail.objects.create(jurnal=j, kode_akun=self.kas, debit=0, kredit=nilai)
        TrJurnal.objects.filter(pk=j.pk).update(status="POSTED")

    def plafon(self, nominal="1000000", akun="5101"):
        return self.client.post("/api/v1/anggaran/", {
            "kode_akun": akun, "bulan": None, "periode": self.periode.pk, "nominal_anggaran": nominal,
        }, format="json")

    def bulanan(self, bulan, tahun, nominal, akun="5101"):
        return self.client.post("/api/v1/anggaran/", {
            "kode_akun": akun, "tahun_anggaran": tahun, "bulan": bulan, "nominal_anggaran": nominal,
        }, format="json")

    def test_plafon_hanya_keuangan_dan_bulanan_tidak_melewati_plafon(self):
        self.as_("BudgetPlanner")
        self.assertEqual(self.plafon().status_code, 403)
        self.as_("Finance")
        res = self.plafon()
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["tahun_anggaran"], 2026)
        self.assertEqual(self.plafon().status_code, 400)  # ganda
        self.as_("BudgetPlanner")
        juli = self.bulanan(7, 2026, "600000")
        self.assertEqual(juli.status_code, 201, juli.data)
        self.assertEqual(juli.data["periode"], self.periode.pk)
        lebih = self.bulanan(1, 2027, "500000")
        self.assertEqual(lebih.status_code, 400)
        self.assertIn("Sisa plafon akun ini Rp 400.000", str(lebih.data))
        self.assertEqual(self.bulanan(1, 2027, "400000").status_code, 201)
        self.assertEqual(self.bulanan(7, 2026, "1").status_code, 400)  # bulan yang sama dua kali
        # Plafon tidak boleh diturunkan di bawah anggaran bulanan yang sudah disusun.
        self.as_("Finance")
        plafon = TrAnggaran.objects.get(bulan__isnull=True)
        turun = self.client.patch(f"/api/v1/anggaran/{plafon.pk}/", {"nominal_anggaran": "900000"}, format="json")
        self.assertEqual(turun.status_code, 400)
        self.as_("BudgetPlanner")
        self.assertEqual(self.client.delete(f"/api/v1/anggaran/{plafon.pk}/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/anggaran/{juli.data['id']}/", {"nominal_anggaran": "500000"}, format="json").status_code, 200)

    def test_akun_bukan_beban_ditolak_dan_tanpa_plafon_bebas(self):
        self.as_("BudgetPlanner")
        self.assertEqual(self.bulanan(8, 2026, "1", akun="411").status_code, 400)
        self.assertEqual(self.bulanan(8, 2026, "99999999", akun="5401").status_code, 201)

    def test_laporan_anggaran_bulanan_realisasi_per_bulan_tp(self):
        self.as_("Finance")
        self.plafon()
        self.bulanan(7, 2026, "300000")
        self.jurnal(date(2026, 7, 10), self.outing, 250000)
        self.jurnal(date(2027, 1, 5), self.outing, 100000)
        self.jurnal(date(2027, 1, 6), self.atk, 50000)
        self.jurnal(date(2027, 7, 1), self.outing, 999)  # di luar TP
        self.as_("BudgetPlanner")
        res = self.client.get(f"/api/v1/laporan/anggaran-bulanan/?periode={self.periode.pk}")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(len(res.data["bulan"]), 12)
        akun = {a["kode_akun"]: a for a in res.data["akun"]}
        outing = akun["5101"]
        self.assertEqual((outing["plafon"], outing["total_anggaran"], outing["total_realisasi"]), (1000000, 300000, 350000))
        self.assertEqual(outing["sisa_plafon"], 650000)
        self.assertEqual((outing["bulan"][0]["anggaran"], outing["bulan"][0]["realisasi"]), (300000, 250000))
        self.assertEqual(outing["bulan"][6]["realisasi"], 100000)
        self.assertIsNone(akun["5401"]["plafon"])

    def test_akses_penyusun_tanpa_jurnal_dan_pembayaran(self):
        self.as_("BudgetPlanner")
        self.assertEqual(self.client.get("/api/v1/anggaran/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/coa/").status_code, 200)
        for url in ("/api/v1/jurnal/", "/api/v1/aset/", "/api/v1/tagihan/", "/api/v1/laporan/laba-rugi/", "/api/v1/siswa/", "/api/v1/gaji/"):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        for role in ("Administration", "TeacherInCharge"):
            self.as_(role)
            self.assertEqual(self.client.get("/api/v1/anggaran/").status_code, 403)
            self.assertEqual(self.client.get("/api/v1/laporan/anggaran-bulanan/").status_code, 403)

    def test_laba_rugi_subtotal_per_kelompok(self):
        self.jurnal(date(2026, 8, 1), self.outing, 100)
        self.jurnal(date(2026, 8, 2), self.kbm, 50)
        self.jurnal(date(2026, 8, 3), self.atk, 25)
        self.as_("Finance")
        res = self.client.get("/api/v1/laporan/laba-rugi/?tahun=2026")
        self.assertEqual(res.status_code, 200, res.data)
        kelompok = [(k["kode"], k["nama"], k["total"]) for k in res.data["kelompok_beban"]]
        self.assertEqual(kelompok, [("51", "BEBAN KEGIATAN SEKOLAH - TK", 150), ("54", "BEBAN OPERASIONAL SEKOLAH", 25)])
        baris = {r["kode_akun"]: r for r in res.data["beban"]}
        self.assertEqual(baris["5134"]["kelompok_kode"], "51")
