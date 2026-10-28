# Checklist rilis Batch 4–5 → `main` — 28 Oktober 2026

Merge ke `main` = deploy produksi. Cron `deploy` di VPS menjalankan `scripts/poll_deploy_vps.sh` tiap 5 menit. Urutannya: `pg_dump` ke `backups/` (deploy berhenti kalau gagal), `migrate`, `collectstatic`, backend naik, lalu Worker Cloudflare dibangun ulang. Dokumen ini hanya persiapan; belum ada merge maupun deploy.

## Isi rilis

- `origin/main..codex/auto-deploy-fe-be`: 5 commit, 27 file. Isinya:
  - perbaikan 400 `siswa/biaya-masuk-default` (`243b7ff`)
  - Batch 4: data diri siswa, klik kelompok, Guru tanpa nominal, pesan diskon (`f26080f`)
  - Batch 5: impor biodata CSV, perapian alamat/HP/tanggal, usia otomatis (`d067d43`)
  - commit dokumen dan merge balik `origin/main`
- Migrasi baru: hanya `operations.0018_siswa_data_diri`. Tiga kolom yang boleh kosong (`nama_panggilan`, `jenis_kelamin`, `tempat_lahir`) ditambahkan di `operations_siswa` dan `operations_historicalsiswa`, tanpa backfill. Reversible: `migrate operations 0017` menghapus ketiga kolom itu.
- Lokal sudah diverifikasi: backend 155 tes OK, frontend 145 tes OK, build bersih, `makemigrations --check` bersih. `0018` sudah diterapkan, dibalik, dan diterapkan ulang di UAT. Skenario API UAT untuk Batch 4 (9) dan Batch 5 (4) lulus.
- Impor biodata **tidak** ikut deploy. Impor dijalankan Staf TU dari aplikasi setelah rilis (bagian 4).

## 1. Cek read-only produksi (web console hPanel)

Buka hPanel → VPS → Web console (login root), lalu tempel satu blok ini. Semua query berjalan di sesi `default_transaction_read_only = on`. Blok ini tidak menampilkan isi `.env.vps`, password, atau data pribadi siswa; hanya hitungan dan nama kelompok.

```sh
cd /opt/beesmartfinance
echo "== SHA ter-deploy"; cat /home/deploy/.local/state/beesmartfinance/backend_sha /home/deploy/.local/state/beesmartfinance/frontend_sha
echo "== Log deploy terakhir"; tail -n 5 /home/deploy/.local/state/beesmartfinance/deploy.log
echo "== Container"; docker compose --env-file .env.vps -f docker-compose.production.yml ps --format 'table {{.Service}}\t{{.Status}}'
echo "== Disk"; df -h / | tail -1
echo "== Backup terakhir"; ls -lt backups | head -4
echo "== Database"
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U beesmartfinance -d db_lebah_madu -At -v ON_ERROR_STOP=1' <<'SQL'
SET default_transaction_read_only = on;
SELECT 'migrasi operations terakhir', max(name) FROM django_migrations WHERE app = 'operations';
SELECT 'kolom 0018 sudah ada (harus 0)', count(*) FROM information_schema.columns WHERE table_name = 'operations_siswa' AND column_name IN ('nama_panggilan', 'jenis_kelamin', 'tempat_lahir');
SELECT 'siswa tidak dihapus / aktif', count(*), count(*) FILTER (WHERE status = 'aktif') FROM operations_siswa WHERE NOT is_deleted;
SELECT 'siswa aktif SPP 0', count(*) FROM operations_siswa WHERE NOT is_deleted AND status = 'aktif' AND spp_nominal <= 0;
SELECT 'biodata terisi: tgl lahir/alamat/ayah/hp ayah/ibu/hp ibu', count(tanggal_lahir), count(nullif(alamat, '')), count(nullif(nama_ayah, '')), count(nullif(kontak_ayah, '')), count(nullif(nama_ibu, '')), count(nullif(kontak_ibu, '')) FROM operations_siswa WHERE NOT is_deleted;
SELECT 'nama siswa kembar (huruf/spasi diabaikan)', count(*) FROM (SELECT lower(regexp_replace(trim(nama), '\s+', ' ', 'g')) k FROM operations_siswa WHERE NOT is_deleted GROUP BY 1 HAVING count(*) > 1) x;
SELECT 'siswa tanpa kelompok', count(*) FROM operations_siswa WHERE NOT is_deleted AND kelompok_id IS NULL;
SELECT 'kelompok', k.id, j.kode, k.nama, count(s.id) FILTER (WHERE s.status = 'aktif') FROM operations_kelompok k JOIN operations_jenjang j ON j.id = k.jenjang_id LEFT JOIN operations_siswa s ON s.kelompok_id = k.id AND NOT s.is_deleted GROUP BY k.id, j.kode, k.nama ORDER BY j.kode, k.nama;
SELECT 'tagihan biaya masuk / bulanan', count(*) FILTER (WHERE jenis = 'BIAYA_MASUK'), count(*) FILTER (WHERE jenis = 'BULANAN') FROM operations_tagihan WHERE NOT is_deleted;
SELECT 'tagihan bulan ini sudah dibuat', count(*) FROM operations_tagihan WHERE NOT is_deleted AND jenis = 'BULANAN' AND periode_bulan = extract(month FROM current_date) AND periode_tahun = extract(year FROM current_date);
SELECT 'akun guru aktif', count(DISTINCT u.id) FROM accounts_user u JOIN accounts_user_groups ug ON ug.user_id = u.id JOIN auth_group g ON g.id = ug.group_id WHERE g.name = 'TeacherInCharge' AND u.is_active;
SELECT 'jurnal DRAFT/PENDING', count(*) FROM tr_jurnal WHERE status IN ('DRAFT', 'PENDING') AND NOT is_deleted;
SELECT 'periode', kode, tgl_mulai, tgl_selesai, status FROM ms_periode_akuntansi ORDER BY tgl_mulai;
SQL
```

