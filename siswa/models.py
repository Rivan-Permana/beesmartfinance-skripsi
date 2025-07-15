from django.db import models
from catering.models import Katering
from jemputan.models import Jemputan

class Siswa(models.Model):
    JENJANG_CHOICES = (
        ('PG', 'Playgroup'),
        ('TK', 'Taman Kanak-kanak'),
    )
    nis = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nama = models.CharField(max_length=100)
    kelas = models.CharField(max_length=50, null=True, blank=True)
    jenjang = models.CharField(max_length=2, choices=JENJANG_CHOICES)
    tanggal_lahir = models.DateField()
    nama_wali = models.CharField(max_length=100)
    kontak_wali = models.CharField(max_length=20)
    katering = models.ForeignKey(Katering, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nis or '-'} - {self.nama}"


class SiswaKatering(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE)
    katering = models.ForeignKey(Katering, on_delete=models.CASCADE)
    tanggal_daftar = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.siswa.nama} - {self.katering}"

    class Meta:
        unique_together = ('siswa', 'katering')


class SiswaJemputan(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE)
    jemputan = models.ForeignKey(Jemputan, on_delete=models.CASCADE)
    tanggal_daftar = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.siswa.nama} - {self.jemputan}"

    class Meta:
        unique_together = ('siswa', 'jemputan')
