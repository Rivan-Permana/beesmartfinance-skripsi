# Rencana backup harian ke luar VPS — 11 November 2026

Status: **rencana lengkap, belum dipasang; dipasang bersama rilis berikutnya**. Dokumen publik: tanpa kunci, token, ID akun, atau isi data.

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
| 4 | Pengguna | hPanel console | Setelah rilis, ambil `scripts/backup_offsite.sh` dari salinan repo poller ke `/opt/beesmartfinance/scripts/`; jalankan sekali manual; harus keluar baris `OK …` | VPS + R2 |
| 5 | Pengguna | hPanel console | Pasang `/etc/cron.d/beesmartfinance-backup`: `0 19 * * * root /opt/beesmartfinance/scripts/backup_offsite.sh >> /var/log/beesmartfinance-backup.log 2>&1` | VPS |
| 6 | Pengguna + Claude | Mac | **Uji pulih:** unduh satu objek dari R2, `age -d -i <kunci> …`, lalu `pg_restore --list` (harus 53 `TABLE DATA`) dan restore penuh ke DB sementara lokal yang langsung dihapus setelah hitungan dicocokkan dengan blok read-only produksi | Lokal, sementara |
| 7 | Claude | Repo | Catat hasil di dokumen ini dan handoff; tambah baris `last_success` ke blok cek read-only rilis | Repo |

Waktu pemasangan: bersama rilis berikutnya (keputusan pengguna 11/11), karena skrip diambil dari `main` di VPS. Blok perintah lengkap ada di lampiran.

## Lampiran: blok perintah

Nilai bertanda `<…>` diisi pengguna di tempat; jangan ditempel ke chat atau repo.

### Langkah 1 — Mac (kunci age)

```sh
brew install age
mkdir -p ~/.config/beesmartfinance && chmod 700 ~/.config/beesmartfinance
age-keygen -o ~/.config/beesmartfinance/backup-age.key
chmod 600 ~/.config/beesmartfinance/backup-age.key
grep 'public key' ~/.config/beesmartfinance/backup-age.key
```

Baris terakhir mencetak kunci publik `age1…` (aman dibagikan). Simpan isi file kunci privat di pengelola password.

### Langkah 2 — Dashboard Cloudflare

1. R2 → Create bucket → nama `beesmartfinance-backup`, lokasi otomatis. Jangan aktifkan akses publik atau domain.
2. Bucket → Settings → Object lifecycle rules → Add rule: prefix `db/`, hapus objek setelah 30 hari.
3. R2 → Manage API tokens → Create API token: izin **Object Read & Write**, terbatas ke bucket `beesmartfinance-backup`. Catat Access Key ID, Secret Access Key, dan endpoint `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.

### Langkah 3 — hPanel console (alat dan konfigurasi)

```sh
apt-get update && apt-get install -y age rclone
age --version; rclone version | head -1
```

`rclone` harus v1.59 atau lebih baru untuk `provider = Cloudflare`. Kalau versi apt lebih lama, pasang dari skrip resmi: `curl -fsSL https://rclone.org/install.sh | bash`, lalu cek versinya lagi.

```sh
install -d -m 700 /etc/beesmartfinance
umask 077
cat > /etc/beesmartfinance/backup.env <<'EOF'
BACKUP_AGE_RECIPIENT=<age1… dari langkah 1>
RCLONE_REMOTE=r2:beesmartfinance-backup
RCLONE_CONFIG_R2_TYPE=s3
RCLONE_CONFIG_R2_PROVIDER=Cloudflare
RCLONE_CONFIG_R2_ACL=private
RCLONE_CONFIG_R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
RCLONE_CONFIG_R2_ACCESS_KEY_ID=<access key id>
RCLONE_CONFIG_R2_SECRET_ACCESS_KEY=<secret access key>
LOCAL_KEEP_DAYS=14
EOF
chmod 600 /etc/beesmartfinance/backup.env
( set -a; . /etc/beesmartfinance/backup.env; set +a; rclone lsf "$RCLONE_REMOTE" --s3-no-check-bucket && echo "akses R2 OK" )
```

