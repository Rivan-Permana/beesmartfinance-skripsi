"""Export rekap katering/jemput — layout mirror spreadsheet legacy (E10.9)."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

from operations.models import KehadiranSiswa, PendaftaranJemputan, Siswa
from operations.services.katering_tarif import katering_breakdown_for_siswa

MONTH_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _fmt_nominal(amount: Decimal | int) -> str:
    n = int(Decimal(amount))
    return f"  {n:,} "


def _katering_rows_for_jenjang(bulan: int, tahun: int, jenjang_kode: str) -> list[tuple[str, Decimal]]:
    rows: list[tuple[str, Decimal]] = []
    qs = (
        Siswa.objects.filter(status="aktif", is_deleted=False, kelompok__jenjang__kode=jenjang_kode)
        .select_related("kelompok__jenjang")
        .order_by("nama")
    )
    for siswa in qs:
        total, _, _, h_all, _ = katering_breakdown_for_siswa(siswa, bulan, tahun)
        if h_all <= 0 or total <= 0:
            continue
        rows.append((siswa.nama, total))
    return rows


def export_laporan_katering_legacy(bulan: int, tahun: int) -> str:
    """CSV dua kolom (TK A | TK B) seperti `laporan katering.csv`."""
    tka = _katering_rows_for_jenjang(bulan, tahun, "TKA")
    tkb = _katering_rows_for_jenjang(bulan, tahun, "TKB")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["LAPORAN CATERING TK LEBAH MADU", "", "", "", "", "", ""])
    w.writerow([f"{MONTH_EN[bulan - 1]}-{tahun}", "", "", "", "", "", ""])
    w.writerow([])
    w.writerow(["No.", "Nama", " Nominal", "", "No.", "Nama", " Nominal"])
    n = max(len(tka), len(tkb))
    for i in range(n):
        left = tka[i] if i < len(tka) else None
        right = tkb[i] if i < len(tkb) else None
        row = [
            i + 1 if left else "",
            left[0] if left else "",
            _fmt_nominal(left[1]) if left else "",
            "",
            i + 1 if right else "",
            right[0] if right else "",
            _fmt_nominal(right[1]) if right else "",
        ]
        w.writerow(row)
    return buf.getvalue()


def _jemput_rows(bulan: int, tahun: int) -> list[tuple[str, Decimal, int, int, int, Decimal]]:
    """Return (nama, tarif, datang, pulang, trips, nominal)."""
    pend = PendaftaranJemputan.objects.filter(is_deleted=False).select_related("siswa", "armada")
    by_siswa: dict[int, dict] = {}
    for p in pend:
        sid = p.siswa_id
        if sid not in by_siswa:
            by_siswa[sid] = {"siswa": p.siswa, "tarif": Decimal(0)}
        by_siswa[sid]["tarif"] = max(by_siswa[sid]["tarif"], p.harga or Decimal(0))

    out: list[tuple[str, Decimal, Decimal, int, int, Decimal]] = []
    for sid, meta in by_siswa.items():
        qs = KehadiranSiswa.objects.filter(
            siswa_id=sid,
            tanggal__year=tahun,
            tanggal__month=bulan,
        )
        datang = qs.filter(jemput_datang=True).count()
        pulang = qs.filter(jemput_pulang=True).count()
        trips = datang + pulang
        if trips <= 0:
            continue
        tarif = meta["tarif"]
        out.append((meta["siswa"].nama, tarif, datang, pulang, trips, tarif * trips))
    out.sort(key=lambda r: r[0].lower())
    return out


def export_laporan_jemput_legacy(bulan: int, tahun: int) -> str:
    """CSV ringkas jemput: tarif × trip (mirror kolom akhir sheet legacy)."""
    rows = _jemput_rows(bulan, tahun)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([f"LAPORAN JEMPUTAN TK LEBAH MADU — {MONTH_EN[bulan - 1]} {tahun}"])
    w.writerow([])
    w.writerow(["No.", "Nama", " Tarif", "Datang", "Pulang", "Trip", " Nominal"])
    for i, (nama, tarif, datang, pulang, trips, nominal) in enumerate(rows, start=1):
        w.writerow([
            i, nama, _fmt_nominal(tarif), datang, pulang, trips, _fmt_nominal(nominal),
        ])
    return buf.getvalue()


def katering_total_system(bulan: int, tahun: int) -> Decimal:
    total = Decimal(0)
    for kode in ("TKA", "TKB"):
        for _, nominal in _katering_rows_for_jenjang(bulan, tahun, kode):
            total += nominal
    return total
