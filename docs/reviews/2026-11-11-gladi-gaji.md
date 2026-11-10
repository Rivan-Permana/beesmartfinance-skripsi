# Gladi modul gaji di UAT — 11 November 2026

Dokumen publik: hanya lulus/gagal dan jumlah, tanpa nama dan nominal. Data: 3 pegawai uji di UAT `bee_uat_browser_20261020`; backup sebelum gladi `~/Backups/beesmartfinance/bee_uat-20261111-015011-before-gladi-gaji.dump`. Produksi tidak disentuh.

## Hasil

| Langkah | Hasil |
|---|---|
| Kasbon diajukan Keuangan | Ditolak 403 (hanya Kepsek yang mengajukan) — sesuai |
| Kasbon diajukan Kepsek, dicairkan Keuangan | Jurnal `AUTO_KASBON` DRAFT, Dr 114 / Cr 112; diajukan Keuangan, disetujui Kepsek → POSTED |
| Slip Januari 2027 untuk 3 pegawai | Tersimpan; potongan kasbon terisi otomatis sebesar angsuran; slip ganda (pegawai+periode sama) ditolak |
| Posting slip → ajukan → setujui | 3 jurnal `GJ-…` tanggal 28/01/2027: Dr 5301; Cr 112 (netto), 114 (potongan kasbon), 211 (potongan asuransi); semua POSTED |
| Saldo kasbon setelah gaji | Berkurang tepat satu angsuran |
| Ubah slip yang sudah dijurnal | Ditolak 400 — sesuai |
| Guru / TU membuka gaji | 403 / 403 — sesuai |
| Laporan Januari | Laba rugi memuat 5301 (kelompok 53); neraca memuat 114 dan 211; tidak ada jurnal tertinggal PENDING |

Kesimpulan: alur dan akuntansinya benar. Masalahnya ada di **beban kerja bulanan** dan beberapa pilihan yang belum diputuskan sekolah.

## Temuan

1. **Semua per slip.** Produksi punya 33 pegawai aktif. Setiap bulan: 33 slip diisi manual (±12 isian per slip, ±400 isian), 33 kali posting, 33 kali ajukan oleh Keuangan, dan 33 persetujuan Kepsek. Tidak ada buat sekaligus, salin dari bulan lalu, posting massal, atau persetujuan massal.
2. **Slip pertama (Januari) tidak punya sumber selain ketik ulang.** Rincian gaji per pegawai disiapkan bendahara di spreadsheet; belum ada impor.
3. **Tarif uang makan/transport per hari di data pegawai dan absensi pegawai tidak dipakai slip.** Uang makan, transport, dan hari hadir diketik manual.
4. **Akun kas gaji selalu 112** (aturan akun sistem); tidak bisa memilih Kas TK/PG/ADM. Tanggal jurnal selalu tanggal 28.
5. **Beban gaji satu akun (5301)** untuk semua unit; laba rugi tidak memisahkan gaji TK/PG/ADM.

## Usulan

| # | Usulan | Saran | Alasan |
|---|---|---|---|
| 1 | Posting massal slip satu periode (Keuangan) dan persetujuan massal jurnal gaji satu periode (Kepsek), dengan daftar yang bisa diperiksa sebelum disetujui | Ya, sebelum Januari | Mengurangi 99 klik per bulan jadi 2 tanpa mengubah model akuntansi (tetap satu jurnal per slip, aturan SoD dan kasbon tetap jalan) |
| 2 | Impor slip dari spreadsheet bendahara (pratinjau → simpan), lalu "salin dari bulan lalu" untuk bulan berikutnya | Ya; minta contoh format kosong ke bendahara sekarang | Menghilangkan ±400 isian manual; impor butuh format kolomnya, jadi format harus didapat sebelum data gaji pertengahan Desember |
| 3 | Akun kas untuk gaji | Tanya bendahara; sementara tetap 112 | Bergantung dari rekening mana gaji dibayar; mengubahnya tanpa jawaban sekolah bisa salah arah |
| 4 | Uang makan/transport dari tarif × absensi | Tunda | Absensi pegawai belum dipakai rutin; manual dulu lebih aman |
| 5 | Pisah beban gaji per unit | Tunda | Butuh keputusan COA (akun gaji per unit) dan tidak menghambat cut-over |
