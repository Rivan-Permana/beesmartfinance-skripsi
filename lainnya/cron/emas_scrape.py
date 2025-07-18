# lainnya/cron/emas_scraper.py

import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from django.db import IntegrityError
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

from lainnya.models import HargaEmas

# Setup logging agar bisa dilihat di crontab log
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

kategori_produk = [
    {"kategori": "Emas Batangan", "kolom": ["Berat", "Harga Dasar", "Harga (+PPh 0.25%)"]},
    {"kategori": "Emas Batangan Gift Series", "kolom": ["Berat", "Harga Dasar", "Harga (+PPh 0.25%)"]},
    {"kategori": "Perak Murni", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 11%"]},
    {"kategori": "Perak Heritage", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 11%"]},
    {"kategori": "Liontin Batik Seri III", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 1.65%", "Harga Sudah Termasuk PPN 1.1% + PPh 22 0.25%"]},
]

def ambil_data_produk(soup, kategori, kolom):
    section = soup.find("th", string=kategori)
    if not section:
        logging.warning(f"⚠️ Kategori '{kategori}' tidak ditemukan di halaman.")
        return []
    
    rows = section.find_parent("tr").find_next_siblings("tr")
    data = []
    for row in rows:
        columns = row.find_all("td")
        if len(columns) >= len(kolom):
            data_entry = {kolom[i]: columns[i].text.strip() for i in range(len(kolom))}
            data_entry["Kategori"] = kategori
            data.append(data_entry)
        else:
            break
    return data

def scrape_harga_emas():
    logging.info("🚀 Memulai scraping harga emas...")
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless=new")

        driver = uc.Chrome(options=options)
        url = "https://www.logammulia.com/id/harga-emas-hari-ini"
        driver.get(url)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Deteksi jika diblokir
        if "cf-browser-verification" in html or "captcha" in html.lower():
            logging.error("❌ Diblokir oleh Cloudflare / Captcha.")
            driver.quit()
            return

        driver.quit()

        total_data = 0
        for produk in kategori_produk:
            data_kategori = ambil_data_produk(soup, produk["kategori"], produk["kolom"])
            for item in data_kategori:
                timestamp = time.time()
                item["rec_timestamp_str"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                item["rec_timestamp"] = int(timestamp)

                try:
                    HargaEmas.objects.update_or_create(
                        kategori=item["Kategori"],
                        berat=item["Berat"],
                        defaults={
                            "harga_dasar": item.get("Harga Dasar", ""),
                            "harga_pph": item.get("Harga (+PPh 0.25%)", ""),
                            "rec_timestamp": item["rec_timestamp"],
                            "rec_timestamp_str": item["rec_timestamp_str"],
                        }
                    )
                    total_data += 1
                except IntegrityError as e:
                    logging.error(f"Gagal simpan data: {e}")
        
        logging.info(f"✅ Scraping selesai. Total data tersimpan: {total_data}")
    
    except WebDriverException as e:
        logging.error(f"❌ Gagal menjalankan WebDriver: {e}")
    except Exception as e:
        logging.error(f"❌ Terjadi error: {e}")
