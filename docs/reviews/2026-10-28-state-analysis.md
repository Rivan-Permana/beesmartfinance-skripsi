# State analysis BeeSmart Finance — 28 Oktober 2026 (sore, setelah rilis Batch 1–3)

Menggantikan versi pagi dokumen ini (snapshot setelah rilis revamp PR #21) dan [state analysis 21 Oktober](./2026-10-21-state-analysis.md). Ini snapshot setelah **rilis kedua hari ini: revisi spreadsheet Batch 1–3 (PR #22)**. Bukti rinci ada di [revisi spreadsheet](./2026-10-28-revisi-spreadsheet.md); di sini dibedakan antara yang terbukti, yang hanya diimplementasikan, dan yang masih terbuka. Proyek tidak lagi terikat skripsi.

## Keadaan saat sesi dihentikan

- **Produksi = `main` `23895b4`** (merge PR #22, 04:59 UTC). Deploy otomatis selesai:
  - backup `backups/db-20261028T050005Z.dump`
  - migrasi `operations.0016_pegawai_status` dan `0017_biaya_masuk_siswa` (05:00:22 UTC)
  - backend aktif 05:00:54 UTC; Worker Cloudflare bundle `index-BO5I_TBs.js` aktif 05:01:55 UTC
- **Sebelum rilis, data periode produksi dikoreksi** (disetujui pengguna, dijalankan pengguna lewat web console): `ms_periode_akuntansi id=1` 2026/2027 dari 30/06/2026–29/06/2027 menjadi **01/07/2026–30/06/2027**. Backup `backups/db-20261028T045714Z-before-periode-fix.dump`. Penyebab: form periode versi lama mengirim tanggal lewat konversi UTC; form sekarang memakai `formatLocalDate`. Tidak ada data yang pindah periode.
- **Branch kerja `codex/auto-deploy-fe-be`** sudah di-merge ke `main` dan `origin/main` sudah di-merge balik (`43926cb`). Belum di produksi: perbaikan 400 `siswa/biaya-masuk-default` **Batch 4** (masukan WA Staf TU + keputusan review 3a/3b, migrasi `operations.0018_siswa_data_diri`; rincian di [revisi spreadsheet](./2026-10-28-revisi-spreadsheet.md#batch-4--masukan-wa-staf-tu--keputusan-review-tier-3--selesai-di-branch-kerja)). Juga **Batch 5** (impor biodata siswa dari CSV, usia otomatis, tanpa migrasi). Rilis berikutnya menjalankan `0018`; setelah rilis, impor biodata produksi dilakukan Staf TU dari aplikasi (backup dulu). Jalankan `git fetch && git merge origin/main` sebelum pekerjaan baru.
- **Untracked:** ~200 path sengaja tidak di-commit (gambar audit, PDF, katalog agen, `.claude/` termasuk `launch.json` dengan konfigurasi `backend-uat`/`frontend-uat`, `scripts/uat_walkthrough.py` berisi password demo, folder cache `.vite/` di root). Jangan `git clean`.
- **Stash di `main`:** `stash@{0}` "periode close-by-kepsek + jurnal Rincian" dibiarkan; kemungkinan bentrok bila di-pop.
- **Server lokal:** Django `127.0.0.1:8000` + Vite `localhost:5173` dari `.claude/launch.json` (aplikasi desktop kadang mematikannya di akhir giliran; nyalakan lagi dengan preview `backend`/`frontend`). UAT (:8001/:5175) mati.
- **Database:**
  - Lokal `db_lebah_madu`: di `0018` (backup `…before-0018`), periode 2026/2027 sudah dikoreksi. Backup sebelum tiap perubahan ada di `~/Backups/beesmartfinance/` (`…before-0016`, `…before-0017`, `…before-periode-fix`).
  - UAT `bee_uat_browser_20261020`: di `0018` (0017 dan 0018 masing-masing diterapkan, dibalik, diterapkan ulang). Tidak punya periode 2026/2027, hanya dua periode uji CLOSED. Data uji: `UAT-`, `KW-`, `GJ-…-R1`, `UAT-B2` (kegiatan, jurnal, kasbon, slip November), `UAT-B3` (siswa Bima Sakti: tagihan biaya masuk dengan diskon SIB, tiga penerimaan, satu masih jurnal DRAFT; tagihan bulanan Oktober 2026).
- **Akses VPS:**
  - SSH `root@187.77.126.25` dengan `~/.ssh/beesmartfinance_hostinger`, host key `SHA256:1e+IUd0Yb5upPGxv4u/Pe7R7MiErTTmV4Wn4LiYmVdw`, wajib VPN.
  - **Sejak ~10:30 WIB SSH timeout** dari WARP (egress `104.28.245.124`, colo SIN): port 22 dan 443 ke IPv4 VPS sama-sama timeout. VPS tidak memblokir (fail2ban kosong, iptables/nft tanpa IP itu, ufw inactive; firewall dan anti-DDoS Hostinger kosong). IPv4 lain lewat WARP normal. Situs produksi menjawab lewat IPv6.
  - Jalur cadangan yang terbukti: **pengguna menjalankan perintah di web console hPanel** (VPS → Web console) lalu menempelkan hasilnya. Query read-only wajib diawali `SET default_transaction_read_only = on;`.
  - Saran yang belum dicoba: ganti mode WARP ke MASQUE.

## Yang sudah dibangun dan dibuktikan

| Area | State | Bukti |
|---|---|---|
| Revamp UI empat role (PR #21) | Produksi sejak 28/10 pagi | Audit visual Admin TU/Keuangan, audit alur tulis 22/10, checklist rilis |
| Batch 1: Beranda Hari/Bulan/Periode + KPI berwarna dan bisa diklik, unduh Excel absensi pegawai, menu katering bulanan, Ubah/Hapus pendaftaran, jabatan otomatis di slip | Produksi (PR #22) | Tes backend periode lintas tahun/hari/param salah; cek DOM desktop dan 375 px; xlsx divalidasi openpyxl |
| Batch 2: akses role per spreadsheet, kasbon diajukan Kepsek dan dicairkan Keuangan, Anggaran Kegiatan + Guru PJ dikelola Keuangan, draf jurnal Staf TU, status pegawai Aktif/Cuti/Non-aktif (`0016`) | Produksi | `operations/test_role_access.py`; 27 skenario API UAT; cek DOM per role; pasca-rilis: 33 aktif + 1 nonaktif |
| Batch 3: biaya masuk siswa (Uang Masuk/Pengembangan/Kegiatan/Seragam), diskon PG/SIPG/SIB/SIKBR netto, tagihan jenis Biaya masuk, penerimaan sebagian dari daftar siswa (`0017`) | Produksi | `operations/test_biaya_masuk.py` (7 tes); 13 skenario API UAT; penerimaan sebagian lewat UI; cek DOM desktop dan 375 px; pasca-rilis: 7 tagihan Bulanan |
| Koreksi periode 2026/2027 | Produksi, lokal (UAT tidak perlu) | Cek dampak read-only (jurnal 28/09–03/11/2026, 2 tertaut periode, tanpa saldo awal); `UPDATE 1` di produksi |
| Pasca-rilis | Terverifikasi dari luar dan dari DB | Publik: `/login` 200, API 401 tanpa token, endpoint baru di schema, bundle baru berisi "Anggaran Kegiatan". DB (web console, read-only): migrasi 0016/0017, 18 jurnal dan 33 siswa sama seperti sebelum rilis, container running |
| Tes terakhir | Backend 146 OK; frontend 33 berkas / 141 tes; `vue-tsc` + build bersih; `makemigrations --check` bersih | Dijalankan 28/10 setelah perubahan kode terakhir |

## Review mendalam pekerjaan terakhir (28/10 sore)

Diperiksa ulang: model/migrasi `0016`–`0017`, service `operations/services/biaya_masuk.py`, `tp_templates._already_billed`, cek duplikat `generate_tagihan`, `SiswaSerializer`, izin per role, UI Data Siswa/Tagihan. Hasil:

1. **Diperbaiki (belum di produksi):** `GET /siswa/biaya-masuk-default/?kelompok=abc` menghasilkan 500. Kini 400 dengan pesan; ada tes regresi. Frontend selalu mengirim id angka, jadi dampak produksi kecil.
2. **Terkonfirmasi aman:** tagihan manual ganda untuk siswa/bulan yang sama tetap ditolak 400 walau `unique_together` diganti constraint bersyarat (`is_deleted=False`); efek sampingnya, tagihan yang sudah dibatalkan kini bisa dibuat ulang untuk periode yang sama (sebelumnya IntegrityError).
3. **Terkonfirmasi aman:** menu Tagihan menyembunyikan Ubah/Batalkan untuk tagihan Biaya masuk; API juga menolak ubah. Total tagihan tidak bisa turun di bawah yang sudah dibayar karena komponen berpenerimaan terkunci.
4. **Catatan desain** (keputusan 28/10 sore: Guru tidak lagi menerima nominal dan pesan diskon diperjelas di Batch 4; laporan diskon per kategori dan biaya masuk kedua ditunda):
   - Guru bisa membaca `GET /siswa/` (dipakai absensi), sehingga ikut menerima nominal SPP, biaya masuk, dan diskon. Sudah begitu untuk SPP sebelum Batch 3.
   - Mengubah diskon setelah ada penerimaan menghasilkan pesan "Uang Masuk sudah ada penerimaan…", bukan pesan tentang diskon. Benar secara aturan, kurang jelas bagi pengguna.
   - Satu siswa hanya punya satu tagihan Biaya masuk. Daftar ulang tahun berikutnya tetap lewat tagihan Juli dari daftar harga; belum ada UI untuk biaya masuk kedua.
   - Diskon dicatat netto. Belum ada laporan total diskon per kategori (PG/SIPG/SIB/SIKBR); kategori hanya tersimpan di siswa dan keterangan baris tagihan.

## Belum dibuktikan atau masih terbuka

1. **Smoke test produksi dengan akun asli belum dilakukan** (Batch 1–3 dan revamp). Pengguna yang login; password produksi tidak lewat chat. Brief untuk pengguna sekolah sudah disiapkan di chat, belum dikirim sampai smoke test selesai.
2. **Backup ke luar VPS belum ada.** Semua backup di `/opt/beesmartfinance/backups/`. Kartu sesi terpisah "Off-site daily backup for production DB" sudah diusulkan (rencana dulu).
3. **SSH dari WARP timeout lewat IPv4** (lihat Akses VPS).
4. **7 jurnal DRAFT/PENDING di produksi** (AUTO_BILLING 2 DRAFT + 1 PENDING, AUTO_PENDAFTARAN 2 DRAFT, AUTO_KEGIATAN 2 PENDING). Tutup buku 2026/2027 akan ditolak sampai diselesaikan; keputusan operasional pengguna.
5. **Void jurnal pencairan kasbon POSTED tidak membuka kasbon** (disengaja; perlu aturan bisnis).
6. **VPS: 12 update Ubuntu tertunda** (terlihat saat login web console). Jadwalkan terpisah, mungkin butuh restart.
7. **Teknis kecil:** bundle frontend utama >500 kB; peringatan drf-spectacular `TarifKateringView` dan enum `status` di schema; poller VPS bergantung pada koneksi GitHub yang pernah putus-sambung.
8. **Belum diuji:** Safari/iPad, pembaca layar, zoom 200%, printer fisik, tampilan Tunggakan/Laporan untuk tagihan Biaya masuk di browser (di API diperlakukan seperti tagihan biasa).
9. **Batch 4–5 dirilis 28/10 17:37 UTC** (PR #23, `main` `0f0bebc`; backup `db-20261028T173437Z-before-batch45.dump`). Backend dan Worker baru aktif; cek read-only pasca-rilis bersih (migrasi `0018`, data tidak berubah); smoke test empat role di produksi lulus. Sebelum impor: buat kelompok TKB Bu Dini/Bu Cita/Bu Okta/Bu Latifah 26/27 ([checklist rilis](./2026-10-28-release-checklist-batch-4-5.md): cek read-only web console, backup, merge, impor); setelah rilis: backup DB, impor biodata (104 siswa terbaca di pratinjau), isi SPP siswa baru sebelum tagihan November, lalu ubah akses spreadsheet biodata menjadi Dibatasi (saat ini siapa pun dengan link bisa membukanya); konfirmasi ke sekolah: apakah katering perlu tarif per anak (jemputan sudah per anak), dan minta Staf TU memuat ulang halaman (Ctrl+Shift+R) karena screenshot WA masih dari versi lama.
10. **Spreadsheet:** baris "Ya, dijemput" → "Ya" dianggap selesai karena teks itu tidak ada di versi sekarang; dibuka lagi hanya bila sekolah masih melihatnya.

## Batas wajib untuk sesi berikutnya

- `main` = produksi. Merge/push ke `main`, `npm run deploy`, dan skrip deploy hanya dengan keputusan rilis eksplisit dari pengguna, setelah cek read-only produksi dan backup.
- Mutasi percobaan hanya di DB UAT `bee_uat_browser_20261020` lewat API terpisah (preview `backend-uat` :8001 dan `frontend-uat` :5175 di `.claude/launch.json`). `db_lebah_madu` lokal dan produksi tidak dimutasi tanpa izin, selalu backup dulu.
- Tier 3 (skema, buku besar, uang, izin, penghapusan data) diajukan sebagai rencana singkat (target, data terdampak, rollback) lalu menunggu persetujuan.
- Jurnal POSTED dilindungi trigger DB; koreksi lewat reversal. Pemisahan tugas: Keuangan tidak membayar tagihan; Kepsek menyetujui/menolak PENDING.
- Batas login 5/menit per IP: buat token sekali per role (untuk UAT bisa lewat `RefreshToken.for_user` di shell), pakai ulang.
- Commit dan push ke `codex/auto-deploy-fe-be` setelah tes lulus, identitas git pengguna, tanpa trailer atau atribusi agen.

## Titik lanjut paling tepat

1. `git fetch && git merge origin/main` di branch kerja; nyalakan server lokal bila perlu.
2. Tunggu hasil smoke test produksi dari pengguna; perbaiki temuan sebagai batch kecil.
3. Usulan prioritas: backup ke luar VPS → keputusan atas catatan desain review (Guru membaca nominal, pesan diskon, laporan diskon) → penyelesaian 7 jurnal tertunda sebelum tutup buku → aturan void pencairan kasbon → update OS VPS → optimasi bundle dan peringatan schema.
