from selenium import webdriver
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time
from datetime import datetime

# Koneksi ke MongoDB
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["pantau_emas"]

# Mengunduh driver Chrome
driver = webdriver.Chrome()
url = "https://www.logammulia.com/id/harga-emas-hari-ini"
driver.get(url)

# Tunggu hingga halaman selesai dimuat
time.sleep(5)

# Ambil konten halaman
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
driver.quit()

# Daftar kategori produk
kategori_produk = [
    {"kategori": "Emas Batangan", "kolom": ["Berat", "Harga Dasar", "Harga (+PPh 0.25%)"]},
    {"kategori": "Emas Batangan Gift Series", "kolom": ["Berat", "Harga Dasar", "Harga (+PPh 0.25%)"]},
    {"kategori": "Perak Murni", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 11%"]},
    {"kategori": "Perak Heritage", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 11%"]},
    {"kategori": "Liontin Batik Seri III", "kolom": ["Berat", "Harga Dasar", "Harga Sudah Termasuk PPN 1.65%", "Harga Sudah Termasuk PPN 1.1% + PPh 22 0.25%"]},
]

# Fungsi untuk membersihkan kunci agar kompatibel dengan MongoDB
def clean_keys(data):
    return {key.replace(".", "_"): value for key, value in data.items()}

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
            data_entry = {kolom[i]: columns[i].text.strip() for i in range(len(kolom))}
            data_entry["Kategori"] = kategori
            data.append(data_entry)
        else:
            break  # Berhenti jika baris kosong atau tidak relevan
    return data

# Ambil data dari semua kategori dan simpan ke MongoDB
today_date = datetime.now().strftime("%Y-%m-%d")

for produk in kategori_produk:
    data_kategori = ambil_data_produk(produk["kategori"], produk["kolom"])
    if data_kategori:
        collection = db[produk["kategori"].replace(" ", "_").lower()]  # Nama koleksi
        
        for item in data_kategori:
            timestamp = time.time()
            item["rec_timestamp_str"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            item["rec_timestamp"] = int(timestamp)
            cleaned_item = clean_keys(item)  # Bersihkan kunci sebelum disimpan
            
            # Update berdasarkan Berat dan Kategori
            collection.update_one(
                {"Kategori": item["Kategori"], "Berat": item["Berat"]},
                {"$set": cleaned_item},
                upsert=True  # Jika tidak ada dokumen yang cocok, tambahkan dokumen baru
            )

        print(f"Data untuk kategori '{produk['kategori']}' berhasil diperbarui atau disisipkan ke MongoDB.")

print("Proses selesai.")
