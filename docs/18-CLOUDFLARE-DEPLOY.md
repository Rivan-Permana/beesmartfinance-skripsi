# Deployment Cloudflare — BeeSmart Finance

## Status 12 Oktober 2026

Frontend Vue/Vite dan gateway API sudah di-deploy langsung dari working directory lokal:

https://beesmartfinance-skripsi.ansinar2003.workers.dev

Worker: `beesmartfinance-skripsi`. Backend Django, PostgreSQL, dan Caddy sudah
berjalan di VPS Hostinger. Origin API: https://srv2054916.hstgr.cloud.
Worker memakai `BACKEND_ORIGIN` dari `frontend/wrangler.jsonc`.
Halaman login merespons 200; API tanpa token merespons 401; login `admin.tu`
dan pembacaan profil melalui URL Cloudflare berhasil (200).
Data demo baru, empat akun peran, COA 186 akun, dan aturan posting sudah ada.
Deployment ini belum mengaktifkan deployment otomatis dari GitHub.

## Menyiapkan deployment otomatis FE–BE

`.github/workflows/ci.yml` sekarang menyiapkan job `deploy` setelah job backend
dan frontend berhasil pada push ke `main`. Job ini membangun frontend dengan
`VITE_API_BASE_URL=/api/v1`, mengirim file backend yang dilacak Git ke
`/opt/beesmartfinance`, menjalankan `scripts/deploy_vps.sh`, memeriksa origin
API, lalu menerbitkan Worker yang sama dengan `wrangler deploy --keep-vars`.
Job tidak berjalan untuk pull request.
Sebelum migrasi, skrip deploy menyimpan dump PostgreSQL di folder `backups/`
pada VPS dan menghentikan deployment bila backup gagal. Salinan di luar VPS
tetap diperlukan untuk memulihkan data jika server hilang.

Sebelum mengaktifkannya, masukkan enam repository secrets di GitHub Actions:
`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `VPS_HOST`, `VPS_USER`,
`VPS_SSH_KEY`, dan `VPS_KNOWN_HOSTS`. Token Cloudflare harus dibatasi ke akun
Worker ini. `VPS_KNOWN_HOSTS` harus berasal dari fingerprint SSH server yang
sudah diverifikasi, bukan hasil penerimaan otomatis saat workflow berjalan.
Gunakan SSH key khusus deployment yang tidak meminta passphrase interaktif.
Akun SSH harus dapat menulis ke `/opt/beesmartfinance` dan menjalankan Docker.
Jangan masukkan nilai secret ke Git atau dokumentasi.

Commit file workflow bersama source dan konfigurasi deployment yang digunakan:
`docker-compose.production.yml`, `docker/`, `scripts/deploy_vps.sh`,
`frontend/wrangler.jsonc`, `frontend/worker/`, dan perubahan frontend/backend
terkait. Repo ini publik; tinjau daftar file sebelum staging. Workflow hanya
mengirim file backend yang dilacak Git dan tidak menghapus `.env.vps` maupun
volume PostgreSQL/media di VPS. Backup database di luar VPS perlu disiapkan
untuk pemulihan jika VPS hilang.

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

## Form Git deployment Cloudflare Workers

Setelah file konfigurasi dan source yang ingin dirilis sudah tersedia di GitHub,
gunakan pengaturan berikut pada form deployment repository:

| Field | Nilai |
| --- | --- |
| Project name | `beesmartfinance-skripsi` |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Deploy command | `npx wrangler deploy --keep-vars` |
| Preview command | `npx wrangler versions upload` |
| Build variable `VITE_API_BASE_URL` | `/api/v1` |

Gunakan Worker yang sudah dibuat untuk menyambungkan repository; jangan membuat
Worker kedua untuk deployment yang sama. Perubahan lokal yang belum di-push
belum akan tersedia pada build dari GitHub.

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
