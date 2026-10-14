"""Regresi cicilan, posting Finance, dan pagination pada database terisolasi."""

import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import MsPeriodeAkuntansi, TrAnggaran, TrJurnal
from operations.models import PembayaranTagihan, Siswa, Tagihan, TagihanDetail
from operations.test_api import _coa


class PaymentRevisionTests(APITestCase):
    def setUp(self):
        self.tu, self.finance, self.principal = [get_user_model().objects.create_user(name) for name in ("tu", "finance", "principal")]
        for user, role in zip((self.tu, self.finance, self.principal), ("Administration", "Finance", "SchoolPrincipal")):
            user.groups.add(Group.objects.get(name=role))
        _coa("1101", "Kas", "D")
        _coa("4101", "Pendapatan", "K")
        _coa("5101", "Beban", "D")
        siswa = Siswa.objects.create(nama="Siswa uji")
        self.tagihan = Tagihan.objects.create(siswa=siswa, periode_bulan=2, periode_tahun=2026, total=Decimal("6350000"))
        self.lines = [TagihanDetail.objects.create(tagihan=self.tagihan, komponen="SPP", akun_pendapatan_id="4101", nominal=n) for n in (Decimal("3000000"), Decimal("3350000"))]
        self.client.force_authenticate(self.tu)

    def payload(self, nominal="2000000", no_bukti="PAY-1"):
        return {"tanggal": "2026-02-01", "no_bukti": no_bukti, "nominal": nominal, "akun_kas": "1101",
                "request_id": str(uuid.uuid4()), "alokasi": [{"detail": self.lines[0].pk, "nominal": nominal}]}

    def pay(self, payload):
        return self.client.post(f"/api/v1/tagihan/{self.tagihan.pk}/bayar/", payload, format="json")

    def test_cicilan_pelunasan_idempotensi_dan_ringkasan(self):
        payload = self.payload()
        first = self.pay(payload)
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data["tagihan"]["status"], "SEBAGIAN")
        self.assertEqual(first.data["tagihan"]["sisa_tagihan"], "4350000.00")
        self.assertEqual(self.pay(payload).data["pembayaran"]["id"], first.data["pembayaran"]["id"])
        self.assertEqual(PembayaranTagihan.objects.count(), 1)
        self.client.force_authenticate(self.finance)
        catat = self.client.post(f'/api/v1/jurnal/{first.data["jurnal_id"]}/catat/')
        self.assertEqual(catat.status_code, 200, catat.data)
        self.assertEqual(catat.data["status"], "POSTED")
        self.assertIsNone(catat.data["approved_by"])
        summary = self.client.get("/api/v1/dashboard/ringkasan/?tahun=2026&bulan=2").data
        self.assertEqual(summary["operasional"]["tagihan_belum_nominal"], Decimal("4350000"))
        self.assertEqual(summary["kas"], Decimal("2000000"))
        self.client.force_authenticate(self.tu)
        final = self.payload("4350000", "PAY-2")
        final["alokasi"] = [{"detail": self.lines[0].pk, "nominal": "1000000"}, {"detail": self.lines[1].pk, "nominal": "3350000"}]
        paid = self.pay(final)
        self.assertEqual(paid.status_code, 200, paid.data)
        self.assertEqual(paid.data["tagihan"]["status"], "LUNAS")
        self.assertEqual(paid.data["tagihan"]["sisa_tagihan"], "0.00")
        self.assertEqual(paid.data["tagihan"]["total"], "6350000.00")

    def test_payload_invalid_tidak_membuat_penerimaan(self):
        cases = [{}, {"nominal": "0"}, {"nominal": "-1"}, {"nominal": "6350001"},
                 {"akun_kas": "4101"}, {"alokasi": [{"detail": 99999, "nominal": "2000000"}]},
                 {"alokasi": [{"detail": self.lines[0].pk, "nominal": "1"}]},
                 {"alokasi": [{"detail": self.lines[0].pk, "nominal": "1000000"}] * 2}]
        for changes in cases:
            with self.subTest(changes=changes):
                payload = {} if not changes else {**self.payload(), **changes}
                self.assertEqual(self.pay(payload).status_code, 400)
                self.assertEqual(PembayaranTagihan.objects.count(), 0)
                self.assertEqual(TrJurnal.objects.count(), 0)

    def test_sisa_komponen_bukti_dan_request_id_dilindungi(self):
        payload = self.payload()
        self.assertEqual(self.pay(payload).status_code, 200)
        self.assertEqual(self.pay({**payload, "no_bukti": "ubah"}).status_code, 400)
        self.assertEqual(self.pay(self.payload(no_bukti="PAY-1")).status_code, 400)
        self.assertEqual(self.pay(self.payload("2000000", "PAY-2")).status_code, 400)
        self.assertEqual(PembayaranTagihan.objects.count(), 1)

    def test_tagihan_berbayar_tidak_dapat_dihapus_atau_diedit(self):
        self.assertEqual(self.pay(self.payload()).status_code, 200)
        url = f"/api/v1/tagihan/{self.tagihan.pk}/"
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.assertEqual(self.client.patch(url, {"periode_bulan": 3}, format="json").status_code, 400)

    def test_pembayaran_lama_diblokir_tanpa_menebak_nominal(self):
        self.tagihan.perlu_rekonsiliasi = True
        self.tagihan.status = "LUNAS"
        self.tagihan.save()
        self.assertEqual(self.pay(self.payload()).status_code, 400)
        invoice = self.client.get(f"/api/v1/tagihan/{self.tagihan.pk}/struk/").data
        self.assertIsNone(invoice["total_terbayar"])
        self.assertIsNone(invoice["sisa_tagihan"])

    def test_reversal_mengembalikan_sisa_dan_kas(self):
        receipt = self.pay(self.payload()).data
        url = f'/api/v1/jurnal/{receipt["jurnal_id"]}/'
        self.client.force_authenticate(self.finance)
        self.assertEqual(self.client.post(url + "catat/").status_code, 200)
        self.assertEqual(self.client.post(url + "void/").status_code, 403)
        self.client.force_authenticate(self.principal)
        self.assertEqual(self.client.post(url + "void/").status_code, 201)
        self.assertEqual(self.client.post(url + "void/").status_code, 400)
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.sisa_tagihan, Decimal("6350000"))
        self.assertEqual(self.tagihan.status, "BELUM")
        self.assertTrue(PembayaranTagihan.objects.get().dibatalkan)

    def test_batal_draft_dan_jurnal_sumber_tidak_dapat_diedit(self):
        receipt = self.pay(self.payload()).data
        url = f'/api/v1/jurnal/{receipt["jurnal_id"]}/'
        self.client.force_authenticate(self.finance)
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.assertEqual(self.client.post(url + "batal-penerimaan/", {"alasan": "Salah input"}, format="json").status_code, 200)
        self.assertEqual(self.client.post(url + "catat/").status_code, 400)
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.total_terbayar, 0)

    def test_posting_menjaga_periode_dan_pagu(self):
        receipt = self.pay(self.payload()).data
        self.client.force_authenticate(self.finance)
        periode = MsPeriodeAkuntansi.objects.create(kode="closed", tgl_mulai=date(2026, 1, 1), tgl_selesai=date(2026, 12, 31), status="CLOSED")
        url = f'/api/v1/jurnal/{receipt["jurnal_id"]}/catat/'
        self.assertEqual(self.client.post(url).status_code, 400)
        self.assertEqual(TrJurnal.objects.get(pk=receipt["jurnal_id"]).status, "DRAFT")
        periode.status = "OPEN"
        periode.save()
        TrAnggaran.objects.create(kode_akun_id="5101", tahun_anggaran=2026, nominal_anggaran=Decimal("100"))
        j = self.client.post("/api/v1/jurnal/", {"no_bukti": "EXP", "tanggal": "2026-02-01", "detail": [
            {"kode_akun": "5101", "debit": "200", "kredit": "0"}, {"kode_akun": "1101", "debit": "0", "kredit": "200"}]}, format="json").data
        self.assertEqual(self.client.post(f'/api/v1/jurnal/{j["id"]}/catat/').status_code, 400)

    def test_pagination_memfilter_sebelum_membagi_halaman(self):
        self.client.force_authenticate(self.finance)
        for i in range(12):
            data = self.client.post("/api/v1/jurnal/", {"no_bukti": f"J{i}", "tanggal": "2026-02-01", "detail": [
                {"kode_akun": "1101", "debit": "10", "kredit": "0"}, {"kode_akun": "4101", "debit": "0", "kredit": "10"}]}, format="json").data
            if i == 0:
                TrJurnal.objects.filter(pk=data["id"]).update(tipe_sumber="AUTO_PAYROLL")
                self.assertEqual(self.client.post(f'/api/v1/jurnal/{data["id"]}/catat/').status_code, 400)
        page = self.client.get("/api/v1/jurnal/?jenis=masuk&page=2&page_size=10").data
        self.assertEqual(page["count"], 12)
        self.assertEqual(len(page["results"]), 2)
        self.assertEqual(self.client.get("/api/v1/jurnal/?jenis=keluar").data["count"], 0)
