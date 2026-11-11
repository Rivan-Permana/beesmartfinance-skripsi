"""Realisasi kegiatan yang diinput Kepsek dicatat Keuangan (Kepsek tidak boleh menyetujui jurnalnya sendiri)."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounting.models import TrJurnal
from operations.models import Kegiatan
from operations.services.activities import post_realisasi_kegiatan
from operations.test_tp_batch import _coa


class KegiatanPostingTests(APITestCase):
    def setUp(self):
        self.kepsek, self.keuangan = (get_user_model().objects.create_user(n) for n in ("kepsek-kg", "keuangan-kg"))
        self.kepsek.groups.add(Group.objects.get(name="SchoolPrincipal"))
        self.keuangan.groups.add(Group.objects.get(name="Finance"))
        _coa("112", "Kas di Bank", "D")
        beban = _coa("5112", "Beban kegiatan", "D")
        kegiatan = Kegiatan.objects.create(nama="AB3", akun_beban=beban, pagu=Decimal("3000000"))
        realisasi = post_realisasi_kegiatan(kegiatan, date(2026, 10, 20), "DP tempat", "2000000", user=self.kepsek)
        self.jurnal = realisasi.jurnal
        TrJurnal.objects.filter(pk=self.jurnal.pk).update(status="PENDING", submitted_by=self.keuangan)

    def test_keuangan_mencatat_realisasi_buatan_kepsek(self):
        self.client.force_authenticate(self.kepsek)
        self.assertEqual(self.client.post(f"/api/v1/jurnal/{self.jurnal.pk}/approve/").status_code, 403)
        self.client.force_authenticate(self.keuangan)
        data = self.client.get(f"/api/v1/jurnal/{self.jurnal.pk}/").data
        self.assertTrue(data["can_finance_post"])
        res = self.client.post(f"/api/v1/jurnal/{self.jurnal.pk}/catat/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(TrJurnal.objects.get(pk=self.jurnal.pk).status, "POSTED")
