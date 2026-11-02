# Desain cut-over pencatatan ke sistem — Januari 2027

Dokumen publik: tanpa nama, nominal, atau isi jawaban sekolah. Jawaban lengkap disimpan lokal (`*-jawaban-sekolah.md`, tidak di-commit).

## Tujuan

Mulai semester 2 (Januari 2027), penerimaan dan pengeluaran sekolah dicatat di BeeSmart, tidak lagi di spreadsheet Recap Cash In/Cash Out. Gaji juga mulai dibuat di modul Gaji pada saat yang sama.

## Yang sudah diketahui dari sekolah (ringkas)

- Bulan pindah: Januari, awal semester 2.
- Pembayaran sebelum Juli hanya tercatat di Recap Cash In. Tidak dibukukan terpisah sebagai pendapatan diterima di muka, dan invoice sekolah sudah tidak menghitungnya lagi.
- Kas PG, TK, dan ADM dipegang satu orang. Tab mutasi rekening adalah kas kecil sekolah di rekening pribadi pemegang kas.
- Rincian gaji per pegawai disiapkan bendahara PG sebelum semester 2.

## Temuan yang mengubah urutan kerja

**Impor biaya masuk dari tab master tidak bisa dijalankan sebelum cut-over.** Penyebabnya, setiap simpan data siswa (`SiswaSerializer._simpan`) memanggil `sinkron_tagihan_biaya_masuk`. Kalau isian biaya masuk diimpor sekarang, tagihan `BIAYA_MASUK` akan terbentuk tanpa penerimaan, baik saat impor maupun saat TU mengubah data siswa itu nanti. Akibatnya, siswa yang sudah lunas di sheet akan tampil menunggak di Tunggakan Tagihan dan invoice gabungan. Jadi impor biaya masuk digabung dengan pencatatan penerimaan historis di bawah ini.

## Model saldo awal per 1 Januari 2027

| Bagian | Cara | Jurnal |
|---|---|---|
| Kas per unit | Keuangan membuat akun Kas PG, Kas TK, Kas ADM, dan Kas kecil rekening di COA (kode berawalan 1, nama berawalan "Kas "), lalu mengisi saldo awal per 1/1/2027 dari saldo akhir sheet 31/12 | Saldo awal COA (`0003_opening_balance`), bukan jurnal |
| Biaya masuk per siswa | Impor dari tab master: komponen, kategori diskon, nominal diskon, dan total terbayar s.d. 31/12. Tagihan `BIAYA_MASUK` dibuat lengkap, ditambah satu **penerimaan saldo awal** per siswa | Penerimaan saldo awal **tanpa jurnal kas**, karena uangnya sudah masuk saldo awal kas |
| SPP, katering, jemputan, LSU Juli–Desember | Tidak dibuat tagihan per bulan. Sisa tunggakan per 31/12 (bila ada) dicatat sebagai satu tagihan per siswa | Tanpa jurnal sampai dibayar |
| Mulai Januari | Tagihan bulanan dibuat dari sistem (generate per kelompok), penerimaan dicatat TU, dan Keuangan mencatat jurnal | Normal |

**Perlu perubahan kode (Desember):**
- Penanda `saldo_awal` pada `PembayaranTagihan`, beserta alokasinya, yang dikecualikan dari pembuatan jurnal. Tier 3: migrasi dan uang.
- Impor biaya masuk dari tab master dengan alur pratinjau → simpan, mengikuti pola `impor_spp`.

## Keputusan terbuka

1. **Pendapatan Juli–Desember di laporan TA 2026/27.** Model di atas hanya mencatat saldo awal, sehingga laba rugi TA 2026/27 di sistem hanya berisi Januari–Juni. Alternatifnya: jurnal ringkasan pendapatan per bulan per pos (SPP, katering, jemputan, LSU, biaya masuk) untuk Juli–Desember, dengan lawan akun saldo awal. Rekomendasi: saldo awal saja, kecuali sekolah atau penguji skripsi meminta laba rugi satu tahun penuh dari sistem.
2. **Kas kecil di rekening pribadi:** dicatat sebagai akun kas tersendiri atau digabung ke Kas ADM.
3. **Kategori tarif khusus (SBD/KHUSUS/PINDAHAN):** sudah bisa dipilih di form siswa sebagai label. Nominal mengikuti kesepakatan dan diketik langsung. Siapa yang menyetujui kesepakatan belum dijawab sekolah.

## Jadwal usulan

| Kapan | Apa |
|---|---|
| Minggu 2 Desember | Bangun penanda saldo awal dan impor biaya masuk, uji di DB UAT dengan salinan tab master |
| Minggu 3 Desember | Rilis (pola Batch 7) dan Keuangan membuat akun kas per unit |
| 31 Des – 2 Jan | Ambil saldo akhir sheet, isi saldo awal kas, jalankan impor biaya masuk (pratinjau → simpan), lalu kunci sheet jadi hanya baca |
| Mulai Januari | Tagihan bulanan, penerimaan, pengeluaran dengan kode sekolah, dan gaji di sistem |

## Rollback

- Backup bernama sebelum impor.
- Impor membuat tagihan dan penerimaan saldo awal tanpa jurnal, sehingga bisa dihapus per siswa selama belum ada penerimaan baru.
- Saldo awal COA bisa dikoreksi Keuangan di halaman COA.
