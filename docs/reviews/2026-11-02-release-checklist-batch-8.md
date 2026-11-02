# Checklist rilis Batch 8 → `main` — 2 November 2026

Merge ke `main` = deploy produksi. Poller `scripts/poll_deploy_vps.sh` di VPS berjalan tiap 5 menit dengan urutan: `pg_dump` ke `backups/` (deploy berhenti kalau dump gagal), `migrate`, `collectstatic`, backend naik, lalu Worker Cloudflare dibangun ulang. Dokumen ini hanya persiapan: belum ada merge maupun deploy. Dokumen ini publik, jadi hasil cek dicatat sebagai lulus/gagal dan hitungan saja, tanpa nominal.

## Isi rilis

- `origin/main..codex/auto-deploy-fe-be`: commit dokumen Batch 7 plus `c017a68` (Batch 8).
- **Tidak ada perubahan skema.** Satu migrasi data:
  - `operations.0021_harga_tp_2026_27` mengubah 3 baris `operations_komponenbiayatemplate`: KEGIATAN RA baru, SERAGAM RA baru, dan SERAGAM PG baru, ke harga 26/27.
  - Baris hanya diubah kalau nilainya masih sama dengan nilai lama di migrasi. Isian manual lewat admin tidak tertimpa.
  - Tagihan yang sudah ada tidak berubah.
  - Reversible: `migrate operations 0020`.
- **Kode tanpa migrasi:**
  - Kategori diskon SBD, KHUSUS, PINDAHAN.
  - Aturan akun kas di `accounting/kas.py`: kode kas lama, atau akun berkode `1…` dengan nama berawalan "Kas ".
  - Field `is_kas` di API COA.
  - Dropdown kas di Tagihan, Data Siswa, dan Pendaftaran membaca field itu.
- **Sudah diverifikasi lokal dan di UAT `bee_uat_browser_20261020`:**
  - Backend 166 tes OK, frontend 151 tes OK, build bersih, `makemigrations --check` bersih.
  - `0021` diterapkan, dibalik ke `0020`, lalu diterapkan ulang. Hanya 3 baris template yang berubah.
  - Skenario API: akun "Kas PG" baru diterima sebagai kas, akun 113 ditolak, Keuangan 403 saat membayar, default harga baru tampil, siswa PINDAHAN+SBD tersimpan.
  - DOM: form siswa 788 px dan 375 px; dropdown kas Tagihan.
- Tidak ada impor data. Impor biaya masuk menunggu cut-over Januari ([desain](./2026-11-02-desain-cutover-januari.md)).

## Risiko yang perlu dicek sebelum merge

1. **Akun yang otomatis jadi "kas".** Akun aktif berkode `1…` yang namanya berawalan "Kas " akan muncul di dropdown penerima dan ikut dihitung di total Kas dan bank di Beranda. Query bagian 1 menampilkan daftarnya. Daftar itu harus berisi akun kas/bank sungguhan saja.
2. **Template harga.** Kalau produksi tidak punya baris template, atau nilainya sudah bukan nilai lama, migrasi tidak mengubah apa pun. Rilis tetap aman, tapi prefill harga tidak berubah. Catat hasilnya.

## 1. Cek read-only produksi (web console hPanel)

Buka hPanel → VPS → Web console (login root), lalu tempel satu blok ini. Semua query berjalan di sesi `default_transaction_read_only = on`. Blok ini tidak menampilkan isi `.env.vps`, password, atau data pribadi siswa.

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
SELECT 'template', kode, jenjang, tipe_siswa, tahun_ke, nominal, aktif FROM operations_komponenbiayatemplate WHERE kode IN ('KEGIATAN', 'SERAGAM') ORDER BY kode, jenjang, tipe_siswa;
SELECT 'akun kas menurut aturan baru', kode_akun, nama_akun, is_active FROM ms_coa WHERE kode_akun IN ('111','112','1011','1101','1102') OR (kode_akun LIKE '1%' AND nama_akun ILIKE 'kas %') ORDER BY kode_akun;
SELECT 'kode pengeluaran / terpetakan / aktif', count(*), count(kode_akun), count(*) FILTER (WHERE aktif) FROM operations_kodepengeluaran;
SELECT 'siswa tidak dihapus / aktif', count(*), count(*) FILTER (WHERE status = 'aktif') FROM operations_siswa WHERE NOT is_deleted;
SELECT 'siswa dengan kategori diskon', count(*) FROM operations_siswa WHERE NOT is_deleted AND diskon_kategori <> '[]'::jsonb;
SELECT 'tagihan bulanan / biaya masuk / perlu dicocokkan', count(*) FILTER (WHERE jenis = 'BULANAN'), count(*) FILTER (WHERE jenis = 'BIAYA_MASUK'), count(*) FILTER (WHERE perlu_rekonsiliasi) FROM operations_tagihan WHERE NOT is_deleted;
SELECT 'jurnal total / DRAFT+PENDING', count(*), count(*) FILTER (WHERE status IN ('DRAFT', 'PENDING')) FROM tr_jurnal WHERE NOT is_deleted;
SELECT 'periode', kode, tgl_mulai, tgl_selesai, status FROM ms_periode_akuntansi ORDER BY tgl_mulai;
SQL
```

Cara membaca hasilnya:

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| SHA backend/frontend | `64dadab…` (merge PR #25) | Produksi sudah berubah sejak rilis Batch 7. Hentikan dan periksa dulu. |
| Container | backend, caddy, db `Up`; db `healthy` | Pulihkan layanan dulu, jangan merge. |
| Disk | Masih jauh dari penuh (2/11: 8%) | Sediakan ruang: deploy membuat dump dan image baru. |
| Backup | Ada `…before-kode-pengeluaran` (2/11) | Catat saja. Semua dump masih di disk VPS yang sama. |
| Migrasi terakhir | `0020_seed_kode_pengeluaran` | Tidak sinkron dengan branch. Jangan merge. |
| Template | Ada baris KEGIATAN/SERAGAM. Tiga baris sasaran bernilai sama dengan nilai "lama" di `0021` | Tidak ada baris atau nilai berbeda: migrasi tidak mengubah apa pun. Catat, lalu putuskan apakah harga diisi lewat admin. |
| Akun kas | Hanya akun kas/bank sungguhan (2/11: kas di tangan dan kas di bank) | Ada akun bukan kas berawalan "Kas ": ganti namanya di COA sebelum merge. |
| Kode pengeluaran | `60 / 42 / 51` | Catat sebagai pembanding baru. |
| Siswa, tagihan, jurnal, periode | Sama dengan snapshot handoff 2/11 | Catat; harus sama sesudah rilis. |

### Hasil cek

_Belum dijalankan._

## 2. Backup manual sebelum merge

Deploy sudah membuat dump sendiri. Backup bernama ini untuk titik pulih yang jelas. Jalankan di web console:

```sh
cd /opt/beesmartfinance
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch8.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

