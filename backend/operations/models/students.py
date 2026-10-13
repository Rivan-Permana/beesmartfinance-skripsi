"""Domain siswa: jenjang, kelompok, siswa, kehadiran."""

from django.db import models
from simple_history.models import HistoricalRecords

from .base import SoftDeleteModel, TimeStampedModel


class Jenjang(models.Model):
    kode = models.CharField(max_length=10, unique=True)   # PG, TK
    nama = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class Kelompok(models.Model):
    jenjang = models.ForeignKey(Jenjang, on_delete=models.CASCADE, related_name="kelompok")
    nama = models.CharField(max_length=50)               # TKA, TKB

    def __str__(self):
        return f"{self.nama} ({self.jenjang.kode})"


class Siswa(SoftDeleteModel, TimeStampedModel):
    STATUS = [
        ("aktif", "Aktif"), ("lulus", "Lulus"), ("cuti", "Cuti"),
        ("pindah", "Pindah"), ("mengulang", "Mengulang Kelas"), ("naik", "Naik Kelas"),
    ]
    nis = models.CharField(max_length=20, unique=True, blank=True, null=True)
    nama = models.CharField(max_length=100)
    kelompok = models.ForeignKey(
        Kelompok, on_delete=models.SET_NULL, blank=True, null=True, related_name="siswa"
    )
    tanggal_lahir = models.DateField(blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    nama_ayah = models.CharField(max_length=100, blank=True, null=True)
    kontak_ayah = models.CharField(max_length=20, blank=True, null=True)
    nama_ibu = models.CharField(max_length=100, blank=True, null=True)
    kontak_ibu = models.CharField(max_length=20, blank=True, null=True)
    spp_nominal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tipe_tp = models.CharField(
        max_length=5,
        choices=[("baru", "Siswa Baru"), ("lama", "Daftar Ulang")],
        default="baru",
        help_text="Status TP untuk komponen biaya tahunan (baru vs daftar ulang).",
    )
    status = models.CharField(max_length=10, choices=STATUS, default="aktif")
    periode = models.ForeignKey(
        "accounting.MsPeriodeAkuntansi", on_delete=models.SET_NULL,
        db_constraint=False, blank=True, null=True, related_name="siswa",
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nis or '-'} - {self.nama}"


class KehadiranSiswa(models.Model):
    STATUS = [
        ("hadir", "Hadir"), ("izin", "Izin"), ("sakit", "Sakit"),
        ("tidak_hadir", "Tidak Hadir"),
    ]
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="kehadiran")
    tanggal = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS)
    ikut_katering = models.BooleanField(default=False)
    jemput_datang = models.BooleanField(default=False)
    jemput_pulang = models.BooleanField(default=False)

    class Meta:
        unique_together = ("siswa", "tanggal")
