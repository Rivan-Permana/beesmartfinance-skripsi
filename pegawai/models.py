from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

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


class PinjamanPegawai(models.Model):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE, related_name='pinjaman')
    tanggal_pinjaman = models.DateField()
    tenor_cicilan = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="bulan")
    jumlah_pinjaman = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    angsuran_per_bulan = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    sudah_terbayar = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tanggal_pelunasan = models.DateField(blank=True, null=True)

    class Meta: ordering = ['-tanggal_pinjaman']
    def __str__(self): return f"Pinjaman {self.pegawai.nama} - {self.tanggal_pinjaman}"

    @property
    def sisa_pinjaman(self):
        return max(Decimal(self.jumlah_pinjaman or 0) - Decimal(self.sudah_terbayar or 0), Decimal('0'))


class GajiPegawai(models.Model):
    BULAN_CHOICES = [(i, i) for i in range(1, 13)]
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE, related_name='gaji')
    periode_bulan = models.PositiveSmallIntegerField(choices=BULAN_CHOICES)
    periode_tahun = models.PositiveIntegerField()

    # INPUT MANUAL
    gaji_pokok = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tunjangan_pengabdian = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tunjangan_jabatan = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    thr = models.DecimalField("THR", max_digits=12, decimal_places=2, default=0)

    # OTOMATIS (diset di save())
    bonus_insentif = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lunch = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # POTONGAN (otomatis)
    pinjaman = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    asuransi = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ('pegawai', 'periode_bulan', 'periode_tahun')
        ordering = ['-periode_tahun', '-periode_bulan']

    def __str__(self):
        return f"Gaji {self.pegawai.nama} {self.periode_bulan}/{self.periode_tahun}"

    # ---- Perhitungan ----
    def _sum_insentif_bulan(self):
        return (AbsenPegawai.objects
                .filter(pegawai=self.pegawai,
                        tanggal__year=self.periode_tahun,
                        tanggal__month=self.periode_bulan)
                .aggregate(x=models.Sum('insentif'))['x'] or Decimal('0'))

    def _sum_hadir_bulan(self):
        return (AbsenPegawai.objects
                .filter(pegawai=self.pegawai,
                        tanggal__year=self.periode_tahun,
                        tanggal__month=self.periode_bulan)
                .aggregate(x=models.Sum('hadir'))['x'] or 0)

    def _sum_pinjaman_bulan(self):
        # Pinjaman aktif = belum lunas
        return (self.pegawai.pinjaman
                .filter(tanggal_pelunasan__isnull=True)
                .aggregate(x=models.Sum('angsuran_per_bulan'))['x'] or Decimal('0'))

    def _asuransi_bulan(self):
        return Decimal('100000') if (self.pegawai.work_periode_tahun or 0) >= 1 else Decimal('0')

    def _transport_bulan(self):
        return Decimal(self.pegawai.uang_transport or 0)

    def _lunch_bulan(self):
        # 20.000 per hari hadir
        hadir = self._sum_hadir_bulan()
        return Decimal(hadir) * Decimal('20000')

    def _total_pendapatan(self):
        return Decimal(self.gaji_pokok or 0) + \
               Decimal(self.tunjangan_pengabdian or 0) + \
               Decimal(self.tunjangan_jabatan or 0) + \
               Decimal(self.bonus_insentif or 0) + \
               Decimal(self.lunch or 0) + \
               Decimal(self.transport or 0) + \
               Decimal(self.thr or 0)

    def save(self, *args, **kwargs):
        # isi otomatis sebelum hitung total
        self.bonus_insentif = self._sum_insentif_bulan()
        self.transport = self._transport_bulan()
        self.lunch = self._lunch_bulan()
        self.pinjaman = self._sum_pinjaman_bulan()
        self.asuransi = self._asuransi_bulan()
        self.total = self._total_pendapatan()
        self.grand_total = self.total - (Decimal(self.pinjaman or 0) + Decimal(self.asuransi or 0))
        super().save(*args, **kwargs)