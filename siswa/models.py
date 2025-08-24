from django.db import models
from catering.models import Katering
from jemputan.models import Jemputan

class Jenjang(models.Model):
    kode = models.CharField(max_length=10, unique=True)  # PG, TK, dsb
    nama = models.CharField(max_length=100)  # Playgroup, Taman Kanak-kanak, dst

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class Kelompok(models.Model):
    jenjang = models.ForeignKey(Jenjang, on_delete=models.CASCADE, related_name='kelompok_list')
    nama = models.CharField(max_length=50)  # TKA, TKB, dst

    def __str__(self):
        return f"{self.nama} ({self.jenjang.kode})"


class Periode(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama

class Siswa(models.Model):
    STATUS_CHOICES = (
        ('aktif', 'Aktif'),
        ('lulus', 'Lulus'),
        ('cuti', 'Cuti'),
        ('pindah', 'Pindah'),
        ('mengulang', 'Mengulang Kelas'),
        ('naik', 'Naik Kelas'),
    )

    nis = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nama = models.CharField(max_length=100)
    kelompok = models.ForeignKey(Kelompok, on_delete=models.SET_NULL, null=True, blank=True)
    tanggal_lahir = models.DateField()
    alamat = models.TextField(null=True, blank=True)

    nama_ayah = models.CharField(max_length=100, null=True, blank=True)
    kontak_ayah = models.CharField(max_length=20, null=True, blank=True)
    nama_ibu = models.CharField(max_length=100, null=True, blank=True)
    kontak_ibu = models.CharField(max_length=20, null=True, blank=True)

    spp = models.IntegerField(null=True, blank=True, help_text="Nominal SPP dalam rupiah")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    periode = models.ForeignKey(Periode, on_delete=models.SET_NULL, null=True, blank=True)
    

    def __str__(self):
        return f"{self.nis or '-'} - {self.nama}"



class SiswaKatering(models.Model):
    siswa = models.ForeignKey('Siswa', on_delete=models.CASCADE)
    katering = models.ForeignKey('catering.Katering', on_delete=models.CASCADE)
    tanggal_daftar = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.siswa.nama} - {self.katering}"

    class Meta:
        unique_together = ('siswa', 'katering')


class SiswaJemputan(models.Model):
    siswa = models.ForeignKey('Siswa', on_delete=models.CASCADE)
    jemputan = models.ForeignKey('jemputan.Jemputan', on_delete=models.CASCADE)
    tanggal_daftar = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.siswa.nama} - {self.jemputan}"

    class Meta:
        unique_together = ('siswa', 'jemputan')


class Kehadiran(models.Model):
    KEHADIRAN_CHOICES = [
        ('hadir', 'Hadir'),
        ('tidak_hadir', 'Tidak Hadir'),
        ('izin', 'Izin'),
        ('sakit', 'Sakit'),
    ]

    siswa = models.ForeignKey('Siswa', on_delete=models.CASCADE)
    tanggal = models.DateField()

    kehadiran = models.CharField(max_length=20, choices=KEHADIRAN_CHOICES)
    katering = models.CharField(max_length=20, blank=True, null=True)  # ikut / tidak_ikut
    jemput_datang = models.BooleanField(default=False)
    jemput_pulang = models.BooleanField(default=False)
    # ⬇️ Tambahan: pendamping jemputan harian
    pendamping = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('siswa', 'tanggal')

    def __str__(self):
        return f"{self.siswa.nama} - {self.tanggal} - {self.kehadiran}"