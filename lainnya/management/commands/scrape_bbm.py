# lainnya/management/commands/scrape_bbm.py
from django.core.management.base import BaseCommand
from lainnya.cron import bbm_scrape

class Command(BaseCommand):
    help = 'Scrape data harga BBM dan simpan ke SQLite'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Memulai scraping harga BBM...")
        bbm_scrape.bbm_scrape()
        self.stdout.write("✅ Scraping selesai.")
