from django.db import models

class Jemputan(models.Model):
    nama_supir = models.CharField(max_length=100)
    no_kendaraan = models.CharField(max_length=20)
    kapasitas = models.PositiveIntegerField()
    keterangan = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nama_supir} - {self.no_kendaraan}"
