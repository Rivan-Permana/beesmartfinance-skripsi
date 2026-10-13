from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from accounting.coa_final_import import import_coa_final
from accounting.models import TrJurnalDetail


class Command(BaseCommand):
    help = "Import COA dari legacy-data COA Final CSV (187+ akun)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Hapus COA lama sebelum import (dev only — pastikan tidak ada jurnal posted penting).",
        )
        parser.add_argument(
            "--seed-rules",
            action="store_true",
            help="Setelah import, jalankan seed_system_posting_rules (kas, gaji, tagihan).",
        )

        parser.add_argument(
            "--path",
            type=str,
            default="",
            help="Path CSV opsional; default: legacy-data/Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv",
        )

    def handle(self, *args, **options):
        if options["path"]:
            csv_path = Path(options["path"])
        else:
            csv_path = (
                Path(settings.BASE_DIR).parent
                / "legacy-data"
                / "Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv"
            )

        if not csv_path.is_file():
            self.stderr.write(self.style.ERROR(f"File tidak ditemukan: {csv_path}"))
            return

        if options["replace"]:
            self.stdout.write(self.style.WARNING("Menghapus COA lama…"))

        stats = import_coa_final(csv_path, replace=options["replace"])
        if options["replace"] and TrJurnalDetail.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Jurnal sudah ada — import mode merge (akun lama tetap, akun baru ditambah)."
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"COA Final OK — baru: {stats['golongan']} gol, {stats['sub']} sub, "
                f"{stats['akun']} akun · total di DB: {stats['akun_total']}"
            )
        )

        if options["seed_rules"]:
            from operations.services.coa_resolve import seed_system_posting_rules

            try:
                mapped = seed_system_posting_rules()
                self.stdout.write(
                    self.style.SUCCESS(
                        "MsPostingRule OK — "
                        + ", ".join(f"{k}={v}" for k, v in mapped.items())
                    )
                )
            except ValueError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
