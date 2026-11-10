"""Paket LSU: buat paket + tagihan, catat dan hapus pertemuan."""

from decimal import Decimal

from django.db import transaction

from .common import audit_user


def sesi_terpakai(paket):
    return paket.pertemuan.count()


def buat_paket(*, siswa, jumlah_sesi, harga, tanggal_mulai, keterangan="", user=None):
    """Paket baru beserta tagihannya. Paket sebelumnya harus sudah habis (sesi dihabiskan, tanpa refund)."""
    from operations.models import PaketLSU, Tagihan, TagihanDetail
    from operations.services.billing import perbarui_status_tagihan
    from operations.services.tp_templates import _akun_for_komponen

    if jumlah_sesi not in (8, 16):
        raise ValueError("Paket LSU berisi 8 atau 16 pertemuan.")
    if harga is None or harga <= 0:
        raise ValueError("Isi harga paket lebih dari nol.")
    with transaction.atomic(), audit_user(user):
        for lama in PaketLSU.objects.select_for_update().filter(siswa=siswa):
            if sesi_terpakai(lama) < lama.jumlah_sesi:
                raise ValueError(
                    f"Paket {lama.jumlah_sesi} pertemuan sejak {lama.tanggal_mulai:%d/%m/%Y} masih punya sisa sesi. "
                    "Habiskan dulu sebelum membuka paket baru."
                )
        tagihan = Tagihan.objects.create(
            siswa=siswa, periode_bulan=tanggal_mulai.month, periode_tahun=tanggal_mulai.year,
            jenis="LSU", total=harga, status="BELUM",
        )
        TagihanDetail.objects.create(
            tagihan=tagihan, komponen="LSU", kategori="LAIN",
            keterangan=f"Paket LSU {jumlah_sesi} pertemuan", akun_pendapatan_id=_akun_for_komponen("LSU"),
            nominal=harga,
        )
        perbarui_status_tagihan(tagihan)
        return PaketLSU.objects.create(
            siswa=siswa, jumlah_sesi=jumlah_sesi, harga=Decimal(harga), tanggal_mulai=tanggal_mulai,
            keterangan=keterangan, tagihan=tagihan, created_by=user,
        )


def hapus_paket(paket, user=None):
    """Hanya paket tanpa pertemuan dan tanpa penerimaan; tagihannya ikut dibatalkan."""
    from operations.models import PaketLSU

    with transaction.atomic(), audit_user(user):
        paket = PaketLSU.objects.select_for_update().get(pk=paket.pk)
        if paket.pertemuan.exists():
            raise ValueError("Paket yang sudah punya catatan pertemuan tidak bisa dihapus.")
        tagihan = paket.tagihan
        if tagihan and tagihan.pembayaran.exists():
            raise ValueError("Tagihan paket ini sudah punya penerimaan. Batalkan penerimaannya dulu.")
        paket.delete()
        if tagihan:
            tagihan.delete()


def catat_pertemuan(paket, *, tanggal, catatan="", user=None):
    from operations.models import PaketLSU, PertemuanLSU

    with transaction.atomic(), audit_user(user):
        paket = PaketLSU.objects.select_for_update().get(pk=paket.pk)
        if tanggal < paket.tanggal_mulai:
            raise ValueError("Tanggal pertemuan sebelum paket dimulai.")
        if sesi_terpakai(paket) >= paket.jumlah_sesi:
            raise ValueError("Semua sesi paket ini sudah terpakai. Buka paket baru.")
        if paket.pertemuan.filter(tanggal=tanggal).exists():
            raise ValueError("Pertemuan di tanggal ini sudah dicatat.")
        return PertemuanLSU.objects.create(paket=paket, tanggal=tanggal, catatan=catatan, created_by=user)
