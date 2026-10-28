"""Impor biodata siswa dari CSV rekap kelas (Batch 5). Semua data di sini rekaan."""

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from operations.models import Jenjang, Kelompok, Siswa, Tagihan
from operations.services.impor_biodata import parse_tanggal, rapikan_alamat, rapikan_telepon

CSV = """,,,,,,,,,,,
RA Contoh,,,,,,,,,,,
,,,,,,,,,,,
Kelas,No.,Nama Siswa,JK,Tempat,Tanggal Lahir,Usia,Alamat,Orang Tua,,,
,,,,,,,,Nama Ayah,No. Tlp,Nama Bunda,No. Tlp
BU MAWAR,1,Anak Satu,P,jakarta,24-Nov-21,4 Tahun,jl melati no 5 rt 4 rw 3,Ayah Satu,0812-1111-2222,Ibu Satu,0813 3333 4444
,2,ANAK  dua,L,Bekasi,4-Agu-21,5 Tahun,,Ayah Dua,+62 812 5555 6666,,
,3,Anak Tiga,X,Bogor,1-Jan-22,4 Tahun,Gg Mangga,,,,
Laki-laki,1,1,1,,,,,,,,
Perempuan,2,1,1,,,,,,,,
,,,,,,,,,,,
Kelas,No.,Nama Siswa,JK,Tempat,Tanggal Lahir,Usia,Alamat,Orang Tua,,,
,,,,,,,,Nama Ayah,No. Tlp,Nama Bunda,No. Tlp
Lebah 1,1,Anak Empat,L,Depok,30-Des-22,3 Tahun,"Perum Asri blok c6, kec cimanggis",Ayah Empat,085642441018'0,Ibu Empat,081277778888
"""


class NormalisasiTests(SimpleTestCase):
    def test_alamat_dirapikan(self):
        self.assertEqual(rapikan_alamat("jl arjuna no.40B rt006 rw05 kel. munjul  kec cipayung,"),
                         "Jl. Arjuna No. 40B RT 006/RW 005 Kel. Munjul Kec. Cipayung")
        self.assertEqual(rapikan_alamat("JALAN RAWABOLA NO. 38,RT.6/RW.7 , kelapa dua"), "Jl. Rawabola No. 38, RT 006/RW 007, Kelapa Dua")
        self.assertEqual(rapikan_alamat("komplek TNI blok c6"), "Komplek TNI Blok C6")
        self.assertIsNone(rapikan_alamat("   "))

    def test_tanggal_dan_telepon(self):
        self.assertEqual(parse_tanggal("4-Agu-21"), date(2021, 8, 4))
        self.assertEqual(parse_tanggal("24/11/2021"), date(2021, 11, 24))
        with self.assertRaises(ValueError):
            parse_tanggal("31-Feb-21")
        self.assertEqual(rapikan_telepon("+62 812 5555 6666"), ("081255556666", None))
        self.assertEqual(rapikan_telepon("81299998888"), ("081299998888", None))
        self.assertEqual(rapikan_telepon("81.299.998.888"), ("081299998888", None))
        nomor, peringatan = rapikan_telepon("085642441018'0")
        self.assertEqual(nomor, "0856424410180")
        self.assertIn("perlu dicek", peringatan)


