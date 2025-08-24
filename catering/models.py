from django.db import models
class Katering(models.Model):
    tanggal = models.DateField()
    menu = models.TextField()
    jumlah_porsi = models.PositiveIntegerField()
    keterangan = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.tanggal} - {self.menu[:30]}"

class KateringEntry(models.Model):
    """
    1 baris = 1 siswa pada 1 tanggal.
    """
    siswa = models.ForeignKey('siswa.Siswa', on_delete=models.CASCADE, related_name='katering_entries')
    tanggal = models.DateField()
    ikut = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('siswa', 'tanggal')
        ordering = ['tanggal']

    def __str__(self):
        return f"{self.siswa} @ {self.tanggal} ({'Ikut' if self.ikut else 'Tidak'})"