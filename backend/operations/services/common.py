"""Helper bersama service layer auto-posting."""

import uuid
from decimal import Decimal

from accounting.models import TrJurnal, TrJurnalDetail
from accounting.utils import audit_user  # noqa: F401 (re-export utk service lain)


def akun_rule(komponen):
    """Ambil akun (kredit) untuk sebuah komponen dari MsPostingRule."""
    from operations.models import MsPostingRule

    rule = MsPostingRule.objects.filter(komponen=komponen, aktif=True).first()
    if not rule:
        raise ValueError(f"MsPostingRule untuk komponen {komponen} belum diset.")
    return rule.akun_kredit_id


def akun_sistem(key, default):
    """Resolve akun sistem (KAS, PIUTANG_KARYAWAN, dst) dari MsPostingRule.

    Bila belum dikonfigurasi, pakai `default`. Ini menghapus kebutuhan meng-edit
    kode saat bagan akun berubah: cukup set MsPostingRule(komponen=key).
    """
    from operations.models import MsPostingRule

    rule = MsPostingRule.objects.filter(komponen=key, aktif=True).first()
    return rule.akun_kredit_id if rule else default


def buat_jurnal(no_bukti, tanggal, keterangan, tipe, baris, user):
    """Buat 1 jurnal DRAFT dari daftar baris (kode_akun, debit, kredit).

    Memvalidasi keseimbangan sebelum menyentuh DB.
    """
    total_debit = sum((b[1] for b in baris), Decimal(0))
    total_kredit = sum((b[2] for b in baris), Decimal(0))
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
