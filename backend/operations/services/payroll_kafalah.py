"""Seed payroll KAFALAH April 2025 + auto potong pinjaman (E10.6 / E10.7)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.db import transaction

from accounting.models import TrJurnal, TrJurnalDetail
from operations.models import GajiPegawai, Pegawai, PinjamanPegawai
from operations.services.legacy_import.kafalah_csv import (
    _normalize_name,
    kafalah_files,
    parse_absen,
    parse_pinjaman,
    parse_salary_table,
)
from operations.services.payroll import apply_potongan_pinjaman, settle_pinjaman_from_gaji


def _nip_kafalah(no: int) -> str:
    return f"KAF-{no:03d}"


@transaction.atomic
def import_kafalah_payroll(
    *,
    legacy_dir: Path,
    periode_bulan: int = 4,
    periode_tahun: int = 2025,
    dry_run: bool = False,
) -> dict:
    files = kafalah_files(legacy_dir)
    for key, path in files.items():
        if not path.is_file():
            raise FileNotFoundError(f"KAFALAH {key} tidak ada: {path}")

    salary_rows = parse_salary_table(files["salary"])
    absen_map = {_normalize_name(r.nama): r for r in parse_absen(files["absen"])}
    pinjaman_rows = parse_pinjaman(files["pinjaman"])
    pinjaman_map = {_normalize_name(r.nama): r for r in pinjaman_rows}

    stats = {
        "pegawai_upserted": 0,
        "pinjaman_upserted": 0,
        "gaji_upserted": 0,
        "pegawai_count": len(salary_rows),
    }

    if dry_run:
        return stats

    for srow in salary_rows:
        norm = _normalize_name(srow.nama)
        absen = absen_map.get(norm)
        hari = absen.hari_hadir if absen else 0

        pegawai, _ = Pegawai.objects.update_or_create(
            nip=_nip_kafalah(srow.no),
            defaults={
                "nama": srow.nama,
                "jabatan": srow.skill,
                "status_aktif": True,
                "tarif_uang_makan_hari": srow.tarif_uang_makan,
                "tarif_transport_hari": srow.tarif_transport,
            },
        )
        stats["pegawai_upserted"] += 1

        prow = pinjaman_map.get(norm)
        if prow and (prow.sisa_balance > 0 or prow.potongan_bulan > 0):
            jumlah = prow.sisa_balance + prow.potongan_bulan
            angsuran = prow.potongan_bulan if prow.potongan_bulan > 0 else prow.sisa_balance
            PinjamanPegawai.objects.update_or_create(
                pegawai=pegawai,
                tanggal_pinjaman=date(periode_tahun, periode_bulan, 1),
                defaults={
                    "jumlah_pinjaman": jumlah,
                    "tenor_bulan": max(1, int((jumlah / angsuran).to_integral_value()) if angsuran else 1),
                    "angsuran_per_bulan": angsuran,
                    "sudah_terbayar": max(jumlah - prow.sisa_balance, Decimal(0)),
                    "is_legacy": True,
                },
            )
            stats["pinjaman_upserted"] += 1

        uang_makan = srow.tarif_uang_makan * hari
        transport = srow.tarif_transport * hari
        potong_asuransi = srow.tunjangan_asuransi if srow.tunjangan_asuransi > 0 else Decimal(0)

        gaji, _ = GajiPegawai.objects.update_or_create(
            pegawai=pegawai,
            periode_bulan=periode_bulan,
            periode_tahun=periode_tahun,
            defaults={
                "gaji_pokok": srow.gaji_pokok,
                "tunjangan_jabatan": srow.tunjangan_jabatan,
                "tunjangan_pengabdian": srow.tunjangan_pengabdian,
                "tunjangan_asuransi": srow.tunjangan_asuransi,
                "bonus_insentif": srow.bonus,
                "uang_makan": uang_makan,
                "transport": transport,
                "thr": srow.insentif_kehadiran,
                "hari_hadir": hari,
                "potongan_asuransi": potong_asuransi,
                "potongan_pinjaman": Decimal(0),
            },
        )
        apply_potongan_pinjaman(gaji, save=True)
        stats["gaji_upserted"] += 1

    return stats
