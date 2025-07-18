# lainnya/cron/bbm_scrape.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
from ..models import HargaBBM
import requests
from bs4 import BeautifulSoup
import time


def get_price_bs4(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        session = requests.Session()
        session.headers.update(headers)

        # Visit homepage first to set cookies (for Cloudflare)
        session.get("https://www.investing.com", timeout=10)

        response = session.get(url, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        price_div = soup.find("div", {"data-test": "instrument-price-last"})

        if price_div:
            raw_price = price_div.text.strip()
            return float(raw_price.replace(",", ""))
        else:
            print("❌ Gagal menemukan elemen harga.")
            return None

    except Exception as e:
        print(f"[ERROR] Gagal scraping dengan BeautifulSoup: {e}")
        return None


def get_price_selenium(url, retries=2):
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36"
        )

        for attempt in range(retries):
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)

                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[data-test="instrument-price-last"]')
                    )
                )

                price_element = driver.find_element(By.CSS_SELECTOR, 'div[data-test="instrument-price-last"]')
                price_text = price_element.text.strip()
                price = float(price_text.replace(",", "").replace("IDR", "").strip())

                return price
            except Exception as e:
                print(f"[WARNING] Attempt {attempt + 1} gagal: {e}")
                time.sleep(5)
            finally:
                if driver:
                    driver.quit()

        print(f"[ERROR] Semua percobaan scraping Selenium gagal untuk {url}")
        return None

    except Exception as e:
        print(f"[FATAL] Error setup selenium: {e}")
        if driver:
            driver.quit()
        return None


def bbm_scrape():
    print("🚀 Memulai scraping harga BBM...")

    brent_url = "https://www.investing.com/commodities/brent-oil"
    usd_idr_url = "https://www.investing.com/currencies/usd-idr"

    print("🔍 Mendapatkan harga USD/IDR...")
    usd_idr = get_price_selenium(usd_idr_url)
    if usd_idr is None:
        print("⚠️ Selenium gagal, coba BS4 untuk USD/IDR...")
        usd_idr = get_price_bs4(usd_idr_url)

    print("🔍 Mendapatkan harga Brent Oil...")
    harga_brent = get_price_selenium(brent_url)
    if harga_brent is None:
        print("⚠️ Selenium gagal, coba BS4 untuk Brent...")
        harga_brent = get_price_bs4(brent_url)

    if harga_brent is None or usd_idr is None:
        print("❌ Gagal mengambil data utama, proses dihentikan.")
        return

    HargaBBM.objects.create(
        harga_brent=harga_brent,
        nilai_tukar_usd_idr=usd_idr
    )

    print(f"✅ Data disimpan: Brent = {harga_brent}, USD/IDR = {usd_idr}")
