# Checklist rilis Batch 9 → `main` — 10 November 2026

Merge ke `main` = deploy produksi. Poller `scripts/poll_deploy_vps.sh` di VPS berjalan tiap 5 menit dengan urutan: `pg_dump` ke `backups/` (deploy berhenti kalau dump gagal), `migrate`, `collectstatic`, backend naik, lalu Worker Cloudflare dibangun ulang. Dokumen ini hanya persiapan: belum ada merge maupun deploy. Dokumen ini publik, jadi hasil cek dicatat sebagai lulus/gagal dan hitungan saja, tanpa nominal.

## Isi rilis

- `origin/main` (`774d93d`, rilis Batch 8) `..codex/auto-deploy-fe-be`: dokumen handoff, `05a9040` (cut-over), `dd8f49d` (LSU, penyusun anggaran, subtotal laba rugi), `a8ecf82` (perbaikan UI), skrip COA produksi.
- **Tiga migrasi:**
  - `operations.0022_komite_portofolio_saldo_awal`:
    - kolom `uang_komite` dan `uang_portofolio` (nullable) di siswa dan riwayatnya;
    - kolom `saldo_awal` (default false) di pembayaran tagihan dan riwayatnya;
    - `akun_kas` dan `jurnal` pembayaran tagihan menjadi nullable;
    - check constraint `pembayaran_tagihan_jurnal_kecuali_saldo_awal`: pembayaran biasa wajib punya akun kas dan jurnal, saldo awal wajib tanpa keduanya. Semua baris lama memenuhi aturan ini karena kedua kolom sebelumnya wajib terisi.
  - `operations.0023_lsu`:
    - tabel baru `operations_paketlsu` dan `operations_pertemuanlsu`;
    - pilihan jenis tagihan dan komponen `LSU`;
    - unique constraint `tagihan_siswa_periode_jenis_unik` dibuat ulang dengan pengecualian jenis LSU. Aturannya jadi lebih longgar, jadi tidak bisa gagal pada data lama.
  - `accounts.0003_budget_planner_group`: grup `BudgetPlanner` (get_or_create).
- **Kode tanpa migrasi:**
  - impor biaya masuk dari tab master (pratinjau dulu, simpan terpisah);
  - pembatalan saldo awal lewat API (TU);
  - plafon tahunan dan anggaran bulanan beserta laporan `/laporan/anggaran-bulanan/`;
  - laba rugi dengan judul kelompok akun dan subtotal;
  - menu LSU untuk TU;
  - peran penyusun anggaran (hanya menu Anggaran; ditolak di jurnal, tagihan, aset, laporan lain).
- **COA dan kode pengeluaran sudah diisi di produksi 10/11** (lihat [handoff](./2026-11-10-handoff.md)), terpisah dari rilis ini.
- **Sudah diverifikasi lokal dan di UAT `bee_uat_browser_20261020`:**
  - Backend 188 tes OK, frontend 159 tes OK, build bersih, `makemigrations --check` bersih, tipe API dibangkitkan ulang.
  - UAT dimigrasi dari `0021` ke `0023` (backup sebelumnya ada).
  - Skenario API 27/27 lulus: impor pratinjau/simpan/ulang tanpa duplikasi, saldo awal tanpa jurnal, sisa dibayar normal jadi jurnal DRAFT, Keuangan 403 saat membatalkan saldo awal, LSU pertemuan ke-9 ditolak, anggaran bulanan melebihi plafon ditolak, penyusun anggaran 403 di jurnal/tagihan/aset/laba rugi.
  - DOM 375 px tanpa geser samping: LSU, form siswa, dialog impor, halaman anggaran penyusun. Laba rugi desktop menampilkan kelompok dan subtotal.
- Tidak ada impor data dalam rilis ini. Impor biaya masuk dijalankan saat cut-over.

## Risiko yang perlu dicek sebelum merge

1. **Migrasi terakhir di produksi harus `operations.0021` dan `accounts.0002`.** Kalau berbeda, branch dan produksi tidak sinkron.
2. **Pembayaran tagihan lama tanpa akun kas atau jurnal.** Seharusnya 0 karena kolomnya wajib. Kalau tidak 0, check constraint baru gagal dan migrasi berhenti.
3. **Anggaran yang sudah ada.** Baris anggaran tanpa bulan sekarang dibaca sebagai plafon tahunan, dan hanya terlihat di laporan bulanan kalau punya periode. Query menampilkan bentuk barisnya (tanpa nominal). Kalau ada baris tanpa bulan dan tanpa periode, Keuangan perlu mengedit dan memilih tahun pelajarannya setelah rilis.
4. **Setiap akun aktif punya sub-golongan.** Subtotal laba rugi memakai sub-golongan. Akun tanpa sub-golongan tetap tampil, tapi masuk kelompok "Lainnya".

## 1. Cek read-only produksi (web console hPanel)