class ImporBiodataApiTests(APITestCase):
    def setUp(self):
        tk = Jenjang.objects.create(kode="TKA", nama="TK A")
        pg = Jenjang.objects.create(kode="PG", nama="Playgroup")
        self.mawar = Kelompok.objects.create(nama="Bu Mawar 26/27", jenjang=tk)
        self.lebah = Kelompok.objects.create(nama="Lebah 1 26/27", jenjang=pg)
        self.lama = Siswa.objects.create(nama="Anak Dua", spp_nominal=750000, alamat="Alamat lama", nama_ibu="Ibu Lama")
        self.tu = get_user_model().objects.create_user("impor-tu")
        self.tu.groups.add(Group.objects.get(name="Administration"))
        self.client.force_authenticate(self.tu)

    def post(self, simpan=False, kelas_map=None, isi=CSV):
        data = {"berkas": SimpleUploadedFile("biodata.csv", isi.encode(), content_type="text/csv"), "simpan": simpan}
        if kelas_map is not None:
            import json
            data["kelas_map"] = json.dumps(kelas_map)
        return self.client.post("/api/v1/siswa/impor-biodata/", data, format="multipart")

    def test_pratinjau_tidak_menyimpan_dan_menyarankan_kelompok(self):
        res = self.post()
        self.assertEqual(res.status_code, 200, res.data)
        self.assertFalse(res.data["disimpan"])
        self.assertEqual(dict(res.data["ringkasan"]), {"baru": 2, "ubah": 1, "sama": 0, "galat": 1, "peringatan": 1})
        self.assertEqual({k["kelas"]: k["kelompok"] for k in res.data["kelas"]}, {"BU MAWAR": self.mawar.pk, "Lebah 1": self.lebah.pk})
        baris = {b["nama"]: b for b in res.data["baris"]}
        self.assertEqual(baris["Anak Tiga"]["aksi"], "galat")
        self.assertIn("L atau P", baris["Anak Tiga"]["galat"])
        dua = baris["ANAK dua"]
        self.assertEqual((dua["aksi"], dua["siswa"]), ("ubah", self.lama.pk))
        # Sel kosong (alamat, ibu) tidak menghapus data lama.
        self.assertNotIn("alamat", dua["perubahan"])
        self.assertNotIn("nama_ibu", dua["perubahan"])
        self.assertEqual(dua["perubahan"]["kontak_ayah"], [None, "081255556666"])
        self.assertNotIn("nama", dua["perubahan"])
        self.assertEqual(baris["Anak Satu"]["nilai"]["alamat"], "Jl. Melati No. 5 RT 004/RW 003")
        self.assertEqual(baris["Anak Empat"]["nilai"]["alamat"], "Perum Asri Blok C6, Kec. Cimanggis")
        self.assertEqual(Siswa.objects.count(), 1)

    def test_simpan_membuat_dan_memperbarui_lalu_impor_ulang_tanpa_duplikat(self):
        res = self.post(simpan=True)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(res.data["disimpan"])
        self.assertEqual(Siswa.objects.count(), 3)
        baru = Siswa.objects.get(nama="Anak Satu")
        self.assertEqual((baru.status, baru.spp_nominal, baru.kelompok_id, baru.jenis_kelamin), ("aktif", 0, self.mawar.pk, "P"))
        self.assertEqual((baru.tempat_lahir, baru.tanggal_lahir, baru.kontak_ibu), ("Jakarta", date(2021, 11, 24), "081333334444"))
        self.assertEqual(baru.history.first().history_change_reason, "Impor biodata CSV")
        self.lama.refresh_from_db()
        self.assertEqual((self.lama.nama, self.lama.spp_nominal, self.lama.alamat, self.lama.nama_ibu), ("Anak Dua", 750000, "Alamat lama", "Ibu Lama"))
        self.assertEqual(self.lama.kelompok_id, self.mawar.pk)
        self.assertFalse(Tagihan.objects.exists())
        ulang = self.post(simpan=True)
        self.assertEqual(dict(ulang.data["ringkasan"]), {"baru": 0, "ubah": 0, "sama": 3, "galat": 1, "peringatan": 1})
        self.assertEqual(Siswa.objects.count(), 3)

    def test_kelas_bisa_tidak_mengubah_kelompok(self):
        res = self.post(simpan=True, kelas_map={"BU MAWAR": None, "Lebah 1": self.lebah.pk})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIsNone(Siswa.objects.get(nama="Anak Satu").kelompok_id)
        self.assertEqual(Siswa.objects.get(nama="Anak Empat").kelompok_id, self.lebah.pk)

    def test_berkas_salah_dan_role_lain_ditolak(self):
        salah = self.post(isi="nama,umur\nA,3\n")
        self.assertEqual(salah.status_code, 400)
        self.assertIn("Nama Siswa", salah.data["berkas"])
        self.assertEqual(self.post(kelas_map={"BU MAWAR": 9999}).status_code, 400)
        for role in ("Finance", "TeacherInCharge", "SchoolPrincipal"):
            user = get_user_model().objects.create_user(f"impor-{role}")
            user.groups.add(Group.objects.get(name=role))
            self.client.force_authenticate(user)
            self.assertEqual(self.post().status_code, 403)
        self.assertEqual(Siswa.objects.count(), 1)
