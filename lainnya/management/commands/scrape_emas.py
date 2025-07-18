# lainnya/management/commands/scrape_emas.py

from django.core.management.base import BaseCommand
from lainnya.cron.emas_scrape import scrape_harga_emas

class Command(BaseCommand):
    help = "Scrape data harga emas dan simpan ke SQLite"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Memulai scraping...")
        scrape_harga_emas()
        self.stdout.write("✅ Scraping selesai.")
