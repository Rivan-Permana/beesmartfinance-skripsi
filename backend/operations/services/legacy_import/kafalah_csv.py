"""Parser workbook KAFALAH legacy (Salary Table, Absen, Pinjaman)."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

KAFALAH_PREFIX = "KAFALAH APRIL '2025.xlsx - "
SALARY_FILE = f"{KAFALAH_PREFIX}Salary Table.csv"
ABSEN_FILE = f"{KAFALAH_PREFIX}Absen.csv"
PINJAMAN_FILE = f"{KAFALAH_PREFIX}Pinjaman.csv"

IDR_RE = re.compile(r"[\d.,]+")


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().strip('"').split()).lower().replace(",", "")


def parse_idr(raw: str) -> Decimal:
    s = (raw or "").strip().replace("Rp", "").replace(" ", "")
    if not s or s in ("-", "–", "`"):
        return Decimal(0)
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        m = IDR_RE.search(raw.replace(".", "").replace(",", ""))
        if not m:
            return Decimal(0)
        try:
            return Decimal(m.group(0))
        except Exception:
            return Decimal(0)


@dataclass
class KafalahSalaryRow:
    no: int
    nama: str
    skill: str
    gaji_pokok: Decimal
    tunjangan_pengabdian: Decimal
    tunjangan_jabatan: Decimal
    tunjangan_asuransi: Decimal
    bonus: Decimal
    tarif_uang_makan: Decimal
    tarif_transport: Decimal
    insentif_kehadiran: Decimal


@dataclass
class KafalahAbsenRow:
    no: int
    nama: str
    hari_hadir: int


@dataclass
class KafalahPinjamanRow:
    no: int
    nama: str
    potongan_bulan: Decimal
    sisa_balance: Decimal
    keterangan: str


def _read_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def parse_salary_table(path: Path) -> list[KafalahSalaryRow]:
    rows = _read_rows(path)
    out: list[KafalahSalaryRow] = []
    for row in rows:
        if len(row) < 12:
            continue
        no_raw = row[0].strip().strip("`")
        if not no_raw.isdigit():
            continue
        out.append(
            KafalahSalaryRow(
                no=int(no_raw),
                nama=row[1].strip().strip('"'),
                skill=row[2].strip(),
                gaji_pokok=parse_idr(row[5]),
                tunjangan_pengabdian=parse_idr(row[6]),
                tunjangan_jabatan=parse_idr(row[7]),
                tunjangan_asuransi=parse_idr(row[8]),
                bonus=parse_idr(row[9]),
                tarif_uang_makan=parse_idr(row[10]),
                tarif_transport=parse_idr(row[11]),
                insentif_kehadiran=parse_idr(row[12]) if len(row) > 12 else Decimal(0),
            )
        )
    return out


def _find_day_start(rows: list[list[str]]) -> int:
    for row in rows[:6]:
        start = _parse_pinjaman_day_start(row)
        if start is not None:
            return start
    return 4


def parse_absen(path: Path) -> list[KafalahAbsenRow]:
    rows = _read_rows(path)
    out: list[KafalahAbsenRow] = []
    for row in rows:
        if len(row) < 37:
            continue
        no_raw = row[0].strip().strip("`")
        if not no_raw.isdigit():
            continue
        total_raw = row[36].strip() if len(row) > 36 else ""
        hari = int(parse_idr(total_raw))
        out.append(
            KafalahAbsenRow(
                no=int(no_raw),
                nama=row[1].strip().strip('"'),
                hari_hadir=hari,
            )
        )
    return out


def _parse_pinjaman_day_start(row: list[str]) -> int | None:
    for i, cell in enumerate(row):
        if i < 3:
            continue
        if cell.strip() != "1":
            continue
        for j in range(1, 31):
            if i + j >= len(row) or row[i + j].strip() != str(j + 1):
                return None
        return i
    return None


def parse_pinjaman(path: Path) -> list[KafalahPinjamanRow]:
    rows = _read_rows(path)
    day_start = _find_day_start(rows)
    out: list[KafalahPinjamanRow] = []
    for row in rows:
        if len(row) < 10:
            continue
        no_raw = row[0].strip().strip("`")
        if not no_raw.isdigit():
            continue
        potongan = Decimal(0)
        for d in range(31):
            idx = day_start + d
            if idx >= len(row):
                break
            potongan += parse_idr(row[idx])
        balance = parse_idr(row[35]) if len(row) > 35 else Decimal(0)
        ket = row[36].strip() if len(row) > 36 else ""
        if balance <= 0 and potongan <= 0:
            continue
        out.append(
            KafalahPinjamanRow(
                no=int(no_raw),
                nama=row[1].strip().strip('"'),
                potongan_bulan=potongan,
                sisa_balance=balance,
                keterangan=ket,
            )
        )
    return out


def kafalah_files(legacy_dir: Path) -> dict[str, Path]:
    return {
        "salary": legacy_dir / SALARY_FILE,
        "absen": legacy_dir / ABSEN_FILE,
        "pinjaman": legacy_dir / PINJAMAN_FILE,
    }
