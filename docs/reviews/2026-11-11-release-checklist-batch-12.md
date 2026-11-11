# Checklist rilis Batch 12 → `main` — 11 November 2026

Merge ke `main` = deploy produksi (poller `scripts/poll_deploy_vps.sh`: dump → migrate → backend → Worker). Dokumen ini hanya persiapan: belum ada merge maupun deploy. Dokumen publik: hasil cek dicatat sebagai lulus/gagal dan hitungan saja, tanpa nama dan nominal.

## Isi rilis

- `origin/main` (`39d06c5`, rilis Batch 11) `..codex/auto-deploy-fe-be`: `869e955`, `99fb092`, `aa083e5`, merge `origin/main`, dan commit dokumen.
- **Tanpa migrasi.** Schema API bertambah (dua endpoint gaji, satu field slip).
  1. **Impor ulang biaya masuk** (`869e955`): siswa yang sudah punya tagihan biaya masuk dan di berkas belum membayar terbaca "sudah", tidak diisi ulang.
  2. **Jurnal realisasi kegiatan dicatat Keuangan** (`99fb092`): `AUTO_KEGIATAN` masuk daftar jurnal yang bisa dicatat Keuangan. Kepsek tetap tidak bisa menyetujui jurnal buatannya sendiri.
  3. **Perintah `pensiunkan_tagihan_lama`** (`99fb092`): hanya berjalan bila dipanggil; default rencana saja.
  4. **Gaji per periode** (`aa083e5`): `POST /gaji/posting-periode/` (Keuangan) dan `POST /gaji/setujui-periode/` (Kepsek), pratinjau bila `simpan=false`; slip memuat `jurnal_status`; panel "Jurnal gaji per periode" di layar Penggajian.
  5. **`scripts/backup_offsite.sh`**: ikut masuk repo, dipasang manual setelah rilis ([rencana](./2026-11-11-rencana-backup-offsite.md)).
- **Sudah diverifikasi lokal dan di UAT:** backend 198 tes OK, frontend 169 tes OK, build bersih, `makemigrations --check` bersih, tipe API diperbarui. Rincian per fitur: [gladi cut-over](./2026-11-11-gladi-cutover.md), [data menggantung](./2026-11-11-data-menggantung.md), [gladi gaji](./2026-11-11-gladi-gaji.md).

## Yang berubah bagi pengguna begitu rilis

1. **Jurnal realisasi kegiatan tidak lagi lewat persetujuan Kepsek.** Berlaku untuk dua jurnal PENDING lama (`KG-1-1`, `KG-1-2`, dibuat akun Kepsek sehingga tidak bisa disetujui siapa pun) **dan semua realisasi berikutnya** yang diinput Guru PJ: alurnya menjadi Guru input → Keuangan Catat, sama seperti pengeluaran manual. Tetap dua orang (Guru ≠ Keuangan) dan tetap dibatasi pagu kegiatan yang diatur Keuangan. Di Keuangan muncul tombol Catat; di "Menunggu persetujuan" Kepsek jurnal kegiatan tidak tampil lagi. Tidak ada yang tercatat sampai Keuangan menekan Catat. Alternatif lebih sempit bila Kepsek harus tetap menyetujui realisasi Guru: Keuangan hanya boleh mencatat jurnal kegiatan yang dibuat Kepsek (perubahan kecil sebelum merge).
2. **Label status slip gaji** berubah dari "Jurnal dibuat" menjadi Draf jurnal / Menunggu persetujuan / Tercatat / Jurnal dibatalkan.
3. **Panel "Jurnal gaji per periode"** tampil untuk Keuangan dan Kepsek bila sudah ada slip.

## 1. Cek read-only produksi (web console hPanel)

