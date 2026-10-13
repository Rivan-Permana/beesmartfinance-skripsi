"""Parser roster siswa dari TP 2025-2026 CSV."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass
class LegacyRosterEntry:
    nama: str
    jenjang_kode: str
    spp_nominal: Decimal


def _clean_name(raw: str) -> str:
    name = raw.strip()
    name = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()
    return " ".join(name.split())


def _parse_rp(raw: str) -> Decimal | None:
    s = raw.strip().replace(",", "").replace(" ", "")
    if not s or s in ("-", "v"):
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def _rows_from_csv(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def parse_playgroup_roster(path: Path) -> list[LegacyRosterEntry]:
    """TP Playgroup.csv — semua baris dengan nomor + nama."""
    out: list[LegacyRosterEntry] = []
    seen: set[str] = set()
    for row in _rows_from_csv(path):
        if len(row) < 2:
            continue
        if not row[0].strip().isdigit():
            continue
        nama = _clean_name(row[1])
        if not nama or nama.lower() == "jumlah":
            continue
        key = nama.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(LegacyRosterEntry(nama=nama, jenjang_kode="PG", spp_nominal=Decimal("850000")))
    return out


def parse_siswa_baru_roster(path: Path) -> list[LegacyRosterEntry]:
    """TP Siswa Baru.csv — calon TK TA 2025/26."""
    out: list[LegacyRosterEntry] = []
    seen: set[str] = set()
    for i, row in enumerate(_rows_from_csv(path)):
        if len(row) < 2:
            continue
        if not row[0].strip().isdigit():
            continue
        nama = _clean_name(row[1])
        if not nama or "tahun pelajaran" in nama.lower():
            continue
        spp = _parse_rp(row[13]) if len(row) > 13 else None
        if spp is None:
            spp = Decimal("1300000")
        jenjang = "TKA" if int(row[0]) % 2 == 1 else "TKB"
        key = nama.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(LegacyRosterEntry(nama=nama, jenjang_kode=jenjang, spp_nominal=spp))
    return out


def parse_daftar_ulang_roster(path: Path) -> list[LegacyRosterEntry]:
    """TP Siswa Daftar Ulang.csv — mostly TK A roster TA 2025/26."""
    out: list[LegacyRosterEntry] = []
    seen: set[str] = set()
    for row in _rows_from_csv(path):
        if len(row) < 2:
            continue
        idx = row[0].strip()
        if not idx.isdigit():
            continue
        nama = _clean_name(row[1])
        if not nama or nama.lower() == "jumlah":
            continue
        key = nama.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(LegacyRosterEntry(
            nama=nama, jenjang_kode="TKA", spp_nominal=Decimal("1300000"),
        ))
    return out


def load_all_tp_rosters(legacy_dir: Path) -> list[LegacyRosterEntry]:
    """Gabung PG + siswa baru + daftar ulang (dedupe by nama+jenjang)."""
    files = [
        ("PG", "TP 2025-2026.xlsx - Playgroup.csv", parse_playgroup_roster),
        ("BARU", "TP 2025-2026.xlsx - Siswa Baru.csv", parse_siswa_baru_roster),
        ("ULANG", "TP 2025-2026.xlsx - Siswa Daftar Ulang.csv", parse_daftar_ulang_roster),
    ]
    merged: dict[tuple[str, str], LegacyRosterEntry] = {}
    for _label, filename, parser in files:
        path = legacy_dir / filename
        if not path.is_file():
            continue
        for entry in parser(path):
            key = (entry.jenjang_kode, entry.nama.lower())
            merged[key] = entry
    return list(merged.values())
