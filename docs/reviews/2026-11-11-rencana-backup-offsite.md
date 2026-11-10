# Rencana backup harian ke luar VPS — 11 November 2026

Status: **rencana, belum dipasang**. Dokumen publik: tanpa kunci, token, ID akun, atau isi data.

## Kondisi sekarang

- Dump database hanya dibuat saat deploy (`scripts/deploy_vps.sh`) dan saat backup bernama dijalankan manual. **Tidak ada backup harian**, bahkan di VPS.
- Semua dump (34 per 10/11, ±7,5 MB) ada di `/opt/beesmartfinance/backups/` pada disk VPS yang sama dengan database. Kalau VPS hilang atau disk rusak, backup ikut hilang.
- Mulai cut-over Januari, data harian sekolah hanya ada di sistem.

## Desain

| Bagian | Pilihan | Alasan |
|---|---|---|
| Jadwal | Setiap hari 02.00 WIB (19.00 UTC), cron root di VPS | Di luar jam kerja sekolah; tidak bentrok dengan poller deploy |
| Isi | `pg_dump -Fc` database produksi, dicek minimal 50 `TABLE DATA` sebelum diunggah | Dump kosong atau terpotong tidak dianggap berhasil |
| Enkripsi | `age` dengan kunci publik di VPS; kunci privat hanya di Mac pengguna (+ salinan di pengelola password) | Kalau bucket atau token bocor, isinya tetap tidak terbaca |
| Tujuan | Cloudflare R2, bucket khusus backup, prefix `db/` | Vendor yang sama dengan Worker; ±0,3 MB/hari jauh di bawah kuota gratis 10 GB |
| Akses | Token R2 khusus bucket itu, izin Object Read & Write saja | Token di VPS tidak bisa menyentuh Worker atau bucket lain |
| Retensi R2 | Aturan lifecycle bucket: hapus objek `db/` setelah 30 hari | Dikelola Cloudflare, bukan skrip |
| Retensi lokal | Dump harian di `backups/daily/` disimpan 14 hari; dump deploy dan backup bernama tidak disentuh | Pemulihan cepat tanpa unduh |
| Verifikasi unggah | Ukuran objek di R2 harus sama dengan file lokal | Unggah setengah jadi dianggap gagal |
| Pemantauan | Log `/var/log/beesmartfinance-backup.log` dan file `backups/daily/last_success`; dicek di blok read-only rilis | Sederhana dulu; notifikasi otomatis bisa menyusul |

Skrip: [`scripts/backup_offsite.sh`](../../scripts/backup_offsite.sh). Dipasang manual di VPS, tidak lewat poller (poller hanya menyalin `scripts/deploy_vps.sh`), jadi tidak butuh rilis ke `main`. Diuji di Mac dengan tiruan `docker`/`age`/`rclone`: alur sukses, dump kurang tabel, dan ukuran R2 beda semuanya berperilaku benar; file sementara terhapus saat gagal.

## Langkah pemasangan

| # | Siapa | Di mana | Langkah | Menulis? |
|---|---|---|---|---|
| 1 | Pengguna | Mac | `brew install age`, lalu `age-keygen -o ~/.config/beesmartfinance/backup-age.key`; simpan salinan kunci privat di pengelola password; kirim **kunci publik** (`age1…`) ke Claude | Lokal |
| 2 | Pengguna | Dashboard Cloudflare → R2 | Buat bucket `beesmartfinance-backup` (tanpa akses publik); tambah lifecycle "hapus setelah 30 hari" untuk prefix `db/`; buat API token R2 khusus bucket itu (Object Read & Write). Catat Access Key ID, Secret, dan endpoint S3 | Akun Cloudflare |
| 3 | Pengguna | hPanel console | `apt-get install -y age rclone`; tulis `/etc/beesmartfinance/backup.env` (0600) berisi kunci publik, remote, dan kredensial R2. Kredensial diketik pengguna, tidak lewat chat | VPS |
| 4 | Pengguna | hPanel console | Salin `scripts/backup_offsite.sh` ke `/opt/beesmartfinance/scripts/`; jalankan sekali manual; harus keluar baris `OK …` | VPS + R2 |
| 5 | Pengguna | hPanel console | Pasang `/etc/cron.d/beesmartfinance-backup`: `0 19 * * * root /opt/beesmartfinance/scripts/backup_offsite.sh >> /var/log/beesmartfinance-backup.log 2>&1` | VPS |
| 6 | Pengguna + Claude | Mac | **Uji pulih:** unduh satu objek dari R2, `age -d -i <kunci> …`, lalu `pg_restore --list` (harus 53 `TABLE DATA`) dan restore penuh ke DB sementara lokal yang langsung dihapus setelah hitungan dicocokkan dengan blok read-only produksi | Lokal, sementara |
| 7 | Claude | Repo | Catat hasil di dokumen ini dan handoff; tambah baris `last_success` ke blok cek read-only rilis | Repo |

Claude menyiapkan blok perintah lengkap untuk langkah 3–5 di chat saat pemasangan.

## Rollback

- Hentikan: hapus `/etc/cron.d/beesmartfinance-backup`.
- Cabut akses: hapus token R2 di dashboard (bucket tetap ada sampai dihapus).
- Hapus total: hapus bucket, `/etc/beesmartfinance/backup.env`, dan folder `backups/daily/`.
- Tidak ada perubahan pada database, aplikasi, atau poller deploy.

## Risiko yang tersisa

- Kunci privat age hilang = backup di R2 tidak bisa dibuka. Mitigasi: salinan di pengelola password, uji pulih di langkah 6.
- Kegagalan harian hanya tercatat di log, tanpa notifikasi. Mitigasi: `last_success` dicek di setiap blok read-only; notifikasi (mis. email cron atau ping ke layanan pemantau) bisa ditambah kemudian.
