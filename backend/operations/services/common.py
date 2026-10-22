"""Helper bersama service layer auto-posting."""

import uuid
from decimal import Decimal

from accounting.models import TrJurnal, TrJurnalDetail
from accounting.utils import audit_user  # noqa: F401 (re-export utk service lain)


def akun_rule(komponen, event_code=None):
    """Ambil akun pendapatan (kredit) untuk komponen tagihan/registrasi."""
    from operations.services.coa_resolve import resolve_komponen_pendapatan

    return resolve_komponen_pendapatan(komponen, event_code=event_code)


def akun_sistem(key, default=None):
    """Resolve akun sistem (KAS, PIUTANG_KARYAWAN, dst) dari MsPostingRule + COA Final."""
    from operations.services.coa_resolve import resolve_system_account

    return resolve_system_account(key, legacy_default=default)


def buat_jurnal(no_bukti, tanggal, keterangan, tipe, baris, user, fiscal_period=None):
    """Buat 1 jurnal DRAFT dari daftar baris (kode_akun, debit, kredit).

    Memvalidasi keseimbangan sebelum menyentuh DB.
    """
    total_debit = sum((b[1] for b in baris), Decimal(0))
    total_kredit = sum((b[2] for b in baris), Decimal(0))
    if total_debit != total_kredit:
        raise ValueError(f"Jurnal tidak seimbang: D={total_debit} K={total_kredit}")

    from accounting.services import tolak_periode_tertutup
    from operations.services.coa_resolve import validate_jurnal_accounts

    tolak_periode_tertutup(tanggal)
    validate_jurnal_accounts([b[0] for b in baris])

    jurnal = TrJurnal.objects.create(
        id=uuid.uuid4(), no_bukti=no_bukti, tanggal=tanggal,
        keterangan=keterangan, tipe_sumber=tipe, status="DRAFT", created_by=user,
        fiscal_period=fiscal_period,
    )
    for kode_akun, debit, kredit in baris:
        TrJurnalDetail.objects.create(
            jurnal=jurnal, kode_akun_id=kode_akun, debit=debit, kredit=kredit
        )
    return jurnal