```sh
cd /opt/beesmartfinance
echo "== SHA ter-deploy"; cat /home/deploy/.local/state/beesmartfinance/backend_sha /home/deploy/.local/state/beesmartfinance/frontend_sha
echo "== Container"; docker compose --env-file .env.vps -f docker-compose.production.yml ps --format 'table {{.Service}}\t{{.Status}}'
echo "== Disk"; df -h / | tail -1
echo "== GitHub"; getent hosts github.com; curl -sS -o /dev/null -w "github %{http_code}\n" https://github.com
echo "== Backup harian"; cat /opt/beesmartfinance/backups/daily/last_success 2>/dev/null || echo "belum ada"
echo "== Database"
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U beesmartfinance -d db_lebah_madu -At -v ON_ERROR_STOP=1' <<'SQL'
SET default_transaction_read_only = on;
SELECT 'migrasi terakhir', app, max(name) FROM django_migrations WHERE app IN ('operations', 'accounts') GROUP BY app ORDER BY app;
SELECT 'jurnal belum POSTED', tipe_sumber, status, count(*) FROM tr_jurnal WHERE NOT is_deleted AND status IN ('DRAFT', 'PENDING') GROUP BY tipe_sumber, status ORDER BY tipe_sumber, status;
SELECT 'jurnal total / POSTED / VOID', count(*), count(*) FILTER (WHERE status = 'POSTED'), count(*) FILTER (WHERE status = 'VOID') FROM tr_jurnal WHERE NOT is_deleted;
SELECT 'tagihan / perlu dicocokkan', count(*), count(*) FILTER (WHERE perlu_rekonsiliasi) FROM operations_tagihan WHERE NOT is_deleted;
SELECT 'pendaftaran / perlu dicocokkan', count(*), count(*) FILTER (WHERE biaya_formulir IS NULL) FROM operations_pendaftaransiswa WHERE NOT is_deleted;
SELECT 'slip gaji / belum dijurnal / jurnal belum POSTED', count(*), count(*) FILTER (WHERE g.jurnal_id IS NULL), count(*) FILTER (WHERE j.status IN ('DRAFT', 'PENDING')) FROM operations_gajipegawai g LEFT JOIN tr_jurnal j ON j.id = g.jurnal_id WHERE NOT g.is_deleted;
SELECT 'pegawai aktif', count(*) FROM operations_pegawai WHERE NOT is_deleted AND status = 'aktif';
SELECT 'COA / kode aktif / siswa aktif', (SELECT count(*) FROM ms_coa), (SELECT count(*) FROM operations_kodepengeluaran WHERE aktif), (SELECT count(*) FROM operations_siswa WHERE NOT is_deleted AND status = 'aktif');
SQL
```

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| SHA | `39d06c5…` (merge PR #29) | Produksi berubah sejak Batch 11. Hentikan dan periksa dulu. |
| Container, disk, GitHub | Up/healthy, disk ±9%, `github 200` | Pulihkan layanan atau tunda merge. |
| Backup harian | `belum ada` | Catat; dipasang di bagian 4. |
| Migrasi | `accounts 0003`, `operations 0023` | Tidak sinkron. Jangan merge. |
| Jurnal belum POSTED | `AUTO_BILLING` DRAFT 2 + PENDING 1; `AUTO_KEGIATAN` PENDING 2; `AUTO_PENDAFTARAN` DRAFT 2 (total 7) | Ada jurnal lain: catat sumbernya; tidak menghalangi rilis, tapi bagian 4 perlu disesuaikan. |
| Jurnal total / POSTED / VOID | Total `18`; POSTED dan VOID dicatat | Pembanding untuk bagian 4. |
| Tagihan / perlu dicocokkan | `7` / `3` | Catat. |
| Pendaftaran / perlu dicocokkan | Kolom kedua `2` (dugaan dari `REG-1`, `REG-2`) | Catat angka sebenarnya; menentukan pekerjaan TU di bagian 4. |
| Slip gaji | Catat ketiga angka | Bila ada slip yang jurnalnya belum POSTED, panel gaji langsung menampilkannya untuk Keuangan/Kepsek. |
| Pegawai aktif | `33` | Catat. |
| COA / kode aktif / siswa | `206` / `60` / `108` | Catat; harus sama sesudah rilis. |

### Hasil cek — 11/11 (web console, read-only)

| Baris | Hasil | Status |
|---|---|---|
| SHA | `39d06c5` keduanya | Sesuai |
| Container, disk, GitHub | backend Up 11 jam, caddy/db Up 3 minggu (db healthy); disk 9%; `github 200` | Sesuai |
| Backup harian | belum ada | Dipasang di bagian 4 |
| Migrasi | `accounts 0003`, `operations 0023` | Sesuai |
| Jurnal belum POSTED | `AUTO_BILLING` DRAFT 2 + PENDING 1; `AUTO_KEGIATAN` PENDING 2; `AUTO_PENDAFTARAN` DRAFT 2 | Sesuai (7) |
| Jurnal total / POSTED / VOID | 18 / 11 / 0 | Pembanding bagian 4: akhir 18 / 15 / 3 |
| Tagihan / perlu dicocokkan | 7 / 3 | Sesuai |
| Pendaftaran / perlu dicocokkan | 4 / 2 | Dua catatan untuk TU di bagian 4 |
| Slip gaji | 1 slip; 0 belum dijurnal; 0 jurnal belum POSTED | Panel gaji tampil tanpa pekerjaan tertunda |
| Pegawai aktif | **30** (catatan 28/10: 33 aktif + 1 nonaktif) | Catatan lama ikut menghitung 3 baris yang dihapus 13/10; angka benar 30 |
| COA / kode aktif / siswa | 206 / 60 / 108 | Sesuai |

Kesimpulan: tidak ada yang menghalangi backup dan merge. Selisih pegawai aktif berasal dari cara hitung catatan 28/10 (ikut menghitung baris terhapus), bukan perubahan data; angka pembanding gaji (jumlah slip per bulan) adalah 30.

## 2. Backup manual sebelum merge

```sh
cd /opt/beesmartfinance
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch12.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

Diharapkan: sekitar `…before-batch11` (288.263 byte), `TABLE DATA` = 53. Dump ini juga menjadi titik pulih untuk pekerjaan data di bagian 4.

Hasil 11/11 04:00 UTC: `backups/db-20261111T040027Z-before-batch12.dump`, 288.363 byte (before-batch11: 288.263), 53 `TABLE DATA`. Titik pulih rilis Batch 12 dan pekerjaan data bagian 4.

Rincian pegawai (read-only, bersama backup): 30 aktif, 1 nonaktif, 3 dihapus lunak (total 34, sama dengan 28/10). Ketiga pegawai itu dihapus pada 13/10 (masa uji coba), jadi angka "33 aktif" di catatan 28/10 ternyata ikut menghitung baris yang sudah dihapus; pegawai aktif memang 30 sejak itu dan tidak ada penghapusan baru. Angka pembanding slip gaji per bulan: 30.

## 3. Rilis

1. PR `codex/auto-deploy-fe-be` → `main`, merge (hanya atas instruksi eksplisit pengguna).
2. Tunggu poller (maks. 5 menit + build ±3 menit). Kode backend berubah, jadi container backend dibuat ulang.
3. Cek dari luar (Claude): `/login` 200; API tanpa token 401; schema memuat `posting-periode`, `setujui-periode`, `jurnal_status`; bundle Worker memuat "Jurnal gaji per periode".
4. Cek read-only ulang (blok bagian 1): SHA baru, backend `Up` beberapa menit; **semua hitungan sama** (rilis tidak mengubah data).
5. Smoke test per role (pengguna login; tanpa menyimpan data):
   - **Keuangan:** Penggajian menampilkan panel dan label status baru; di Pengeluaran, `KG-1-1`/`KG-1-2` punya tombol Catat (jangan ditekan dulu).
   - **Kepsek:** Penggajian menampilkan panel versi Kepsek; Beranda "Menunggu persetujuan" tidak lagi memuat dua jurnal kegiatan.
   - **Staf TU:** dialog Impor biaya masuk terbuka; Pendaftaran menampilkan catatan "Perlu dicocokkan".
   - **Guru:** Absensi tetap jalan; Gaji tidak bisa dibuka.

### Hasil rilis — 11/11

- PR #30 di-merge ke `main` 04:02:10 UTC (`0b749dc`) dari sesi Claude atas instruksi pengguna, setelah cek read-only dan backup `before-batch12`.
- Backend baru terlihat dari luar 04:05:29 UTC: schema memuat `posting-periode`, `setujui-periode`, dan `jurnal_status`.
- Worker baru terlihat 04:07:04 UTC, bundle `index-BX7rLtFN.js`; chunk GajiListView memuat "Jurnal gaji per periode".
- Cek dari luar: `/login` 200; API tanpa token 401, lewat Worker maupun origin.
- Cek read-only pasca-rilis (web console): SHA backend dan frontend `0b749dc`; backend Up 4 menit, db healthy, disk 9%. Migrasi tetap `0003`/`0023`. Semua hitungan sama dengan sebelum merge: jurnal belum POSTED 7 (rincian sama), total 18 / POSTED 11 / VOID 0; tagihan 7 / 3; pendaftaran 4 / 2; slip gaji 1 / 0 / 0; pegawai aktif 30; COA 206, kode aktif 60, siswa 108. Rilis tidak mengubah data.
- Smoke test produksi per role (11/11; pengguna login di browser bawaan, Claude memeriksa tanpa menyimpan data, lalu logout tiap role):
  - **Keuangan:** Penggajian menampilkan panel "Jurnal gaji per periode" (Oktober 2026, 0 belum dijurnal, 0 menunggu; tombol nonaktif) dan label "Tercatat"; pratinjau posting periode kosong 200 dengan 0 slip. `KG-1-1`/`KG-1-2` tampil di Pengeluaran dan rinciannya punya tombol "Catat ke buku besar" (tidak ditekan; keduanya tetap PENDING).
  - **Kepsek:** Beranda tanpa error; "Menunggu persetujuan" kosong dan tidak memuat jurnal kegiatan; panel gaji versi Kepsek tampil (tombol nonaktif); pratinjau setujui periode 200 dengan 0 jurnal; posting periode 403.
  - **Staf TU:** dialog "Impor biaya masuk dari tab master" terbuka lalu ditutup; Pendaftaran menampilkan 2 dari 4 catatan "Perlu dicocokkan" (layar dan API); gaji 403.
  - **Guru:** menu Absensi Siswa, Rekap Absensi, Kegiatan; Absensi siswa tanpa error dan tanpa rupiah; gaji, posting periode, dan setujui periode 403.

  Semua lulus. Di luar Batch 12 (perilaku lama): API daftar jurnal masih bisa dibaca akun Guru walau menunya tidak ada.

## 4. Setelah rilis: pekerjaan data (masing-masing atas persetujuan pengguna)

Urut dari yang paling aman. Rincian dan blok perintah: [data menggantung](./2026-11-11-data-menggantung.md), [rencana backup](./2026-11-11-rencana-backup-offsite.md).

| # | Siapa | Apa | Hasil yang dicek |
|---|---|---|---|
| 1 | Pengguna | Pasang backup harian ke R2 (langkah 1–6 rencana backup), termasuk uji pulih | Baris `OK …` di log; `last_success` terisi; hitungan uji pulih = produksi |
| 2 | Keuangan | Periksa bukti, lalu Catat `KG-1-1` dan `KG-1-2` | `AUTO_KEGIATAN` PENDING 2 → 0; POSTED +2 |
| 3 | TU lalu Keuangan | TU mengisi biaya formulir/sit-in dua pendaftaran sesuai bukti; Keuangan Catat `REG-1`, `REG-2` | Pendaftaran perlu dicocokkan → 0; `AUTO_PENDAFTARAN` DRAFT 2 → 0; POSTED +2 |
| 4 | Superuser | `pensiunkan_tagihan_lama 1 2 3` rencana dulu, lalu `--terapkan` | **Selesai 11/11:** tagihan 7 → 4, perlu dicocokkan 3 → 0; `AUTO_BILLING` belum POSTED 3 → 0; VOID 0 → 3, audit oleh `keuangan` |

Hasil akhir: jurnal belum POSTED 7 → 0, POSTED +4, VOID +3, total tetap 18.

## Rollback

- **Kode:** revert merge commit di `main`, lalu push. Tidak ada migrasi. Jurnal yang sudah dicatat tetap tercatat (koreksi lewat jurnal pembalik).
- **Pekerjaan data bagian 4:** jurnal kegiatan/pendaftaran yang sudah POSTED dikoreksi lewat jurnal pembalik; tagihan yang dipensiunkan dipulihkan dengan `pg_restore` dari `before-batch12` (kehilangan data sesudahnya) atau dibuat ulang lewat alur cut-over.
- **Backup:** hapus cron dan token R2 (lihat rencana backup).

## Keputusan sebelum merge

0. ~~Alur realisasi kegiatan~~ **diputuskan pengguna 11/11:** realisasi kegiatan dicatat Keuangan tanpa persetujuan Kepsek (Guru input → Keuangan Catat), seragam dengan pengeluaran manual.
1. Hasil cek bagian 1 sudah ditempel dan diterima.
2. Backup bagian 2 berhasil.
3. Merge lewat PR, bukan push langsung ke `main`.
