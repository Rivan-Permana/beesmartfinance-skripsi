# Checklist rilis Batch 10 → `main` — 10 November 2026

Merge ke `main` = deploy produksi. Poller `scripts/poll_deploy_vps.sh` di VPS berjalan tiap 5 menit dengan urutan: `pg_dump` ke `backups/` (deploy berhenti kalau dump gagal), `migrate`, `collectstatic`, backend naik, lalu Worker Cloudflare dibangun ulang. Dokumen ini hanya persiapan: belum ada merge maupun deploy. Dokumen ini publik, jadi hasil cek dicatat sebagai lulus/gagal dan hitungan saja, tanpa nominal.

## Isi rilis

- `origin/main` (`7cd5b97`, rilis Batch 9) `..codex/auto-deploy-fe-be`: `d454043`, `21cdd71`, `7294c1a`, merge `origin/main`, dan commit dokumen.
- **Tidak ada migrasi, tidak ada perubahan schema API.** Hanya kode:
  1. **Batal saldo awal dari riwayat pembayaran (TU).** Tombol "Batalkan saldo awal" hanya pada penerimaan saldo awal yang belum dibatalkan; alasan wajib. Memakai endpoint `batal-saldo-awal` yang sudah ada sejak Batch 9. Tidak ada jurnal yang berubah.
  2. **Redirect `/`.** Halaman utama dihitung setelah sesi dimuat, jadi membuka `/` dengan sesi tersimpan langsung ke beranda peran, bukan halaman login.
  3. **Akun pendapatan LSU.** Komponen LSU memakai akun `418` bila ada dan aktif; kalau tidak, tetap `417`. Hanya tagihan LSU baru yang terpengaruh.
  4. **Daftar Pengeluaran.** Selain jurnal berakun beban `5…`, juga memuat jurnal yang mendebit akun kode pengeluaran non-beban (mis. DVD → 313, TMB → 121) sambil mengkredit akun kas. Transfer antar kas, pendapatan, dan pengembalian ke kas tetap tidak masuk.
- **Sudah diverifikasi lokal dan di UAT `bee_uat_browser_20261020`:**
  - Backend 191 tes OK, frontend 164 tes OK, build bersih, `makemigrations --check` bersih, schema sama.
  - Tes redirect `/` gagal di kode lama dan lulus di kode baru.
  - UAT: `/` dengan sesi TU → `/siswa`. Batal saldo awal: tombol hanya pada saldo awal, kirim nonaktif sebelum alasan diisi, status jadi Dibatalkan, tagihan kembali SEBAGIAN. Dialog 375 px tanpa geser samping.
  - UAT: setelah akun 418 dibuat, paket LSU baru tercatat ke 418; pembayaran menghasilkan jurnal DRAFT 112 D / 418 K.
  - UAT: jurnal 313 ← 112 masuk Pengeluaran (21 → 22), transfer 115 ← 112 tidak. Jurnal uji dihapus.

## Risiko yang perlu dicek sebelum merge

1. **Posting rule LSU.** Kalau produksi punya `MsPostingRule` TAGIHAN/LSU, rule itu menang atas urutan 418 → 417. Seharusnya belum ada (rule hanya dibuat lewat perintah manual).
2. **Daftar Pengeluaran bertambah.** Jurnal lama yang mendebit 121 (TMB) atau 313 (DVD) dari kas akan ikut tampil. Query menghitung berapa jurnal yang akan bertambah, supaya Keuangan tidak kaget.
3. **Tagihan LSU dan saldo awal di produksi.** Seharusnya 0 dan 0 (belum dipakai). Tidak memengaruhi rilis, hanya pembanding.

## 1. Cek read-only produksi (web console hPanel)

