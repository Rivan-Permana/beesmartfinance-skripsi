"""Service penyusutan aset tetap."""

from datetime import date
from decimal import Decimal

from django.db import transaction

from .common import audit_user, buat_jurnal


def post_penyusutan(asset, user=None, tanggal=None):
    """Penyusutan periodik (Dr Beban Depresiasi, Cr Akumulasi Penyusutan)."""
    nominal = asset.penyusutan_per_bulan
    if nominal <= 0:
        raise ValueError("Nominal penyusutan nol.")
    tanggal = tanggal or date.today()
    with transaction.atomic():
        with audit_user(user):
            jurnal = buat_jurnal(
                no_bukti=f"DP-{asset.id}-{tanggal:%Y%m}",
                tanggal=tanggal,
                keterangan=f"Penyusutan {asset.nama} {tanggal:%m/%Y}",
                tipe="AUTO_DEPRESIASI",
                baris=[
                    (asset.akun_beban_depr_id, nominal, Decimal(0)),
                    (asset.akun_akumulasi_id, Decimal(0), nominal),
                ],
                user=user,
            )
            asset.akumulasi_penyusutan = asset.akumulasi_penyusutan + nominal
            asset.save(update_fields=["akumulasi_penyusutan", "updated_at"])
    return jurnal
