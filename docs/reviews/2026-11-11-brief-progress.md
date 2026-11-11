# Brief progress BeeSmart Finance — 10–11 November 2026

Dokumen publik: tanpa nama, nominal, atau isi jawaban sekolah. Status rinci dan titik masuk kode ada di [handoff](./2026-11-10-handoff.md).

## Ringkasan

Dalam dua hari, sistem dibawa dari "fitur cut-over masih di branch" menjadi "siap cut-over Januari", dengan lima rilis ke produksi (Batch 9–13), pengisian COA produksi, dua gladi di UAT, dan pembersihan data uji coba yang menggantung. Yang tersisa: pemasangan backup harian ke luar VPS, pekerjaan manual Keuangan dan TU (di bawah), dan data yang memang harus datang dari sekolah.

## Yang sudah selesai

### Rilis ke produksi

| Batch | PR | Isi utama |
|---|---|---|
| 9 | #27 | Iuran Komite dan Portofolio per siswa; penerimaan saldo awal tanpa jurnal; impor biaya masuk dari tab master; modul LSU; peran penyusun anggaran dengan plafon tahunan; subtotal laba rugi per kelompok akun |
| 10 | #28 | Batal saldo awal dari riwayat pembayaran; perbaikan redirect `/`; akun pendapatan LSU 418; Pengeluaran memuat kode non-beban (DVD, TMB) |
| 11 | #29 | Kode tanpa akun tetap (STR Sentra) tampil "Akun per transaksi", bukan peringatan |
| 12 | #30 | Posting dan persetujuan gaji per periode (99 klik/bulan jadi 2); Keuangan mencatat jurnal realisasi kegiatan; perbaikan impor ulang biaya masuk; perintah pensiun tagihan lama; skrip backup |
| 13 | #31 | Baca jurnal hanya untuk Keuangan, Kepsek, TU (Guru dan penyusun anggaran ditolak) |

Setiap rilis: cek read-only produksi, backup bernama, PR, merge, cek pasca-rilis, smoke test per role. Semua lulus; tidak ada rilis yang mengubah data.

### Data produksi

- **COA dan kode pengeluaran:** 17 akun baru (kas unit 115–118; beban TK 5135–5139, PG 5235–5239; 5409, 5410; 313) dan 14 kode baru; 5 kode UMUM lama dinonaktifkan. Lalu akun 418 Pendapatan LSU. COA kini 206 akun.
- **User penyusun anggaran** dibuat dengan password acak dari VPS (tidak pernah lewat chat).
- **Tiga tagihan uji coba Sep–Okt** dipensiunkan beserta jurnalnya (VOID, tercatat di log audit). Jurnal belum POSTED turun 7 → 4.

### Gladi di UAT (data siswa disamarkan)

- **Cut-over:** impor biodata, tarif SPP, dan biaya masuk lancar (101 tagihan, 98 penerimaan saldo awal, 0 jurnal baru); tagihan Januari dan laporan benar. Temuan utama: saldo awal kas harus lewat **satu jurnal saldo awal per 31/12** (lawan 312 Laba Ditahan; akun 112 cukup selisih), bukan kolom saldo awal COA. Urutan 11 langkah hari-H ada di [gladi cut-over](./2026-11-11-gladi-cutover.md).
- **Gaji:** alur dan jurnal benar; beban kerja per slip diatasi dengan fitur per periode di Batch 12.

## Keputusan yang sudah diambil

1. Plafon tahunan dikosongkan sampai ada anggaran resmi per akun.
2. STR (Sentra) tetap dipilih akunnya per transaksi.
3. Jurnal saldo awal cut-over: lawan 312 Laba Ditahan; 112 cukup jurnal selisih.
4. Realisasi kegiatan: Guru input, Keuangan Catat, tanpa persetujuan Kepsek.
5. Tiga tagihan uji coba dipensiunkan; siswanya ikut alur cut-over biasa.
6. Backup harian ke R2 (terenkripsi, retensi 30 hari) dipasang terpisah, kapan pun pengguna siap.

## Yang tersisa

