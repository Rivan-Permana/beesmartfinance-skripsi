"""Service core accounting: reversing entry & fiscal year closing."""

import uuid
from datetime import date
from decimal import Decimal

from django.db import connection, transaction
from django.utils import timezone

from .models import MsPeriodeAkuntansi, TrJurnal, TrJurnalDetail
from .utils import audit_user

FINANCE_POST_SOURCES = {"MANUAL", "AUTO_BILLING", "AUTO_PENDAFTARAN", "AUTO_SITIN"}


def can_finance_post(jurnal):
    return jurnal.tipe_sumber in FINANCE_POST_SOURCES and any(
        d.kode_akun_id.startswith(("4", "5")) for d in jurnal.detail.all()
    )


def post_jurnal(jurnal, user, *, approve=False):
    with transaction.atomic(), audit_user(user):
        jurnal = TrJurnal.objects.select_for_update().get(pk=jurnal.pk)
        if jurnal.is_deleted or jurnal.reversals.exists():
            raise ValueError("Jurnal yang dihapus atau dibalik tidak dapat dicatat ulang.")
        if not approve and not can_finance_post(jurnal):
            raise ValueError("Jurnal ini masih memerlukan persetujuan Kepala Sekolah.")
        if not approve and jurnal.status == "POSTED":
            return jurnal
        allowed = ("PENDING",) if approve else ("DRAFT", "PENDING")
        if jurnal.status not in allowed:
            raise ValueError("Status jurnal tidak dapat dicatat ke buku besar.")
        if approve and jurnal.created_by_id == user.pk:
            raise ValueError("Approver tidak boleh sama dengan pembuat (SoD).")
        if jurnal.tipe_sumber == "AUTO_BILLING":
            from operations.models import PembayaranTagihan
            pembayaran = PembayaranTagihan.objects.select_related("tagihan").filter(jurnal=jurnal).first()
            if not pembayaran or pembayaran.dibatalkan or pembayaran.tagihan.perlu_rekonsiliasi:
                raise ValueError("Pembayaran tagihan perlu direkonsiliasi sebelum dicatat.")
        detail = list(jurnal.detail.select_related("kode_akun"))
        if not detail or any(
            not d.kode_akun.is_active or d.debit < 0 or d.kredit < 0
            or (d.debit > 0 and d.kredit > 0) for d in detail
        ):
            raise ValueError("Periksa akun aktif dan nilai debit/kredit jurnal.")
        debit = sum((d.debit for d in detail), Decimal(0))
        if debit <= 0 or debit != sum((d.kredit for d in detail), Decimal(0)):
            raise ValueError("Jurnal harus seimbang dan lebih dari nol.")
        jurnal.status = "POSTED"
        jurnal.posted_at = timezone.now()
        fields = ["status", "posted_at"]
        if approve:
            jurnal.approved_by = user
            jurnal.approved_at = timezone.now()
            fields += ["approved_by", "approved_at"]
        else:
            jurnal.submitted_by = user
            fields.append("submitted_by")
        jurnal.save(update_fields=fields)
        return jurnal


def post_reversal(jurnal, user=None):
    """Buat jurnal pembalik (debit/kredit ditukar) atas jurnal POSTED.

    Jurnal asli tetap utuh (immutable); pembalik ini me-net-kan saldonya
    dan menyimpan tautan reversal_of -> asli. Sesuai prinsip auditability:
    koreksi via reversing entry, bukan hapus.
    """
    with transaction.atomic():
        with audit_user(user):
            jurnal = TrJurnal.objects.select_for_update().get(pk=jurnal.pk)
            if jurnal.status != "POSTED":
                raise ValueError("Hanya jurnal POSTED yang bisa dibalik.")
            if jurnal.reversals.exists():
                raise ValueError("Jurnal ini sudah pernah dibalik.")
            detail = list(jurnal.detail.all())
            pembalik = TrJurnal.objects.create(
                id=uuid.uuid4(),
                no_bukti=f"REV-{jurnal.no_bukti}",
                tanggal=date.today(),
                keterangan=f"Pembalik atas {jurnal.no_bukti}",
                tipe_sumber="REVERSAL",
                status="DRAFT",
                approved_by=user,
                reversal_of=jurnal,
            )
            for d in detail:
                TrJurnalDetail.objects.create(
                    jurnal=pembalik, kode_akun=d.kode_akun,
                    debit=d.kredit, kredit=d.debit,  # ditukar
                )
            pembalik.status = "POSTED"
            pembalik.posted_at = timezone.now()
            pembalik.save(update_fields=["status", "posted_at"])
            from operations.services.billing import batalkan_pembayaran_jurnal
            batalkan_pembayaran_jurnal(jurnal, user, f"Pembalik {pembalik.no_bukti}")
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
