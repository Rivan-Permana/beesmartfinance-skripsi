"""Seed data riil dari folder legacy-data (Epic E10 / story 10.1)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

from operations.services.katering_tarif import set_tarif_katering_period
from operations.services.legacy_import.importer import (
    DEMO_ABSENSI_MONTHS,
    import_legacy_demo_full,
    import_legacy_month,
    legacy_data_dir,
)


class Command(BaseCommand):
    help = (
        "Import data legacy untuk demo: roster TP 2025/26 + absensi TK (--demo-full), "
        "atau satu bulan (--month YYYY-MM)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--demo-full",
            action="store_true",
            help="Roster TP (PG+TK baru+ulang) + absensi Jul 2025–Jun 2026 — rekomendasi demo.",
        )
        parser.add_argument(
            "--month",
            default="",
            help="Satu bulan absensi saja, format YYYY-MM (contoh: 2024-08).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse saja, tanpa tulis ke database.",
        )
        parser.add_argument(
            "--legacy-dir",
            default="",
            help="Path folder legacy-data (default: <repo>/legacy-data).",
        )
        parser.add_argument(
            "--keep-demo",
            action="store_true",
            help="Jangan hapus siswa demo LM-* sebelum import.",
        )
        parser.add_argument(
            "--skip-users",
            action="store_true",
            help="Lewati seed_demo users (asumsi user sudah ada).",
        )

    def handle(self, *args, **options):
        demo_full: bool = options["demo_full"]
        month_str: str = options["month"]

        if not demo_full and not month_str:
            demo_full = True
            self.stdout.write(
                self.style.WARNING("Default: --demo-full (roster TP + absensi Jul 2025–Jun 2026)"),
            )

        if demo_full and month_str:
            self.stderr.write(self.style.ERROR("Pilih --demo-full ATAU --month, jangan keduanya."))
            return

        if not options["skip_users"]:
            call_command("seed_demo", users_only=True)

        leg_dir = legacy_data_dir()
        if options["legacy_dir"]:
            leg_dir = Path(options["legacy_dir"])

        if not leg_dir.is_dir():
            self.stderr.write(self.style.ERROR(f"Folder legacy tidak ada: {leg_dir}"))
            return

        dry = options["dry_run"]
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — tidak ada perubahan DB"))

        if demo_full:
            stats = import_legacy_demo_full(
                legacy_dir=leg_dir,
                dry_run=dry,
                replace_demo=not options["keep_demo"],
                stdout=self.stdout,
            )
            if not dry:
                for tahun, bulan in DEMO_ABSENSI_MONTHS:
                    set_tarif_katering_period(bulan, tahun, Decimal("20000"), Decimal("10000"))
                self.stdout.write(
                    "  tarif katering Jul 2025–Jun 2026: Sen–Kam 20.000, Jumat 10.000",
                )
        else:
            try:
                tahun_s, bulan_s = month_str.split("-")
                tahun, bulan = int(tahun_s), int(bulan_s)
                if not 1 <= bulan <= 12:
                    raise ValueError
            except ValueError:
                self.stderr.write(self.style.ERROR("--month harus format YYYY-MM"))
                return

            stats = import_legacy_month(
                bulan=bulan,
                tahun=tahun,
                legacy_dir=leg_dir,
                dry_run=dry,
                replace_demo=not options["keep_demo"],
                stdout=self.stdout,
            )
            if not dry:
                set_tarif_katering_period(bulan, tahun, Decimal("20000"), Decimal("10000"))
                self.stdout.write(
                    f"  tarif katering {bulan}/{tahun}: Sen–Kam 20.000, Jumat 10.000",
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_legacy: siswa +{stats['siswa_created']} ~{stats['siswa_updated']} "
                f"| roster TP ~{stats.get('roster_only', 0)} "
                f"| kehadiran {stats['kehadiran_upserted']} "
                f"| jemput {stats.get('jemput_matched', 0)} "
                f"(skip {stats.get('jemput_skipped', 0)}) "
                f"| pendaftaran jemput +{stats.get('pendaftaran_jemput', 0)} "
                f"| KAFALAH pegawai {stats.get('kafalah_pegawai', 0)} "
                f"gaji {stats.get('kafalah_gaji', 0)} "
                f"| anggaran {stats.get('anggaran_rows', 0)} "
                f"| skip tanpa hari {stats['skipped_no_days']} "
                f"| bulan {', '.join(stats.get('months', [])) or '-'} "
                f"| files {', '.join(stats['files']) or '-'}"
            )
        )
