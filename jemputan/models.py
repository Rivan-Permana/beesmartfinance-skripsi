from django.db import models
from django.core.validators import RegexValidator, MinValueValidator

phone_validator = RegexValidator(
    regex=r'^[0-9+\-\s()]{6,20}$',
    message="Format No. HP tidak valid."
)

class Jemputan(models.Model):
    nama_supir   = models.CharField("Nama Supir", max_length=100)
    no_hp        = models.CharField("No. HP", max_length=25, validators=[phone_validator], blank=True)
    no_kendaraan = models.CharField("No. Kendaraan", max_length=20, unique=True)
    jenis_mobil  = models.CharField("Jenis Mobil", max_length=50, blank=True)
    kapasitas    = models.PositiveIntegerField("Kapasitas", validators=[MinValueValidator(1)], help_text="Jumlah kursi penumpang")
    pendamping   = models.CharField("Pendamping", max_length=100, blank=True)
    keterangan   = models.CharField("Keterangan", max_length=255, blank=True)

    class Meta:
        verbose_name = "Jemputan"
        verbose_name_plural = "Jemputan"
        ordering = ["nama_supir", "no_kendaraan"]
        indexes = [
            models.Index(fields=["nama_supir"]),
            models.Index(fields=["no_kendaraan"]),
        ]

    def __str__(self):
        supir = self.nama_supir or "-"
        plat  = self.no_kendaraan or "-"
        return f"{supir} — {plat}"
