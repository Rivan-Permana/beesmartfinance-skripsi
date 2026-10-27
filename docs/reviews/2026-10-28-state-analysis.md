# State analysis BeeSmart Finance — 28 Oktober 2026

Menggantikan [state analysis 21 Oktober](./2026-10-21-state-analysis.md). Ini snapshot setelah revamp UI, audit visual, audit alur tulis, keputusan lanjutan 1–5, dan **rilis produksi pertama hasil revamp**. Bukti rinci ada di dokumen yang ditautkan; di sini dibedakan antara yang sudah terbukti, yang hanya diimplementasikan, dan yang belum dikerjakan.

## Keadaan saat sesi dihentikan

- **Produksi sudah memakai versi revamp.** PR #21 di-merge ke `main` sebagai `cec1df7` pada 28/10/2026, dan poller VPS men-deploy otomatis:
  - backup `backups/db-20261027T210503Z.dump`
  - migrasi `operations.0014`/`0015`
  - backend dibangun ulang
  - Worker Cloudflare versi `f8f52c07`
- **Branch kerja `codex/auto-deploy-fe-be`** HEAD `f4de8d1` (sudah di-push). Branch ini unggul 1 commit dokumen dari `main`, dan `main` unggul 1 merge commit (`cec1df7`). Isi kodenya sama. Jalankan `git merge origin/main` di branch sebelum pekerjaan baru supaya PR berikutnya bersih.
- **Tracked changes:** 0. Ada 199 path untracked (gambar audit, PDF, katalog agen, `.claude/`, `scripts/uat_walkthrough.py` yang memuat password demo). Sengaja tidak di-commit; jangan `git clean`.
- **Stash di `main`:** `stash@{0}` "periode close-by-kepsek + jurnal Rincian" dibiarkan atas keputusan pengguna. Stash ini menyentuh area tutup buku yang sudah berubah, jadi kemungkinan besar bentrok bila di-pop.
- **Server lokal yang masih hidup:** Django `127.0.0.1:8000` dan Vite `localhost:5173`, keduanya dijalankan dari `.claude/launch.json`. Server UAT (:8001/:5175) sudah dimatikan.
- **Database:**
  - Demo lokal `db_lebah_madu`: sudah `0015`, dimigrasi 28/10 atas persetujuan pengguna, dengan backup `~/Backups/beesmartfinance/db_lebah_madu-20261028-033824-before-migrate-0014-0015.dump`.
  - UAT `bee_uat_browser_20261020`: sudah `0015`, dan berisi data uji `UAT-`, `KW-`, `GJ-…-R1` serta dua periode CLOSED.
- **Akses VPS:** host key `SHA256:1e+IUd0Yb5upPGxv4u/Pe7R7MiErTTmV4Wn4LiYmVdw` sudah diverifikasi pengguna dan tersimpan di `known_hosts`. Login memakai `~/.ssh/beesmartfinance_hostinger` sebagai `root@187.77.126.25`, dan **wajib VPN**. Koneksi SSH dan koneksi VPS ke GitHub putus-sambung; ulangi bila timeout.

## Yang sudah dibangun dan dibuktikan

| Area | State | Bukti |
|---|---|---|
| Revamp UI empat role | Ter-deploy di produksi | [Sistem desain](../design-system.md), [audit Admin TU](./2026-10-22-audit-visual-admin-tu.md), [audit Keuangan/Kepsek/Guru](./2026-10-22-audit-visual-keuangan.md) |
| Alur tulis (jurnal, tagihan, gaji, kasbon, pendaftaran, tutup buku, cetak, tampilan error) | Diaudit di DB UAT; 7 temuan diperbaiki | [Audit alur tulis](./2026-10-22-audit-alur-tulis.md): 66/68 langkah API lulus; dua sisanya menjadi keputusan 1–2 |
| Keputusan 1: potongan gaji hanya dari kasbon yang sudah cair (`is_legacy`, migrasi `0014`) | Selesai, ter-deploy | Tes backend dan skenario UAT C2 |
| Keputusan 2: saldo kasbon berkurang saat jurnal gaji disetujui, kembali saat void (`PotonganKasbonGaji`, migrasi `0015`) | Selesai, ter-deploy | Tes approve/void/saldo kurang; skenario UAT slip #6 |
| Keputusan 3: Kepala Sekolah bisa menolak jurnal PENDING (`POST /jurnal/{id}/tolak/`) | Selesai, ter-deploy | Tes API; alur UI di UAT; endpoint terlihat di schema produksi |
| Keputusan 4: kwitansi cetak per pembayaran tagihan | Selesai, ter-deploy | Tes komponen; tampilan cetak diukur lewat DOM di UAT |
| Keputusan 5: slip gaji terbuka lagi setelah void/batal draf; nomor bukti `-R1` | Selesai, ter-deploy | Tes service/API; skenario UAT slip #7 |
| Rilis produksi | Selesai 28/10 | [Checklist rilis](./2026-10-22-release-checklist.md): cek read-only 22/10 dan 28/10, lalu verifikasi pasca-deploy (login 200, endpoint baru ada, container berjalan, data utuh: 18 jurnal, 2 kasbon, 1 slip) |
| Tes terakhir | Backend 127 OK; frontend 32 berkas / 132 tes; `vue-tsc` + build bersih | Dijalankan 22/10 setelah commit terakhir yang mengubah kode |

