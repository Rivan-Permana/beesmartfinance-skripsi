"""Impor SPP dari tab master Recap Cash In (Batch 6). Semua data di sini rekaan."""

import csv
import io
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from operations.models import Siswa, Tagihan

BULAN = ["Juli", "Agustus", "September", "Oktober"]


def master_csv(siswa):
    """Tata letak tab master: baris nomor kolom, judul, sub-judul per bulan, lalu satu baris per siswa."""
    kiri = ["", "", "Nama", "PUTIH", "OLGA", "Jenis", "KELAS", "STATUS"]
    judul, sub = list(kiri), [""] * len(kiri)
    for b in BULAN:
        judul += [b, "", "", "", "", "", ""]
        sub += ["Tgl", "SPP", "Tgl", "Cat", "Jem", "Tgl", "LSU"]
    rows = [[str(i) for i in range(len(judul))], judul, sub]
    for no, (guru, nama, kelas, spp) in enumerate(siswa, start=1):
        row = [guru, str(no), nama, "S", "S", "P", kelas, "BARU"]
        for v in spp + [""] * (len(BULAN) - len(spp)):
            row += ["3-Agu" if v else "", v, "", "176.000", "", "", ""]
        rows.append(row)
    rows.append(["Laki-laki", "", "54", "", "", "", "", ""])
    out = io.StringIO()
    csv.writer(out).writerows(rows)
    return out.getvalue()


class ImporSppTests(APITestCase):
    def setUp(self):
        mk = lambda nama, spp="0": Siswa.objects.create(nama=nama, spp_nominal=spp)  # noqa: E731
        self.baru = mk("Anak Baru")
        self.sama = mk("Anak Sama", "1350000")
        self.beda = mk("Anak Beda", "1300000")
        self.variasi = mk("Anak Variasi")
        self.kosong = mk("Anak Kosong")
        self.janggal = mk("Anak Janggal")
        self.tu = get_user_model().objects.create_user("spp-tu")
        self.tu.groups.add(Group.objects.get(name="Administration"))
        self.client.force_authenticate(self.tu)
        self.csv = master_csv([
            ("BU MAWAR", "anak  BARU", "TK A", ["1.350.000", "1.350.000", "1.350.000"]),
            ("", "Anak Sama", "TK A", ["1.350.000"]),
            ("", "Anak Beda", "TK B", ["1.350.000", "1.350.000"]),
            ("", "Anak Variasi", "TK B", ["1.300.000", "650.000"]),
            ("", "Anak Kosong", "PG Lebah 1", []),
            ("", "Anak Janggal", "PG Lebah 1", ["Rp2.950.000"]),
            ("", "Anak Tidak Ada", "PG Lebah 1", ["950.000"]),
        ])

    def post(self, simpan=False, isi=None):
        berkas = SimpleUploadedFile("master.csv", (isi or self.csv).encode(), content_type="text/csv")
        return self.client.post("/api/v1/siswa/impor-spp/", {"berkas": berkas, "simpan": simpan}, format="multipart")

    def test_pratinjau_menandai_dan_tidak_menyimpan(self):
        res = self.post()
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(dict(res.data["ringkasan"]), {"isi": 1, "sama": 1, "beda": 1, "cek": 3, "galat": 1})
        baris = {b["nama"]: b for b in res.data["baris"]}
        self.assertEqual((baris["anak BARU"]["aksi"], baris["anak BARU"]["spp_baru"]), ("isi", "1350000.00"))
        self.assertEqual(baris["anak BARU"]["kelas"], "TK A")
        self.assertEqual((baris["Anak Beda"]["spp_lama"], baris["Anak Beda"]["spp_baru"]), ("1300000.00", "1350000.00"))
        self.assertIn("berbeda antar bulan", baris["Anak Variasi"]["alasan"])
        self.assertEqual(baris["Anak Variasi"]["nilai"], [650000, 1300000])
        self.assertIn("Belum ada pembayaran", baris["Anak Kosong"]["alasan"])
        self.assertIn("beberapa bulan", baris["Anak Janggal"]["alasan"])
        self.assertIn("tidak ditemukan", baris["Anak Tidak Ada"]["alasan"])
        self.assertNotIn("54", baris)
        self.baru.refresh_from_db()
        self.assertEqual(self.baru.spp_nominal, 0)

    def test_simpan_hanya_mengisi_spp_nol_lalu_impor_ulang_sama(self):
        res = self.post(simpan=True)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["diisi"], 1)
        for siswa, harap in ((self.baru, "1350000"), (self.beda, "1300000"), (self.variasi, "0"), (self.janggal, "0")):
            siswa.refresh_from_db()
            self.assertEqual(siswa.spp_nominal, Decimal(harap))
        self.assertEqual(self.baru.history.first().history_change_reason, "Impor SPP CSV")
        self.assertFalse(Tagihan.objects.exists())
        ulang = self.post(simpan=True)
        self.assertEqual((ulang.data["diisi"], ulang.data["ringkasan"]["isi"], ulang.data["ringkasan"]["sama"]), (0, 0, 2))

    def test_berkas_salah_dan_role_lain_ditolak(self):
        salah = self.post(isi="Kelas,No.,Nama Siswa\nBU A,1,Anak\n")
        self.assertEqual(salah.status_code, 400)
        self.assertIn("tab master", salah.data["berkas"])
        for role in ("Finance", "TeacherInCharge", "SchoolPrincipal"):
            user = get_user_model().objects.create_user(f"spp-{role}")
            user.groups.add(Group.objects.get(name=role))
            self.client.force_authenticate(user)
            self.assertEqual(self.post(simpan=True).status_code, 403)
        self.baru.refresh_from_db()
        self.assertEqual(self.baru.spp_nominal, 0)
