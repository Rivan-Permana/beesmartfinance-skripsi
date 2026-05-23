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
