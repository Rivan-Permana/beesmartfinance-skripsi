"""Domain registrasi calon siswa (sit-in/trial -> admission)."""

from decimal import Decimal

from django.db import models
from simple_history.models import HistoricalRecords

from .base import SoftDeleteModel, TimeStampedModel


class PendaftaranSiswa(SoftDeleteModel, TimeStampedModel):
    STATUS = [
        ("TRIAL", "Sit-in/Trial"),
        ("REGISTERED", "Terdaftar"),
        ("BATAL", "Batal"),
    ]
    nama_calon = models.CharField(max_length=100)
    jenjang = models.ForeignKey(
        "operations.Jenjang", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="pendaftaran",
    )
    tanggal_daftar = models.DateField()
    biaya_sitin = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    biaya_pendaftaran = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    biaya_formulir = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS, default="TRIAL")
    siswa = models.OneToOneField(
        "operations.Siswa", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="pendaftaran",
    )
    jurnal_sitin = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="pendaftaran_sitin",
    )
    jurnal_pendaftaran = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="pendaftaran_admission",
    )

    history = HistoricalRecords()

    class Meta:
        constraints = [models.CheckConstraint(
            condition=models.Q(biaya_formulir__isnull=True) | (models.Q(biaya_formulir__gte=0) & models.Q(biaya_sitin__gte=0)),
            name="pendaftaran_biaya_nonnegatif",
        )]

    @property
    def perlu_rekonsiliasi(self):
        return self.biaya_formulir is None

    def pembayaran_aktif(self, komponen):
        jurnal = self.jurnal_sitin if komponen == "SITIN" else self.jurnal_pendaftaran
        return bool(jurnal and not jurnal.is_deleted and jurnal.status in {"DRAFT", "PENDING", "POSTED"}
                    and not list(jurnal.reversals.all()))

    @property
    def total_biaya(self):
        return None if self.perlu_rekonsiliasi else self.biaya_formulir + self.biaya_sitin

    @property
    def total_terbayar(self):
        if self.perlu_rekonsiliasi:
            return None
        return ((self.biaya_sitin if self.pembayaran_aktif("SITIN") else Decimal(0))
                + (self.biaya_formulir if self.pembayaran_aktif("FORMULIR") else Decimal(0)))

    @property
    def sisa_biaya(self):
        return None if self.perlu_rekonsiliasi else self.total_biaya - self.total_terbayar

    def __str__(self):
        return f"{self.nama_calon} ({self.status})"