| # | Siapa | Apa | Kapan |
|---|---|---|---|
| 1 | Keuangan, TU | Pekerjaan manual di bawah (4 jurnal) | Secepatnya, sebelum Desember |
| 2 | Pengguna | Pasang backup harian ([rencana](./2026-11-11-rencana-backup-offsite.md)) | Sebelum cut-over; semua backup masih di disk VPS yang sama |
| 3 | Sekolah (Bendahara) | Contoh format spreadsheet gaji (kosong) dan rekening pembayaran gaji | Sekarang, supaya impor slip bisa dibangun sebelum data gaji pertengahan Desember |
| 4 | Sekolah (TU) | Daftar tunggakan katering/jemputan/LSU Juli–Desember; tarif SPP siswa yang belum pernah bayar | Sebelum 31 Desember |
| 5 | Sekolah (Bendahara) | Ekspor sheet master dan biodata per 31/12; saldo akhir kas per unit | 31 Desember |
| 6 | Yayasan | Anggaran resmi per akun (untuk plafon) | Kapan tersedia |
| 7 | Pengguna + Claude | Cut-over 31 Des – 2 Jan sesuai [urutan hari-H](./2026-11-11-gladi-cutover.md) | 31 Des – 2 Jan |

## Pekerjaan manual untuk Keuangan dan TU

Empat jurnal lama masih "belum tercatat". Nominalnya harus dari bukti asli, jadi dikerjakan langsung oleh petugasnya. Setelah selesai, pengguna menjalankan satu cek read-only: jurnal belum POSTED harus 0.

**Keuangan — dua pengeluaran kegiatan (DP tempat dan DP kaos AB3)**
1. Buka menu **Pengeluaran**, cari jurnal `KG-1-1` dan `KG-1-2`.
2. Klik **Periksa jurnal**, cocokkan nominal dan tanggal dengan bukti/nota DP.
3. Kalau cocok, klik **Catat ke buku besar**. Kalau tidak cocok, jangan dicatat; laporkan ke pengguna.

**TU lalu Keuangan — dua biaya pendaftaran lama**
1. **TU:** buka menu **Pendaftaran**. Ada dua catatan berlabel **Perlu dicocokkan**. Untuk masing-masing, klik **Ubah calon** (di HP: **Ubah**), isi **biaya formulir** dan **biaya sit-in** sesuai kuitansi pendaftaran (isi 0 kalau memang tidak ada), lalu simpan.
2. **Keuangan:** buka menu **Pemasukan**, cari jurnal `REG-1` dan `REG-2`, klik **Periksa jurnal**, lalu **Catat ke buku besar**.
3. Kalau aplikasi menolak mencatat, artinya total biaya yang diisi TU tidak sama dengan nilai jurnal. Cek ulang kuitansinya; jangan diubah-ubah sampai cocok tanpa bukti.

### Pesan siap kirim (WhatsApp)

> **Untuk Keuangan:**
> Assalamu'alaikum. Mohon bantuannya di aplikasi BeeSmart: di menu Pengeluaran ada dua catatan DP kegiatan AB3 (DP tempat dan DP kaos) yang belum dibukukan. Tolong dicek dengan nota DP-nya, kalau sudah sesuai klik "Catat ke buku besar". Lalu setelah TU melengkapi dua data pendaftaran, di menu Pemasukan akan ada dua penerimaan biaya pendaftaran yang juga perlu dicatat dengan cara yang sama. Kalau ada yang tidak cocok dengan bukti, jangan dicatat dulu, kabari saya ya. Terima kasih.
>
> **Untuk TU:**
> Assalamu'alaikum. Mohon bantuannya di aplikasi BeeSmart: di menu Pendaftaran ada dua data berlabel "Perlu dicocokkan". Tolong dibuka satu per satu, klik "Ubah calon", lalu isi biaya formulir dan biaya sit-in sesuai kuitansi pendaftarannya (isi 0 kalau memang tidak ada), kemudian simpan. Setelah itu Keuangan bisa membukukannya. Terima kasih.

## Posisi teknis

- **Produksi:** Batch 13 (setelah PR #31 di-merge); migrasi `operations.0023`, `accounts.0003`. Backup bernama terakhir `…before-batch13`.
- **Branch kerja `codex/auto-deploy-fe-be`:** sama dengan `main` plus commit dokumen; tidak ada kode yang menunggu rilis.
- **UAT `bee_uat_browser_20261020`:** berisi data gladi (siswa samaran, slip gaji uji). Backup sebelum gladi tersedia bila perlu dibersihkan.
