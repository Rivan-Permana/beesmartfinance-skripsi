# Checklist rilis Batch 7 → `main` — 2 November 2026

Merge ke `main` = deploy produksi. Cron `deploy` di VPS menjalankan `scripts/poll_deploy_vps.sh` tiap 5 menit. Urutannya: `pg_dump` ke `backups/` (deploy berhenti kalau gagal), `migrate`, `collectstatic`, backend naik, lalu Worker Cloudflare dibangun ulang. Dokumen ini hanya persiapan; belum ada merge maupun deploy.

## Isi rilis

- `origin/main..codex/auto-deploy-fe-be`: 4 commit, 41 file.
  - `a5840b8` Batch 7: invoice gabungan per siswa, tab "Perlu dilengkapi", kode pengeluaran → akun COA, ukuran seragam
  - `9c5a41f`, `4979a74` dokumen; `c413730` merge balik `origin/main`
- Migrasi baru:
  - `operations.0019_info_jenjang_seragam_kode_pengeluaran`
    - `operations_jenjang`: 6 kolom teks (rekening bank/nomor/atas nama, kontak nama/WA, catatan invoice), default `''`
    - `operations_siswa` dan `operations_historicalsiswa`: `ukuran_seragam_putih`, `ukuran_seragam_olga`, default `''`
    - tabel baru `operations_kodepengeluaran`
  - `operations.0020_seed_kode_pengeluaran`: 46 kode. Akun hanya diisi untuk 19 kode yang jelas, dan hanya kalau akunnya ada di `ms_coa`.
  - Tidak ada baris lama yang diubah. Keduanya reversible: `migrate operations 0018` menghapus kode, kolom, dan tabel itu.
- Sudah diverifikasi lokal dan di UAT `bee_uat_browser_20261020`:
  - backend 163 tes OK, frontend 151 tes OK, build bersih, `makemigrations --check` bersih
  - `0019`/`0020` diterapkan, dibalik ke `0018`, lalu diterapkan ulang
  - skenario API per role lulus; cek DOM desktop + 375 px lulus
- Tidak ada impor data. Rekening dan kontak per jenjang diisi Staf TU setelah rilis (bagian 4).

## 1. Cek read-only produksi (web console hPanel)

Buka hPanel → VPS → Web console (login root), lalu tempel satu blok ini. Semua query berjalan di sesi `default_transaction_read_only = on`. Blok ini tidak menampilkan isi `.env.vps`, password, atau data pribadi siswa; hanya hitungan, kode jenjang, dan nama kelompok.

```sh
cd /opt/beesmartfinance
echo "== SHA ter-deploy"; cat /home/deploy/.local/state/beesmartfinance/backend_sha /home/deploy/.local/state/beesmartfinance/frontend_sha
echo "== Log deploy terakhir"; tail -n 5 /home/deploy/.local/state/beesmartfinance/deploy.log
echo "== Container"; docker compose --env-file .env.vps -f docker-compose.production.yml ps --format 'table {{.Service}}\t{{.Status}}'
echo "== Disk"; df -h / | tail -1
echo "== Backup"; ls -lt backups | head -5; echo "jumlah dump: $(ls backups | wc -l), total: $(du -sh backups | cut -f1)"
echo "== Database"
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U beesmartfinance -d db_lebah_madu -At -v ON_ERROR_STOP=1' <<'SQL'
SET default_transaction_read_only = on;
SELECT 'migrasi operations terakhir', max(name) FROM django_migrations WHERE app = 'operations';
SELECT 'kolom/tabel 0019 sudah ada (harus 0)', (SELECT count(*) FROM information_schema.columns WHERE (table_name = 'operations_jenjang' AND column_name LIKE 'rekening_%') OR (table_name = 'operations_siswa' AND column_name LIKE 'ukuran_seragam_%')) + (SELECT count(*) FROM information_schema.tables WHERE table_name = 'operations_kodepengeluaran');
SELECT 'akun seed kode ada / aktif (harus 19 / 19)', count(*), count(*) FILTER (WHERE is_active) FROM ms_coa WHERE kode_akun IN ('5301','5302','5401','5406','5407','5112','5212','5120','5220','5124','5224','5116','5216','5103','5203','5110','5210','5218','5206');
SELECT 'siswa tidak dihapus / aktif', count(*), count(*) FILTER (WHERE status = 'aktif') FROM operations_siswa WHERE NOT is_deleted;
SELECT 'aktif: SPP 0 / tanpa kelompok / kedua HP kosong', count(*) FILTER (WHERE spp_nominal <= 0), count(*) FILTER (WHERE kelompok_id IS NULL), count(*) FILTER (WHERE coalesce(trim(kontak_ayah), '') = '' AND coalesce(trim(kontak_ibu), '') = '') FROM operations_siswa WHERE NOT is_deleted AND status = 'aktif';
SELECT 'jenjang', j.kode, count(k.id) FROM operations_jenjang j LEFT JOIN operations_kelompok k ON k.jenjang_id = j.id GROUP BY j.kode ORDER BY j.kode;
SELECT 'tagihan bulanan / biaya masuk / perlu dicocokkan', count(*) FILTER (WHERE jenis = 'BULANAN'), count(*) FILTER (WHERE jenis = 'BIAYA_MASUK'), count(*) FILTER (WHERE perlu_rekonsiliasi) FROM operations_tagihan WHERE NOT is_deleted;
SELECT 'jurnal total / DRAFT+PENDING', count(*), count(*) FILTER (WHERE status IN ('DRAFT', 'PENDING')) FROM tr_jurnal WHERE NOT is_deleted;
SELECT 'periode', kode, tgl_mulai, tgl_selesai, status FROM ms_periode_akuntansi ORDER BY tgl_mulai;
SQL
```

