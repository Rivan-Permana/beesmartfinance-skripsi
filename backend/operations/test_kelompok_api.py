from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from operations.models import Jenjang, Kelompok, Siswa

User = get_user_model()


class KelompokApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin_kel", password="x")
        Group.objects.get_or_create(name="Administration")
        self.admin.groups.add(Group.objects.get(name="Administration"))
        self.client.force_authenticate(self.admin)

        self.j1 = Jenjang.objects.create(kode="TKA", nama="TK A")
        self.j2 = Jenjang.objects.create(kode="TKB", nama="TK B")
        self.k1 = Kelompok.objects.create(jenjang=self.j1, nama="Melati")
        self.k2 = Kelompok.objects.create(jenjang=self.j2, nama="Mawar")
        self.s1 = Siswa.objects.create(nama="Ana", kelompok=self.k1, status="aktif")
        self.s2 = Siswa.objects.create(nama="Budi", kelompok=self.k1, status="aktif")

    def test_pindah_siswa(self):
        res = self.client.post(
            f"/api/v1/kelompok/{self.k2.id}/pindah-siswa/",
            {"siswa_ids": [self.s1.id, self.s2.id]},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.s1.refresh_from_db()
        self.s2.refresh_from_db()
        self.assertEqual(self.s1.kelompok_id, self.k2.id)
        self.assertEqual(self.s2.kelompok_id, self.k2.id)

    def test_hapus_kelompok_berisi_siswa_ditolak(self):
        res = self.client.delete(f"/api/v1/kelompok/{self.k1.id}/")
        self.assertEqual(res.status_code, 400)
        body = str(res.data).lower()
        self.assertIn("siswa aktif", body)
