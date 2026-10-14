"""Test modul operasional: soft-delete, history, dan auto-posting tagihan."""

from decimal import Decimal
import uuid

from django.test import TestCase

from datetime import date

from accounting.models import MsCoa, MsGolongan, MsSubGolongan, TrJurnal
from operations.models import (
    FixedAsset,
    GajiPegawai,
    Pegawai,
    Siswa,
    Tagihan,
    TagihanDetail,
)
from operations.services import (
    post_gaji,
    post_pembayaran_tagihan,
    post_penyusutan,
)


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

        pembayaran = post_pembayaran_tagihan(tagihan, tanggal=date(2026, 2, 1), no_bukti="P1", nominal=tagihan.total,
            alokasi=[{"detail": tagihan.detail.first().pk, "nominal": tagihan.total}], request_id=uuid.uuid4(), user=None)
        jurnal = pembayaran.jurnal

        tagihan.refresh_from_db()
        self.assertEqual(tagihan.status, "LUNAS")
        self.assertEqual(tagihan.pembayaran.first().jurnal_id, jurnal.id)
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
        payload = dict(tanggal=date(2026, 3, 1), no_bukti="P2", nominal=tagihan.total,
            alokasi=[{"detail": tagihan.detail.first().pk, "nominal": tagihan.total}], request_id=uuid.uuid4())
        post_pembayaran_tagihan(tagihan, user=None, **payload)
        payload["request_id"] = uuid.uuid4()
        with self.assertRaises(ValueError):
            post_pembayaran_tagihan(tagihan, user=None, **payload)


class ExpenseCycleTests(TestCase):
    def setUp(self):
        _coa("1101", "KAS", "D")
        _coa("1103", "PIUTANG KARYAWAN", "D")
        _coa("2101", "UTANG ASURANSI", "K")
        _coa("5201", "BEBAN GAJI", "D")
        _coa("1201", "PERALATAN", "D")
        _coa("1202", "AKUM PENYUSUTAN", "K")
        _coa("5301", "BEBAN PENYUSUTAN", "D")
        self.pegawai = Pegawai.objects.create(nama="Pak Guru", jabatan="Guru")

    def test_payroll_seimbang_dengan_potongan(self):
        gaji = GajiPegawai.objects.create(
            pegawai=self.pegawai, periode_bulan=2, periode_tahun=2026,
            gaji_pokok=Decimal("3000000"), tunjangan_jabatan=Decimal("500000"),
            potongan_pinjaman=Decimal("200000"), potongan_asuransi=Decimal("100000"),
        )
        jurnal = post_gaji(gaji, user=None)
        gaji.refresh_from_db()
        self.assertEqual(gaji.jurnal_id, jurnal.id)
        td = sum(d.debit for d in jurnal.detail.all())
        tk = sum(d.kredit for d in jurnal.detail.all())
        self.assertEqual(td, tk)
        self.assertEqual(td, Decimal("3500000"))  # bruto

    def test_penyusutan_menambah_akumulasi(self):
        aset = FixedAsset.objects.create(
            nama="Laptop", akun_aset_id="1201", akun_akumulasi_id="1202",
            akun_beban_depr_id="5301", tanggal_perolehan=date(2026, 1, 1),
            harga_perolehan=Decimal("12000000"), umur_manfaat_bulan=12,
        )
        jurnal = post_penyusutan(aset, user=None, tanggal=date(2026, 2, 28))
        aset.refresh_from_db()
        self.assertEqual(aset.akumulasi_penyusutan, Decimal("1000000"))
        td = sum(d.debit for d in jurnal.detail.all())
        tk = sum(d.kredit for d in jurnal.detail.all())
        self.assertEqual(td, tk)
        self.assertEqual(td, Decimal("1000000"))
