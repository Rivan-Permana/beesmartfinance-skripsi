# Deployment Cloudflare — BeeSmart Finance

## Status 13 Oktober 2026

Frontend Vue/Vite dan gateway API sudah di-deploy langsung dari working directory lokal:

https://beesmartfinance-skripsi.ansinar2003.workers.dev

Worker: `beesmartfinance-skripsi`. Backend Django, PostgreSQL, dan Caddy sudah
berjalan di VPS Hostinger. Origin API: https://srv2054916.hstgr.cloud.
Worker memakai `BACKEND_ORIGIN` dari `frontend/wrangler.jsonc`.
Halaman login merespons 200; API tanpa token merespons 401; login `admin.tu`
dan pembacaan profil melalui URL Cloudflare berhasil (200).
Data demo baru, empat akun peran, COA 186 akun, dan aturan posting sudah ada.
Source produksi sudah tersedia di branch `main`. Deployment otomatis diatur
melalui VPS karena GitHub Actions milik akun ini sedang diblokir oleh status
billing GitHub; repository dan runner standar yang digunakan tetap gratis.

## Deployment otomatis FE–BE tanpa GitHub Actions

`deploy` di VPS menjalankan `scripts/poll_deploy_vps.sh` setiap lima menit.
Skrip mengambil commit terbaru `main` dari repository publik, lalu hanya
melakukan deployment jika SHA berubah. Source backend yang dilacak Git disalin
ke `/opt/beesmartfinance`, diikuti `scripts/deploy_vps.sh`. Skrip itu menyimpan
dump PostgreSQL di `backups/` sebelum migrasi dan berhenti jika backup gagal.
Frontend dibangun dalam image Node 22 dan diterbitkan ke Worker yang sama
dengan `wrangler deploy --keep-vars`. Setelah berhasil, SHA disimpan terpisah
untuk backend dan frontend sehingga kegagalan salah satu tahap bisa diulang.
Deploy pertama dan setiap commit baru mungkin memerlukan beberapa menit.

Token Cloudflare untuk deployment VPS disimpan di
`/home/deploy/.config/beesmartfinance/cloudflare.env` (mode `0600`) sebagai
`CLOUDFLARE_ACCOUNT_ID` dan `CLOUDFLARE_API_TOKEN`; jangan masukkan nilainya
ke Git, chat, atau dokumentasi. Cron milik `deploy` mencatat output ke
`/home/deploy/.local/state/beesmartfinance/deploy.log`. Periksa SHA terakhir di
`backend_sha` dan `frontend_sha` dalam folder state yang sama. Script hanya
menyalin file yang diperlukan dan tidak menimpa `.env.vps` atau volume Docker.
Backup database di luar VPS tetap diperlukan untuk pemulihan jika server hilang.

## Deployment frontend dari terminal

```sh
cd frontend
npm ci
VITE_API_BASE_URL=/api/v1 npm run deploy
```

Wrangler memakai `frontend/wrangler.jsonc`, mengunggah `dist`, dan melayani route
Vue melalui fallback SPA. Origin backend tersimpan sebagai variabel Worker di
berkas konfigurasi; `--keep-vars` juga mempertahankan variabel lain yang diatur
melalui dashboard Cloudflare.

## Menyambungkan backend permanen

Backend memakai Django 5.2, Python 3.13+, dan PostgreSQL. VPS Hostinger:
`187.77.126.25`, `srv2054916.hstgr.cloud`, Ubuntu 26.04 LTS, 2 CPU, 8 GB RAM,
lokasi Jakarta. Koneksi internet awal ke VPS timeout dari IP lokal, sedangkan
probe dari beberapa lokasi lain berhasil; akses SSH dari Mac berhasil setelah
memakai VPN. Docker Engine dan Compose dipasang dari repositori resmi Docker.

Konfigurasi produksi tersedia di `docker-compose.production.yml`:
Gunicorn menjalankan Django; Caddy melayani HTTPS, static files, dan media;
PostgreSQL hanya berada di jaringan internal Docker. Database, file upload,
dan sertifikat memiliki volume permanen. Dockerfile produksi menggunakan
dependensi dari `uv.lock` dengan extra `production`.

Source deployment terpilih berada di `/opt/beesmartfinance`. `.env` lokal,
database lokal, dan data operasional pribadi tidak disalin. Untuk deployment
ulang backend setelah memperbarui source yang dipilih, jalankan di VPS:

```sh
cd /opt/beesmartfinance
sh scripts/deploy_vps.sh
```

`scripts/init_vps_env.py` sudah dijalankan sekali saat provisioning. File
`.env.vps` menyimpan secret unik dengan permission `0600`; jangan buat ulang
file ini karena database dan sesi Django bergantung pada secret yang ada.
Script deployment membangun image backend,
menjalankan migrasi, mengumpulkan static files, dan memulai layanan. Port 80 dan
443 harus dapat diakses untuk HTTPS; PostgreSQL dan Gunicorn tidak memiliki
port publik. Script tidak membuat ulang akun demo atau mengimpor database lokal.

Variabel Worker yang sudah diterapkan:

```text
BACKEND_ORIGIN=https://srv2054916.hstgr.cloud
```

Nilainya hanya origin HTTPS, tanpa `/api/v1`, query, atau kredensial. Gateway
meneruskan `/api/*` dan `/media/*` ke origin tersebut. JWT tetap diteruskan ke
backend dan response API tidak di-cache. Jika origin belum dikonfigurasi,
gateway mengembalikan JSON 503 agar kegagalan koneksi tidak berubah menjadi HTML SPA.

Konfigurasi backend yang diperlukan:

- Compose produksi mengatur Gunicorn, debug nonaktif, HTTPS, dan origin frontend.
- `.env.vps` menyimpan hostname API, password database, dan secret Django.
- Volume Docker menyimpan PostgreSQL dan gambar katering; Caddy melayani file
  upload meskipun Django berjalan dengan `DEBUG=false`.
- Akun demo: `admin.tu` (Administration), `keuangan` (Finance), `kepsek`
  (SchoolPrincipal), dan `guru.kegiatan` (TeacherInCharge). Password acak unik
  tersimpan hanya di VPS pada `/root/beesmartfinance-demo-accounts.json` dengan
  permission `0600`. Buka Konsol web Hostinger atau SSH sebagai root, lalu baca
  file tersebut untuk login. Simpan password di pengelola sandi dan hapus file
  setelah disalin. Jangan kirim isi file melalui chat.
- Seeder membuat data siswa dan pegawai fiktif. COA master final diimpor dari
  file daftar akun saja; tidak ada jurnal, data siswa lokal, atau database lokal
  yang dipindahkan.
- Backup harian database dan file upload ke lokasi di luar VPS belum dikonfigurasi.

Frontend ini tidak memerlukan Cloudflare Tunnel ke laptop untuk hosting permanen.

## Referensi

- [Cloudflare Static Assets](https://developers.cloudflare.com/workers/static-assets/binding/)
- [Workers Builds configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)
- [Docker Engine di Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