```sh
cd /opt/beesmartfinance
echo "== SHA ter-deploy"; cat /home/deploy/.local/state/beesmartfinance/backend_sha /home/deploy/.local/state/beesmartfinance/frontend_sha
echo "== Log deploy terakhir"; tail -n 3 /home/deploy/.local/state/beesmartfinance/deploy.log
echo "== Container"; docker compose --env-file .env.vps -f docker-compose.production.yml ps --format 'table {{.Service}}\t{{.Status}}'
echo "== Disk"; df -h / | tail -1
echo "== GitHub"; getent hosts github.com; curl -sS -o /dev/null -w "github %{http_code}\n" https://github.com
echo "== Database"
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U beesmartfinance -d db_lebah_madu -At -v ON_ERROR_STOP=1' <<'SQL'
SET default_transaction_read_only = on;
SELECT 'migrasi terakhir', app, max(name) FROM django_migrations WHERE app IN ('operations', 'accounts') GROUP BY app ORDER BY app;
SELECT 'posting rule LSU', count(*) FROM operations_mspostingrule WHERE komponen = 'LSU';
SELECT 'akun 418', count(*) FROM ms_coa WHERE kode_akun = '418';
SELECT 'paket LSU / tagihan LSU', (SELECT count(*) FROM operations_paketlsu), (SELECT count(*) FROM operations_tagihan WHERE jenis = 'LSU' AND NOT is_deleted);
SELECT 'pembayaran / saldo awal', count(*), count(*) FILTER (WHERE saldo_awal) FROM operations_pembayarantagihan;
SELECT 'jurnal pengeluaran lama (akun 5) / tambahan dari kode non-beban', count(*) FILTER (WHERE beban), count(*) FILTER (WHERE NOT beban AND kode_non_beban AND kredit_kas) FROM (
  SELECT j.id,
    bool_or(d.kode_akun LIKE '5%') AS beban,
    bool_or(d.debit > 0 AND d.kode_akun IN (SELECT kode_akun FROM operations_kodepengeluaran WHERE kode_akun IS NOT NULL AND kode_akun NOT LIKE '5%')) AS kode_non_beban,
    bool_or(d.kredit > 0 AND (d.kode_akun IN ('111','112','1011','1101','1102') OR (d.kode_akun LIKE '1%' AND c.nama_akun ILIKE 'kas %'))) AS kredit_kas
  FROM tr_jurnal j JOIN tr_jurnal_detail d ON d.jurnal_id = j.id JOIN ms_coa c ON c.kode_akun = d.kode_akun
  WHERE NOT j.is_deleted GROUP BY j.id) x;
SELECT 'COA / kode pengeluaran aktif', (SELECT count(*) FROM ms_coa), (SELECT count(*) FROM operations_kodepengeluaran WHERE aktif);
SELECT 'siswa aktif / jurnal / tagihan', (SELECT count(*) FROM operations_siswa WHERE NOT is_deleted AND status = 'aktif'), (SELECT count(*) FROM tr_jurnal WHERE NOT is_deleted), (SELECT count(*) FROM operations_tagihan WHERE NOT is_deleted);
SQL
```

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| SHA backend/frontend | `7cd5b97…` (merge PR #27) | Produksi berubah sejak Batch 9. Hentikan dan periksa dulu. |
| Container, disk | backend/caddy/db `Up`, db `healthy`; disk 9% | Pulihkan layanan dulu. |
| GitHub | Alamat IP dan `github 200` | Tunda merge sampai koneksi pulih. |
| Migrasi terakhir | `accounts 0003_budget_planner_group`, `operations 0023_lsu` | Tidak sinkron. Jangan merge. |
| Posting rule LSU | `0` | Ada rule: LSU tetap ke akun rule itu. Catat, lalu putuskan apakah rule diubah ke 418. |
| Akun 418 | `0` (dibuat Keuangan setelah rilis) | Sudah ada: LSU langsung ke 418 setelah rilis. Catat. |
| Paket / tagihan LSU | `0` / `0` | Catat. Tagihan lama tetap di akunnya. |
| Pembayaran / saldo awal | `3` / `0` | Catat. |
| Jurnal pengeluaran | Kolom pertama = jumlah sekarang di daftar Pengeluaran; kolom kedua = tambahan setelah rilis | Catat kolom kedua; Keuangan diberi tahu kalau tidak 0. |
| COA, kode, siswa, jurnal, tagihan | 205 / 60; 108 / 18 / 7 (10/11) | Catat; harus sama sesudah rilis. |

### Hasil cek — 10 November 2026 (web console, read-only)

| Baris | Hasil | Status |
|---|---|---|
| SHA backend/frontend | `7cd5b97` keduanya; Worker version `1e0e2cab…` | Sesuai |
| Container, disk | backend Up 54 menit, caddy dan db Up 3 minggu (db healthy); disk 9% | Sesuai |
| GitHub | `github.com` resolve, `github 200` | Sesuai |
| Migrasi terakhir | `accounts 0003_budget_planner_group`, `operations 0023_lsu` | Sesuai |
| Posting rule LSU | 0 | Sesuai; LSU mengikuti urutan 418 → 417 |
| Akun 418 | 0 | Dibuat Keuangan setelah rilis |
| Paket / tagihan LSU | 0 / 0 | Sesuai |
| Pembayaran / saldo awal | 3 / 0 | Sesuai |
| Jurnal pengeluaran | 5 jurnal berakun beban; tambahan dari kode non-beban 0 | Daftar Pengeluaran tidak berubah saat rilis |
| COA, kode, siswa, jurnal, tagihan | 205 / 60; 108 / 18 / 7 | Sama dengan pasca-rilis Batch 9 |

Kesimpulan: tidak ada yang menghalangi backup dan merge.

## 2. Backup manual sebelum merge

```sh
cd /opt/beesmartfinance
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch10.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

Yang diharapkan: ukuran sekitar `…before-batch9` (278.077 byte), `TABLE DATA` = 53 (51 + dua tabel LSU dari Batch 9). Kalau ukurannya 0 atau perintah gagal, jangan merge.

Hasil 10/11 16:27 UTC: `backups/db-20261110T162737Z-before-batch10.dump`, 288.196 byte (before-batch9: 278.077; selisih dari skema Batch 9: dua tabel LSU, kolom Komite/Portofolio/saldo awal, dan constraint baru), 53 `TABLE DATA`. Titik pulih rilis Batch 10.

## 3. Rilis

1. Buka PR `codex/auto-deploy-fe-be` → `main`, lalu merge. Hanya atas instruksi eksplisit pengguna.
2. Tunggu poller (maks. 5 menit, ditambah build ±3 menit). Pantau: `tail -f /home/deploy/.local/state/beesmartfinance/deploy.log`.
3. Cek pasca-rilis:
   - **Read-only:** jalankan ulang blok bagian 1. Yang boleh berubah hanya SHA dan dump deploy baru. Migrasi tetap `0023`/`0003`; semua hitungan sama.
   - **Dari luar** (Claude): `/login` 200, API tanpa token 401; bundle Worker memuat "Batalkan saldo awal" dan teks Pengeluaran "transfer ke yayasan".
4. Smoke test per role (pengguna login; tanpa menyimpan data):
   - **Staf TU:** buka `/` dengan sesi aktif (muat ulang) → langsung ke Data siswa. Riwayat pembayaran lama tetap menampilkan kwitansi; tidak ada tombol batal pada pembayaran biasa.
   - **Keuangan:** `/` → Beranda. Pengeluaran memuat jurnal lama ditambah hitungan kolom kedua bagian 1. Lalu buat akun `418 Pendapatan LSU` (sub-golongan 41, posisi K) lewat Daftar Akun → Tambah akun. Ini satu-satunya penulisan data, atas persetujuan pengguna.
   - **Kepsek:** `/` → Beranda tanpa error.
   - **Guru:** `/` → Kegiatan; Absensi tanpa nominal.

### Hasil rilis — 10 November 2026

- PR #28 di-merge ke `main` pukul 16:29:01 UTC (`242d519`) dari sesi Claude atas instruksi pengguna, setelah cek read-only dan backup `before-batch10`.
- Worker baru terlihat dari luar 16:31:21 UTC, bundle `index-x02cqMm3.js`: chunk TagihanListView memuat "Batalkan saldo awal", JurnalListView memuat teks Pengeluaran "transfer ke yayasan".
- Cek dari luar: `/login` 200; API tanpa token 401, lewat Worker maupun origin.
- Cek read-only pasca-rilis (web console): SHA backend dan frontend `242d519`; Worker version `cfc17d85…`; backend Up 5 menit, db healthy, disk 9%. Migrasi tetap `0003`/`0023`. Tidak berubah: posting rule LSU 0, akun 418 0, paket/tagihan LSU 0/0, pembayaran 3/0, jurnal pengeluaran 5/0, COA 205, kode aktif 60, siswa 108, jurnal 18, tagihan 7.
- Smoke test per role: menunggu pengguna.

## Rollback

- **Kode:** revert merge commit di `main`, lalu push. Tidak ada migrasi yang perlu dibalik. Saldo awal yang sudah dibatalkan tetap dibatalkan (data, bukan kode). Tagihan LSU yang sudah tercatat ke 418 tetap di 418.
- **Total:** `pg_restore` dari dump `before-batch10`.

## Keputusan sebelum merge

1. Hasil cek bagian 1 sudah ditempel dan diterima.
2. Backup bagian 2 berhasil.
3. Merge lewat PR, bukan push langsung ke `main`.
