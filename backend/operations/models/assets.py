"""Domain aset tetap & penyusutan."""

from decimal import Decimal

from django.db import models
from simple_history.models import HistoricalRecords

from .base import SoftDeleteModel, TimeStampedModel


class FixedAsset(SoftDeleteModel, TimeStampedModel):
    METODE = [("garis_lurus", "Garis Lurus")]
    nama = models.CharField(max_length=150)
    akun_aset = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="aset", db_column="akun_aset",
    )
    akun_akumulasi = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="aset_akumulasi", db_column="akun_akumulasi",
    )
    akun_beban_depr = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="aset_beban", db_column="akun_beban_depr",
    )
    tanggal_perolehan = models.DateField()
    harga_perolehan = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    umur_manfaat_bulan = models.PositiveIntegerField(default=1)
    metode = models.CharField(max_length=20, choices=METODE, default="garis_lurus")
    akumulasi_penyusutan = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    history = HistoricalRecords()

    @property
    def penyusutan_per_bulan(self) -> Decimal:
        if self.umur_manfaat_bulan <= 0:
            return Decimal(0)
        return self.harga_perolehan / self.umur_manfaat_bulan

    def __str__(self):
        return self.nama
