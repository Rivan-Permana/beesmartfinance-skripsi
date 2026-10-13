"""Parser absensi jemput legacy (matrix CSV per armada / bulan)."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
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

ARMADA_HEADER = re.compile(r"^Absen Jemputan\s+(.+)$", re.IGNORECASE)


@dataclass
class LegacyJemputDay:
    tanggal: date
    jemput_datang: bool
    jemput_pulang: bool


@dataclass
class LegacyJemputStudent:
    nama: str
    tarif_per_trip: Decimal
    armada_label: str
    jenjang_label: str
    days: list[LegacyJemputDay] = field(default_factory=list)


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def _parse_tarif(raw: str) -> Decimal:
    cleaned = raw.strip().replace(",", "").replace(" ", "")
    if not cleaned:
        return Decimal(0)
    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal(0)


def _parse_jemput_day_start(row: list[str]) -> int | None:
    for i in range(3, len(row) - 1):
        if row[i].strip().upper() == "J" and row[i + 1].strip().upper() == "A":
            return i
    return None


def _trip_flag(raw: str) -> bool:
    return raw.strip() in ("1", "1.0")


def _parse_student_row(
    row: list[str],
    *,
    day_start: int,
    year: int,
    month: int,
    armada_label: str,
    jenjang_label: str,
) -> LegacyJemputStudent | None:
    if len(row) < 3:
        return None
    no_raw = row[0].strip()
    if not no_raw.isdigit():
        return None
    nama = row[1].strip()
    if not nama:
        return None

    tarif = _parse_tarif(row[2])
    days: list[LegacyJemputDay] = []
    for day_num in range(1, 32):
        j_col = day_start + 2 * (day_num - 1)
        a_col = j_col + 1
        if a_col >= len(row):
            break
        j_flag = _trip_flag(row[j_col])
        a_flag = _trip_flag(row[a_col])
        if not j_flag and not a_flag:
            continue
        try:
            tanggal = date(year, month, day_num)
        except ValueError:
            continue
        days.append(LegacyJemputDay(
            tanggal=tanggal,
            jemput_datang=j_flag,
            jemput_pulang=a_flag,
        ))

    if not days and tarif <= 0:
        return None
    return LegacyJemputStudent(
        nama=nama,
        tarif_per_trip=tarif,
        armada_label=armada_label,
        jenjang_label=jenjang_label,
        days=days,
    )


def parse_jemput_csv(
    path: Path,
    *,
    target_bulan: int,
    target_tahun: int,
) -> list[LegacyJemputStudent]:
    """Parse file jemput; gabung semua armada untuk bulan target."""
    by_key: dict[tuple[str, str], LegacyJemputStudent] = {}

    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    armada_label = path.stem
    in_target = False
    day_start: int | None = None
    jenjang_label = ""

    for row in rows:
        if row and row[0].strip():
            armada_match = ARMADA_HEADER.match(row[0].strip())
            if armada_match:
                armada_label = armada_match.group(1).strip()
                in_target = False
                day_start = None
                continue

            month_match = MONTH_HEADER.match(row[0].strip())
            if month_match:
                month_num = MONTH_ID[month_match.group(1).upper()]
                year_num = int(month_match.group(2))
                in_target = month_num == target_bulan and year_num == target_tahun
                day_start = None
                jenjang_label = ""
                continue

        if not in_target:
            continue

        label = row[0].strip().upper() if row else ""
        if label in ("KINDERGARTEN", "PLAYGROUP", "TK A", "TK B"):
            jenjang_label = label
            ds = _parse_jemput_day_start(row)
            if ds is not None:
                day_start = ds
            continue

        if row and row[0].strip().upper() == "NO.":
            continue

        if day_start is None:
            continue

        parsed = _parse_student_row(
            row,
            day_start=day_start,
            year=target_tahun,
            month=target_bulan,
            armada_label=armada_label,
            jenjang_label=jenjang_label,
        )
        if not parsed:
            continue
        key = (_normalize_name(parsed.nama), parsed.armada_label.lower())
        if key not in by_key:
            by_key[key] = parsed
        else:
            existing = by_key[key]
            if parsed.tarif_per_trip > 0:
                existing.tarif_per_trip = parsed.tarif_per_trip
            by_date = {d.tanggal: d for d in existing.days}
            for d in parsed.days:
                prev = by_date.get(d.tanggal)
                if prev:
                    prev.jemput_datang = prev.jemput_datang or d.jemput_datang
                    prev.jemput_pulang = prev.jemput_pulang or d.jemput_pulang
                else:
                    by_date[d.tanggal] = d
            existing.days = sorted(by_date.values(), key=lambda x: x.tanggal)

    return list(by_key.values())
