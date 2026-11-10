"""Learning Support Unit (LSU): paket terapi 8/16 pertemuan per siswa.

Sesi dihabiskan tanpa refund. Terapis menyerahkan kehadiran ke TU, TU yang mencatat pertemuan.
Tiap paket ditagih sekali lewat Tagihan jenis LSU.
"""

from django.conf import settings
from django.db import models

from .base import TimeStampedModel


class PaketLSU(TimeStampedModel):
    JUMLAH_SESI = [(8, "8 pertemuan"), (16, "16 pertemuan")]

    siswa = models.ForeignKey("operations.Siswa", on_delete=models.PROTECT, related_name="paket_lsu")
    jumlah_sesi = models.PositiveSmallIntegerField(choices=JUMLAH_SESI)
    harga = models.DecimalField(max_digits=18, decimal_places=2)
    tanggal_mulai = models.DateField()
    keterangan = models.CharField(max_length=255, blank=True, default="")
    tagihan = models.OneToOneField(
        "operations.Tagihan", on_delete=models.PROTECT, related_name="paket_lsu", null=True, blank=True,
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ["-tanggal_mulai", "-pk"]
        constraints = [models.CheckConstraint(condition=models.Q(harga__gt=0), name="paket_lsu_harga_positif")]

    def __str__(self):
        return f"LSU {self.siswa} {self.jumlah_sesi}x"


class PertemuanLSU(models.Model):
    paket = models.ForeignKey(PaketLSU, on_delete=models.CASCADE, related_name="pertemuan")
    tanggal = models.DateField()
    catatan = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tanggal", "pk"]
        constraints = [models.UniqueConstraint(fields=["paket", "tanggal"], name="pertemuan_lsu_sekali_sehari")]
