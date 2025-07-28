from django.db import models

class Pegawai(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    nik = models.CharField(max_length=20, unique=True, default='0000000000000000')
    nip = models.CharField(max_length=20, blank=True, null=True)
    nama = models.CharField(max_length=100)
    jabatan = models.CharField(max_length=50)
    work_periode_bulan = models.PositiveIntegerField(default=0)
    work_periode_tahun = models.PositiveIntegerField(default=0)
    nomor_hp = models.CharField(max_length=20)
    alamat = models.TextField(default="")
    uang_transport = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')  # << Tambahkan ini


    def __str__(self):
        return self.nama

class AbsenPegawai(models.Model):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE)
    tanggal = models.DateField(auto_now_add=True)

    hadir = models.IntegerField(default=0)
    tidak_hadir = models.IntegerField(default=0)
    izin = models.IntegerField(default=0)
    sakit = models.IntegerField(default=0)
    insentif = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    terlambat = models.IntegerField(default=0)

    class Meta:
        unique_together = ('pegawai', 'tanggal')


    @property
    def total(self):
        return self.insentif
