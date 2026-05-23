"""Test modul operasional: soft-delete, history, dan auto-posting tagihan."""

from decimal import Decimal

from django.test import TestCase

from accounting.models import MsCoa, MsGolongan, MsSubGolongan, TrJurnal
from operations.models import Siswa, Tagihan, TagihanDetail
from operations.services import post_pembayaran_tagihan


def _coa(kode, nama, posisi):
    g, _ = MsGolongan.objects.get_or_create(
        kode_golongan=kode[0], defaults={"nama_golongan": "G" + kode[0]}
    )
    sg, _ = MsSubGolongan.objects.get_or_create(
        kode_sub=kode[:2], defaults={"golongan": g, "nama_sub": "SG" + kode[:2]}
    )
    return MsCoa.objects.create(
        kode_akun=kode, sub_golongan=sg, nama_akun=nama, posisi_normal=posisi
    )


class SoftDeleteHistoryTests(TestCase):
    def test_soft_delete_menyembunyikan_tapi_menyimpan(self):
        s = Siswa.objects.create(nama="Budi")
        s.delete()
        self.assertEqual(Siswa.objects.filter(pk=s.pk).count(), 0)        # tersembunyi
        self.assertEqual(Siswa.all_objects.filter(pk=s.pk).count(), 1)    # tetap ada
        self.assertTrue(Siswa.all_objects.get(pk=s.pk).is_deleted)

    def test_history_terekam(self):
        s = Siswa.objects.create(nama="Ani")
        s.nama = "Ani Updated"
        s.save()
        self.assertGreaterEqual(s.history.count(), 2)  # create + update


class AutoPostingTests(TestCase):
    def setUp(self):
        self.kas = _coa("1101", "KAS", "D")
        self.spp = _coa("4101", "PENDAPATAN SPP", "K")
        self.siswa = Siswa.objects.create(nama="Citra", spp_nominal=Decimal("500000"))

    def test_pembayaran_membuat_jurnal_seimbang(self):
        tagihan = Tagihan.objects.create(
            siswa=self.siswa, periode_bulan=2, periode_tahun=2026,
            total=Decimal("500000"),
        )
        TagihanDetail.objects.create(
            tagihan=tagihan, komponen="SPP",
            akun_pendapatan=self.spp, nominal=Decimal("500000"),
        )

        jurnal = post_pembayaran_tagihan(tagihan, user=None)

        tagihan.refresh_from_db()
        self.assertEqual(tagihan.status, "LUNAS")
        self.assertEqual(tagihan.jurnal_id, jurnal.id)
        self.assertEqual(jurnal.status, "DRAFT")  # menunggu approval (maker-checker)

        total_debit = sum(d.debit for d in jurnal.detail.all())
        total_kredit = sum(d.kredit for d in jurnal.detail.all())
        self.assertEqual(total_debit, total_kredit)          # seimbang
        self.assertEqual(total_debit, Decimal("500000"))

    def test_double_posting_ditolak(self):
        tagihan = Tagihan.objects.create(
            siswa=self.siswa, periode_bulan=3, periode_tahun=2026, total=Decimal("100"),
        )
        TagihanDetail.objects.create(
            tagihan=tagihan, komponen="SPP", akun_pendapatan=self.spp, nominal=Decimal("100"),
        )
        post_pembayaran_tagihan(tagihan, user=None)
        with self.assertRaises(ValueError):
            post_pembayaran_tagihan(tagihan, user=None)
