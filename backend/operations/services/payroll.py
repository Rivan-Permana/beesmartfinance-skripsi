"""Service siklus pengeluaran kepegawaian: kasbon & payroll."""

from datetime import date
from decimal import Decimal

from django.db import transaction

from .common import akun_sistem, audit_user, buat_jurnal


def apply_potongan_pinjaman(gaji, *, save: bool = False) -> Decimal:
    """Hitung potongan kasbon aktif pegawai untuk periode gaji."""
    potong = Decimal(0)
    for pinj in gaji.pegawai.pinjaman.filter(is_deleted=False).order_by("tanggal_pinjaman"):
        sisa = pinj.sisa_pinjaman
        if sisa <= 0:
            continue
        angsuran = pinj.angsuran_per_bulan if pinj.angsuran_per_bulan > 0 else sisa
        potong += min(sisa, angsuran)
    gaji.potongan_pinjaman = potong
    if save:
        gaji.save(update_fields=["potongan_pinjaman", "updated_at"])
    return potong


def settle_pinjaman_from_gaji(gaji) -> None:
    """Kurangi saldo pinjaman setelah gaji diposting."""
    sisa_potong = gaji.potongan_pinjaman
    if sisa_potong <= 0:
        return
    for pinj in gaji.pegawai.pinjaman.filter(is_deleted=False).order_by("tanggal_pinjaman"):
        if sisa_potong <= 0:
            break
        bayar = min(pinj.sisa_pinjaman, pinj.angsuran_per_bulan or pinj.sisa_pinjaman, sisa_potong)
        if bayar <= 0:
            continue
        pinj.sudah_terbayar += bayar
        pinj.save(update_fields=["sudah_terbayar", "updated_at"])
        sisa_potong -= bayar


def post_pencairan_kasbon(pinjaman, user=None, akun_piutang=None, akun_kas=None):
    """Pencairan kasbon pegawai (Dr Piutang Karyawan, Cr Kas)."""
    if pinjaman.jurnal_id:
        raise ValueError("Pinjaman ini sudah dijurnal.")
    akun_piutang = akun_piutang or akun_sistem("PIUTANG_KARYAWAN", "114")
    akun_kas = akun_kas or akun_sistem("KAS", "111")
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


def post_gaji(gaji, user=None, akun_beban=None, akun_kas=None,
              akun_piutang=None, akun_utang_asuransi=None):
    """Payroll: Dr Beban Gaji (bruto); Cr Kas (netto)/Piutang/Utang Asuransi."""
    if gaji.jurnal_id:
        raise ValueError("Gaji periode ini sudah dijurnal.")
    akun_beban = akun_beban or akun_sistem("BEBAN_GAJI", "5301")
    akun_kas = akun_kas or akun_sistem("KAS", "111")
    akun_piutang = akun_piutang or akun_sistem("PIUTANG_KARYAWAN", "114")
    akun_utang_asuransi = akun_utang_asuransi or akun_sistem("UTANG_ASURANSI", "211")

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
            settle_pinjaman_from_gaji(gaji)
    return jurnal
