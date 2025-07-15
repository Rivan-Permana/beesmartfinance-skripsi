from django.db import models

class Katering(models.Model):
    tanggal = models.DateField()
    menu = models.TextField()
    jumlah_porsi = models.PositiveIntegerField()
    keterangan = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.tanggal} - {self.menu[:30]}"