Cara membaca hasilnya:

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| SHA backend/frontend | `23895b4…` (merge PR #22) | Produksi sudah berubah sejak 28/10 pagi. Hentikan dan periksa dulu. |
| Container | backend, caddy, db `Up`; db `healthy` | Jangan merge. Pulihkan layanan dulu. |
| Disk | Masih jauh dari penuh (28/10: 7%) | Deploy membuat dump dan image baru, jadi sediakan ruang. |
| migrasi operations terakhir | `0017_biaya_masuk_siswa` | Tidak sinkron dengan branch. Jangan merge. |
| kolom 0018 sudah ada | `0` | Ada perubahan skema manual. Periksa dulu. |
| siswa / aktif | Dicatat (28/10: 33 siswa) | Dipakai untuk pembanding sesudah rilis dan sesudah impor. |
| siswa aktif SPP 0 | Dicatat | Siswa ini ikut bertanda "Belum diisi" setelah rilis. |
| biodata terisi | Dicatat | Kolom yang sudah terisi bisa ditimpa isi spreadsheet saat impor (sel kosong tidak menghapus). |
| nama siswa kembar | `0` | Baris dengan nama kembar akan dilewati impor. Ubah lewat form satu per satu. |
| kelompok (id, jenjang, nama, siswa aktif) | Ada kelompok untuk 11 kelas di spreadsheet: 8 kelas TK (Bu Indri, Bu Desi, Bu Ita, Bu Mei, Bu Dini, Bu Cita, Bu Okta, Bu Latifah) dan PG Lebah 1, Lebah 2, Kepompong | Kelas yang belum punya kelompok dibuat dulu di menu Kelompok sebelum impor. Kalau tidak, siswa barunya tersimpan tanpa kelompok. Pada 22/10 produksi baru punya 7 kelompok. |
| tagihan bulan ini sudah dibuat | Dicatat | Siswa baru hasil impor tidak punya tagihan Oktober. Tagihan berikutnya memakai SPP yang diisi setelah impor. |
| akun guru aktif | ≥ 1 | Batch 4 menyembunyikan nominal dari role Guru. Tidak memblokir rilis. |
| jurnal DRAFT/PENDING | 7 (sama seperti 28/10) | Tidak terkait rilis. Tetap menghalangi tutup buku. |
| periode | 2026/2027 01/07/2026–30/06/2027 OPEN | Periksa sebelum rilis. |

### Hasil cek — 28 Oktober 2026 (web console, read-only)

| Cek | Hasil | Penilaian |
|---|---|---|
| SHA backend / frontend | `23895b4` / `23895b4`; log terakhir: Worker ter-deploy | Sesuai |
| Container | backend Up 2 jam, caddy Up 11 hari, db Up 11 hari (healthy) | Sesuai |
| Disk | 6,4 GB dari 96 GB (7%) | Cukup |
| Backup terakhir | `db-20261028T050005Z.dump` (248 KB, dari deploy 28/10) | Ada; masih hanya di VPS |
| Migrasi / kolom 0018 | `0017_biaya_masuk_siswa` / 0 | Sesuai |
| Siswa | 32, semuanya aktif; SPP 0: 0; nama kembar: 0; tanpa kelompok: 2 | Aman. Impor tidak akan bentrok nama. |
| Biodata terisi | tgl lahir 0, alamat 0, nama ayah 2, HP ayah 1, nama ibu 5, HP ibu 4 | Impor hampir hanya mengisi kolom kosong. |
| Kelompok | PG: Kepompong (3), Lebah 1 (10), Lebah 2 (10). TKA: Bu Desi (0), Bu Indri (7), Bu Ita (0), Bu Mei (0). | **Belum ada kelompok untuk Bu Dini, Bu Cita, Bu Okta, Bu Latifah.** Buat dulu sebelum impor. Tidak memblokir merge. |
| Tagihan | Bulanan 7 (bulan ini 3), Biaya masuk 0 | Tidak terkait rilis |
| Akun Guru aktif | 1 | Terdampak 3a (tanpa nominal); tidak memblokir |
| Jurnal DRAFT/PENDING | 7 | Sama seperti sebelumnya |
| Periode | 2026/2027, 01/07/2026–30/06/2027, OPEN | Sesuai |

Kesimpulan: tidak ada yang menghalangi backup dan merge. Sebelum impor biodata, buat 4 kelompok yang belum ada. Jenjangnya **TKB** (konfirmasi pengguna 28/10): `Bu Dini 26/27`, `Bu Cita 26/27`, `Bu Okta 26/27`, `Bu Latifah 26/27`.

## 2. Backup manual sebelum merge

Deploy sudah membuat dump sendiri. Backup bernama ini untuk titik pulih yang jelas sebelum rilis. Jalankan di web console:

```sh
cd /opt/beesmartfinance
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch45.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

Diharapkan: ukuran file mirip dump sebelumnya (28/10: ±248 KB) dan jumlah `TABLE DATA` sekitar 50. Kalau ukurannya 0 atau perintah gagal, jangan merge.

Hasil 28/10 17:34–17:35 UTC: `backups/db-20261028T173437Z-before-batch45.dump` dan `…T173528Z-before-batch45.dump` (blok dijalankan dua kali). Keduanya 249.159 byte dengan 50 `TABLE DATA`, isinya setara. Titik pulih rilis: `db-20261028T173437Z-before-batch45.dump`.

## 3. Rilis

1. Merge PR `codex/auto-deploy-fe-be` → `main` di GitHub. Hanya kamu yang melakukan ini, sebagai keputusan rilis.
2. Tunggu poller (maks. 5 menit + build ±3 menit). Pantau di web console:
   ```sh
   tail -f /home/deploy/.local/state/beesmartfinance/deploy.log
   ```
   Selesai bila ada baris `Deploy backend <sha>` lalu `Deploy frontend <sha>`, dan `backend_sha`/`frontend_sha` sama dengan SHA merge. Ctrl+C untuk berhenti memantau.
3. Cek pasca-rilis:
   - Read-only dari web console: jalankan ulang blok di bagian 1. Yang diharapkan berubah hanya:
     - migrasi menjadi `0018_siswa_data_diri`
     - kolom 0018 menjadi `3`
     - ada backup `db-…Z.dump` baru dari deploy
     Jumlah siswa, tagihan, dan jurnal harus sama dengan sebelum rilis.
   - Dari luar (bisa Claude jalankan):
     - `/login` 200
     - API tanpa token 401
     - schema berisi `/api/v1/siswa/impor-biodata/`
     - bundle Worker berisi "Impor biodata"
4. Smoke test per role (kamu yang login):
   - **Staf TU:** Data siswa tampil; form siswa berisi Nama panggilan, Jenis kelamin, Tempat/Tanggal lahir, dan usia muncul setelah tanggal diisi; klik nama kelompok di menu Kelompok membuka daftar siswanya.
   - **Guru:** Absensi Siswa tetap jalan.
   - **Keuangan:** Data siswa masih menampilkan SPP dan biaya masuk.
   - **Kepsek:** Beranda normal.

### Hasil rilis — 28 Oktober 2026

- PR #23 di-merge ke `main` pukul 17:37 UTC (`0f0bebc`), atas keputusan rilis pengguna, setelah cek read-only dan backup `before-batch45`.
- Backend baru aktif ±17:41 UTC: schema produksi memuat `/api/v1/siswa/impor-biodata/`.
- Worker berganti ke bundle `index-B5KPjw6I.js` ±17:42 UTC (sebelumnya `index-BO5I_TBs.js`). Bundle memuat "Impor biodata", "Nama panggilan", "Belum diisi", "Lihat siswa", dan path `impor-biodata`.
- Cek dari luar: `/login` 200; API tanpa token 401 lewat Worker dan origin.
- Cek read-only pasca-rilis (web console, ±17:58 UTC):
  - SHA backend dan frontend `0f0bebc`
  - backend Up 20 menit, db healthy, disk 8%
  - dump deploy `db-20261028T174003Z.dump` (249.159 byte)
  - migrasi `0018_siswa_data_diri`, kolom 0018 = 3
  - 32 siswa aktif, SPP 0 = 0, biodata terisi sama seperti sebelum rilis
  - 7 kelompok, 7 tagihan bulanan, 7 jurnal DRAFT/PENDING, periode 2026/2027 OPEN

  Tidak ada data yang berubah.
- Log poller sempat mencatat `curl: (22) … 502` sebelum `Deploy frontend`. Itu dari cek schema saat backend baru restart; curl mengulang (`--retry 10`) sampai berhasil, karena `backend_sha` tersimpan dan tahap frontend berjalan. Tidak perlu tindakan.
- Belum: smoke test per role oleh pengguna.

## 4. Impor biodata (setelah rilis, oleh Staf TU)

1. Buat backup lagi persis sebelum impor (blok bagian 2, ganti akhiran `before-batch45` menjadi `before-impor-biodata`).
2. Pastikan semua kelompok untuk 11 kelas sudah ada. Staf TU membuat 4 kelompok TKB di menu Kelompok → Tambah kelompok: Bu Dini 26/27, Bu Cita 26/27, Bu Okta 26/27, Bu Latifah 26/27. Saran pemetaan di pratinjau impor otomatis mengenali nama ini.
3. Di Google Sheets, buka tab biodata → File → Download → Comma-separated values (.csv).
4. Login sebagai Staf TU → Data siswa → **Impor biodata** → pilih CSV. Periksa pratinjau sebelum menyimpan:
   - Total siswa baru + diperbarui + sudah sama + bermasalah = **104** (hasil pratinjau lokal 28/10). Kalau jauh berbeda, berhenti.
   - Tiap kelas terpasang ke kelompok yang benar. Kelas TK masuk ke kelompok TKA/TKB yang sesuai gurunya; Lebah 1, Lebah 2, Kepompong masuk ke PG.
   - "Diperbarui": sekitar 33 siswa lama. Cek beberapa perubahan alamat dan HP. Nama lama tidak diubah.
   - "Bermasalah": harusnya 0. Ada 2 nomor HP bertanda "perlu dicek" yang bisa diperbaiki manual sesudahnya.
5. Tekan **Simpan**, lalu catat ringkasan di toast.
6. Cek read-only setelah impor:
   ```sh
   cd /opt/beesmartfinance
   docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
     sh -c 'psql -U beesmartfinance -d db_lebah_madu -At' <<'SQL'
   SET default_transaction_read_only = on;
   SELECT 'siswa / aktif / SPP 0', count(*), count(*) FILTER (WHERE status = 'aktif'), count(*) FILTER (WHERE status = 'aktif' AND spp_nominal <= 0) FROM operations_siswa WHERE NOT is_deleted;
   SELECT 'riwayat impor (dibuat / diubah)', count(*) FILTER (WHERE history_type = '+'), count(*) FILTER (WHERE history_type = '~') FROM operations_historicalsiswa WHERE history_change_reason = 'Impor biodata CSV';
   SELECT 'tanpa kelompok', count(*) FROM operations_siswa WHERE NOT is_deleted AND kelompok_id IS NULL;
   SELECT 'tagihan / jurnal (harus sama)', (SELECT count(*) FROM operations_tagihan WHERE NOT is_deleted), (SELECT count(*) FROM tr_jurnal WHERE NOT is_deleted);
   SQL
   ```
7. Isi SPP semua siswa bertanda **Belum diisi** sebelum tagihan November dibuat.
8. Ubah akses spreadsheet biodata menjadi **Dibatasi**.

## Rollback

- **Kode:**
  1. Revert merge commit di `main` lalu push. Poller men-deploy ulang dan membuat dump baru lebih dulu.
  2. Sebelum revert, jalankan di VPS:
     `docker compose --env-file .env.vps -f docker-compose.production.yml run --rm backend python manage.py migrate operations 0017`
     Isi nama panggilan, jenis kelamin, dan tempat lahir hilang; data lain tidak tersentuh.
- **Impor:** `pg_restore` dari dump `before-impor-biodata`. Perubahan lain sesudah impor (penerimaan, absensi) ikut hilang, jadi lakukan segera kalau hasil impor salah. Alternatifnya, hapus siswa baru yang salah lewat menu Data siswa satu per satu.
- **Total:** `pg_restore` dari dump `before-batch45`.

## Keputusan sebelum merge

1. Hasil cek bagian 1 sudah ditempel dan diterima.
2. Backup bagian 2 berhasil.
3. Merge lewat PR, bukan push langsung ke `main`.
