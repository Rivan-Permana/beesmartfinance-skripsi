"""Import roster & absensi dari legacy-data CSV."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

from django.db import transaction

from operations.models import ArmadaJemputan, Jenjang, KehadiranSiswa, Kelompok, PendaftaranJemputan, Siswa
from operations.services.legacy_import.absensi_csv import parse_absensi_csv
from operations.services.legacy_import.jemput_csv import parse_jemput_csv
from operations.services.legacy_import.tp_roster import load_all_tp_rosters

DEFAULT_SPP_RA = Decimal("1300000")

LEGACY_ABSENSI_FILES = {
    "TKA": "Absen siswa (3).xlsx - TK A.csv",
    "TKB": "Absen siswa (3).xlsx - TK B.csv",
}

# Map blok CSV legacy → bulan demo (TP 2025/26).
# Sep/Nov/Feb di CSV asli kosong → mirror bulan tetangga yang punya data.
DEMO_ABSENSI_SCHEDULE: list[tuple[int, int, int, int]] = [
    (2024, 7, 2025, 7),
    (2024, 8, 2025, 8),
    (2024, 8, 2025, 9),
    (2024, 10, 2025, 10),
    (2024, 10, 2025, 11),
    (2024, 12, 2025, 12),
    (2025, 1, 2026, 1),
    *[(2024, 8, 2026, m) for m in range(2, 7)],
    (2024, 7, 2026, 7),
]


def demo_target_months() -> list[tuple[int, int]]:
    """Bulan unik yang ditulis ke DB (urutan kronologis)."""
    seen: list[tuple[int, int]] = []
    for _, _, ty, tm in DEMO_ABSENSI_SCHEDULE:
        pair = (ty, tm)
        if pair not in seen:
            seen.append(pair)
    return seen


# Backward compat untuk kode yang expect list (tahun, bulan) target saja
DEMO_ABSENSI_MONTHS: list[tuple[int, int]] = demo_target_months()

JEMPUT_FILE_PREFIX = "Absen Jemputan 2023-2024 (version 1) (2).xlsx - "
JEMPUT_SOURCE_FILES: dict[tuple[int, int], str] = {
    (2023, 7): "Juli 23.csv",
    (2023, 8): "Agustus 23.csv",
    (2023, 9): "September 23.csv",
    (2023, 10): "Oktober 23.csv",
    (2023, 11): "November 23.csv",
    (2023, 12): "Desember 23.csv",
    (2024, 1): "Januari 24.csv",
    (2024, 2): "Februari 24.csv",
    (2024, 3): "Maret 24.csv",
    (2024, 4): " April 24.csv",
    (2024, 5): "Mei 24.csv",
    (2024, 6): "Juni 24.csv",
}

DEMO_JEMPUT_SCHEDULE: list[tuple[int, int, int, int]] = [
    *[(2023, m, 2025, m) for m in range(7, 13)],
    *[(2024, m, 2026, m) for m in range(1, 7)],
]

KELOMPOK_BY_JENJANG = {
    "PG": "PG Merah",
    "TKA": "TKA Melati",
    "TKB": "TKB Mawar",
}

JENJANG_META = {
    "PG": ("PG", "Playgroup"),
    "TKA": ("TKA", "TK A"),
    "TKB": ("TKB", "TK B"),
}


def legacy_data_dir(base: Path | None = None) -> Path:
    from django.conf import settings
    root = Path(settings.BASE_DIR).parent
    return base or (root / "legacy-data")


def _legacy_nis(jenjang_kode: str, nama: str) -> str:
    digest = hashlib.sha1(_normalize_key(nama).encode()).hexdigest()[:8].upper()
    return f"LEG-{jenjang_kode}-{digest}"


def _normalize_key(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def _empty_stats() -> dict:
    return {
        "siswa_created": 0,
        "siswa_updated": 0,
        "kehadiran_upserted": 0,
        "skipped_no_days": 0,
        "roster_only": 0,
        "jemput_matched": 0,
        "jemput_skipped": 0,
        "pendaftaran_jemput": 0,
        "files": [],
        "months": [],
    }


def _merge_stats(total: dict, part: dict) -> None:
    for key in (
        "siswa_created", "siswa_updated", "kehadiran_upserted", "skipped_no_days",
        "roster_only", "jemput_matched", "jemput_skipped", "pendaftaran_jemput",
    ):
        total[key] += part.get(key, 0)
    for f in part.get("files", []):
        if f not in total["files"]:
            total["files"].append(f)
    for m in part.get("months", []):
        if m not in total["months"]:
            total["months"].append(m)


def _ensure_jenjang_kelompok() -> dict[str, Kelompok]:
    kelompok_map: dict[str, Kelompok] = {}
    for kode, (j_kode, j_nama) in JENJANG_META.items():
        j, _ = Jenjang.objects.get_or_create(kode=j_kode, defaults={"nama": j_nama})
        k_nama = KELOMPOK_BY_JENJANG[kode]
        k, _ = Kelompok.objects.get_or_create(jenjang=j, nama=k_nama)
        kelompok_map[kode] = k
    return kelompok_map


def _upsert_siswa(
    *,
    jenjang_kode: str,
    nama: str,
    spp: Decimal,
    kelompok_map: dict[str, Kelompok],
    dry_run: bool,
    stats: dict,
    tipe_tp: str = "baru",
) -> Siswa | None:
    nis = _legacy_nis(jenjang_kode, nama)
    kel = kelompok_map.get(jenjang_kode)
    if dry_run:
        stats["siswa_created"] += 1
        return None
    siswa, created = Siswa.objects.update_or_create(
        nis=nis,
        defaults={
            "nama": nama.strip(),
            "kelompok": kel,
            "spp_nominal": spp,
            "status": "aktif",
            "nama_ibu": "—",
            "tipe_tp": tipe_tp,
        },
    )
    if created:
        stats["siswa_created"] += 1
    else:
        stats["siswa_updated"] += 1
        siswa.nama = nama.strip()
        siswa.kelompok = kel
        siswa.spp_nominal = spp
        siswa.tipe_tp = tipe_tp
        siswa.save(update_fields=["nama", "kelompok", "spp_nominal", "tipe_tp", "updated_at"])
    return siswa


def _jenjang_kode_from_label(label: str) -> str | None:
    u = label.upper()
    if u == "PLAYGROUP":
        return "PG"
    if u in ("KINDERGARTEN", "TK A"):
        return "TKA"
    if u == "TK B":
        return "TKB"
    return None


def _find_siswa_for_jemput(nama: str, jenjang_label: str) -> Siswa | None:
    token = nama.strip().split()[0].lower()
    if not token:
        return None
    kode = _jenjang_kode_from_label(jenjang_label)
    qs = Siswa.objects.filter(status="aktif", nama__icontains=token)
    if kode:
        qs = qs.filter(kelompok__jenjang__kode=kode)
    matches = list(qs[:5])
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        exact = [s for s in matches if s.nama.lower().split()[0] == token]
        if len(exact) == 1:
            return exact[0]
    return None


def _ensure_armada(label: str, dry_run: bool) -> ArmadaJemputan | None:
    if dry_run:
        return None
    armada, _ = ArmadaJemputan.objects.get_or_create(
        nama_supir=label[:100],
        defaults={"jenis_mobil": "Legacy", "kapasitas": 7, "keterangan": "Import legacy"},
    )
    return armada


def import_jemput_month(
    *,
    bulan: int,
    tahun: int,
    legacy_dir: Path,
    source_bulan: int,
    source_tahun: int,
    dry_run: bool = False,
    stats: dict | None = None,
) -> dict:
    """Import absensi jemput per-trip + pendaftaran tarif."""
    from datetime import date

    stats = stats or _empty_stats()
    fname = JEMPUT_SOURCE_FILES.get((source_tahun, source_bulan))
    if not fname:
        return stats
    path = legacy_dir / f"{JEMPUT_FILE_PREFIX}{fname}"
    if not path.is_file():
        return stats

    label = f"Jemput {tahun}-{bulan:02d}"
    if label not in stats["files"]:
        stats["files"].append(label)

    rows = parse_jemput_csv(path, target_bulan=source_bulan, target_tahun=source_tahun)
    for legacy in rows:
        if dry_run:
            if legacy.days:
                stats["jemput_matched"] += 1
                stats["kehadiran_upserted"] += len(legacy.days)
            continue

        siswa = _find_siswa_for_jemput(legacy.nama, legacy.jenjang_label)
        if not siswa:
            stats["jemput_skipped"] += 1
            continue

        stats["jemput_matched"] += 1
        armada = _ensure_armada(legacy.armada_label, dry_run=False)
        if armada and legacy.tarif_per_trip > 0:
            _, created = PendaftaranJemputan.objects.update_or_create(
                siswa=siswa,
                armada=armada,
                defaults={"harga": legacy.tarif_per_trip},
            )
            if created:
                stats["pendaftaran_jemput"] += 1

        for day in legacy.days:
            try:
                tanggal = date(tahun, bulan, day.tanggal.day)
            except ValueError:
                continue
            rec, created = KehadiranSiswa.objects.get_or_create(
                siswa=siswa,
                tanggal=tanggal,
                defaults={
                    "status": "hadir",
                    "ikut_katering": False,
                    "jemput_datang": day.jemput_datang,
                    "jemput_pulang": day.jemput_pulang,
                },
            )
            if not created:
                rec.jemput_datang = rec.jemput_datang or day.jemput_datang
                rec.jemput_pulang = rec.jemput_pulang or day.jemput_pulang
                rec.save(update_fields=["jemput_datang", "jemput_pulang"])
            stats["kehadiran_upserted"] += 1

    return stats


def import_tp_rosters(
    *,
    legacy_dir: Path,
    dry_run: bool = False,
    kelompok_map: dict[str, Kelompok] | None = None,
    stats: dict | None = None,
) -> dict:
    """Import roster TP 2025/26 (PG + siswa baru + daftar ulang) — tanpa absensi."""
    stats = stats or _empty_stats()
    kelompok_map = kelompok_map or _ensure_jenjang_kelompok()
    entries = load_all_tp_rosters(legacy_dir)
    stats["files"].append("TP 2025-2026 (roster)")
    stats["roster_only"] = len(entries)

    tipe_by_source = [
        ("TP 2025-2026.xlsx - Playgroup.csv", "baru"),
        ("TP 2025-2026.xlsx - Siswa Baru.csv", "baru"),
        ("TP 2025-2026.xlsx - Siswa Daftar Ulang.csv", "lama"),
    ]
    from operations.services.legacy_import.tp_roster import (
        parse_daftar_ulang_roster,
        parse_playgroup_roster,
        parse_siswa_baru_roster,
    )
    parsers = {
        "TP 2025-2026.xlsx - Playgroup.csv": parse_playgroup_roster,
        "TP 2025-2026.xlsx - Siswa Baru.csv": parse_siswa_baru_roster,
        "TP 2025-2026.xlsx - Siswa Daftar Ulang.csv": parse_daftar_ulang_roster,
    }
    for filename, tipe in tipe_by_source:
        path = legacy_dir / filename
        if not path.is_file():
            continue
        for entry in parsers[filename](path):
            _upsert_siswa(
                jenjang_kode=entry.jenjang_kode,
                nama=entry.nama,
                spp=entry.spp_nominal,
                kelompok_map=kelompok_map,
                dry_run=dry_run,
                stats=stats,
                tipe_tp=tipe,
            )

    return stats


def import_legacy_month(
    *,
    bulan: int,
    tahun: int,
    legacy_dir: Path,
    dry_run: bool = False,
    replace_demo: bool = False,
    source_bulan: int | None = None,
    source_tahun: int | None = None,
    kelompok_map: dict[str, Kelompok] | None = None,
    stats: dict | None = None,
    stdout=None,
) -> dict:
    """Import absensi katering TK A/B untuk satu bulan target (baca blok CSV source)."""
    from datetime import date

    stats = stats or _empty_stats()
    kelompok_map = kelompok_map or _ensure_jenjang_kelompok()
    stats["months"].append(f"{tahun}-{bulan:02d}")

    parse_bulan = source_bulan if source_bulan is not None else bulan
    parse_tahun = source_tahun if source_tahun is not None else tahun

    if replace_demo and not dry_run:
        deleted = Siswa.objects.filter(nis__startswith="LM-").delete()
        removed = deleted[0] if isinstance(deleted, tuple) else deleted
        if stdout and removed:
            stdout.write(f"  hapus {removed} siswa demo (LM-*)")

    for j_kode, filename in LEGACY_ABSENSI_FILES.items():
        path = legacy_dir / filename
        if not path.is_file():
            if stdout:
                stdout.write(f"  skip: {filename} tidak ditemukan")
            continue

        students = parse_absensi_csv(
            path,
            target_bulan=parse_bulan,
            target_tahun=parse_tahun,
        )
        if filename not in stats["files"]:
            stats["files"].append(filename)

        for legacy in students:
            if not legacy.days:
                stats["skipped_no_days"] += 1
                continue

            siswa = _upsert_siswa(
                jenjang_kode=j_kode,
                nama=legacy.nama,
                spp=DEFAULT_SPP_RA,
                kelompok_map=kelompok_map,
                dry_run=dry_run,
                stats=stats,
            )

            if dry_run:
                stats["kehadiran_upserted"] += len(legacy.days)
                continue

            assert siswa is not None
            for day in legacy.days:
                try:
                    tanggal = date(tahun, bulan, day.tanggal.day)
                except ValueError:
                    continue
                rec, created = KehadiranSiswa.objects.get_or_create(
                    siswa=siswa,
                    tanggal=tanggal,
                    defaults={
                        "status": "hadir",
                        "ikut_katering": day.ikut_katering,
                        "jemput_datang": False,
                        "jemput_pulang": False,
                    },
                )
                if not created and day.ikut_katering and not rec.ikut_katering:
                    rec.ikut_katering = True
                    rec.save(update_fields=["ikut_katering"])
                elif created:
                    pass
                stats["kehadiran_upserted"] += 1

    return stats


@transaction.atomic
def import_legacy_demo_full(
    *,
    legacy_dir: Path,
    dry_run: bool = False,
    replace_demo: bool = True,
    absensi_months: list[tuple[int, int]] | None = None,
    stdout=None,
) -> dict:
    """
    Paket demo: roster TP 2025/26 (PG+TK) + absensi multi-bulan (Jul 2025–Jun 2026).
    """
    stats = _empty_stats()
    kelompok_map = _ensure_jenjang_kelompok()
    if absensi_months:
        targets = set(absensi_months)
        schedule = [
            (sy, sm, ty, tm)
            for sy, sm, ty, tm in DEMO_ABSENSI_SCHEDULE
            if (ty, tm) in targets
        ]
    else:
        schedule = DEMO_ABSENSI_SCHEDULE

    if not dry_run:
        cleared, _ = KehadiranSiswa.objects.filter(siswa__nis__startswith="LEG-").delete()
        if stdout and cleared:
            stdout.write(f"  bersihkan {cleared} kehadiran legacy lama")

    if stdout:
        stdout.write("  [1/3] roster TP 2025/26 (PG, siswa baru, daftar ulang)...")
    tp_stats = import_tp_rosters(
        legacy_dir=legacy_dir,
        dry_run=dry_run,
        kelompok_map=kelompok_map,
        stats=_empty_stats(),
    )
    _merge_stats(stats, tp_stats)

    if stdout:
        stdout.write(f"  [2/3] absensi katering {len(schedule)} blok → {len(demo_target_months())} bulan demo...")
    first_month = True
    for src_tahun, src_bulan, tgt_tahun, tgt_bulan in schedule:
        month_stats = import_legacy_month(
            bulan=tgt_bulan,
            tahun=tgt_tahun,
            source_bulan=src_bulan,
            source_tahun=src_tahun,
            legacy_dir=legacy_dir,
            dry_run=dry_run,
            replace_demo=replace_demo and first_month,
            kelompok_map=kelompok_map,
            stats=_empty_stats(),
            stdout=stdout if first_month else None,
        )
        _merge_stats(stats, month_stats)
        first_month = False

    if stdout:
        stdout.write(f"  [3/3] absensi jemput {len(DEMO_JEMPUT_SCHEDULE)} bulan...")
    for src_tahun, src_bulan, tgt_tahun, tgt_bulan in DEMO_JEMPUT_SCHEDULE:
        j_stats = import_jemput_month(
            bulan=tgt_bulan,
            tahun=tgt_tahun,
            source_bulan=src_bulan,
            source_tahun=src_tahun,
            legacy_dir=legacy_dir,
            dry_run=dry_run,
            stats=_empty_stats(),
        )
        _merge_stats(stats, j_stats)

    if not dry_run:
        from operations.services.tp_templates import ensure_tp_templates

        n_tpl = ensure_tp_templates()
        if stdout:
            stdout.write(f"  template TP: {n_tpl} komponen biaya tahunan")

    if stdout:
        stdout.write("  [4/5] payroll KAFALAH April 2025...")
    try:
        from operations.services.payroll_kafalah import import_kafalah_payroll

        k_stats = import_kafalah_payroll(
            legacy_dir=legacy_dir,
            dry_run=dry_run,
        )
        stats["kafalah_pegawai"] = k_stats.get("pegawai_upserted", 0)
        stats["kafalah_gaji"] = k_stats.get("gaji_upserted", 0)
        stats["kafalah_pinjaman"] = k_stats.get("pinjaman_upserted", 0)
    except FileNotFoundError as exc:
        if stdout:
            stdout.write(f"  skip KAFALAH: {exc}")

    if stdout:
        stdout.write("  [5/5] anggaran legacy + realisasi demo...")
    try:
        from operations.services.legacy_import.anggaran_import import import_legacy_anggaran

        a_stats = import_legacy_anggaran(
            legacy_dir=legacy_dir,
            tahun_anggaran=2026,
            dry_run=dry_run,
        )
        stats["anggaran_rows"] = a_stats.get("anggaran_upserted", 0)
        stats["anggaran_jurnal"] = a_stats.get("realisasi_jurnal", 0)
    except FileNotFoundError as exc:
        if stdout:
            stdout.write(f"  skip anggaran: {exc}")

    return stats
