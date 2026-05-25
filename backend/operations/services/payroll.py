"""Service siklus pengeluaran kepegawaian: kasbon & payroll."""

from datetime import date
from decimal import Decimal

from django.db import transaction

from .common import audit_user, buat_jurnal


def post_pencairan_kasbon(pinjaman, user=None, akun_piutang="1103", akun_kas="1101"):
    """Pencairan kasbon pegawai (Dr Piutang Karyawan, Cr Kas)."""
    if pinjaman.jurnal_id:
        raise ValueError("Pinjaman ini sudah dijurnal.")
    with transaction.atomic():
        with audit_user(user):
            jurnal = buat_jurnal(
                no_bukti=f"KB-{pinjaman.id}",
                tanggal=pinjaman.tanggal_pinjaman,
                keterangan=f"Pencairan kasbon {pinjaman.pegawai}",
                tipe="AUTO_KASBON",
                baris=[
                    (akun_piutang, pinjaman.jumlah_pinjaman, Decimal(0)),
                    (akun_kas, Decimal(0), pinjaman.jumlah_pinjaman),
                ],
                user=user,
            )
            pinjaman.jurnal = jurnal
            pinjaman.save(update_fields=["jurnal", "updated_at"])
    return jurnal


def post_gaji(gaji, user=None, akun_beban="5201", akun_kas="1101",
              akun_piutang="1103", akun_utang_asuransi="2101"):
    """Payroll: Dr Beban Gaji (bruto); Cr Kas (netto)/Piutang/Utang Asuransi."""
    if gaji.jurnal_id:
        raise ValueError("Gaji periode ini sudah dijurnal.")

    baris = [(akun_beban, gaji.total_bruto, Decimal(0)),
             (akun_kas, Decimal(0), gaji.total_netto)]
    if gaji.potongan_pinjaman:
        baris.append((akun_piutang, Decimal(0), gaji.potongan_pinjaman))
    if gaji.potongan_asuransi:
        baris.append((akun_utang_asuransi, Decimal(0), gaji.potongan_asuransi))

    with transaction.atomic():
        with audit_user(user):
            jurnal = buat_jurnal(
                no_bukti=f"GJ-{gaji.id}-{gaji.periode_tahun}{gaji.periode_bulan:02d}",
                tanggal=date(gaji.periode_tahun, gaji.periode_bulan, 28),
                keterangan=f"Gaji {gaji.pegawai} {gaji.periode_bulan}/{gaji.periode_tahun}",
                tipe="AUTO_PAYROLL", baris=baris, user=user,
            )
            gaji.jurnal = jurnal
            gaji.save(update_fields=["jurnal", "updated_at"])
    return jurnal
