"""Import anggaran legacy (realisasi anggaran sekolah CSV)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from operations.services.legacy_import.kafalah_csv import parse_idr

ANGGARAN_FILE = "realisasi anggaran sekolah.xlsx - Sheet1.csv"

# Bucket legacy → kode akun (prioritas: T_AKUN flat, lalu COA gabungan dotted).
BUCKET_COA_CANDIDATES: dict[str, list[str]] = {
    "kindergarden activities": ["51101", "5.1.1.01"],
    "playgroup activities": ["51201", "5.1.2.01", "51101"],
    "cash out": ["5102", "5.3.01"],
    "salary": ["5101", "5201", "5.2.01"],
}


@dataclass
class LegacyAnggaranRow:
    label: str
    pagu: Decimal
    realisasi: Decimal
    coa_candidates: list[str]


def parse_anggaran_csv(path: Path) -> list[LegacyAnggaranRow]:
    out: list[LegacyAnggaranRow] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            label = (row[2] or "").strip()
            if not label:
                continue
            candidates = BUCKET_COA_CANDIDATES.get(label.lower())
            if not candidates:
                continue
            pagu = parse_idr(row[3])
            realisasi = parse_idr(row[4])
            if pagu <= 0 and realisasi <= 0:
                continue
            out.append(
                LegacyAnggaranRow(
                    label=label,
                    pagu=pagu,
                    realisasi=realisasi,
                    coa_candidates=candidates,
                )
            )
    return out