Buka hPanel → VPS → Web console (login root), lalu tempel satu blok ini. Semua query berjalan di sesi `default_transaction_read_only = on`. Blok ini tidak menampilkan isi `.env.vps`, password, nominal, atau data pribadi siswa.

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
SELECT 'migrasi terakhir', app, max(name) FROM django_migrations WHERE app IN ('operations', 'accounts') GROUP BY app ORDER BY app;
SELECT 'grup', string_agg(name, ', ' ORDER BY name) FROM auth_group;
SELECT 'tabel LSU sudah ada?', to_regclass('operations_paketlsu') IS NOT NULL, to_regclass('operations_pertemuanlsu') IS NOT NULL;
SELECT 'pembayaran total / tanpa akun kas / tanpa jurnal', count(*), count(*) FILTER (WHERE akun_kas_id IS NULL), count(*) FILTER (WHERE jurnal_id IS NULL) FROM operations_pembayarantagihan;
SELECT 'tagihan per jenis', jenis, count(*) FROM operations_tagihan WHERE NOT is_deleted GROUP BY jenis ORDER BY jenis;
SELECT 'tagihan perlu dicocokkan', count(*) FROM operations_tagihan WHERE NOT is_deleted AND perlu_rekonsiliasi;
SELECT 'anggaran bulanan / tanpa bulan+periode / tanpa bulan tanpa periode', count(*) FILTER (WHERE bulan IS NOT NULL), count(*) FILTER (WHERE bulan IS NULL AND periode_id IS NOT NULL), count(*) FILTER (WHERE bulan IS NULL AND periode_id IS NULL) FROM tr_anggaran;
SELECT 'akun aktif tanpa sub-golongan', count(*) FROM ms_coa WHERE is_active AND sub_golongan_id IS NULL;
SELECT 'COA total / aktif', count(*), count(*) FILTER (WHERE is_active) FROM ms_coa;
SELECT 'kode pengeluaran / terpetakan / aktif', count(*), count(kode_akun), count(*) FILTER (WHERE aktif) FROM operations_kodepengeluaran;
SELECT 'siswa tidak dihapus / aktif', count(*), count(*) FILTER (WHERE status = 'aktif') FROM operations_siswa WHERE NOT is_deleted;
SELECT 'jurnal total / DRAFT+PENDING', count(*), count(*) FILTER (WHERE status IN ('DRAFT', 'PENDING')) FROM tr_jurnal WHERE NOT is_deleted;
SELECT 'periode', kode, tgl_mulai, tgl_selesai, status FROM ms_periode_akuntansi ORDER BY tgl_mulai;
SQL
```

Cara membaca hasilnya:

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| SHA backend/frontend | `774d93d…` (merge PR #26) | Produksi sudah berubah sejak rilis Batch 8. Hentikan dan periksa dulu. |
| Container | backend, caddy, db `Up`; db `healthy` | Pulihkan layanan dulu, jangan merge. |
| Disk | Masih jauh dari penuh (2/11: 8%) | Sediakan ruang: deploy membuat dump dan image baru. |
| Backup | Ada `…before-coa-kode` (10/11, 276.912 byte) | Catat saja. Semua dump masih di disk VPS yang sama. |
| Migrasi terakhir | `accounts 0002_seed_groups`, `operations 0021_harga_tp_2026_27` | Tidak sinkron dengan branch. Jangan merge. |
| Grup | Empat grup lama (Administration, Finance, SchoolPrincipal, TeacherInCharge), belum ada `BudgetPlanner` | Kalau sudah ada, migrasi tetap aman (get_or_create). Catat. |
| Tabel LSU | `f`, `f` | Kalau sudah ada, ada yang membuat tabel di luar migrasi. Jangan merge. |
| Pembayaran tanpa akun kas / jurnal | `0` / `0` | Constraint baru akan gagal. Jangan merge; periksa barisnya. |
| Tagihan per jenis | Hanya `BULANAN` (2/11: 7) dan mungkin `BIAYA_MASUK` | Catat; harus sama sesudah rilis. |
| Anggaran | Kolom ketiga `0` | Catat jumlahnya. Setelah rilis Keuangan memilih tahun pelajaran untuk baris itu lewat menu Anggaran. |
| Akun aktif tanpa sub-golongan | `0` | Catat; akun itu masuk "Lainnya" di laba rugi. |
| COA | `205` total (setelah pengisian 10/11) | Ada perubahan COA sesudah pengisian. Catat. |
| Kode pengeluaran | `74 / 58 / 60` | Catat sebagai pembanding baru. |
| Siswa, jurnal, periode | Siswa 108, jurnal sama dengan snapshot terakhir, periode 2026/2027 OPEN | Catat; harus sama sesudah rilis. |

### Hasil cek — (isi saat dijalankan)

| Baris | Hasil | Status |
|---|---|---|
| SHA backend/frontend | | |
| Container | | |
| Disk | | |
| Backup | | |
| Migrasi terakhir | | |
| Grup | | |
| Tabel LSU | | |
| Pembayaran tanpa akun kas / jurnal | | |
| Tagihan per jenis | | |
| Anggaran | | |
| Akun aktif tanpa sub-golongan | | |
| COA / kode pengeluaran | | |
| Siswa, jurnal, periode | | |

## 2. Backup manual sebelum merge

Deploy sudah membuat dump sendiri. Backup bernama ini untuk titik pulih yang jelas. Jalankan di web console:

```sh
cd /opt/beesmartfinance
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch9.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

