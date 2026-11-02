"""Domain pengeluaran: kode singkat sekolah -> akun COA untuk input cepat."""

from django.db import models


class KodePengeluaran(models.Model):
    """Kode buku kas sekolah (ATK, PLN, AB3, ...) per unit, dipetakan ke akun beban."""

    UNIT = [("UMUM", "Umum"), ("TK", "TK"), ("PG", "PG")]

    kode = models.CharField(max_length=20)
    unit = models.CharField(max_length=5, choices=UNIT, default="UMUM")
    nama = models.CharField(max_length=120, blank=True, default="")
    # Kosong = arti kode belum dikonfirmasi sekolah; akun dipilih manual saat input.
    akun = models.ForeignKey(
        "accounting.MsCoa", on_delete=models.DO_NOTHING, db_constraint=False,
        blank=True, null=True, related_name="kode_pengeluaran", db_column="kode_akun",
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        ordering = ["kode", "unit"]
        constraints = [
            models.UniqueConstraint(fields=["kode", "unit"], name="kode_pengeluaran_unit_unik"),
        ]

    def __str__(self):
        return self.kode if self.unit == "UMUM" else f"{self.kode} {self.unit}"