Cara membaca hasilnya:

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| SHA backend/frontend | `99b4a13…` (merge PR #24) | Produksi sudah berubah sejak 28/10 malam. Hentikan dan periksa dulu. |
| Container | backend, caddy, db `Up`; db `healthy` | Jangan merge. Pulihkan layanan dulu. |
| Disk | Masih jauh dari penuh (28/10: 8%) | Deploy membuat dump dan image baru, jadi sediakan ruang. |
| Backup | Ada `…before-batch6` dan dump deploy 28/10 | Catat. Semua dump masih di disk VPS yang sama. |
| migrasi operations terakhir | `0018_siswa_data_diri` | Tidak sinkron dengan branch. Jangan merge. |
| kolom/tabel 0019 sudah ada | `0` | Ada perubahan skema manual. Periksa dulu. |
| akun seed kode | `19 / 19` | Kode yang akunnya tidak ada tetap tersimpan tapi "belum dipetakan". Tidak memblokir; catat. |
| siswa / aktif | Dicatat (28/10: 108 / 108) | Pembanding sesudah rilis. |
| SPP 0 / tanpa kelompok / kedua HP kosong | Dicatat (28/10: SPP 0 = 10, tanpa kelompok = 2) | Perkiraan isi tab "Perlu dilengkapi"; tab juga menandai SPP di luar kisaran dan HP janggal. |
| jenjang (kode, jumlah kelompok) | PG, TKA, TKB | Rekening dan kontak diisi per kode ini setelah rilis. |
| tagihan | Dicatat (28/10: bulanan 7) | Invoice gabungan hanya berisi tagihan yang ada di sistem. |
| jurnal | Dicatat; DRAFT/PENDING 7 | Harus sama sesudah rilis. |
| periode | 2026/2027 01/07/2026–30/06/2027 OPEN | Periksa sebelum rilis. |

### Hasil cek — 2 November 2026 (web console, read-only)

| Cek | Hasil | Penilaian |
|---|---|---|
| SHA backend / frontend | `99b4a13` / `99b4a13`; log terakhir: Worker ter-deploy | Sesuai |
| Container | backend Up 4 hari, caddy Up 2 minggu, db Up 2 minggu (healthy) | Sesuai |
| Disk | 7,1 GB dari 96 GB (8%) | Cukup |
| Backup | Terakhir `db-20261028T192504Z.dump` (268 KB, deploy batch 6) dan `…before-batch6`; 24 dump, total 5,4 MB | Ada; masih hanya di VPS |
| Migrasi / kolom-tabel 0019 | `0018_siswa_data_diri` / 0 | Sesuai |
| Akun seed kode | 19 / 19 aktif | Semua 19 kode akan terpetakan |
| Siswa | 108, semuanya aktif; SPP 0: 10; tanpa kelompok: 2; kedua HP kosong: 4 | Sama seperti 28/10; perkiraan isi tab Perlu dilengkapi |
| Jenjang | PG (3 kelompok), TKA (4), TKB (4) | Rekening/kontak diisi untuk 3 jenjang |
| Tagihan | Bulanan 7, biaya masuk 0, perlu dicocokkan 3 | 3 tagihan lama akan muncul sebagai peringatan "perlu dicocokkan" di invoice |
| Jurnal | 18 total, DRAFT/PENDING 7 | Sama seperti sebelumnya |
| Periode | 2026/2027, 01/07/2026–30/06/2027, OPEN | Sesuai |

Kesimpulan: tidak ada yang menghalangi backup dan merge.

Cek dari luar sebelum rilis (2 November, Claude): `/login` Worker 200; schema produksi belum memuat `perlu-dilengkapi` (sesuai, Batch 7 belum dirilis).

## 2. Backup manual sebelum merge

Deploy sudah membuat dump sendiri. Backup bernama ini untuk titik pulih yang jelas sebelum rilis. Jalankan di web console:

```sh
cd /opt/beesmartfinance
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch7.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

Diharapkan: ukuran file sedikit di atas dump `before-batch6` dan jumlah `TABLE DATA` sekitar 50. Kalau ukurannya 0 atau perintah gagal, jangan merge.

Hasil 2/11 02:52 UTC: `backups/db-20261102T025212Z-before-batch7.dump`, 271.840 byte (before-batch6: 268.168), 50 `TABLE DATA`. Titik pulih rilis Batch 7.

## 3. Rilis

1. Buka PR `codex/auto-deploy-fe-be` → `main` lalu merge di GitHub. Hanya kamu yang melakukan ini, sebagai keputusan rilis.
2. Tunggu poller (maks. 5 menit + build ±3 menit). Pantau di web console:
   ```sh
   tail -f /home/deploy/.local/state/beesmartfinance/deploy.log
   ```
   Selesai bila ada baris `Deploy backend <sha>` lalu `Deploy frontend <sha>`. Ctrl+C untuk berhenti memantau. Satu baris `curl: (22) … 502` sebelum frontend wajar (backend sedang restart, curl mengulang).
3. Cek pasca-rilis:
   - Read-only dari web console: jalankan ulang blok di bagian 1, tanpa query `kolom/tabel 0019`. Tambahkan dua query ini di dalam blok SQL:
     ```sql
     SELECT 'kode pengeluaran / terpetakan', count(*), count(kode_akun) FROM operations_kodepengeluaran;
     SELECT 'kolom 0019', count(*) FROM information_schema.columns WHERE (table_name = 'operations_jenjang' AND (column_name LIKE 'rekening_%' OR column_name LIKE 'kontak_%' OR column_name = 'catatan_invoice')) OR (table_name = 'operations_siswa' AND column_name LIKE 'ukuran_seragam_%');
     ```
     Yang diharapkan berubah hanya:
     - migrasi menjadi `0020_seed_kode_pengeluaran`
     - kode pengeluaran `46 / 19`, kolom 0019 = `8`
     - ada backup `db-…Z.dump` baru dari deploy
     Jumlah siswa, tagihan, dan jurnal harus sama dengan sebelum rilis.
   - Dari luar (bisa Claude jalankan): `/login` 200; API tanpa token 401; schema memuat `/api/v1/siswa/perlu-dilengkapi/`, `invoice-gabungan`, dan `/api/v1/kode-pengeluaran/`; bundle Worker memuat "Perlu dilengkapi" dan "Invoice tunggakan".
4. Smoke test per role (kamu yang login):
   - **Staf TU:**
     - Data siswa → tab Perlu dilengkapi tampil dengan jumlah; Lengkapi membuka form (tutup dengan Batal).
     - Form siswa berisi Ukuran seragam putih dan olahraga.
     - Tombol Invoice di baris siswa membuka dialog; tanpa rekening muncul pesan "Rekening … belum diatur".
     - Kelompok → Jenjang → Ubah: bagian "Info pembayaran di invoice" tampil.
     - Pengeluaran → Buat draf jurnal: ketik `PLN` di Kode sekolah, akun 5406 terisi (tutup dengan Batal).
   - **Keuangan:** Daftar akun → panel Kode pengeluaran sekolah dengan "19 dari 46 kode sudah dipetakan" dan tombol Tambah kode. Tunggakan tagihan → kolom Invoice.
   - **Kepsek:** Beranda normal; Tunggakan tagihan → Invoice siswa terbuka.
   - **Guru:** Absensi Siswa tetap jalan; tidak ada tombol Invoice atau tab Perlu dilengkapi.

## 4. Setelah rilis (Staf TU)

1. Isi rekening, atas nama, kontak konfirmasi, dan catatan invoice per jenjang di menu Kelompok → Jenjang → Ubah. Datanya dari template INV TK/INV PG sekolah; jangan dicatat di repo.
2. Selesaikan daftar di tab Perlu dilengkapi.
3. Keuangan memetakan kode yang masih kosong setelah sekolah menjawab pertanyaan arti kode.

## Rollback

- **Kode:**
  1. Sebelum revert, jalankan di VPS:
     `docker compose --env-file .env.vps -f docker-compose.production.yml run --rm backend python manage.py migrate operations 0018`
     Rekening/kontak jenjang, ukuran seragam, dan kode pengeluaran hilang; data lain tidak tersentuh.
  2. Revert merge commit di `main` lalu push. Poller men-deploy ulang dan membuat dump baru lebih dulu.
- **Total:** `pg_restore` dari dump `before-batch7`.

## Keputusan sebelum merge

1. Hasil cek bagian 1 sudah ditempel dan diterima.
2. Backup bagian 2 berhasil.
3. Merge lewat PR, bukan push langsung ke `main`.