## Revisi dari spreadsheet pengguna (28/10, setelah rilis)

Pengguna mengirim 37 baris revisi per role. Batch 1 (Beranda filter Hari/Bulan/Periode + tampilan berwarna, Absensi Pegawai urut abjad + unduh Excel, Katering menu bulanan, aksi Ubah/Hapus Pendaftaran, jabatan otomatis di slip gaji) selesai di branch kerja, belum di produksi. Batch 2 (akses role, kasbon, pengeluaran tanpa approval, status Cuti) dan Batch 3 (diskon dan komponen biaya siswa) menunggu keputusan. Rincian: [revisi spreadsheet](./2026-10-28-revisi-spreadsheet.md). Proyek tidak lagi terikat skripsi.

## Belum dibuktikan atau masih terbuka

1. **Smoke test produksi dengan akun asli belum dilakukan.** Verifikasi pasca-deploy hanya lewat HTTP status, schema, dan DB. Alur nyata (login tiap role, approve/tolak, bayar dan cetak kwitansi, slip gaji) belum dicoba di web online. Password produksi hanya ada di VPS (`/root/beesmartfinance-demo-accounts.json`) dan tidak boleh lewat chat.
2. **Void jurnal pencairan kasbon yang sudah POSTED** tidak membuka kasbonnya. Ini disengaja, karena sebagian kasbon mungkin sudah terpotong gaji; perlu aturan bisnis sebelum diubah.
3. **Ada 7 jurnal DRAFT/PENDING di produksi** (tagihan 3, pendaftaran 2, kegiatan 2; Sep–Okt 2026). Tutup buku 2026/2027 akan ditolak sampai jurnal-jurnal ini dicatat, disetujui, atau dibatalkan. Menyelesaikannya adalah keputusan operasional pengguna, bukan perbaikan kode.
4. **Backup harian ke luar VPS belum ada.** Backup saat ini hanya `pg_dump` per deploy, disimpan di VPS yang sama.
5. **Koneksi VPS ke GitHub tidak stabil.** Poller sempat gagal fetch berkali-kali (timeout :443) sebelum berhasil, sehingga rilis bisa tertunda tanpa notifikasi.
6. **Bundle frontend utama >500 kB** (warning Vite) belum dioptimasi.
7. **Peringatan drf-spectacular** `TarifKateringView: unable to guess serializer` muncul setiap schema dibangun. Tidak berdampak ke runtime, tapi mencemari log.
8. **Dokumen setelah rilis** (`f4de8d1` dan dokumen ini) baru ada di branch kerja; akan masuk `main` lewat PR berikutnya. Setiap push ke `main` memicu deploy.
9. **Belum diuji:** Safari/iPad, pembaca layar, zoom 200%, dan printer fisik. Pengujian cetak dilakukan lewat emulasi `print`.

## Batas wajib untuk sesi berikutnya

- `main` = produksi. Merge atau push ke `main`, `npm run deploy`, dan skrip deploy hanya boleh dengan keputusan rilis eksplisit dari pengguna, setelah cek read-only produksi dan backup.
- Mutasi percobaan hanya di DB UAT `bee_uat_browser_20261020` lewat API terpisah, dengan `DB_NAME=… runserver 127.0.0.1:8001` dan Vite `API_PROXY_TARGET=http://127.0.0.1:8001 npx vite --port 5175`. `db_lebah_madu` lokal dan produksi tidak dimutasi tanpa izin.
- Perubahan skema atau buku besar (tier 3) diajukan sebagai rencana singkat dulu (target, data, rollback) dan baru dikerjakan setelah disetujui.
- Trigger DB melindungi jurnal POSTED; koreksi selalu lewat reversal.
- Batas login 5/menit per IP. Commit dan push ke branch kerja setelah tes lulus, tanpa trailer agen.

## Titik lanjut paling tepat

1. Sinkronkan branch dengan `origin/main`, lalu nyalakan lingkungan yang dibutuhkan.
2. Smoke test produksi read-only per role. Pengguna yang login dengan akun asli, atau pengguna menyediakan akses yang aman.
3. Pilih revisi berikutnya dari daftar terbuka. Usulan prioritas: backup harian di luar VPS, ketahanan poller (retry/notifikasi), aturan void pencairan kasbon, optimasi bundle, lalu peringatan schema.
