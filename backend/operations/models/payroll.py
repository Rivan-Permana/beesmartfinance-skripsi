"""Domain kepegawaian-keuangan: kasbon (pinjaman) & payroll (gaji)."""

from decimal import Decimal

from django.db import models
from simple_history.models import HistoricalRecords

from .base import SoftDeleteModel, TimeStampedModel


class PinjamanPegawai(SoftDeleteModel, TimeStampedModel):
    pegawai = models.ForeignKey(
        "operations.Pegawai", on_delete=models.PROTECT, related_name="pinjaman"
    )
    tanggal_pinjaman = models.DateField()
    jumlah_pinjaman = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tenor_bulan = models.PositiveIntegerField(default=1)
    angsuran_per_bulan = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    sudah_terbayar = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    jurnal = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="pinjaman",
    )
    # Saldo kasbon dari impor KAFALAH: sudah dicairkan di luar sistem, tanpa jurnal pencairan.
    is_legacy = models.BooleanField(default=False)

    history = HistoricalRecords()

    @property
    def sisa_pinjaman(self) -> Decimal:
        return max(self.jumlah_pinjaman - self.sudah_terbayar, Decimal(0))


class GajiPegawai(SoftDeleteModel, TimeStampedModel):
    pegawai = models.ForeignKey(
        "operations.Pegawai", on_delete=models.PROTECT, related_name="gaji"
    )
    periode_bulan = models.PositiveSmallIntegerField()
    periode_tahun = models.PositiveIntegerField()

    gaji_pokok = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tunjangan_jabatan = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tunjangan_pengabdian = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tunjangan_asuransi = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    uang_makan = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    transport = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    bonus_insentif = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    thr = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    hari_hadir = models.PositiveSmallIntegerField(default=0)

    potongan_pinjaman = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    potongan_asuransi = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    jurnal = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="gaji",
    )
    # True setelah potongan kasbon slip ini mengurangi saldo pinjaman (saat jurnal gaji POSTED).
    kasbon_diselesaikan = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        unique_together = ("pegawai", "periode_bulan", "periode_tahun")

    @property
    def total_bruto(self) -> Decimal:
        return (
            self.gaji_pokok + self.tunjangan_jabatan + self.tunjangan_pengabdian
            + self.tunjangan_asuransi + self.uang_makan + self.transport
            + self.bonus_insentif + self.thr
        )

    @property
    def total_potongan(self) -> Decimal:
        return self.potongan_pinjaman + self.potongan_asuransi

    @property
    def total_netto(self) -> Decimal:
        return self.total_bruto - self.total_potongan


class PotonganKasbonGaji(TimeStampedModel):
    """Bagian potongan slip gaji yang melunasi satu kasbon; dasar pengembalian saat jurnal gaji di-void."""

    gaji = models.ForeignKey(GajiPegawai, on_delete=models.PROTECT, related_name="potongan_kasbon")
    pinjaman = models.ForeignKey(PinjamanPegawai, on_delete=models.PROTECT, related_name="potongan_gaji")
    nominal = models.DecimalField(max_digits=18, decimal_places=2)
