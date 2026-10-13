"""Parser absensi siswa legacy (matrix CSV dari spreadsheet TK)."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

MONTH_ID = {
    "JANUARI": 1,
    "FEBRUARI": 2,
    "MARET": 3,
    "APRIL": 4,
    "MEI": 5,
    "JUNI": 6,
    "JULI": 7,
    "AGUSTUS": 8,
    "SEPTEMBER": 9,
    "OKTOBER": 10,
    "NOVEMBER": 11,
    "DESEMBER": 12,
}

MONTH_HEADER = re.compile(
    r"^(JANUARI|FEBRUARI|MARET|APRIL|MEI|JUNI|JULI|AGUSTUS|SEPTEMBER|OKTOBER|NOVEMBER|DESEMBER)\s+(\d{4})\s*$",
    re.IGNORECASE,
)


@dataclass
class LegacyAttendanceDay:
    tanggal: date
    ikut_katering: bool
    catering_amount: int | None = None


@dataclass
class LegacyStudentMonth:
    nama: str
    catering_enrolled: bool
    days: list[LegacyAttendanceDay] = field(default_factory=list)


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def _parse_day_row(row: list[str]) -> int | None:
    for i, cell in enumerate(row):
        if cell.strip() == "1":
            for j in range(1, 31):
                if i + j >= len(row) or row[i + j].strip() != str(j + 1):
                    return None
            return i
    return None


def _cell_catering_value(raw: str) -> int | None:
    s = raw.strip().replace(",", "")
    if not s:
        return None
    if s.isdigit():
        v = int(s)
        if v in (10, 20):
            return v
    return None


def _parse_student_row(
    row: list[str],
    day_start: int,
    year: int,
    month: int,
) -> LegacyStudentMonth | None:
    if len(row) < 2:
        return None
    no_raw = row[0].strip()
    if not no_raw.isdigit():
        return None
    nama = row[1].strip()
    if not nama:
        return None

    flag = row[2].strip().upper() if len(row) > 2 else ""
    catering_enrolled = flag == "C"

    days: list[LegacyAttendanceDay] = []
    for day_num in range(1, 32):
        col = day_start + day_num - 1
        if col >= len(row):
            break
        amount = _cell_catering_value(row[col])
        if amount is None:
            continue
        try:
            tanggal = date(year, month, day_num)
        except ValueError:
            continue
        days.append(LegacyAttendanceDay(
            tanggal=tanggal,
            ikut_katering=True,
            catering_amount=amount,
        ))

    if not days and not catering_enrolled:
        return None
    return LegacyStudentMonth(nama=nama, catering_enrolled=catering_enrolled, days=days)


def _merge_student(existing: LegacyStudentMonth, incoming: LegacyStudentMonth) -> None:
    existing.catering_enrolled = existing.catering_enrolled or incoming.catering_enrolled
    by_date = {d.tanggal: d for d in existing.days}
    for d in incoming.days:
        by_date[d.tanggal] = d
    existing.days = sorted(by_date.values(), key=lambda x: x.tanggal)


def parse_absensi_csv(
    path: Path,
    *,
    target_bulan: int,
    target_tahun: int,
) -> list[LegacyStudentMonth]:
    """Parse satu file TK A/B; gabung semua blok siswa untuk bulan target."""
    by_name: dict[str, LegacyStudentMonth] = {}

    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    in_target = False
    day_start: int | None = None

    for row in rows:
        if row and row[0].strip():
            m = MONTH_HEADER.match(row[0].strip())
            if m:
                month_num = MONTH_ID[m.group(1).upper()]
                year_num = int(m.group(2))
                in_target = month_num == target_bulan and year_num == target_tahun
                day_start = None
                continue

        if not in_target:
            continue

        if row and row[0].strip().upper() == "NO.":
            day_start = None
            continue

        if day_start is None:
            ds = _parse_day_row(row)
            if ds is not None:
                day_start = ds
            continue

        parsed = _parse_student_row(row, day_start, target_tahun, target_bulan)
        if not parsed:
            continue
        key = _normalize_name(parsed.nama)
        if key not in by_name:
            by_name[key] = parsed
        else:
            _merge_student(by_name[key], parsed)

    return list(by_name.values())
