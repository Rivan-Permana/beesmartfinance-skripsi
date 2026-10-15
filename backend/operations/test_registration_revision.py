from datetime import date
from decimal import Decimal
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import MsCoa, TrJurnal, TrJurnalDetail
from operations.models import PendaftaranSiswa, Siswa


class RegistrationRevisionTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user("registration-admin")
        self.admin.groups.add(Group.objects.get(name="Administration"))
        self.finance = get_user_model().objects.create_user("registration-finance")
        self.finance.groups.add(Group.objects.get(name="Finance"))
        self.principal = get_user_model().objects.create_user("registration-principal")
        self.principal.groups.add(Group.objects.get(name="SchoolPrincipal"))
        for code, normal in [("111", "D"), ("415", "K"), ("416", "K")]:
            MsCoa.objects.create(kode_akun=code, nama_akun=code, posisi_normal=normal)
        self.client.force_authenticate(self.admin)

    def create(self, **extra):
        payload = {"nama_calon": "Calon Uji", "tanggal_daftar": "2026-10-01",
                   "biaya_sitin": "750000.00", "biaya_formulir": "100000.00", **extra}
        result = self.client.post("/api/v1/pendaftaran-siswa/", payload, format="json")
        self.assertEqual(result.status_code, 201, result.data)
        return result.data

    def pay(self, pk, components=None, amount="850000.00", reference="REG-TEST-1"):
        return self.client.post(f"/api/v1/pendaftaran-siswa/{pk}/bayar/", {
            "komponen": components or ["FORMULIR", "SITIN"], "nominal": amount,
            "tanggal": "2026-10-15", "no_bukti": reference, "akun_kas": "111",
        }, format="json")

    def test_combined_payment_total_and_retry_do_not_duplicate_receipt(self):
        record = self.create()
        self.assertEqual(record["total_biaya"], "850000.00")
        payment = self.pay(record["id"])
        self.assertEqual(payment.status_code, 200, payment.data)
        jurnal = TrJurnal.objects.get(pk=payment.data["jurnal_id"])
        self.assertEqual(jurnal.tanggal, date(2026, 10, 15))
        self.assertEqual(sum(jurnal.detail.values_list("debit", flat=True)), Decimal("850000"))
        self.assertEqual(set(jurnal.detail.values_list("kode_akun_id", flat=True)), {"111", "415", "416"})
        self.assertEqual(self.pay(record["id"]).status_code, 200)
        self.assertEqual(TrJurnal.objects.count(), 1)
        saved = self.client.get(f'/api/v1/pendaftaran-siswa/{record["id"]}/').data
        self.assertEqual(saved["total_terbayar"], "850000.00")
        self.assertEqual(saved["sisa_biaya"], "0.00")

    def test_sitin_then_formulir_only_charges_remaining_component(self):
        record = self.create()
        first = self.pay(record["id"], ["SITIN"], "750000", "SIT-TEST-1")
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data["pendaftaran"]["sisa_biaya"], "100000.00")
        second = self.pay(record["id"], ["FORMULIR"], "100000", "FORM-TEST-1")
        self.assertEqual(second.status_code, 200, second.data)
        self.assertEqual(second.data["pendaftaran"]["sisa_biaya"], "0.00")
        self.assertEqual(TrJurnal.objects.count(), 2)
        self.assertEqual(self.pay(record["id"], reference="DUPLICATE").status_code, 400)

    def test_finalization_alone_does_not_create_money_or_duplicate_student(self):
        record = self.create()
        url = f'/api/v1/pendaftaran-siswa/{record["id"]}/finalisasi/'
        first = self.client.post(url, {"spp_nominal": "400000"}, format="json")
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data["status"], "REGISTERED")
        self.assertEqual(first.data["sisa_biaya"], "850000.00")
        self.assertEqual(TrJurnal.objects.count(), 0)
        again = self.client.post(url, {"spp_nominal": "400000"}, format="json")
        self.assertEqual(again.status_code, 200, again.data)
        self.assertEqual(Siswa.objects.count(), 1)
        self.assertEqual(self.pay(record["id"]).status_code, 200)

    def test_legacy_amount_is_not_silently_reinterpreted(self):
        old = PendaftaranSiswa.objects.create(nama_calon="Lama", tanggal_daftar=date(2026, 10, 1),
            biaya_sitin=750000, biaya_pendaftaran=850000)
        data = self.client.get(f"/api/v1/pendaftaran-siswa/{old.pk}/").data
        self.assertIsNone(data["total_biaya"])
        self.assertIsNone(data["total_terbayar"])
        self.assertTrue(data["perlu_rekonsiliasi"])
        self.assertEqual(self.pay(old.pk).status_code, 400)
        old.refresh_from_db()
        self.assertEqual(old.biaya_pendaftaran, Decimal("850000"))

    def test_invalid_payment_and_fee_changes_do_not_change_receipt(self):
        record = self.create()
        url = f'/api/v1/pendaftaran-siswa/{record["id"]}/'
        self.assertEqual(self.pay(record["id"], amount="850001").status_code, 400)
        self.assertEqual(self.pay(record["id"], ["FORMULIR", "FORMULIR"], "200000").status_code, 400)
        self.assertEqual(self.client.post(url + "bayar/", {}, format="json").status_code, 400)
        self.assertEqual(TrJurnal.objects.count(), 0)
        self.assertEqual(self.pay(record["id"]).status_code, 200)
        self.assertEqual(self.client.patch(url, {"biaya_formulir": "200000"}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.client.force_authenticate(self.finance)
        self.assertEqual(self.pay(record["id"]).status_code, 403)

    def test_no_unconfirmed_default_fees_and_no_invalid_spp(self):
        response = self.client.post("/api/v1/pendaftaran-siswa/", {"nama_calon": "Tanpa Biaya", "tanggal_daftar": "2026-10-01"}, format="json")
        self.assertEqual(response.status_code, 400)
        free = self.create(biaya_sitin="0", biaya_formulir="0")
        self.assertEqual(self.client.post(f'/api/v1/pendaftaran-siswa/{free["id"]}/finalisasi/', {"spp_nominal": "NaN"}, format="json").status_code, 400)

    def test_cancellation_restores_remaining_fees_without_canceling_student(self):
        record = self.create()
        paid = self.pay(record["id"])
        self.assertEqual(paid.status_code, 200, paid.data)
        journal_id = paid.data["jurnal_id"]
        self.client.force_authenticate(self.finance)
        cancel = self.client.post(f"/api/v1/jurnal/{journal_id}/batal-penerimaan/", {"alasan": "Bukti penerimaan salah"}, format="json")
        self.assertEqual(cancel.status_code, 200, cancel.data)
        self.client.force_authenticate(self.admin)
        data = self.client.get(f'/api/v1/pendaftaran-siswa/{record["id"]}/').data
        self.assertEqual(data["sisa_biaya"], "850000.00")
        self.assertEqual(self.pay(record["id"], reference="REG-CORRECTED").status_code, 200)

    def test_finance_can_post_real_receipt_and_reversal_reopens_payment(self):
        record = self.create()
        response = self.pay(record["id"])
        journal_id = response.data["jurnal_id"]
        self.client.post(f'/api/v1/pendaftaran-siswa/{record["id"]}/finalisasi/', {"spp_nominal": "0"}, format="json")
        self.client.force_authenticate(self.finance)
        posted = self.client.post(f"/api/v1/jurnal/{journal_id}/catat/")
        self.assertEqual(posted.status_code, 200, posted.data)
        self.client.force_authenticate(self.principal)
        self.assertEqual(self.client.post(f"/api/v1/jurnal/{journal_id}/void/").status_code, 201)
        self.client.force_authenticate(self.admin)
        data = self.client.get(f'/api/v1/pendaftaran-siswa/{record["id"]}/').data
        self.assertEqual(data["sisa_biaya"], "850000.00")
        self.assertEqual(data["status"], "REGISTERED")
        self.assertEqual(Siswa.objects.count(), 1)

    def test_legacy_receipt_stays_flagged_and_cannot_be_posted(self):
        old = PendaftaranSiswa.objects.create(nama_calon="Lama", tanggal_daftar=date(2026, 10, 1), biaya_pendaftaran=850000)
        journal = TrJurnal.objects.create(id=uuid.uuid4(), no_bukti="LEGACY-REG", tanggal=old.tanggal_daftar, tipe_sumber="AUTO_PENDAFTARAN")
        TrJurnalDetail.objects.create(jurnal=journal, kode_akun_id="111", debit=850000)
        TrJurnalDetail.objects.create(jurnal=journal, kode_akun_id="415", kredit=850000)
        old.jurnal_pendaftaran = journal
        old.save()
        self.client.force_authenticate(self.finance)
        payload = self.client.get(f"/api/v1/jurnal/{journal.pk}/").data
        self.assertTrue(payload["perlu_rekonsiliasi"])
        self.assertFalse(payload["can_finance_post"])
        self.assertEqual(self.client.post(f"/api/v1/jurnal/{journal.pk}/catat/").status_code, 400)
        journal.refresh_from_db()
        self.assertEqual(journal.status, "DRAFT")

    def test_legacy_unpaid_mapping_is_explicit_and_keeps_historical_amount(self):
        old = PendaftaranSiswa.objects.create(nama_calon="Lama", tanggal_daftar=date(2026, 10, 1), biaya_sitin=750000, biaya_pendaftaran=850000)
        response = self.client.patch(f"/api/v1/pendaftaran-siswa/{old.pk}/", {"biaya_formulir": "100000", "biaya_sitin": "750000"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["total_biaya"], "850000.00")
        self.assertEqual(response.data["biaya_pendaftaran"], "850000.00")
        self.assertFalse(response.data["perlu_rekonsiliasi"])
