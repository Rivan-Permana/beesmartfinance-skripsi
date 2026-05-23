"""Service layer: auto-posting siklus operasional -> core accounting.

Aturan akuntansi (balance, immutability, anggaran) tetap dijaga trigger DB;
service ini menyusun jurnal yang benar lalu menyerahkan ke core sebagai DRAFT
(menunggu approval Principal sesuai alur maker-checker).
"""

import uuid
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from django.db import connection, transaction

from accounting.models import TrJurnal, TrJurnalDetail


@contextmanager
def audit_user(user):
    """Kirim user aplikasi ke sesi DB agar trigger audit mencatat pelakunya.

    Memakai set_config(..., is_local=true) = SET LOCAL, valid hanya dalam
    transaksi berjalan.
    """
    user_id = "" if user is None else str(user.pk)
    with connection.cursor() as cur:
        cur.execute("SELECT set_config('app.current_user_id', %s, true)", [user_id])
    yield


def post_pembayaran_tagihan(tagihan, user=None, akun_kas_kode="1101"):
    """Buat jurnal DRAFT saat tagihan dibayar lunas (siklus pendapatan).

    Debit  : Kas/Bank (akun_kas_kode)        sebesar total tagihan
    Kredit : akun pendapatan tiap komponen   sesuai TagihanDetail
    """
    if tagihan.jurnal_id:
        raise ValueError("Tagihan ini sudah memiliki jurnal.")

    detail = list(tagihan.detail.all())
    if not detail:
        raise ValueError("Tagihan tidak memiliki rincian komponen.")

    total_kredit = sum((d.nominal for d in detail), start=tagihan.total.__class__(0))

    with transaction.atomic():
        with audit_user(user):
            jurnal = TrJurnal.objects.create(
                id=uuid.uuid4(),
                no_bukti=f"BL-{tagihan.id}-{tagihan.periode_tahun}{tagihan.periode_bulan:02d}",
                tanggal=date.today(),
                keterangan=f"Pembayaran tagihan {tagihan.siswa} "
                           f"periode {tagihan.periode_bulan}/{tagihan.periode_tahun}",
                tipe_sumber="AUTO_BILLING",
                status="DRAFT",
                created_by=user,
            )
            TrJurnalDetail.objects.create(
                jurnal=jurnal, kode_akun_id=akun_kas_kode,
                debit=total_kredit, kredit=0,
            )
            for d in detail:
                TrJurnalDetail.objects.create(
                    jurnal=jurnal, kode_akun=d.akun_pendapatan,
                    debit=0, kredit=d.nominal,
                )

            tagihan.jurnal = jurnal
            tagihan.status = "LUNAS"
            tagihan.total = total_kredit
            tagihan.save(update_fields=["jurnal", "status", "total", "updated_at"])

    return jurnal


def _buat_jurnal(no_bukti, tanggal, keterangan, tipe, baris, user):
    """Helper: buat 1 jurnal DRAFT dari daftar baris (kode_akun, debit, kredit).

    Memvalidasi keseimbangan sebelum menyentuh DB.
    """
    total_debit = sum((b[1] for b in baris), start=Decimal(0))
    total_kredit = sum((b[2] for b in baris), start=Decimal(0))
    if total_debit != total_kredit:
        raise ValueError(f"Jurnal tidak seimbang: D={total_debit} K={total_kredit}")

    jurnal = TrJurnal.objects.create(
        id=uuid.uuid4(), no_bukti=no_bukti, tanggal=tanggal,
        keterangan=keterangan, tipe_sumber=tipe, status="DRAFT", created_by=user,
    )
    for kode_akun, debit, kredit in baris:
        TrJurnalDetail.objects.create(
            jurnal=jurnal, kode_akun_id=kode_akun, debit=debit, kredit=kredit
        )
    return jurnal


def post_pencairan_kasbon(pinjaman, user=None, akun_piutang="1103", akun_kas="1101"):
    """Pencairan kasbon pegawai (Dr Piutang Karyawan, Cr Kas)."""
    if pinjaman.jurnal_id:
        raise ValueError("Pinjaman ini sudah dijurnal.")
    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
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
    """Payroll (siklus pengeluaran).

    Dr Beban Gaji (bruto)
    Cr Kas (netto), Cr Piutang Karyawan (potongan pinjaman),
    Cr Utang Asuransi (potongan asuransi)
    """
    if gaji.jurnal_id:
        raise ValueError("Gaji periode ini sudah dijurnal.")
    from datetime import date

    baris = [(akun_beban, gaji.total_bruto, Decimal(0)),
             (akun_kas, Decimal(0), gaji.total_netto)]
    if gaji.potongan_pinjaman:
        baris.append((akun_piutang, Decimal(0), gaji.potongan_pinjaman))
    if gaji.potongan_asuransi:
        baris.append((akun_utang_asuransi, Decimal(0), gaji.potongan_asuransi))

    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
                no_bukti=f"GJ-{gaji.id}-{gaji.periode_tahun}{gaji.periode_bulan:02d}",
                tanggal=date(gaji.periode_tahun, gaji.periode_bulan, 28),
                keterangan=f"Gaji {gaji.pegawai} {gaji.periode_bulan}/{gaji.periode_tahun}",
                tipe="AUTO_PAYROLL", baris=baris, user=user,
            )
            gaji.jurnal = jurnal
            gaji.save(update_fields=["jurnal", "updated_at"])
    return jurnal


def post_penyusutan(asset, user=None, tanggal=None):
    """Penyusutan periodik (Dr Beban Depresiasi, Cr Akumulasi Penyusutan)."""
    from datetime import date

    nominal = asset.penyusutan_per_bulan
    if nominal <= 0:
        raise ValueError("Nominal penyusutan nol.")
    tanggal = tanggal or date.today()
    with transaction.atomic():
        with audit_user(user):
            jurnal = _buat_jurnal(
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
