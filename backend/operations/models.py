"""Model operasional sekolah (Django ORM, fully managed).

Modul operasional dibangun penuh dgn Django ORM dan auto-posting ke core
accounting melalui service layer (lihat operations/services.py).
Audit pakai django-simple-history; penghapusan memakai soft-delete.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


# --------------------------------------------------------------------------
# Base
# --------------------------------------------------------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()       # default: sembunyikan yang terhapus
    all_objects = models.Manager()      # akses penuh termasuk terhapus

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


# --------------------------------------------------------------------------
# Master sekolah
# --------------------------------------------------------------------------
class Jenjang(models.Model):
    kode = models.CharField(max_length=10, unique=True)   # PG, TK
    nama = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class Kelompok(models.Model):
    jenjang = models.ForeignKey(Jenjang, on_delete=models.CASCADE, related_name="kelompok")
    nama = models.CharField(max_length=50)               # TKA, TKB

    def __str__(self):
        return f"{self.nama} ({self.jenjang.kode})"


class Siswa(SoftDeleteModel, TimeStampedModel):
    STATUS = [
        ("aktif", "Aktif"), ("lulus", "Lulus"), ("cuti", "Cuti"),
        ("pindah", "Pindah"), ("mengulang", "Mengulang Kelas"), ("naik", "Naik Kelas"),
    ]
    nis = models.CharField(max_length=20, unique=True, blank=True, null=True)
    nama = models.CharField(max_length=100)
    kelompok = models.ForeignKey(
        Kelompok, on_delete=models.SET_NULL, blank=True, null=True, related_name="siswa"
    )
    tanggal_lahir = models.DateField(blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    nama_ayah = models.CharField(max_length=100, blank=True, null=True)
    kontak_ayah = models.CharField(max_length=20, blank=True, null=True)
    nama_ibu = models.CharField(max_length=100, blank=True, null=True)
    kontak_ibu = models.CharField(max_length=20, blank=True, null=True)
    spp_nominal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="aktif")
    periode = models.ForeignKey(
        "accounting.MsPeriodeAkuntansi", on_delete=models.SET_NULL,
        db_constraint=False, blank=True, null=True, related_name="siswa",
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nis or '-'} - {self.nama}"


class Pegawai(SoftDeleteModel, TimeStampedModel):
    nip = models.CharField(max_length=20, unique=True, blank=True, null=True)
    nama = models.CharField(max_length=100)
    jabatan = models.CharField(max_length=50, blank=True, null=True)
    nomor_hp = models.CharField(max_length=20, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    status_aktif = models.BooleanField(default=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        blank=True, null=True, related_name="pegawai",
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nip or '-'} - {self.nama}"


# --------------------------------------------------------------------------
# Aturan posting (mapping event -> akun COA) — agar auto-journal tak hardcode
# --------------------------------------------------------------------------
class MsPostingRule(models.Model):
    event_code = models.CharField(max_length=40)        # TAGIHAN_PEMBAYARAN, dst
    komponen = models.CharField(max_length=40, blank=True, default="")
    akun_debit = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="rule_debit", db_column="akun_debit",
    )
    akun_kredit = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="rule_kredit", db_column="akun_kredit",
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        unique_together = ("event_code", "komponen")

    def __str__(self):
        return f"{self.event_code}/{self.komponen or '-'}"


# --------------------------------------------------------------------------
# Siklus pendapatan: tagihan siswa
# --------------------------------------------------------------------------
class Tagihan(SoftDeleteModel, TimeStampedModel):
    STATUS = [
        ("BELUM", "Belum Lunas"), ("SEBAGIAN", "Sebagian"), ("LUNAS", "Lunas"),
    ]
    siswa = models.ForeignKey(Siswa, on_delete=models.PROTECT, related_name="tagihan")
    periode_bulan = models.PositiveSmallIntegerField()
    periode_tahun = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="BELUM")
    # tautan ke jurnal core setelah dibayar (sub-ledger <-> general ledger)
    jurnal = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="tagihan",
    )

    history = HistoricalRecords()

    class Meta:
        unique_together = ("siswa", "periode_bulan", "periode_tahun")

    def __str__(self):
        return f"Tagihan {self.siswa} {self.periode_bulan}/{self.periode_tahun}"


class TagihanDetail(models.Model):
    KOMPONEN = [
        ("SPP", "SPP"), ("KATERING", "Katering"),
        ("JEMPUTAN", "Jemputan"), ("LAIN", "Lain-lain"),
    ]
    tagihan = models.ForeignKey(Tagihan, on_delete=models.CASCADE, related_name="detail")
    komponen = models.CharField(max_length=20, choices=KOMPONEN)
    akun_pendapatan = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="tagihan_detail", db_column="akun_pendapatan",
    )
    nominal = models.DecimalField(max_digits=18, decimal_places=2, default=0)


# --------------------------------------------------------------------------
# Absensi
# --------------------------------------------------------------------------
class KehadiranSiswa(models.Model):
    STATUS = [
        ("hadir", "Hadir"), ("izin", "Izin"), ("sakit", "Sakit"),
        ("tidak_hadir", "Tidak Hadir"),
    ]
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="kehadiran")
    tanggal = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS)
    ikut_katering = models.BooleanField(default=False)
    jemput_datang = models.BooleanField(default=False)
    jemput_pulang = models.BooleanField(default=False)

    class Meta:
        unique_together = ("siswa", "tanggal")


class AbsenPegawai(models.Model):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE, related_name="absen")
    tanggal = models.DateField()
    hadir = models.PositiveIntegerField(default=0)
    izin = models.PositiveIntegerField(default=0)
    sakit = models.PositiveIntegerField(default=0)
    terlambat = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("pegawai", "tanggal")


# --------------------------------------------------------------------------
# Layanan: katering & jemputan
# --------------------------------------------------------------------------
class MenuKatering(models.Model):
    tanggal = models.DateField()
    gambar = models.ImageField(upload_to="katering/", blank=True, null=True)
    keterangan = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = ("tanggal",)


class ArmadaJemputan(models.Model):
    nama_supir = models.CharField(max_length=100)
    jenis_mobil = models.CharField(max_length=50, blank=True, default="")
    kapasitas = models.PositiveIntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.nama_supir} ({self.jenis_mobil})"


class PendaftaranJemputan(SoftDeleteModel, TimeStampedModel):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name="jemputan")
    armada = models.ForeignKey(
        ArmadaJemputan, on_delete=models.SET_NULL, blank=True, null=True, related_name="penumpang"
    )
    harga = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        unique_together = ("siswa", "armada")


# --------------------------------------------------------------------------
# Kepegawaian: kasbon (pinjaman) & payroll
# --------------------------------------------------------------------------
class PinjamanPegawai(SoftDeleteModel, TimeStampedModel):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.PROTECT, related_name="pinjaman")
    tanggal_pinjaman = models.DateField()
    jumlah_pinjaman = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tenor_bulan = models.PositiveIntegerField(default=1)
    angsuran_per_bulan = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    sudah_terbayar = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    jurnal = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="pinjaman",
    )

    history = HistoricalRecords()

    @property
    def sisa_pinjaman(self):
        return max(self.jumlah_pinjaman - self.sudah_terbayar, self.jumlah_pinjaman.__class__(0))


class GajiPegawai(SoftDeleteModel, TimeStampedModel):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.PROTECT, related_name="gaji")
    periode_bulan = models.PositiveSmallIntegerField()
    periode_tahun = models.PositiveIntegerField()

    gaji_pokok = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tunjangan_jabatan = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tunjangan_pengabdian = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    transport = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    bonus_insentif = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    thr = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    potongan_pinjaman = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    potongan_asuransi = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    jurnal = models.ForeignKey(
        "accounting.TrJurnal", on_delete=models.SET_NULL, db_constraint=False,
        blank=True, null=True, related_name="gaji",
    )

    history = HistoricalRecords()

    class Meta:
        unique_together = ("pegawai", "periode_bulan", "periode_tahun")

    @property
    def total_bruto(self):
        return (
            self.gaji_pokok + self.tunjangan_jabatan + self.tunjangan_pengabdian
            + self.transport + self.bonus_insentif + self.thr
        )

    @property
    def total_potongan(self):
        return self.potongan_pinjaman + self.potongan_asuransi

    @property
    def total_netto(self):
        return self.total_bruto - self.total_potongan


# --------------------------------------------------------------------------
# Aset tetap & penyusutan
# --------------------------------------------------------------------------
class FixedAsset(SoftDeleteModel, TimeStampedModel):
    METODE = [("garis_lurus", "Garis Lurus")]
    nama = models.CharField(max_length=150)
    akun_aset = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="aset", db_column="akun_aset",
    )
    akun_akumulasi = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="aset_akumulasi", db_column="akun_akumulasi",
    )
    akun_beban_depr = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="aset_beban", db_column="akun_beban_depr",
    )
    tanggal_perolehan = models.DateField()
    harga_perolehan = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    umur_manfaat_bulan = models.PositiveIntegerField(default=1)
    metode = models.CharField(max_length=20, choices=METODE, default="garis_lurus")
    akumulasi_penyusutan = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    history = HistoricalRecords()

    @property
    def penyusutan_per_bulan(self):
        if self.umur_manfaat_bulan <= 0:
            return self.harga_perolehan.__class__(0)
        return self.harga_perolehan / self.umur_manfaat_bulan

    def __str__(self):
        return self.nama

