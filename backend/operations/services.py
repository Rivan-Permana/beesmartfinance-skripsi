"""Service layer: auto-posting siklus operasional -> core accounting.

Aturan akuntansi (balance, immutability, anggaran) tetap dijaga trigger DB;
service ini menyusun jurnal yang benar lalu menyerahkan ke core sebagai DRAFT
(menunggu approval Principal sesuai alur maker-checker).
"""

import uuid
from contextlib import contextmanager
from datetime import date

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
