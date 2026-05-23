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
