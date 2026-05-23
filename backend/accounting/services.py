"""Service core accounting: reversing entry & fiscal year closing."""

import uuid
from datetime import date
from decimal import Decimal

from django.db import connection, transaction

from .models import MsPeriodeAkuntansi, TrJurnal, TrJurnalDetail
from .utils import audit_user


def post_reversal(jurnal, user=None):
    """Buat jurnal pembalik (debit/kredit ditukar) atas jurnal POSTED.

    Jurnal asli tetap utuh (immutable); pembalik ini me-net-kan saldonya
    dan menyimpan tautan reversal_of -> asli. Sesuai prinsip auditability:
    koreksi via reversing entry, bukan hapus.
    """
    if jurnal.status != "POSTED":
        raise ValueError("Hanya jurnal POSTED yang bisa dibalik.")
    if jurnal.reversals.exists():
        raise ValueError("Jurnal ini sudah pernah dibalik.")

    detail = list(jurnal.detail.all())
    with transaction.atomic():
        with audit_user(user):
            pembalik = TrJurnal.objects.create(
                id=uuid.uuid4(),
                no_bukti=f"REV-{jurnal.no_bukti}",
                tanggal=date.today(),
                keterangan=f"Pembalik atas {jurnal.no_bukti}",
                tipe_sumber="REVERSAL",
                status="POSTED",
                approved_by=user,
                reversal_of=jurnal,
            )
            for d in detail:
                TrJurnalDetail.objects.create(
                    jurnal=pembalik, kode_akun=d.kode_akun,
                    debit=d.kredit, kredit=d.debit,  # ditukar
                )
    return pembalik


def close_period(periode, user=None, akun_ekuitas="3102"):
    """Tutup buku: nolkan akun nominal (Pendapatan 4.x & Beban 5.x) ke ekuitas.

    Surplus -> kredit ekuitas (laba ditahan); defisit -> debit ekuitas.
    """
    if periode.status == "CLOSED":
        raise ValueError("Periode sudah CLOSED.")

    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT d.kode_akun,
                   substring(c.kode_akun FROM 1 FOR 1) AS gol,
                   COALESCE(SUM(d.debit), 0)  AS deb,
                   COALESCE(SUM(d.kredit), 0) AS kre
            FROM tr_jurnal_detail d
            JOIN tr_jurnal j ON j.id = d.jurnal_id
            JOIN ms_coa c ON c.kode_akun = d.kode_akun
            WHERE j.status = 'POSTED' AND NOT j.is_deleted
              AND j.tanggal BETWEEN %s AND %s
              AND substring(c.kode_akun FROM 1 FOR 1) IN ('4', '5')
            GROUP BY d.kode_akun, gol
            """,
            [periode.tgl_mulai, periode.tgl_selesai],
        )
        rows = cur.fetchall()

    baris = []
    total_pendapatan = Decimal(0)
    total_beban = Decimal(0)
    for kode, gol, deb, kre in rows:
        deb, kre = Decimal(deb), Decimal(kre)
        if gol == "4":                       # pendapatan (saldo normal K)
            bal = kre - deb
            if bal != 0:
                baris.append((kode, bal, Decimal(0)))   # debit utk menutup
                total_pendapatan += bal
        else:                                # beban (saldo normal D)
            bal = deb - kre
            if bal != 0:
                baris.append((kode, Decimal(0), bal))   # kredit utk menutup
                total_beban += bal

    surplus = total_pendapatan - total_beban
    if surplus > 0:
        baris.append((akun_ekuitas, Decimal(0), surplus))
    elif surplus < 0:
        baris.append((akun_ekuitas, -surplus, Decimal(0)))

    if not baris:
        raise ValueError("Tidak ada akun nominal untuk ditutup.")

    with transaction.atomic():
        with audit_user(user):
            jurnal = TrJurnal.objects.create(
                id=uuid.uuid4(),
                no_bukti=f"CLOSE-{periode.kode.replace('/', '-')}",
                tanggal=periode.tgl_selesai,
                keterangan=f"Jurnal penutup periode {periode.kode}",
                tipe_sumber="CLOSING",
                status="POSTED",
                approved_by=user,
            )
            for kode, debit, kredit in baris:
                TrJurnalDetail.objects.create(
                    jurnal=jurnal, kode_akun_id=kode, debit=debit, kredit=kredit
                )
            MsPeriodeAkuntansi.objects.filter(pk=periode.pk).update(status="CLOSED")
    return jurnal
