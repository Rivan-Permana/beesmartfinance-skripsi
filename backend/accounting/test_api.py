from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan

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
        resp = self.client.post("/api/jurnal/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 401)

    def test_hanya_finance_boleh_buat(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.post("/api/jurnal/", self._payload(), format="json").status_code,
            403,
        )
        self.client.force_authenticate(self.finance)
        resp = self.client.post("/api/jurnal/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], "DRAFT")

    def test_jurnal_tidak_seimbang_ditolak(self):
        self.client.force_authenticate(self.finance)
        bad = self._payload()
        bad["detail"][0]["debit"] = "999"
        self.assertEqual(
            self.client.post("/api/jurnal/", bad, format="json").status_code, 400
        )

    def test_alur_maker_checker(self):
        self.client.force_authenticate(self.finance)
        jid = self.client.post("/api/jurnal/", self._payload(), format="json").data["id"]
        # submit oleh finance
        r = self.client.post(f"/api/jurnal/{jid}/submit/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "PENDING")
        # finance tidak boleh approve
        self.assertEqual(self.client.post(f"/api/jurnal/{jid}/approve/").status_code, 403)
        # principal approve -> POSTED
        self.client.force_authenticate(self.principal)
        r = self.client.post(f"/api/jurnal/{jid}/approve/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "POSTED")
