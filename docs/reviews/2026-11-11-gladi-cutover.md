# Gladi cut-over di UAT — 11 November 2026

Dokumen publik: hanya lulus/gagal, jumlah, dan durasi. Tanpa nama siswa/pegawai dan tanpa nominal. Bahan (tab master dan Biodata Siswa per 29/10) disalin dengan nama samaran "Gladi NNN" dan hanya disimpan di laptop; tidak ada nama asli yang tersisa di salinan (dicek: 0 dari 108).

- DB: UAT `bee_uat_browser_20261020` (lewat backend-uat :8001, frontend-uat :5175). Backup sebelum gladi: `~/Backups/beesmartfinance/bee_uat-20261111-004414-before-gladi.dump`.
- Produksi, `main`, dan `db_lebah_madu` lokal tidak disentuh.
- Data gladi tetap di UAT (104 siswa samaran, tagihan, satu jurnal saldo awal contoh). Pulihkan dengan backup di atas bila UAT perlu bersih.

## Hasil per langkah

| Langkah | Hasil | Durasi |
|---|---|---|
| Impor biodata (pratinjau → simpan, kelas dipetakan ke kelompok) | 104 baru, 0 galat | < 1 dtk |
| Impor tarif SPP (pratinjau → simpan) | 90 terisi; 14 cek (9 nominal beda antar bulan, 3 belum pernah bayar, 2 di luar rentang); 4 galat (siswa tidak ada di biodata) | < 1 dtk |
| Impor biaya masuk (pratinjau → simpan, tanggal 31/12/2026) | 101 tagihan Juli 2026 (88 lunas, 10 sebagian, 3 belum); 98 penerimaan saldo awal; **0 jurnal baru**; 3 cek (cicilan melebihi biaya setelah diskon); 4 galat (sama seperti SPP) | ±3 dtk |
| Impor biaya masuk ulang | Tidak ada data ganda (101 tagihan, maks 1 saldo awal per tagihan). Lihat temuan 2. | ±3 dtk |
| Saldo awal kas lewat kolom saldo awal COA | **Gagal sebagai model**: lihat temuan 1 | — |
| Saldo awal kas lewat jurnal 31/12 (Dr 115–118, Cr 312), Keuangan ajukan, Kepsek setujui | POSTED; kenaikan aset = kenaikan ekuitas (neraca tidak bergeser) | < 1 dtk |
| Tunggakan SPP Juli–Oktober (Buat tagihan per siswa per bulan) | 19 siswa punya bulan kosong: 11 tagihan dibuat untuk 9 siswa; 6 siswa tanpa tarif SPP; 4 siswa tidak ada di sistem. Juli tidak menagih ulang komponen tahunan | < 1 dtk (API) |
| Tagihan Januari 2027 (pratinjau → buat sekaligus) | 102 dibuat, 16 dilewati (tanpa komponen = tanpa tarif SPP); buat ulang 0 | < 1 dtk |
| Pembayaran Januari ke Kas PG lalu dicatat Keuangan | Lunas; jurnal POSTED Dr 115 / Cr 411 | < 1 dtk |
| Invoice gabungan siswa dengan biaya masuk sebagian | Memuat sisa biaya masuk + SPP Januari; total = jumlah sisa semua tagihan | — |
| Laporan Januari | Laba rugi memuat 411; neraca memuat 115–118 | — |
| Daftar Tunggakan Tagihan | 227 tagihan, tampil ±0,3 dtk, tanpa galat, tanpa geser samping | — |

## Temuan

