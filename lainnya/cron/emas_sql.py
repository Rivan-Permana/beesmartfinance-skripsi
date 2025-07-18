from selenium import webdriver
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime

# Koneksi ke SQLite
conn = sqlite3.connect("palugada.db")
cursor = conn.cursor()

# Matikan foreign key constraint sementara
cursor.execute('PRAGMA foreign_keys=off;')

# Tambahkan kolom baru jika belum ada
try:
    cursor.execute('ALTER TABLE emas ADD COLUMN harga_dasar_int INTEGER;')
except sqlite3.OperationalError:
    pass  # Kolom sudah ada

try:
    cursor.execute('ALTER TABLE emas ADD COLUMN harga_termasuk_ppn_int INTEGER;')
except sqlite3.OperationalError:
    pass  # Kolom sudah ada

try:
    cursor.execute('ALTER TABLE emas ADD COLUMN harga_termasuk_ppn TEXT;')
except sqlite3.OperationalError:
    pass  # Kolom sudah ada

# Aktifkan kembali foreign key constraint
cursor.execute('PRAGMA foreign_keys=on;')

# Membuat tabel emas jika belum ada
cursor.execute('''
    CREATE TABLE IF NOT EXISTS emas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategori TEXT,
        berat TEXT,
        harga_dasar TEXT,
        harga_dasar_int INTEGER,
        harga_termasuk_ppn_int INTEGER,
        harga_termasuk_ppn TEXT,
        rec_timestamp_str TEXT,
        rec_timestamp INTEGER
    )
''')

# Fungsi untuk mengubah teks harga jadi integer
def text_to_int(text):
    try:
        return int(text.replace(",", "").replace(".", "").strip())
    except Exception:
        return 0

# Unduh driver Chrome
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

# Ambil data dari semua kategori dan simpan ke SQLite
today_date = datetime.now().strftime("%Y-%m-%d")

for produk in kategori_produk:
    data_kategori = ambil_data_produk(produk["kategori"], produk["kolom"])
    if data_kategori:
        for item in data_kategori:
            timestamp = time.time()
            rec_timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            rec_timestamp = int(timestamp)

            # Mengubah harga dasar dan harga termasuk PPN ke integer
            harga_dasar_int = text_to_int(item[1])  # item[1] = harga dasar
            harga_termasuk_ppn_int = text_to_int(item[2])  # item[2] = harga termasuk PPN

            # Simpan data ke SQLite
            cursor.execute('''
                INSERT INTO emas (
                    kategori, berat, harga_dasar, harga_dasar_int, harga_termasuk_ppn_int, harga_termasuk_ppn, rec_timestamp_str, rec_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item[3],  # Kategori
                item[0],  # Berat
                item[1],  # Harga Dasar (string)
                harga_dasar_int,  # Harga Dasar (integer)
                harga_termasuk_ppn_int,  # Harga Termasuk PPN (integer)
                item[2],  # Harga Termasuk PPN (string)
                rec_timestamp_str,
                rec_timestamp
            ))

        print(f"Data untuk kategori '{produk['kategori']}' berhasil diperbarui atau disisipkan ke SQLite.")

# Commit perubahan dan tutup koneksi
conn.commit()
conn.close()

print("Proses selesai.")
