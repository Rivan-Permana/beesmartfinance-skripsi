"""Validasi hitung sistem vs CSV legacy (E10.11)."""

from __future__ import annotations

import csv
import re
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from operations.services.legacy_export import katering_total_system
from operations.services.legacy_import.importer import legacy_data_dir
from operations.services.legacy_import.kafalah_csv import parse_idr

LAPORAN_KATERING = "Absen siswa (3).xlsx - laporan katering.csv"
MONTH_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
HEADER_RE = re.compile(r"^([A-Za-z]+)-(\d{4})$")


def _legacy_katering_total(path: Path) -> tuple[int, int, Decimal] | None:
    """Return (bulan, tahun, total_nominal) dari header sheet legacy."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        return None
    m = HEADER_RE.match((rows[1][0] or "").strip())
    if not m:
        return None
    month_name, year_s = m.group(1), m.group(2)
    try:
        bulan = MONTH_EN.index(month_name) + 1
        tahun = int(year_s)
    except (ValueError, IndexError):
        return None
    total = Decimal(0)
    for row in rows[4:]:
        if len(row) < 7:
            continue
        for col in (2, 6):
            if col < len(row):
                total += parse_idr(row[col])
    return bulan, tahun, total


class Command(BaseCommand):
    help = "Bandingkan total rekap katering sistem vs laporan katering.csv legacy."

    def add_arguments(self, parser):
        parser.add_argument("--month", default="", help="YYYY-MM (optional — default dari CSV legacy).")
        parser.add_argument(
            "--toleransi",
            type=int,
            default=0,
            help="Selisih nominal maksimum yang dianggap OK (Rp).",
        )
        parser.add_argument("--report", action="store_true", help="Tampilkan detail per banding.")
        parser.add_argument(
            "--legacy-dir",
            default="",
            help="Folder legacy-data (default: <repo>/legacy-data).",
        )

    def handle(self, *args, **options):
        leg_dir = legacy_data_dir()
        if options["legacy_dir"]:
            leg_dir = Path(options["legacy_dir"])
        csv_path = leg_dir / LAPORAN_KATERING
        if not csv_path.is_file():
            self.stderr.write(self.style.ERROR(f"File tidak ada: {csv_path}"))
            return

        parsed = _legacy_katering_total(csv_path)
        if not parsed:
            self.stderr.write(self.style.ERROR("Header periode laporan katering tidak dikenali."))
            return
        bulan, tahun, legacy_total = parsed

        if options["month"]:
            try:
                y, m = options["month"].split("-")
                tahun, bulan = int(y), int(m)
            except ValueError:
                self.stderr.write(self.style.ERROR("--month harus YYYY-MM"))
                return

        system_total = katering_total_system(bulan, tahun)
        delta = abs(system_total - legacy_total)
        tol = options["toleransi"]
        ok = delta <= tol

        if options["report"]:
            self.stdout.write(f"Periode       : {bulan}/{tahun}")
            self.stdout.write(f"Legacy CSV    : Rp {legacy_total:,.0f}".replace(",", "."))
            self.stdout.write(f"Sistem (DB)   : Rp {system_total:,.0f}".replace(",", "."))
            self.stdout.write(f"Selisih       : Rp {delta:,.0f}".replace(",", "."))
            self.stdout.write(f"Toleransi     : Rp {tol:,.0f}".replace(",", "."))

        if ok:
            self.stdout.write(self.style.SUCCESS(
                f"validate_legacy OK — selisih Rp {delta:,.0f} ≤ toleransi".replace(",", "."),
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"validate_legacy GAGAL — selisih Rp {delta:,.0f} > toleransi Rp {tol:,.0f}".replace(",", "."),
            ))
            self.stdout.write(
                "Catatan: DB demo (Jul 2025–Jun 2026) ≠ Jul 2024 di CSV — "
                "bandingkan bulan yang sama setelah seed periode tersebut.",
            )
