"""Core accounting models.

PENTING: semua model di sini `managed = False`. DDL tabel, trigger, view,
dan constraint dimiliki oleh raw SQL di `database/schemas/*.sql` dan diterapkan
lewat migrasi RunSQL (lihat accounting/migrations). Django hanya membaca/menulis
data, tidak pernah mengubah strukturnya.
"""

from django.conf import settings
from django.db import models


class MsGolongan(models.Model):
    kode_golongan = models.CharField(max_length=5, unique=True)
    nama_golongan = models.CharField(max_length=50)
    deskripsi = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ms_golongan"

    def __str__(self):
        return f"{self.kode_golongan} - {self.nama_golongan}"


class MsSubGolongan(models.Model):
    golongan = models.ForeignKey(
        MsGolongan, on_delete=models.DO_NOTHING, db_column="golongan_id",
        db_constraint=False, related_name="sub_golongan",
    )
    kode_sub = models.CharField(max_length=10, unique=True)
    nama_sub = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "ms_sub_golongan"

    def __str__(self):
        return f"{self.kode_sub} - {self.nama_sub}"


class MsCoa(models.Model):
    POSISI_CHOICES = [("D", "Debit"), ("K", "Kredit")]

    kode_akun = models.CharField(max_length=20, primary_key=True)
    sub_golongan = models.ForeignKey(
        MsSubGolongan, on_delete=models.DO_NOTHING, db_column="sub_golongan_id",
        db_constraint=False, related_name="akun", blank=True, null=True,
    )
    nama_akun = models.CharField(max_length=255)
    posisi_normal = models.CharField(max_length=1, choices=POSISI_CHOICES)
    is_active = models.BooleanField(default=True)
    saldo_awal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tanggal_saldo_awal = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "ms_coa"

    def __str__(self):
        return f"{self.kode_akun} - {self.nama_akun}"


class MsPeriodeAkuntansi(models.Model):
    STATUS_CHOICES = [("OPEN", "Open"), ("CLOSED", "Closed")]

    kode = models.CharField(max_length=20, unique=True)  # contoh: 2025/2026
    tgl_mulai = models.DateField()
    tgl_selesai = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")

    class Meta:
        managed = False
        db_table = "ms_periode_akuntansi"

    def __str__(self):
        return f"{self.kode} ({self.status})"


class TrJurnal(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PENDING", "Pending"),
        ("POSTED", "Posted"),
        ("VOID", "Void"),
    ]

    id = models.UUIDField(primary_key=True)
    no_bukti = models.CharField(max_length=50, unique=True)
    tanggal = models.DateField()
    keterangan = models.TextField(blank=True, null=True)
    tipe_sumber = models.CharField(max_length=20, default="MANUAL")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="DRAFT")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
        db_column="created_by_id", db_constraint=False,
        related_name="jurnal_dibuat", blank=True, null=True,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
        db_column="submitted_by_id", db_constraint=False,
        related_name="jurnal_disubmit", blank=True, null=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
        db_column="approved_by_id", db_constraint=False,
        related_name="jurnal_disetujui", blank=True, null=True,
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    posted_at = models.DateTimeField(blank=True, null=True)
    reversal_of = models.ForeignKey(
        "self", on_delete=models.DO_NOTHING, db_column="reversal_of_id",
        db_constraint=False, related_name="reversals", blank=True, null=True,
    )
    fiscal_period = models.ForeignKey(
        MsPeriodeAkuntansi, on_delete=models.DO_NOTHING, db_column="fiscal_period_id",
        db_constraint=False, related_name="jurnal", blank=True, null=True,
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "tr_jurnal"

    def __str__(self):
        return f"{self.no_bukti} ({self.status})"


class TrJurnalDetail(models.Model):
    id = models.BigAutoField(primary_key=True)
    jurnal = models.ForeignKey(
        TrJurnal, on_delete=models.DO_NOTHING, db_column="jurnal_id",
        db_constraint=False, related_name="detail",
    )
    kode_akun = models.ForeignKey(
        MsCoa, on_delete=models.DO_NOTHING, db_column="kode_akun",
        db_constraint=False, related_name="jurnal_detail",
    )
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    kredit = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        managed = False
        db_table = "tr_jurnal_detail"


class TrAnggaran(models.Model):
    kode_akun = models.ForeignKey(
        MsCoa, on_delete=models.DO_NOTHING, db_column="kode_akun",
        db_constraint=False, related_name="anggaran",
    )
    tahun_anggaran = models.IntegerField()
    bulan = models.IntegerField(blank=True, null=True)
    nominal_anggaran = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    keterangan = models.TextField(blank=True, null=True)
    carry_over = models.BooleanField(default=False)
    periode = models.ForeignKey(
        MsPeriodeAkuntansi, on_delete=models.DO_NOTHING, db_column="periode_id",
        db_constraint=False, related_name="anggaran", blank=True, null=True,
    )

    class Meta:
        managed = False
        db_table = "tr_anggaran"


class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    table_name = models.TextField()
    row_pk = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=10)
    old_data = models.JSONField(blank=True, null=True)
    new_data = models.JSONField(blank=True, null=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,
        db_column="changed_by", db_constraint=False,
        related_name="audit_entries", blank=True, null=True,
    )
    changed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "audit_log"
