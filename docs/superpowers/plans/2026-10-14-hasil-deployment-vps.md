# Hasil deployment revisi — 14 Oktober 2026

Paket revisi diterbitkan setelah pengguna secara eksplisit menyetujui deployment backend, frontend, dan migration dengan database VPS sebagai basis. Data dummy lokal tidak diimpor. Aplikasi berjalan dengan backend dan PostgreSQL di VPS, sehingga penggunaan online tidak membutuhkan laptop menyala. Supabase tidak diperlukan untuk konfigurasi ini.

## Rilis

- Commit `b745d6b4e55bb5a1183e5a54c0cbd5032dd5a39b` diterbitkan ke `main`. Hanya 37 file paket revisi masuk commit; perubahan dokumen dan skrip lain milik pengguna tidak dimasukkan.
- Backend Hostinger VPS dan frontend Cloudflare sudah memakai SHA tersebut, dikonfirmasi melalui kedua file state deployment.
- Worker `beesmartfinance-skripsi` menerbitkan versi `08c1cc96-cb17-4d90-8514-d0ce6e6f268f`.
- Migration `operations.0012_historicaltagihan_perlu_rekonsiliasi_and_more` berhasil pada produksi. Build frontend dan pemeriksaan TypeScript berhasil di VPS.
- Backup sebelum deployment berada di VPS: `/opt/beesmartfinance/backups/db-20261014T120806Z.dump`, 210.911 byte, mode `0600`. Backup verifikasi sebelumnya juga dipertahankan di VPS.
- Waktu mulai deployment backend: 14 Oktober 2026 pukul 19:08 WIB. Tidak ada database penuh yang diekspor ke laptop.

## Perilaku paket

Dropdown jurnal menerima seluruh akun aktif termasuk akun lawan Kas/Bank. Konsumen daftar pegawai mengikuti pagination. Faktur memakai nama RA Lebah Madu dan aturan layout cetak baru. Finance dapat mencatat jurnal pendapatan/pengeluaran dalam cakupan yang ditentukan tanpa approval Kepala Sekolah. Pembayaran tagihan memiliki nominal, rincian alokasi, tanggal, bukti, idempotensi, riwayat, serta status BELUM/SEBAGIAN/LUNAS; pembatalan mengikuti kontrol audit yang ada.

## Bukti pemeriksaan

Sebelum deployment, dump VPS direstore ke database sementara di server yang sama. Migration kandidat berhasil; nilai kolom lama pada 48 tabel asli tetap utuh. Metadata Django menambah tiga content type dan 12 permission. Database serta source verifikasi sementara dibersihkan setelah pemeriksaan. Sebanyak 43 tes regresi backend pada PostgreSQL terisolasi sebelumnya sudah berhasil.

Sesudah deployment, pemeriksaan read-only melalui view API dengan role Finance yang sudah ada menghasilkan:

| Endpoint | Hasil | Jumlah |
|---|---|---|
| Tagihan | 200 | 5 record |
| Jurnal pemasukan | 200 | 5 record; kontrak status baru tersedia |
| Pegawai halaman 2 | 200 | 6 dari 31 record yang terlihat |

Jumlah seluruh record termasuk soft-delete tetap 32 siswa, 34 pegawai, 5 tagihan, dan 5 jurnal. Tiga tagihan lama mendapat penanda rekonsiliasi dan dibayar/sisanya tetap tidak diketahui; tidak dibuatkan pembayaran historis berdasarkan dugaan. Tabel pembayaran baru masih kosong. Payload faktur menghasilkan nama RA Lebah Madu.

Probe HTTP publik dari koneksi laptop menghasilkan halaman `/login` 200, aset baru `TagihanListView-HCDsRibK.js` 200, API tagihan melalui Cloudflare 401 tanpa token, dan API origin VPS 401 tanpa token. Ini membuktikan halaman/aset tersedia serta akses API tetap memerlukan autentikasi; bukan pengujian seluruh interaksi browser.

Pemeriksaan API pertama sempat gagal karena request buatan memakai hostname `testserver` yang memang tidak diizinkan produksi. Request diperbaiki memakai hostname origin yang benar; konfigurasi ALLOWED_HOSTS tidak dilonggarkan. Probe HTTP dengan Python urllib dari VPS mendapat 403 pada Cloudflare, sedangkan curl dalam proses deployment dan probe publik dari laptop berhasil. Hasil probe yang gagal tidak digunakan sebagai bukti keberhasilan.

## Pekerjaan tersisa dan batas

- Tiga tagihan lama memerlukan bukti pembayaran untuk rekonsiliasi. Pembayaran baru dan posting jurnal billing lama terkait tetap diblokir sampai kasusnya diselesaikan dengan benar.
- Cetak melalui dialog browser/printer, pengujian beban/concurrency, dan perjalanan UI lengkap belum diperiksa. Pemeriksaan produksi di atas tidak menciptakan pembayaran/transaksi baru.
- Penyelarasan paket pendaftaran serta saldo awal belum termasuk rilis ini dan membutuhkan penetapan aturan/data sebelum diterapkan.
- Backup baru masih berada pada VPS yang sama. Backup di luar server belum dikonfigurasi.
- Scheduler deployment yang disebut dokumen sebelumnya tidak ditemukan pada crontab root/deploy, cron sistem, atau timer proyek yang diperiksa. Rilis ini dijalankan langsung memakai skrip deployment proyek. Jangan mengandalkan polling otomatis untuk rilis berikutnya sebelum scheduler dikonfirmasi/dipasang secara terpisah.
- Log build memuat peringatan dependensi yang sudah ada serta ukuran bundle; build tetap berhasil. Paket ini tidak mengganti dependensi atau menambah fitur hosting lain.

Laporan ini disimpan sebagai artefak lokal sesudah rilis; SHA deployment di atas mengacu pada commit paket aplikasi, bukan penerbitan laporan ini.
