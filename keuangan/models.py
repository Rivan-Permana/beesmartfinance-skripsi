# models.py
from django.db import models

class Keuangan(models.Model):
    JENIS_CHOICES = (
        ('Masuk', 'Pemasukan'),
        ('Keluar', 'Pengeluaran'),
    )

    tanggal = models.DateField()
    deskripsi = models.CharField(max_length=255)
    jenis = models.CharField(max_length=10, choices=JENIS_CHOICES)
    jumlah = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.tanggal} - {self.deskripsi}"
