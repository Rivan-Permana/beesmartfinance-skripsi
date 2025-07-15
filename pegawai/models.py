from django.db import models

class Pegawai(models.Model):
    nama = models.CharField(max_length=100)
    jabatan = models.CharField(max_length=50)
    email = models.EmailField()
    nomor_hp = models.CharField(max_length=20)

    def __str__(self):
        return self.nama
