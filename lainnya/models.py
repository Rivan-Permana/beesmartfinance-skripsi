# lainnya/models.py
from django.db import models

class HargaEmas(models.Model):
    kategori = models.CharField(max_length=100)
    berat = models.CharField(max_length=50)
    harga_dasar = models.CharField(max_length=50)
    harga_pph = models.CharField(max_length=50, null=True, blank=True)
    rec_timestamp = models.IntegerField()
    rec_timestamp_str = models.CharField(max_length=50)

    class Meta:
        unique_together = ('kategori', 'berat')


class HargaBBM(models.Model):
    brent_price = models.FloatField()
    usd_idr = models.FloatField()
    harga_bbm_dasar = models.FloatField()

    bp_ldn_price = models.FloatField()
    bp_ldn_trend = models.CharField(max_length=20)

    bp_bre_price = models.FloatField()
    bp_bre_trend = models.CharField(max_length=20)

    bp_nyc_price = models.FloatField()
    bp_nyc_trend = models.CharField(max_length=20)

    bp_fra_price = models.FloatField()
    bp_fra_trend = models.CharField(max_length=20)

    kesimpulan = models.TextField()

    rectimestamp = models.DateTimeField()
    rectimestamp_epoch = models.BigIntegerField()

    def __str__(self):
        return f"Harga BBM {self.rectimestamp} - Brent: {self.brent_price}"