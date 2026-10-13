"""Domain layanan sekolah: katering & jemputan."""

from django.db import models

from .base import SoftDeleteModel, TimeStampedModel


class MenuKatering(models.Model):
    tanggal = models.DateField()
    gambar = models.ImageField(upload_to="katering/", blank=True, null=True)
    keterangan = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = ("tanggal",)


class TarifKatering(models.Model):
    """Tarif katering per periode bulan — Sen–Kam vs Jumat (snack)."""

    periode_bulan = models.PositiveSmallIntegerField()
    periode_tahun = models.PositiveSmallIntegerField()
    tarif_harian = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text="Tarif Senin–Kamis (makan siang).",
    )
    tarif_jumat = models.DecimalField(
        max_digits=18, decimal_places=2, default=10_000,
        help_text="Tarif snack Jumat.",
    )

    class Meta:
        unique_together = ("periode_bulan", "periode_tahun")
        ordering = ["-periode_tahun", "-periode_bulan"]

    def __str__(self):
        return f"Katering {self.periode_bulan}/{self.periode_tahun}: Rp {self.tarif_harian}"


class ArmadaJemputan(models.Model):
    nama_supir = models.CharField(max_length=100)
    jenis_mobil = models.CharField(max_length=50, blank=True, default="")
    kapasitas = models.PositiveIntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.nama_supir} ({self.jenis_mobil})"


class PendaftaranJemputan(SoftDeleteModel, TimeStampedModel):
    siswa = models.ForeignKey(
        "operations.Siswa", on_delete=models.CASCADE, related_name="jemputan"
    )
    armada = models.ForeignKey(
        ArmadaJemputan, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="penumpang",
    )
    harga = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        unique_together = ("siswa", "armada")
