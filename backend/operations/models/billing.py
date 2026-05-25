"""Domain billing: posting rule & tagihan siswa (siklus pendapatan)."""

from django.db import models
from simple_history.models import HistoricalRecords

from .base import SoftDeleteModel, TimeStampedModel


class MsPostingRule(models.Model):
    """Mapping event -> akun COA, agar auto-journal tidak hardcode."""

    event_code = models.CharField(max_length=40)
    komponen = models.CharField(max_length=40, blank=True, default="")
    akun_debit = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="rule_debit", db_column="akun_debit",
    )
    akun_kredit = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="rule_kredit", db_column="akun_kredit",
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        unique_together = ("event_code", "komponen")

    def __str__(self):
        return f"{self.event_code}/{self.komponen or '-'}"


class Tagihan(SoftDeleteModel, TimeStampedModel):
    STATUS = [
        ("BELUM", "Belum Lunas"), ("SEBAGIAN", "Sebagian"), ("LUNAS", "Lunas"),
    ]
    siswa = models.ForeignKey(
        "operations.Siswa", on_delete=models.PROTECT, related_name="tagihan"
    )
    periode_bulan = models.PositiveSmallIntegerField()
    periode_tahun = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="BELUM")
    # tautan ke jurnal core setelah dibayar (sub-ledger <-> general ledger)
    jurnal = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="tagihan",
    )

    history = HistoricalRecords()

    class Meta:
        unique_together = ("siswa", "periode_bulan", "periode_tahun")

    def __str__(self):
        return f"Tagihan {self.siswa} {self.periode_bulan}/{self.periode_tahun}"


class TagihanDetail(models.Model):
    KOMPONEN = [
        ("SPP", "SPP"), ("KATERING", "Katering"),
        ("JEMPUTAN", "Jemputan"), ("LAIN", "Lain-lain"),
    ]
    tagihan = models.ForeignKey(Tagihan, on_delete=models.CASCADE, related_name="detail")
    komponen = models.CharField(max_length=20, choices=KOMPONEN)
    akun_pendapatan = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="tagihan_detail", db_column="akun_pendapatan",
    )
    nominal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
