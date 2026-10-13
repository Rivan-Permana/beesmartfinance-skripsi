"""Domain kepegawaian: pegawai & absensi."""

from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from .base import SoftDeleteModel, TimeStampedModel


class Pegawai(SoftDeleteModel, TimeStampedModel):
    nip = models.CharField(max_length=20, unique=True, blank=True, null=True)
    nama = models.CharField(max_length=100)
    jabatan = models.CharField(max_length=50, blank=True, null=True)
    nomor_hp = models.CharField(max_length=20, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    status_aktif = models.BooleanField(default=True)
    tanggal_mulai_kerja = models.DateField(blank=True, null=True)
    tanggal_selesai_kerja = models.DateField(blank=True, null=True)
    tarif_uang_makan_hari = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Tarif harian uang makan (KAFALAH Lunch).",
    )
    tarif_transport_hari = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Tarif harian transport (KAFALAH Transport).",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        blank=True, null=True, related_name="pegawai",
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nip or '-'} - {self.nama}"


class AbsenPegawai(models.Model):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE, related_name="absen")
    tanggal = models.DateField()
    hadir = models.PositiveIntegerField(default=0)
    izin = models.PositiveIntegerField(default=0)
    sakit = models.PositiveIntegerField(default=0)
    terlambat = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("pegawai", "tanggal")
