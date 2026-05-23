# File: database/seeds/etl_migration.py

import pandas as pd
import psycopg2
import uuid
import os
from datetime import datetime

# === KONFIGURASI DATABASE ===
DB_CONFIG = {
    "dbname": "db_lebah_madu",
    "user": "postgres",
    "password": "BeeSF1007",  # <--- GANTI INI
    "host": "localhost",
    "port": "5432"
}

# === SETUP PATH FOLDER ===
# Script ini ada di beesmartfinance/database/seeds/
# Kita mau baca file di beesmartfinance/database/raw_data/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(CURRENT_DIR, '../raw_data')

def get_file(filename):
    return os.path.join(RAW_DATA_DIR, filename)

def run_migration():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print(f"✅ Terhubung ke database. Membaca data dari: {RAW_DATA_DIR}")

        # 1. MIGRASI GOLONGAN
        print("⏳ Migrasi Golongan...")
        df_gol = pd.read_csv(get_file('T_GOLKUN.csv'))
        df_gol.columns = df_gol.columns.str.strip()
        for _, row in df_gol.iterrows():
            cur.execute("""
                INSERT INTO ms_golongan (kode_golongan, nama_golongan) VALUES (%s, %s)
                ON CONFLICT (kode_golongan) DO NOTHING;
            """, (str(row['NOGOL']), row['NAMGOL']))

        # 2. MIGRASI SUB-GOLONGAN
        print("⏳ Migrasi Sub-Golongan...")
        df_sub = pd.read_csv(get_file('T_SUBGOL.csv'))
        df_sub.columns = df_sub.columns.str.strip()
        for _, row in df_sub.iterrows():
            cur.execute("SELECT id FROM ms_golongan WHERE kode_golongan = %s", (str(row['NOGOL']),))
            res = cur.fetchone()
            if res:
                cur.execute("""
                    INSERT INTO ms_sub_golongan (kode_sub, nama_sub, golongan_id) VALUES (%s, %s, %s)
                    ON CONFLICT (kode_sub) DO NOTHING;
                """, (str(row['NOSUBGOL']), row['NAMSUBGOL'], res[0]))

        # 3. MIGRASI COA (GABUNGAN LAMA & BARU)
        print("⏳ Migrasi COA...")
        # Load COA Lama
        df_akun = pd.read_csv(get_file('T_AKUN.csv'))
        df_akun.columns = df_akun.columns.str.strip()

        # Load COA Baru (jika ada, uncomment baris bawah ini setelah file direname)
        # df_new_coa = pd.read_csv(get_file('coa_baru.csv'))

        # Logic Insert COA Lama
        for _, row in df_akun.iterrows():
            kode = str(row['NOKUN'])
            posisi = 'D' if kode.startswith(('1', '5')) else 'K'
            cur.execute("SELECT id FROM ms_sub_golongan WHERE kode_sub = %s", (str(row['NOSUBGOL']),))
            res = cur.fetchone()
            if res:
                cur.execute("""
                    INSERT INTO ms_coa (kode_akun, nama_akun, sub_golongan_id, posisi_normal)
                    VALUES (%s, %s, %s, %s) ON CONFLICT (kode_akun) DO NOTHING;
                """, (kode, row['NAMKUN'], res[0], posisi))

        # 4. MIGRASI TRANSAKSI
        print("⏳ Migrasi Jurnal Transaksi (Loading...)")
        df_jurnal = pd.read_csv(get_file('T_JURNAL.csv'))
        df_jurnal.columns = df_jurnal.columns.str.strip()

        grouped = df_jurnal.groupby('NO_TRANS')
        count = 0

        for no_bukti, items in grouped:
            first = items.iloc[0]
            jurnal_uuid = str(uuid.uuid4())

            # Header
            cur.execute("""
                INSERT INTO tr_jurnal (id, no_bukti, tanggal, keterangan, tipe_sumber)
                VALUES (%s, %s, %s, %s, 'MIGRATION')
                ON CONFLICT (no_bukti) DO NOTHING RETURNING id;
            """, (jurnal_uuid, str(no_bukti), pd.to_datetime(first['TGL_TRAN']).date(), first['KET']))

            # Cek ID (apakah insert baru atau sudah ada)
            res_id = cur.fetchone()
            active_uuid = res_id[0] if res_id else None

            # Jika header sudah ada, ambil UUID-nya
            if not active_uuid:
                cur.execute("SELECT id FROM tr_jurnal WHERE no_bukti = %s", (str(no_bukti),))
                active_uuid = cur.fetchone()[0]

            # Detail
            for _, detail in items.iterrows():
                # Pastikan akun ada di master
                cur.execute("SELECT 1 FROM ms_coa WHERE kode_akun = %s", (str(detail['NOKUN']),))
                if cur.fetchone():
                    cur.execute("""
                        INSERT INTO tr_jurnal_detail (jurnal_id, kode_akun, debit, kredit)
                        VALUES (%s, %s, %s, %s);
                    """, (active_uuid, str(detail['NOKUN']), detail['DEBET'], detail['KREDIT']))
            count += 1

        conn.commit()
        print(f"🎉 SUKSES! {count} Transaksi berhasil dimigrasi.")

    except Exception as e:
        print(f"❌ Error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_migration()