Yang diharapkan: ukuran file sedikit di atas `…before-coa-kode` (276.912 byte), dan `TABLE DATA` = 51. Kalau ukurannya 0 atau perintah gagal, jangan merge.

## 3. Rilis

1. Buka PR `codex/auto-deploy-fe-be` → `main`, lalu merge. Ini keputusan rilis dan hanya dilakukan atas instruksi eksplisit pengguna.
2. Tunggu poller (maks. 5 menit, ditambah build ±3 menit). Pantau di web console:
   ```sh
   tail -f /home/deploy/.local/state/beesmartfinance/deploy.log
   ```
   Rilis selesai bila muncul baris `Deploy backend <sha>` lalu `Deploy frontend <sha>`. Satu baris `curl: (22) … 502` sebelum frontend itu wajar.
3. Cek pasca-rilis:
   - **Read-only:** jalankan ulang blok bagian 1. Yang boleh berubah hanya:
     - migrasi menjadi `accounts 0003_budget_planner_group` dan `operations 0023_lsu`;
     - grup `BudgetPlanner` muncul;
     - tabel LSU `t`, `t` (kosong);
     - ada dump deploy baru.
     Pembayaran, tagihan, anggaran, COA, kode pengeluaran, siswa, dan jurnal harus sama.
   - **Dari luar** (bisa Claude jalankan):
     - `/login` 200, API tanpa token 401.
     - Schema memuat `paket-lsu`, `anggaran-bulanan`, `impor-biaya-masuk`, `batal-saldo-awal`, dan `uang_komite`.
     - Bundle Worker memuat "Impor biaya masuk" dan "Penyusun Anggaran".
4. Smoke test per role (pengguna yang login; tanpa menyimpan data):
   - **Staf TU:**
     - Menu LSU terbuka, daftar kosong, tombol Paket baru membuka form. Tutup dengan Batal.
     - Form siswa menampilkan isian Iuran Komite dan Portofolio beserta teks bantunya. Tutup dengan Batal.
     - Data Siswa → Impor biaya masuk membuka dialog. Tutup tanpa memilih berkas.
     - Riwayat tagihan lama tetap tampil dengan kwitansi seperti sebelumnya.
   - **Keuangan:**
     - Laporan laba rugi menampilkan judul kelompok dan subtotal; total pendapatan, beban, dan laba sama dengan sebelum rilis.
     - Menu Anggaran: form tambah menampilkan pilihan plafon tahunan dan tahun pelajaran. Tutup dengan Batal.
   - **Kepsek:** Beranda dan laba rugi sama dengan sebelum rilis; panel anggaran bulanan tampil.
   - **Guru:** Absensi tetap jalan, tanpa nominal; menu LSU tidak ada.
   - **Penyusun anggaran:** belum ada user di produksi. Dilewati sampai superuser membuatnya (lihat bagian 4).

## 4. Setelah rilis

1. **Superuser** membuat user penyusun anggaran dan memasukkannya ke grup `BudgetPlanner` (Django admin). Lalu smoke test: login masuk ke Anggaran, menu lain tidak ada, jurnal dan tagihan ditolak.
2. **Keuangan** mengisi plafon tahunan per akun beban untuk TP 2026/2027.
3. **Cut-over 31 Des–2 Jan** sesuai [desain](./2026-11-02-desain-cutover-januari.md): saldo awal kas, impor biaya masuk (pratinjau → simpan).

## Rollback

- **Kode, selama belum ada data baru:** aman hanya jika belum ada paket LSU, tagihan LSU, atau penerimaan saldo awal.
  1. Sebelum revert, jalankan di VPS:
     ```sh
     docker compose --env-file .env.vps -f docker-compose.production.yml run --rm backend python manage.py migrate operations 0021
     docker compose --env-file .env.vps -f docker-compose.production.yml run --rm backend python manage.py migrate accounts 0002
     ```
     `operations 0021` menghapus tabel LSU dan kolom Komite/Portofolio/saldo awal, lalu mengembalikan akun kas dan jurnal pembayaran menjadi wajib. `accounts 0002` menghapus grup `BudgetPlanner` beserta keanggotaannya.
  2. Revert merge commit di `main`, lalu push. Poller men-deploy ulang dan membuat dump baru lebih dulu.
- **Kalau sudah ada data baru:** pembalikan `0022` gagal selama ada penerimaan saldo awal (tanpa jurnal), dan `0023` menghapus data LSU. Pilihannya: perbaiki maju (fix-forward), atau `pg_restore` dari dump `before-batch9` dengan kehilangan data sesudahnya.
- **Total:** `pg_restore` dari dump `before-batch9`.

## Keputusan sebelum merge

1. Hasil cek bagian 1 sudah ditempel dan diterima, terutama migrasi terakhir dan pembayaran tanpa akun kas/jurnal = 0.
2. Backup bagian 2 berhasil.
3. Merge lewat PR, bukan push langsung ke `main`.
