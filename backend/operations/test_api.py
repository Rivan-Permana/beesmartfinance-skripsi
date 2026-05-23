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
        r = self.client.post("/api/tagihan/", payload, format="json")
        self.assertEqual(r.status_code, 201)
        tid = r.data["id"]

        r = self.client.post(f"/api/tagihan/{tid}/bayar/")
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
        r = self.client.post(f"/api/gaji/{self.gaji.id}/posting/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("jurnal_id", r.data)

    def test_susutkan_aset(self):
        r = self.client.post(f"/api/aset/{self.aset.id}/susutkan/")
        self.assertEqual(r.status_code, 200)
        self.aset.refresh_from_db()
        self.assertEqual(self.aset.akumulasi_penyusutan, Decimal("500000"))
