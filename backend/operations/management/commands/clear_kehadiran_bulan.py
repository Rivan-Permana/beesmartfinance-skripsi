"""Hapus record absensi siswa untuk satu bulan kalender — bersihkan data import legacy."""

from __future__ import annotations

import calendar
import re
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from operations.models import KehadiranSiswa

_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


class Command(BaseCommand):
    help = (
        "Hapus semua kehadiran siswa dalam satu bulan (YYYY-MM). "
        "Berguna membersihkan data import legacy sebelum input absensi manual."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "bulan",
            help="Periode target, format YYYY-MM (contoh: 2026-07).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Tampilkan jumlah yang akan dihapus tanpa menghapus.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Lewati konfirmasi interaktif (untuk script/automation).",
        )

    def handle(self, *args, **options):
        bulan_str: str = options["bulan"].strip()
        m = _MONTH_RE.match(bulan_str)
        if not m:
            raise CommandError("Format bulan harus YYYY-MM, contoh: 2026-07")

        tahun, bulan = int(m.group(1)), int(m.group(2))
        if bulan < 1 or bulan > 12:
            raise CommandError("Bulan harus 01–12.")

        last_day = calendar.monthrange(tahun, bulan)[1]
        start = date(tahun, bulan, 1)
        end = date(tahun, bulan, last_day)

        qs = KehadiranSiswa.objects.filter(tanggal__gte=start, tanggal__lte=end)
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(f"Tidak ada absensi {bulan_str} — tidak ada yang dihapus."))
            return

        self.stdout.write(
            f"Akan menghapus {count} record absensi siswa "
            f"({start.isoformat()} s/d {end.isoformat()})."
        )

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Dry-run OK — {count} record akan dihapus jika dijalankan tanpa --dry-run."))
            return

        if not options["yes"]:
            self.stdout.write(
                self.style.WARNING(
                    "Jalankan ulang dengan --yes untuk konfirmasi, "
                    f"contoh: python manage.py clear_kehadiran_bulan {bulan_str} --yes"
                )
            )
            return

        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Selesai — {deleted} record absensi {bulan_str} dihapus."))