Yang diharapkan: ukuran file kira-kira sama dengan `…before-kode-pengeluaran`, dan `TABLE DATA` = 51. Kalau ukurannya 0 atau perintah gagal, jangan merge.

## 3. Rilis

1. Buka PR `codex/auto-deploy-fe-be` → `main`, lalu merge. Ini keputusan rilis dan hanya dilakukan atas instruksi eksplisit pengguna.
2. Tunggu poller (maks. 5 menit, ditambah build ±3 menit). Pantau di web console:
   ```sh
   tail -f /home/deploy/.local/state/beesmartfinance/deploy.log
   ```
   Rilis selesai bila muncul baris `Deploy backend <sha>` lalu `Deploy frontend <sha>`. Satu baris `curl: (22) … 502` sebelum frontend itu wajar.
3. Cek pasca-rilis:
   - **Read-only:** jalankan ulang blok bagian 1. Yang boleh berubah hanya:
     - migrasi menjadi `0021_harga_tp_2026_27`;
     - tiga baris template sasaran bernilai harga 26/27 (sama dengan nilai "baru" di `0021`);
     - ada dump deploy baru.
     Siswa, tagihan, jurnal, dan kode pengeluaran harus sama.
   - **Dari luar** (bisa Claude jalankan):
     - `/login` 200, API tanpa token 401.
     - Schema memuat `is_kas` dan `PINDAHAN`.
     - Bundle Worker memuat "PINDAHAN" dan teks bantu "Akun kas baru".
4. Smoke test per role (pengguna yang login; tanpa menyimpan data):
   - **Staf TU:**
     - Form siswa → Status diskon menampilkan 7 kategori dan teks bantu SBD/KHUSUS/PINDAHAN.
     - "Isi dari daftar harga" untuk kelompok TK dengan siswa baru menampilkan harga 26/27. Tutup dengan Batal.
     - Tunggakan/Tagihan → Catat pembayaran: dropdown Kas/Bank berisi akun kas yang sama dengan sebelum rilis. Tutup tanpa menyimpan.
   - **Keuangan:** form Tambah akun di COA menampilkan teks bantu akun kas. Tutup dengan Batal.
   - **Kepsek:** Beranda, angka Kas dan bank sama dengan sebelum rilis.
   - **Guru:** Absensi tetap jalan, tanpa nominal.

## 4. Setelah rilis (Keuangan)

1. Buat akun kas per unit di COA sesuai keputusan kas: kode berawalan `1…`, nama berawalan "Kas ", misalnya Kas PG, Kas TK, Kas ADM. Saldo awal diisi saat cut-over Januari, bukan sekarang.
2. Lanjutkan pemetaan kode pengeluaran yang tersisa setelah akun baru dibuat.

## Rollback

- **Kode:**
  1. Sebelum revert, jalankan di VPS:
     `docker compose --env-file .env.vps -f docker-compose.production.yml run --rm backend python manage.py migrate operations 0020`
     Tiga baris template kembali ke harga lama.
  2. Revert merge commit di `main`, lalu push. Poller men-deploy ulang dan membuat dump baru lebih dulu.
  3. Kalau setelah rilis sudah ada siswa yang disimpan dengan kategori SBD/KHUSUS/PINDAHAN, setelah revert form siswa itu ditolak saat disimpan karena kategorinya tidak dikenal. Kosongkan kategorinya lebih dulu.
- **Total:** `pg_restore` dari dump `before-batch8`.

## Keputusan sebelum merge

1. Hasil cek bagian 1 sudah ditempel dan diterima, terutama daftar akun kas.
2. Backup bagian 2 berhasil.
3. Merge lewat PR, bukan push langsung ke `main`.
