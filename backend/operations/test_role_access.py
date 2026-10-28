"""Matriks akses per role setelah revisi spreadsheet 28/10/2026 (Batch 2)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.test_api import _coa
from operations.models import Jenjang, Kelompok, Pegawai, Siswa


class RoleAccessMatrixTests(APITestCase):
    def setUp(self):
        self.users = {}
        for role in ("Finance", "SchoolPrincipal", "Administration", "TeacherInCharge"):
            user = get_user_model().objects.create_user(f"matrix-{role}")
            user.groups.add(Group.objects.get(name=role))
            self.users[role] = user
        self.pegawai = Pegawai.objects.create(nama="Bu Ani", jabatan="Walas")
        jenjang = Jenjang.objects.create(kode="TKA", nama="TK A")
        self.kelompok = Kelompok.objects.create(nama="Lebah", jenjang=jenjang)
        self.siswa = Siswa.objects.create(nama="Ayu", kelompok=self.kelompok)
        _coa("1101", "KAS", "D")
        _coa("5101", "BEBAN KEGIATAN", "D")

    def as_role(self, role):
        self.client.force_authenticate(self.users[role])
        return self.client

    def test_teacher_records_student_attendance(self):
        payload = {"siswa": self.siswa.pk, "tanggal": "2026-10-28", "status": "hadir"}
        self.assertEqual(self.as_role("TeacherInCharge").post("/api/v1/kehadiran-siswa/", payload).status_code, 201)
        self.assertEqual(self.as_role("Finance").post("/api/v1/kehadiran-siswa/", payload).status_code, 403)

    def test_finance_reads_students_and_registrations_only(self):
        client = self.as_role("Finance")
        self.assertEqual(client.get("/api/v1/siswa/").status_code, 200)
        self.assertEqual(client.get("/api/v1/kelompok/").status_code, 200)
        self.assertEqual(client.get("/api/v1/pendaftaran-siswa/").status_code, 200)
        self.assertEqual(client.post("/api/v1/siswa/", {"nama": "X"}).status_code, 403)
        self.assertEqual(client.patch(f"/api/v1/siswa/{self.siswa.pk}/", {"nama": "Y"}).status_code, 403)
        self.assertEqual(client.post("/api/v1/pendaftaran-siswa/", {"nama_calon": "X", "tanggal_daftar": "2026-10-01"}).status_code, 403)

    def test_principal_reads_staff_attendance_recap_but_cannot_record(self):
        client = self.as_role("SchoolPrincipal")
        self.assertEqual(client.get("/api/v1/absen-pegawai/rekap-bulanan/?bulan=10&tahun=2026").status_code, 200)
        self.assertEqual(client.post("/api/v1/absen-pegawai/", {"pegawai": self.pegawai.pk, "tanggal": "2026-10-28", "hadir": 1}).status_code, 403)

    def test_principal_requests_loan_and_finance_disburses(self):
        payload = {"pegawai": self.pegawai.pk, "tanggal_pinjaman": "2026-10-28", "jumlah_pinjaman": "500000", "tenor_bulan": 2, "angsuran_per_bulan": "250000"}
        self.assertEqual(self.as_role("Finance").post("/api/v1/pinjaman/", payload).status_code, 403)
        created = self.as_role("SchoolPrincipal").post("/api/v1/pinjaman/", payload)
        self.assertEqual(created.status_code, 201, created.data)
        loan = created.data["id"]
        self.assertEqual(self.client.post(f"/api/v1/pinjaman/{loan}/cairkan/").status_code, 403)
        self.assertEqual(self.as_role("Finance").patch(f"/api/v1/pinjaman/{loan}/", {"tenor_bulan": 4}).status_code, 200)
        self.assertNotEqual(self.client.post(f"/api/v1/pinjaman/{loan}/cairkan/").status_code, 403)
        self.assertEqual(self.as_role("Administration").get("/api/v1/pinjaman/").status_code, 403)

    def test_principal_creates_salary_slip_but_only_finance_posts(self):
        created = self.as_role("SchoolPrincipal").post("/api/v1/gaji/", {"pegawai": self.pegawai.pk, "periode_bulan": 10, "periode_tahun": 2026, "gaji_pokok": "1000000"})
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(self.client.post(f"/api/v1/gaji/{created.data['id']}/posting/").status_code, 403)
        self.assertNotEqual(self.as_role("Finance").post(f"/api/v1/gaji/{created.data['id']}/posting/").status_code, 403)

    def test_finance_manages_activity_budget_principal_reads(self):
        payload = {"nama": "Manasik", "akun_beban": "5101", "pagu": "2000000", "penanggung_jawab": self.pegawai.pk}
        self.assertEqual(self.as_role("SchoolPrincipal").post("/api/v1/kegiatan/", payload).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/kegiatan/").status_code, 200)
        created = self.as_role("Finance").post("/api/v1/kegiatan/", payload)
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["penanggung_jawab_nama"], "Bu Ani")
        realisasi = {"tanggal": "2026-10-28", "deskripsi": "Sewa bus", "nominal": "100000"}
        self.assertEqual(self.as_role("SchoolPrincipal").post(f"/api/v1/kegiatan/{created.data['id']}/realisasi/", realisasi).status_code, 403)
        self.assertEqual(self.as_role("Finance").post(f"/api/v1/kegiatan/{created.data['id']}/realisasi/", realisasi).status_code, 403)

    def test_administration_drafts_journal_finance_records(self):
        payload = {"no_bukti": "TU-1", "tanggal": "2026-10-28", "keterangan": "Beli ATK", "detail": [
            {"kode_akun": "5101", "debit": "1000", "kredit": "0"},
            {"kode_akun": "1101", "debit": "0", "kredit": "1000"},
        ]}
        client = self.as_role("Administration")
        created = client.post("/api/v1/jurnal/", payload, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["status"], "DRAFT")
        self.assertEqual(client.post(f"/api/v1/jurnal/{created.data['id']}/catat/").status_code, 403)
        self.assertEqual(client.post(f"/api/v1/jurnal/{created.data['id']}/submit/").status_code, 403)
        self.assertEqual(client.delete(f"/api/v1/jurnal/{created.data['id']}/").status_code, 204)
        self.assertEqual(self.as_role("TeacherInCharge").post("/api/v1/jurnal/", payload, format="json").status_code, 403)


class PegawaiStatusTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("status-admin")
        user.groups.add(Group.objects.get(name="Administration"))
        self.client.force_authenticate(user)

    def test_cuti_is_not_active_and_status_aktif_follows_status(self):
        pegawai = Pegawai.objects.create(nama="Pak Budi")
        response = self.client.patch(f"/api/v1/pegawai/{pegawai.pk}/", {"status": "cuti", "status_aktif": True}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual((response.data["status"], response.data["status_aktif"]), ("cuti", False))
        pegawai.refresh_from_db()
        pegawai.status = "aktif"
        pegawai.save(update_fields=["status"])
        pegawai.refresh_from_db()
        self.assertTrue(pegawai.status_aktif)
        self.assertEqual(self.client.patch(f"/api/v1/pegawai/{pegawai.pk}/", {"status": "pensiun"}, format="json").status_code, 400)

    def test_salary_slip_still_allowed_for_employee_on_leave(self):
        pegawai = Pegawai.objects.create(nama="Bu Cuti", status="cuti")
        finance = get_user_model().objects.create_user("status-finance")
        finance.groups.add(Group.objects.get(name="Finance"))
        self.client.force_authenticate(finance)
        response = self.client.post("/api/v1/gaji/", {"pegawai": pegawai.pk, "periode_bulan": 10, "periode_tahun": 2026, "gaji_pokok": "1000000"})
        self.assertEqual(response.status_code, 201, response.data)
