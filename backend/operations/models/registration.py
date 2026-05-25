"""Domain registrasi calon siswa (sit-in/trial -> admission)."""

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

    def __str__(self):
        return f"{self.nama_calon} ({self.status})"
