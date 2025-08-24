# models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Keuangan(models.Model):
    JENIS_CHOICES = (
        ('Masuk', 'Pemasukan'),
        ('Keluar', 'Pengeluaran'),
    )

    tanggal = models.DateField()
    deskripsi = models.CharField(max_length=255)
    jenis = models.CharField(max_length=10, choices=JENIS_CHOICES)
    jumlah = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.tanggal} - {self.deskripsi}"

class COA(models.Model):
    class Category(models.TextChoices):
        TK = "TK", _("TK")
        PLAYGROUP = "PLAYGROUP", _("Playgroup")

    nomor_akun = models.CharField(
        max_length=20,
        help_text="Contoh: 1, 11, 1101"
    )
    tipe_akun = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Contoh: ASET, ASET LANCAR"
    )
    nama_akun = models.CharField(
        max_length=150,
        null=True,
        blank=True,
    )
    category = models.CharField(max_length=10, choices=Category.choices)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "COA"
        verbose_name_plural = "COA"
        constraints = [
            models.UniqueConstraint(
                fields=["category", "nomor_akun"],
                name="uniq_nomor_akun_per_category"
            )
        ]
        ordering = ["nomor_akun"]

    def __str__(self):
        tipe = self.tipe_akun.upper() if self.tipe_akun else "-"
        nama = self.nama_akun.upper() if self.nama_akun else "-"
        return f"[{self.category}] {self.nomor_akun} - {tipe} - {nama}"