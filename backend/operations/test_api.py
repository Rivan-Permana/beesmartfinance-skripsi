from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan
from operations.models import Siswa

User = get_user_model()


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


class TagihanApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin1", password="x")
        self.admin.groups.add(Group.objects.get(name="Administration"))
        _coa("1101", "KAS", "D")
        _coa("4101", "PENDAPATAN SPP", "K")
        self.siswa = Siswa.objects.create(nama="Dina", spp_nominal=Decimal("500000"))
        self.client.force_authenticate(self.admin)

    def test_buat_tagihan_lalu_bayar_auto_jurnal(self):
        payload = {
            "siswa": self.siswa.id, "periode_bulan": 2, "periode_tahun": 2026,
            "total": "500000",
            "detail": [
                {"komponen": "SPP", "akun_pendapatan": "4101", "nominal": "500000"}
            ],
        }
        r = self.client.post("/api/v1/tagihan/", payload, format="json")
        self.assertEqual(r.status_code, 201)
        tid = r.data["id"]

        r = self.client.post(f"/api/v1/tagihan/{tid}/bayar/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("jurnal_id", r.data)
        self.assertEqual(r.data["tagihan"]["status"], "LUNAS")


class KeuanganActionApiTests(APITestCase):
    def setUp(self):
        self.finance = User.objects.create_user("finance3", password="x")
        self.finance.groups.add(Group.objects.get(name="Finance"))
        for kode, nama, pos in [
            ("1101", "KAS", "D"), ("1103", "PIUTANG", "D"),
            ("2101", "UTANG ASURANSI", "K"), ("5201", "BEBAN GAJI", "D"),
            ("1201", "PERALATAN", "D"), ("1202", "AKUM", "K"), ("5301", "BEBAN DEPR", "D"),
        ]:
            _coa(kode, nama, pos)
        from operations.models import FixedAsset, GajiPegawai, Pegawai
        from datetime import date

        self.pegawai = Pegawai.objects.create(nama="Guru A")
        self.gaji = GajiPegawai.objects.create(
            pegawai=self.pegawai, periode_bulan=2, periode_tahun=2026,
            gaji_pokok=Decimal("3000000"),
        )
        self.aset = FixedAsset.objects.create(
            nama="AC", akun_aset_id="1201", akun_akumulasi_id="1202",
            akun_beban_depr_id="5301", tanggal_perolehan=date(2026, 1, 1),
            harga_perolehan=Decimal("6000000"), umur_manfaat_bulan=12,
        )
        self.client.force_authenticate(self.finance)

    def test_posting_gaji(self):
        r = self.client.post(f"/api/v1/gaji/{self.gaji.id}/posting/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("jurnal_id", r.data)

    def test_susutkan_aset(self):
        r = self.client.post(f"/api/v1/aset/{self.aset.id}/susutkan/")
        self.assertEqual(r.status_code, 200)
        self.aset.refresh_from_db()
        self.assertEqual(self.aset.akumulasi_penyusutan, Decimal("500000"))

    def test_gaji_tidak_bisa_dibaca_administration(self):
        # data gaji sensitif: Administration tidak boleh baca
        admin = User.objects.create_user("admx", password="x")
        admin.groups.add(Group.objects.get(name="Administration"))
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get("/api/v1/gaji/").status_code, 403)
        # Finance boleh
        self.client.force_authenticate(self.finance)
        self.assertEqual(self.client.get("/api/v1/gaji/").status_code, 200)


class GapFeatureApiTests(APITestCase):
    def setUp(self):
        from operations.models import Kegiatan, MsPostingRule, PendaftaranSiswa

        self.admin = User.objects.create_user("adm", password="x")
        self.admin.groups.add(Group.objects.get(name="Administration"))
        self.teacher = User.objects.create_user("teach", password="x")
        self.teacher.groups.add(Group.objects.get(name="TeacherInCharge"))

        _coa("1101", "KAS", "D")
        _coa("4101", "PEND SPP", "K")
        _coa("4102", "PEND SITIN", "K")
        _coa("4103", "PEND DAFTAR", "K")
        _coa("5101", "BEBAN KEGIATAN", "D")
        for komp, akun in [("SPP", "4101"), ("SITIN", "4102"), ("PENDAFTARAN", "4103")]:
            MsPostingRule.objects.create(
                event_code="TAGIHAN" if komp == "SPP" else komp,
                komponen=komp, akun_debit_id="1101", akun_kredit_id=akun,
            )
        self.MsPostingRule = MsPostingRule
        self.Kegiatan = Kegiatan
        self.PendaftaranSiswa = PendaftaranSiswa

    def test_generate_tagihan_dari_spp(self):
        siswa = Siswa.objects.create(nama="Eka", spp_nominal=Decimal("500000"))
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/v1/tagihan/generate/", {
            "siswa": siswa.id, "periode_bulan": 2, "periode_tahun": 2026,
        }, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["total"], "500000.00")

    def test_struk_tagihan(self):
        siswa = Siswa.objects.create(nama="Fajar", spp_nominal=Decimal("300000"))
        self.client.force_authenticate(self.admin)
        tid = self.client.post("/api/v1/tagihan/generate/", {
            "siswa": siswa.id, "periode_bulan": 3, "periode_tahun": 2026,
        }, format="json").data["id"]
        r = self.client.get(f"/api/v1/tagihan/{tid}/struk/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["rincian"]), 1)

    def test_kegiatan_realisasi_dan_pagu(self):
        self.client.force_authenticate(self.teacher)
        keg = self.Kegiatan.objects.create(
            nama="Outing", akun_beban_id="5101", pagu=Decimal("1000000"),
        )
        r = self.client.post(f"/api/v1/kegiatan/{keg.id}/realisasi/", {
            "nominal": "400000", "deskripsi": "sewa bus", "tanggal": "2026-02-10",
        }, format="json")
        self.assertEqual(r.status_code, 201)
        # melebihi pagu -> ditolak
        r = self.client.post(f"/api/v1/kegiatan/{keg.id}/realisasi/", {
            "nominal": "700000", "tanggal": "2026-02-11",
        }, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.get(f"/api/v1/kegiatan/{keg.id}/laporan/")
        self.assertEqual(r.data["realisasi"], Decimal("400000"))

    def test_pendaftaran_sitin_lalu_finalisasi(self):
        self.client.force_authenticate(self.admin)
        pid = self.client.post("/api/v1/pendaftaran-siswa/", {
            "nama_calon": "Gita", "tanggal_daftar": "2026-01-10",
            "biaya_sitin": "100000", "biaya_pendaftaran": "500000",
        }, format="json").data["id"]
        self.assertEqual(self.client.post(f"/api/v1/pendaftaran-siswa/{pid}/bayar-sitin/").status_code, 200)
        r = self.client.post(f"/api/v1/pendaftaran-siswa/{pid}/finalisasi/", {"spp_nominal": "400000"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "REGISTERED")
        self.assertIsNotNone(r.data["siswa"])
