"""Service realisasi kegiatan (Teacher in Charge)."""

from decimal import Decimal

from django.db import transaction

from .common import akun_sistem, audit_user, buat_jurnal


def post_realisasi_kegiatan(kegiatan, tanggal, deskripsi, nominal, user=None,
                            akun_kas=None):
    """Realisasi (pengeluaran) kegiatan -> auto-journal beban, cek pagu kegiatan."""
    from operations.models import RealisasiKegiatan

    akun_kas = akun_kas or akun_sistem("KAS", "1101")
    nominal = Decimal(str(nominal))
    if nominal <= 0:
        raise ValueError("Nominal realisasi harus > 0.")
    if kegiatan.realisasi + nominal > kegiatan.pagu:
        raise ValueError(
            f"Melebihi pagu kegiatan (pagu {kegiatan.pagu}, "
            f"terpakai {kegiatan.realisasi})."
        )

    seq = RealisasiKegiatan.objects.filter(kegiatan=kegiatan).count() + 1
    with transaction.atomic():
        with audit_user(user):
            jurnal = buat_jurnal(
                no_bukti=f"KG-{kegiatan.id}-{seq}",
                tanggal=tanggal,
                keterangan=f"Realisasi {kegiatan.nama}: {deskripsi}",
                tipe="AUTO_KEGIATAN",
                baris=[
                    (kegiatan.akun_beban_id, nominal, Decimal(0)),
                    (akun_kas, Decimal(0), nominal),
                ],
                user=user,
            )
            realisasi = RealisasiKegiatan.objects.create(
                kegiatan=kegiatan, tanggal=tanggal, deskripsi=deskripsi,
                nominal=nominal, jurnal=jurnal,
            )
    return realisasi
