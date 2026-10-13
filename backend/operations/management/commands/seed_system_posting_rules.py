from django.core.management.base import BaseCommand

from operations.services.coa_resolve import seed_system_posting_rules


class Command(BaseCommand):
    help = "Mapping akun COA Final ke MsPostingRule (kas, gaji, kasbon, tagihan)."

    def handle(self, *args, **options):
        mapped = seed_system_posting_rules()
        self.stdout.write(
            self.style.SUCCESS(
                "MsPostingRule sistem OK — "
                + ", ".join(f"{k}={v}" for k, v in mapped.items())
            )
        )
