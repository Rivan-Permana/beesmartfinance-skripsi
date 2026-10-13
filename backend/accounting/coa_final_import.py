"""Import Chart of Accounts dari spreadsheet COA Final Lebah Madu."""

from __future__ import annotations

import csv
from pathlib import Path

from accounting.models import MsCoa, MsGolongan, MsSubGolongan, TrJurnalDetail


def _posisi_normal(kode: str) -> str:
    first = kode[0]
    if first in ("1", "5", "9"):
        return "D"
    if first in ("2", "3", "4"):
        return "K"
    return "D"


def _parent_golongan_kode(kode_sub: str) -> str:
    return kode_sub[0]


def _parent_sub_kode(kode_akun: str, sub_codes: set[str]) -> str | None:
    for length in range(len(kode_akun) - 1, 1, -1):
        prefix = kode_akun[:length]
        if prefix in sub_codes:
            return prefix
    return None


def import_coa_final(csv_path: Path, *, replace: bool = False) -> dict[str, int]:
    """
    Muat golongan, sub-golongan, dan akun leaf dari COA Final CSV.
    Returns counts: golongan, sub, akun, akun_total.
    """
    if replace and not TrJurnalDetail.objects.exists():
        MsCoa.objects.all().delete()
        MsSubGolongan.objects.all().delete()
        MsGolongan.objects.all().delete()
    elif replace:
        # Jurnal sudah ada — merge saja, jangan hapus akun lama.
        replace = False

    rows: list[tuple[str, str, str, str]] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i < 3:
                continue
            if not row or not row[0].strip():
                continue
            kode = row[0].strip()
            tipe = row[1].strip() if len(row) > 1 else ""
            nama = row[2].strip() if len(row) > 2 else ""
            rows.append((kode, tipe, nama, row[3].strip() if len(row) > 3 else ""))

    gol_rows: list[tuple[str, str]] = []
    sub_rows: list[tuple[str, str]] = []
    leaf_rows: list[tuple[str, str]] = []

    for kode, tipe, nama, _jenis in rows:
        if nama:
            leaf_rows.append((kode, nama))
        elif tipe:
            if len(kode) == 1:
                gol_rows.append((kode, tipe))
            else:
                sub_rows.append((kode, tipe))

    sub_codes = {k for k, _ in sub_rows}

    gol_count = 0
    for kode, nama in gol_rows:
        _, created = MsGolongan.objects.update_or_create(
            kode_golongan=kode,
            defaults={"nama_golongan": nama[:50], "deskripsi": None},
        )
        if created:
            gol_count += 1

    sub_count = 0
    for kode, nama in sub_rows:
        gol = MsGolongan.objects.filter(kode_golongan=_parent_golongan_kode(kode)).first()
        if not gol:
            continue
        _, created = MsSubGolongan.objects.update_or_create(
            kode_sub=kode,
            defaults={"golongan": gol, "nama_sub": nama[:100]},
        )
        if created:
            sub_count += 1

    akun_count = 0
    seen_kode: set[str] = set()
    for kode, nama in leaf_rows:
        if kode in seen_kode:
            continue
        seen_kode.add(kode)
        sub_kode = _parent_sub_kode(kode, sub_codes)
        sub = MsSubGolongan.objects.filter(kode_sub=sub_kode).first() if sub_kode else None
        _, created = MsCoa.objects.update_or_create(
            kode_akun=kode,
            defaults={
                "sub_golongan": sub,
                "nama_akun": nama[:255],
                "posisi_normal": _posisi_normal(kode),
                "is_active": True,
            },
        )
        if created:
            akun_count += 1

    return {
        "golongan": gol_count,
        "sub": sub_count,
        "akun": akun_count,
        "akun_total": MsCoa.objects.count(),
    }