1. **Saldo awal kas tidak bisa lewat kolom saldo awal COA.** Saldo awal bertanggal 1/1/2027 ditolak untuk akun yang sudah punya transaksi sebelumnya (di UAT: 312; di produksi: 112 sudah punya jurnal sejak September 2026). Saldo awal COA juga tidak punya lawan, sehingga neraca bergeser. **Pengganti:** satu jurnal "saldo awal cut-over" per 31/12/2026 lewat alur biasa (Keuangan buat dan ajukan, Kepsek setujui). Untuk akun kas yang sudah dipakai di sistem (112), nominal jurnalnya adalah selisih saldo sheet 31/12 dikurangi saldo sistem 31/12, bukan saldo sheet penuh. Lawan akun perlu diputuskan (Laba Ditahan 312 atau Modal 311).
2. **Impor biaya masuk ulang menampilkan "diisi" untuk siswa yang belum membayar sama sekali.** Penanda "sudah" hanya membaca penerimaan saldo awal; siswa dengan terbayar 0 tidak punya penerimaan, jadi dianggap "isi" lagi. Tidak ada data ganda (tagihan disinkronkan, bukan dibuat baru), tetapi ringkasannya menyesatkan dan impor ulang akan menimpa isian biaya masuk yang sudah diubah TU. Perbaikan kecil: anggap "sudah" bila tagihan biaya masuk siswa itu sudah ada.
3. **Siswa di master yang tidak ada di sistem (4 di data 29/10)** muncul sebagai galat di impor SPP dan biaya masuk. Di hari-H, cek ulang daftar galat; tambahkan siswanya dulu, lalu impor ulang.
4. **Siswa tanpa tarif SPP (14 di data 29/10)** tidak mendapat tagihan Januari dan tunggakannya tidak bisa dibuat. TU mengisi tarif manual (dari baris "cek" impor SPP) sebelum langkah tunggakan dan tagihan Januari.
5. **Tunggakan cukup dengan "Buat tagihan" per siswa per bulan.** Volumenya kecil, jadi fitur impor tunggakan tidak perlu. Selalu pakai "Periksa rincian" dulu: katering dan jemputan dihitung otomatis dari absensi dan bisa ikut. **Jangan** pakai "Buat sekaligus" untuk Juli–Desember karena menagih semua siswa.
6. **Tunggakan katering, jemputan, dan LSU tidak bisa dibaca dari tab master** (tab hanya mencatat yang sudah bayar, tanpa daftar pelanggan). TU menyiapkan daftarnya.
7. Bukan masalah cut-over: neraca API tidak memasukkan laba tahun berjalan ke ekuitas, dan halaman laporan menampilkan selisihnya secara terbuka (perilaku lama).

## Urutan hari-H (draf, 31 Des – 2 Jan)

1. Backup bernama `before-cutover` (pola checklist rilis).
2. Ekspor tab master dan Biodata Siswa per 31/12; catat saldo akhir kas per unit dari sheet.
3. TU: impor biodata (pratinjau → simpan bila ada siswa baru). Galat nama → perbaiki dulu.
4. TU: impor tarif SPP; isi tarif manual untuk baris "cek".
5. TU: impor biaya masuk, tanggal 31/12/2026: pratinjau → selesaikan "cek" dengan Bendahara → simpan.
6. Keuangan: jurnal saldo awal cut-over 31/12 (temuan 1) → ajukan → Kepsek setujui. Cek neraca.
7. TU: tunggakan SPP per siswa per bulan lewat "Buat tagihan" → "Periksa rincian" → buat.
8. TU: tunggakan katering/jemputan/LSU dari daftar TU.
9. TU: tagihan Januari: pratinjau → buat sekaligus. Jumlah dilewati harus 0 untuk siswa aktif yang bayar SPP.
10. Cek: Tunggakan Tagihan, invoice gabungan 2–3 siswa, neraca, laba rugi Januari.
11. Kunci sheet jadi hanya baca.

## Keputusan yang dibutuhkan

1. Lawan akun jurnal saldo awal cut-over: 312 Laba Ditahan (saran) atau 311 Modal.
2. Saldo kas 112 di sistem vs sheet: jurnal selisih per 31/12 (saran) atau saldo sheet penuh dengan pembalikan jurnal 2026.
3. Perbaiki temuan 2 sebelum hari-H (saran: ya, kecil).
