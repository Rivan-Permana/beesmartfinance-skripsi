"""Import pagu anggaran + jurnal realisasi demo dari CSV legacy (E10.8)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.db import transaction

from accounting.models import MsCoa, TrAnggaran, TrJurnal, TrJurnalDetail
from operations.services.common import akun_sistem
from operations.services.legacy_import.anggaran_csv import ANGGARAN_FILE, parse_anggaran_csv


def resolve_kode_akun(candidates: list[str]) -> str | None:
    """Ambil kode akun pertama yang ada di ms_coa."""
    for kode in candidates:
        if MsCoa.objects.filter(kode_akun=kode).exists():
            return kode
    return None


@transaction.atomic
def import_legacy_anggaran(
    *,
    legacy_dir: Path,
    tahun_anggaran: int = 2026,
    dry_run: bool = False,
) -> dict:
    path = legacy_dir / ANGGARAN_FILE
    if not path.is_file():
        raise FileNotFoundError(f"Anggaran CSV tidak ada: {path}")

    rows = parse_anggaran_csv(path)
    stats = {
        "anggaran_upserted": 0,
        "realisasi_jurnal": 0,
        "rows": len(rows),
        "skipped_no_coa": 0,
    }

    if dry_run:
        return stats

    kas = akun_sistem("KAS", "1101")
    if not MsCoa.objects.filter(kode_akun=kas).exists():
        kas = MsCoa.objects.filter(kode_akun__startswith="110").values_list(
            "kode_akun", flat=True,
        ).first()
    if not kas:
        stats["skipped_no_coa"] = len(rows)
        return stats

    tanggal = date(tahun_anggaran, 6, 30)

    for row in rows:
        kode = resolve_kode_akun(row.coa_candidates)
        if not kode:
            stats["skipped_no_coa"] += 1
            continue

        TrAnggaran.objects.update_or_create(
            kode_akun_id=kode,
            tahun_anggaran=tahun_anggaran,
            bulan=None,
            defaults={
                "nominal_anggaran": row.pagu,
                "keterangan": f"Legacy: {row.label}",
            },
        )
        stats["anggaran_upserted"] += 1

        if row.realisasi <= 0:
            continue

        no = f"LEG-ANG-{row.label.replace(' ', '')[:16].upper()}-{tahun_anggaran}"
        if TrJurnal.objects.filter(no_bukti=no, is_deleted=False).exists():
            continue

        jurnal = TrJurnal.objects.create(
            id=uuid.uuid4(),
            no_bukti=no,
            tanggal=tanggal,
            keterangan=f"Realisasi legacy {row.label} {tahun_anggaran}",
            tipe_sumber="AUTO_ANGGARAN_LEGACY",
            status="POSTED",
        )
        TrJurnalDetail.objects.create(
            jurnal=jurnal, kode_akun_id=kode, debit=row.realisasi, kredit=Decimal(0),
        )
        TrJurnalDetail.objects.create(
            jurnal=jurnal, kode_akun_id=kas, debit=Decimal(0), kredit=row.realisasi,
        )
        stats["realisasi_jurnal"] += 1

    return stats