### Langkah 4 — hPanel console (pasang skrip, jalankan sekali)

Setelah rilis yang memuat `scripts/backup_offsite.sh`, ambil skrip dari salinan repo poller (milik user `deploy`):

```sh
sudo -u deploy git -C /home/deploy/.cache/beesmartfinance-source show FETCH_HEAD:scripts/backup_offsite.sh > /opt/beesmartfinance/scripts/backup_offsite.sh
chmod 700 /opt/beesmartfinance/scripts/backup_offsite.sh
/opt/beesmartfinance/scripts/backup_offsite.sh
```

Diharapkan satu baris `OK db-<waktu>.dump.age <ukuran> byte, 53 TABLE DATA`. Baris `GAGAL: …` menyebut tahap yang gagal (pg_dump, enkripsi, unggah, atau ukuran).

### Langkah 5 — hPanel console (cron harian)

```sh
cat > /etc/cron.d/beesmartfinance-backup <<'EOF'
MAILTO=""
0 19 * * * root /opt/beesmartfinance/scripts/backup_offsite.sh >> /var/log/beesmartfinance-backup.log 2>&1
EOF
chmod 644 /etc/cron.d/beesmartfinance-backup
```

Cek keesokan harinya: `tail -n 3 /var/log/beesmartfinance-backup.log; cat /opt/beesmartfinance/backups/daily/last_success`.

### Langkah 6 — Mac (uji pulih)

Unduh satu objek `db/db-<waktu>.dump.age` dari dashboard R2 (bucket → objek → Download), lalu:

```sh
f=~/Downloads/db-<waktu>.dump.age
out=~/Backups/beesmartfinance/restore-check.dump
age -d -i ~/.config/beesmartfinance/backup-age.key -o "$out" "$f" && chmod 600 "$out"
pg_restore --list "$out" | grep -c "TABLE DATA"
createdb bee_restore_check
pg_restore --no-owner --no-privileges -d bee_restore_check "$out"
psql -d bee_restore_check -At -c "SELECT (SELECT count(*) FROM ms_coa), (SELECT count(*) FROM operations_siswa WHERE NOT is_deleted), (SELECT count(*) FROM tr_jurnal WHERE NOT is_deleted), (SELECT count(*) FROM operations_tagihan WHERE NOT is_deleted)"
dropdb bee_restore_check && rm -f "$out" "$f"
```

Hitungan harus sama dengan blok read-only produksi pada hari dump dibuat. Database sementara dan kedua file dihapus di baris terakhir.

### Tambahan untuk blok read-only rilis

```sh
echo "== Backup harian"; cat /opt/beesmartfinance/backups/daily/last_success 2>/dev/null || echo "belum ada"; tail -n 1 /var/log/beesmartfinance-backup.log 2>/dev/null
```

Biaya: satu unggahan dan satu pengecekan ukuran per hari (operasi kelas A/B R2 jauh di bawah kuota gratis); tidak ada `rclone sync` yang mendaftar ulang isi bucket.

## Rollback

- Hentikan: hapus `/etc/cron.d/beesmartfinance-backup`.
- Cabut akses: hapus token R2 di dashboard (bucket tetap ada sampai dihapus).
- Hapus total: hapus bucket, `/etc/beesmartfinance/backup.env`, dan folder `backups/daily/`.
- Tidak ada perubahan pada database, aplikasi, atau poller deploy.

## Risiko yang tersisa

- Kunci privat age hilang = backup di R2 tidak bisa dibuka. Mitigasi: salinan di pengelola password, uji pulih di langkah 6.
- Kegagalan harian hanya tercatat di log, tanpa notifikasi. Mitigasi: `last_success` dicek di setiap blok read-only; notifikasi (mis. email cron atau ping ke layanan pemantau) bisa ditambah kemudian.
