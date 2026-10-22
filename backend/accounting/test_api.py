from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan, TrJurnal

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


class JurnalApiTests(APITestCase):
    def setUp(self):
        self.finance = User.objects.create_user("finance", password="x")
        self.finance.groups.add(Group.objects.get(name="Finance"))
        self.principal = User.objects.create_user("principal", password="x")
        self.principal.groups.add(Group.objects.get(name="SchoolPrincipal"))
        self.admin = User.objects.create_user("admin1", password="x")
        self.admin.groups.add(Group.objects.get(name="Administration"))
        _coa("1101", "KAS", "D")
        _coa("4101", "PENDAPATAN", "K")

    def _payload(self, no="JV1"):
        return {
            "no_bukti": no, "tanggal": "2026-02-01", "keterangan": "tes",
            "detail": [
                {"kode_akun": "1101", "debit": "1000", "kredit": "0"},
                {"kode_akun": "4101", "debit": "0", "kredit": "1000"},
            ],
        }

    def test_butuh_autentikasi(self):
        resp = self.client.post("/api/v1/jurnal/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 401)

    def test_hanya_finance_boleh_buat(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.post("/api/v1/jurnal/", self._payload(), format="json").status_code,
            403,
        )
        self.client.force_authenticate(self.finance)
        resp = self.client.post("/api/v1/jurnal/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], "DRAFT")

    def test_jurnal_tidak_seimbang_ditolak(self):
        self.client.force_authenticate(self.finance)
        bad = self._payload()
        bad["detail"][0]["debit"] = "999"
        self.assertEqual(
            self.client.post("/api/v1/jurnal/", bad, format="json").status_code, 400
        )

    def test_alur_maker_checker(self):
        self.client.force_authenticate(self.finance)
        jid = self.client.post("/api/v1/jurnal/", self._payload(), format="json").data["id"]
        # submit oleh finance
        TrJurnal.objects.filter(pk=jid).update(tipe_sumber="AUTO_PAYROLL")
        r = self.client.post(f"/api/v1/jurnal/{jid}/submit/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "PENDING")
        # finance tidak boleh approve
        self.assertEqual(self.client.post(f"/api/v1/jurnal/{jid}/approve/").status_code, 403)
        # principal approve -> POSTED
        self.client.force_authenticate(self.principal)
        r = self.client.post(f"/api/v1/jurnal/{jid}/approve/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "POSTED")

    def test_void_membuat_pembalik(self):
        self.client.force_authenticate(self.finance)
        jid = self.client.post("/api/v1/jurnal/", self._payload("JV9"), format="json").data["id"]
        self.client.post(f"/api/v1/jurnal/{jid}/submit/")
        self.client.force_authenticate(self.principal)
        self.client.post(f"/api/v1/jurnal/{jid}/approve/")
        r = self.client.post(f"/api/v1/jurnal/{jid}/void/")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["pembalik"]["tipe_sumber"], "REVERSAL")

    def test_laporan_neraca_saldo(self):
        self.client.force_authenticate(self.finance)
        self.assertEqual(self.client.get("/api/v1/laporan/neraca-saldo/").status_code, 200)

    def test_pelanggaran_constraint_jadi_400_bukan_500(self):
        # baris dgn debit & kredit sama-sama > 0 melanggar CHECK one_side_only.
        self.client.force_authenticate(self.finance)
        bad = {
            "no_bukti": "BADC", "tanggal": "2026-02-01", "keterangan": "x",
            "detail": [
                {"kode_akun": "1101", "debit": "500", "kredit": "500"},
                {"kode_akun": "4101", "debit": "500", "kredit": "500"},
            ],
        }
        resp = self.client.post("/api/v1/jurnal/", bad, format="json")
        self.assertEqual(resp.status_code, 400)  # ditangani exception handler, bukan 500

    def test_void_hanya_principal(self):
        # Administration tidak boleh void
        self.client.force_authenticate(self.finance)
        jid = self.client.post("/api/v1/jurnal/", self._payload("JVX"), format="json").data["id"]
        self.client.post(f"/api/v1/jurnal/{jid}/submit/")
        self.client.force_authenticate(self.principal)
        self.client.post(f"/api/v1/jurnal/{jid}/approve/")
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(f"/api/v1/jurnal/{jid}/void/").status_code, 403)

    def test_delete_jurnal_hanya_finance(self):
        self.client.force_authenticate(self.finance)
        jid = self.client.post("/api/v1/jurnal/", self._payload("JVD"), format="json").data["id"]
        self.client.force_authenticate(self.admin)  # bukan Finance
        self.assertEqual(self.client.delete(f"/api/v1/jurnal/{jid}/").status_code, 403)


class DashboardRingkasanTests(APITestCase):
    def setUp(self):
        self.principal = User.objects.create_user("principal_dash", password="x")
        self.principal.groups.add(Group.objects.get(name="SchoolPrincipal"))
        _coa("1101", "KAS", "D")

    def test_ringkasan_menyertakan_operasional(self):
        self.client.force_authenticate(self.principal)
        r = self.client.get("/api/v1/dashboard/ringkasan/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("operasional", r.data)
        ops = r.data["operasional"]
        self.assertIn("siswa_aktif", ops)
        self.assertIn("absensi_sparkline", ops)
        self.assertEqual(len(ops["absensi_sparkline"]), 6)


class AuditLogApiTests(APITestCase):
    def setUp(self):
        import uuid as _uuid

        from accounting.models import AuditLog, TrJurnal, TrJurnalDetail

        self.finance = User.objects.create_user("finance_audit", password="x")
        self.finance.groups.add(Group.objects.get(name="Finance"))
        self.principal = User.objects.create_user("principal_audit", password="x")
        self.principal.groups.add(Group.objects.get(name="SchoolPrincipal"))
        self.admin = User.objects.create_user("admin_audit", password="x")
        self.admin.groups.add(Group.objects.get(name="Administration"))
        _coa("1101", "KAS", "D")
        _coa("4101", "PENDAPATAN", "K")

        j = TrJurnal.objects.create(
            id=_uuid.uuid4(), no_bukti="AUD1", tanggal="2026-02-01", status="DRAFT",
        )
        TrJurnalDetail.objects.create(
            jurnal=j, kode_akun_id="1101", debit=1000, kredit=0,
        )
        self.audit_id = AuditLog.objects.filter(table_name="tr_jurnal").first().id

    def test_finance_dan_principal_boleh_baca(self):
        for user in (self.finance, self.principal):
            self.client.force_authenticate(user)
            r = self.client.get("/api/v1/audit-log/")
            self.assertEqual(r.status_code, 200)
            self.assertGreaterEqual(r.data["count"], 1)

    def test_administration_ditolak(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/v1/audit-log/").status_code, 403)

    def test_filter_table_name(self):
        self.client.force_authenticate(self.principal)
        r = self.client.get("/api/v1/audit-log/", {"table_name": "tr_jurnal"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(all(x["table_name"] == "tr_jurnal" for x in r.data["results"]))

    def test_detail_menyertakan_username(self):
        self.client.force_authenticate(self.finance)
        r = self.client.get(f"/api/v1/audit-log/{self.audit_id}/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("changed_by_username", r.data)


class ClosingApiTests(APITestCase):
    def setUp(self):
        from datetime import date
        import uuid as _uuid

        from accounting.models import MsPeriodeAkuntansi, TrJurnal, TrJurnalDetail

        self.principal = User.objects.create_user("principal2", password="x")
        self.principal.groups.add(Group.objects.get(name="SchoolPrincipal"))
        _coa("4101", "PENDAPATAN", "K")
        _coa("5101", "BEBAN", "D")
        _coa("3102", "LABA DITAHAN", "K")
        self.periode = MsPeriodeAkuntansi.objects.create(
            kode="2026", tgl_mulai=date(2026, 1, 1), tgl_selesai=date(2026, 12, 31),
        )
        j = TrJurnal.objects.create(
            id=_uuid.uuid4(), no_bukti="OP1", tanggal=date(2026, 3, 1), status="POSTED"
        )
        TrJurnalDetail.objects.create(jurnal=j, kode_akun_id="4101", debit=0, kredit=1000000)
        TrJurnalDetail.objects.create(jurnal=j, kode_akun_id="5101", debit=400000, kredit=0)

    def test_tutup_periode_menghasilkan_jurnal_penutup(self):
        self.client.force_authenticate(self.principal)
        r = self.client.post(f"/api/v1/periode/{self.periode.id}/tutup/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("jurnal_penutup", r.data)
        self.assertEqual(r.data["periode"]["status"], "CLOSED")
        self.periode.refresh_from_db()
        self.assertEqual(self.periode.status, "CLOSED")

    def _jurnal(self, no, tanggal, status="DRAFT"):
        import uuid as _uuid

        from accounting.models import TrJurnalDetail

        j = TrJurnal.objects.create(id=_uuid.uuid4(), no_bukti=no, tanggal=tanggal, status="DRAFT")
        TrJurnalDetail.objects.create(jurnal=j, kode_akun_id="5101", debit=1000, kredit=0)
        TrJurnalDetail.objects.create(jurnal=j, kode_akun_id="4101", debit=0, kredit=1000)
        if status != "DRAFT":
            TrJurnal.objects.filter(pk=j.pk).update(status=status)
        return j

    def test_tutup_memakai_laba_ditahan_coa_final(self):
        MsCoa.objects.filter(pk="3102").update(is_active=False)
        _coa("312", "Laba Ditahan", "K")
        self.client.force_authenticate(self.principal)
        r = self.client.post(f"/api/v1/periode/{self.periode.id}/tutup/")
        self.assertEqual(r.status_code, 200, r.data)
        penutup = TrJurnal.objects.get(pk=r.data["jurnal_penutup"])
        self.assertTrue(penutup.detail.filter(kode_akun_id="312").exists())

    def test_tutup_ditolak_bila_ada_jurnal_tertunda(self):
        from datetime import date

        self._jurnal("PND1", date(2026, 5, 1), status="PENDING")
        self.client.force_authenticate(self.principal)
        r = self.client.post(f"/api/v1/periode/{self.periode.id}/tutup/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("DRAFT/PENDING", str(r.data))
        self.periode.refresh_from_db()
        self.assertEqual(self.periode.status, "OPEN")

    def test_periode_tertutup_mengunci_jurnal_dan_periode(self):
        finance = User.objects.create_user("finance9", password="x")
        finance.groups.add(Group.objects.get(name="Finance"))
        self.client.force_authenticate(self.principal)
        self.assertEqual(self.client.post(f"/api/v1/periode/{self.periode.id}/tutup/").status_code, 200)
        self.client.force_authenticate(finance)
        r = self.client.post("/api/v1/jurnal/", {
            "no_bukti": "LATE1", "tanggal": "2026-06-01", "keterangan": "x",
            "detail": [{"kode_akun": "5101", "debit": "1000", "kredit": "0"},
                       {"kode_akun": "4101", "debit": "0", "kredit": "1000"}],
        }, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("sudah ditutup", str(r.data))
        url = f"/api/v1/periode/{self.periode.id}/"
        self.assertEqual(self.client.patch(url, {"tgl_selesai": "2026-11-30"}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 400)

    def test_periode_tumpang_tindih_ditolak(self):
        finance = User.objects.create_user("finance8", password="x")
        finance.groups.add(Group.objects.get(name="Finance"))
        self.client.force_authenticate(finance)
        r = self.client.post("/api/v1/periode/", {"kode": "X", "tgl_mulai": "2026-12-01", "tgl_selesai": "2027-06-30"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/v1/periode/", {"kode": "Y", "tgl_mulai": "2027-06-30", "tgl_selesai": "2027-01-01"}, format="json")
        self.assertEqual(r.status_code, 400)
