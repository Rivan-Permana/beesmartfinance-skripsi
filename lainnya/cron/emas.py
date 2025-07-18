import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time
from datetime import datetime

# Ganti dengan API Key dari ScraperAPI kamu
API_KEY = "968e58501f5391bb8e160e271c5da2a4"
TARGET_URL = "https://www.logammulia.com/id/harga-emas-hari-ini"
SCRAPER_API_URL = f"http://api.scraperapi.com/?api_key={API_KEY}&url={TARGET_URL}&render=true"

# Ambil konten HTML dari halaman
response = requests.get(SCRAPER_API_URL)
soup = BeautifulSoup(response.text, "html.parser")

# Koneksi ke MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["palugada"]
collection = db["emas"]

# Fungsi untuk mengubah teks harga jadi integer
def text_to_int(text):
    try:
        return int(text.replace(",", "").replace(".", "").strip())
    except Exception:
        return 0

# Daftar kategori produk
kategori_produk = [
    {"kategori": "Emas Batangan", "kolom": ["Berat", "Harga Dasar", "Harga (+PPh 0.25%)"]},
    {"kategori": "Emas Batangan Gift Series", "kolom": ["Berat", "Harga Dasar", "Harga (+PPh 0.25%)"]},
    {"kategori": "Perak Murni", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 11%"]},
    {"kategori": "Perak Heritage", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 11%"]},
    {"kategori": "Liontin Batik Seri III", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 1.65%", "Harga Sudah Termasuk PPN 1.1% + PPh 22 0.25%"]},
]

# Fungsi untuk mengambil data dari kategori tertentu
def ambil_data_produk(kategori, kolom):
    section = soup.find("th", string=kategori)
    if not section:
        return []  # Jika kategori tidak ditemukan
    rows = section.find_parent("tr").find_next_siblings("tr")
    
    data = []
    for row in rows:
        columns = row.find_all("td")
        if len(columns) >= len(kolom):
            data_entry = [columns[i].text.strip() for i in range(len(kolom))]
            data_entry.append(kategori)  # Menambahkan kategori sebagai elemen terakhir
            data.append(data_entry)
        else:
            break  # Berhenti jika baris kosong atau tidak relevan
    return data

# Ambil data dari semua kategori dan simpan ke MongoDB
for produk in kategori_produk:
    data_kategori = ambil_data_produk(produk["kategori"], produk["kolom"])
    if data_kategori:
        for item in data_kategori:
            timestamp = time.time()
            rec_timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            rec_timestamp = int(timestamp)

            harga_dasar_int = text_to_int(item[1])
            harga_termasuk_ppn_int = text_to_int(item[2])

            document = {
                "kategori": item[3],
                "berat": item[0],
                "harga_dasar": item[1],
                "harga_dasar_int": harga_dasar_int,
                "harga_termasuk_ppn_int": harga_termasuk_ppn_int,
                "harga_termasuk_ppn": item[2],
                "rec_timestamp_str": rec_timestamp_str,
                "rec_timestamp": rec_timestamp
            }

            collection.insert_one(document)

        print(f"Data untuk kategori '{produk['kategori']}' berhasil disimpan ke MongoDB.")

print("Proses selesai.")
