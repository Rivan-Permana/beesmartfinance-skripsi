"""Domain kegiatan sekolah (alur Teacher in Charge: anggaran & realisasi)."""

from decimal import Decimal

from django.db import models
from simple_history.models import HistoricalRecords

from .base import SoftDeleteModel, TimeStampedModel


class Kegiatan(SoftDeleteModel, TimeStampedModel):
    STATUS = [("RENCANA", "Rencana"), ("BERJALAN", "Berjalan"), ("SELESAI", "Selesai")]
    nama = models.CharField(max_length=150)
    akun_beban = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="kegiatan", db_column="akun_beban",
    )
    pagu = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    penanggung_jawab = models.ForeignKey(
        "operations.Pegawai", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="kegiatan",
    )
    tanggal_mulai = models.DateField(blank=True, null=True)
    tanggal_selesai = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS, default="RENCANA")

    history = HistoricalRecords()

    @property
    def realisasi(self) -> Decimal:
        return (
            self.realisasi_list.aggregate(t=models.Sum("nominal"))["t"] or Decimal(0)
        )

    @property
    def sisa_pagu(self) -> Decimal:
        return self.pagu - self.realisasi

    @property
    def rasio_utilisasi(self) -> float:
        return float(self.realisasi / self.pagu) if self.pagu else 0.0

    def __str__(self):
        return self.nama


class RealisasiKegiatan(models.Model):
    kegiatan = models.ForeignKey(
        Kegiatan, on_delete=models.CASCADE, related_name="realisasi_list"
    )
    tanggal = models.DateField()
    deskripsi = models.CharField(max_length=255, blank=True, default="")
    nominal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    jurnal = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="realisasi_kegiatan",
    )
