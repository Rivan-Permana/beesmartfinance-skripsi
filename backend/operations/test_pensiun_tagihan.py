"""Perintah pensiunkan_tagihan_lama: rencana dulu, terapkan hanya dengan --terapkan, tolak kasus di luar kriteria."""

from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

from accounting.models import TrJurnal
from operations.models import Siswa, Tagihan, TagihanDetail
from operations.services.common import buat_jurnal
from operations.test_tp_batch import _coa


class PensiunTagihanTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("keuangan-pensiun")
        _coa("112", "Kas di Bank", "D")
        _coa("411", "SPP", "K")
        self.siswa = Siswa.objects.create(nama="Siswa lama", spp_nominal=1, status="aktif")

    def lama(self, bulan, status_jurnal="DRAFT", flag=True):
        jurnal = buat_jurnal(f"BL-{bulan}", date(2026, 10, 13), "Pembayaran lama", "AUTO_BILLING",
                             [("112", Decimal("100"), Decimal(0)), ("411", Decimal(0), Decimal("100"))], None)
        if status_jurnal != "DRAFT":
            TrJurnal.objects.filter(pk=jurnal.pk).update(status=status_jurnal)
        t = Tagihan.objects.create(siswa=self.siswa, periode_bulan=bulan, periode_tahun=2026, total=Decimal("100"),
                                   status="LUNAS", perlu_rekonsiliasi=flag, jurnal=jurnal)
        TagihanDetail.objects.create(tagihan=t, komponen="SPP", akun_pendapatan_id="411", nominal=Decimal("100"))
        return t

    def jalankan(self, *ids, terapkan=False):
        out = StringIO()
        args = [*map(str, ids), "--alasan", "Uji pensiun", "--oleh", self.user.username]
        call_command("pensiunkan_tagihan_lama", *args, *(["--terapkan"] if terapkan else []), stdout=out)
        return out.getvalue()

    def test_rencana_tidak_mengubah_lalu_terapkan(self):
        a, b = self.lama(9), self.lama(10, "PENDING")
        out = self.jalankan(a.pk, b.pk)
        self.assertIn("Rencana saja (2 tagihan)", out)
        self.assertEqual(Tagihan.objects.filter(pk__in=[a.pk, b.pk]).count(), 2)
        self.assertEqual(set(TrJurnal.objects.values_list("status", flat=True)), {"DRAFT", "PENDING"})

        self.assertIn("Selesai: 2 tagihan", self.jalankan(a.pk, b.pk, terapkan=True))
        self.assertFalse(Tagihan.objects.filter(pk__in=[a.pk, b.pk]).exists())
        self.assertEqual(Tagihan.all_objects.filter(pk__in=[a.pk, b.pk], is_deleted=True).count(), 2)
        jurnal = TrJurnal.objects.get(pk=a.jurnal_id)
        self.assertEqual(jurnal.status, "VOID")
        self.assertIn("Dipensiunkan: Uji pensiun", jurnal.keterangan)
        self.assertEqual(TrJurnal.objects.get(pk=b.jurnal_id).status, "VOID")

    def test_tolak_semua_bila_satu_tidak_memenuhi(self):
        a, posted, biasa = self.lama(9), self.lama(10, "POSTED"), self.lama(11, flag=False)
        for ids in ((a.pk, posted.pk), (a.pk, biasa.pk), (a.pk, 999)):
            with self.assertRaises(CommandError):
                self.jalankan(*ids, terapkan=True)
        self.assertEqual(Tagihan.objects.count(), 3)
        self.assertEqual(TrJurnal.objects.get(pk=a.jurnal_id).status, "DRAFT")
