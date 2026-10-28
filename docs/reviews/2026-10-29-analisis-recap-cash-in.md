# Analisis spreadsheet Recap Cash In 26/27 — 29 Oktober 2026

Tujuan: memetakan pekerjaan manual di spreadsheet sekolah ke fitur BeeSmart Finance (sudah ada / sebagian / belum), memvalidasi data sistem, dan mengusulkan otomatisasi. Dokumen ini hanya berisi struktur, pola, dan agregat; tidak ada nama siswa atau data pribadi. Salinan CSV hanya disimpan sementara di scratchpad dan dihapus setelah analisis.

Bagian Cash Out 26/27 (tab PG, TK, OPR, MUTASI REK, BUDGETING, YoY, CAT) belum dianalisis karena spreadsheet itu tidak dibagikan publik (ekspor CSV 401).

## Peta tab

| Tab | Fungsi di sekolah | Isi utama |
|---|---|---|
| **master** (108 siswa × 115 kolom) | Buku besar penerimaan per siswa | Ukuran seragam (Putih, Olga), JK, kelas, status (BARU / NAIK KELAS / LANJUTAN / MENGULANG), kategori dan jumlah diskon, komponen biaya masuk (Uang Masuk, Portofolio PG, Kegiatan, Pengembangan, Komite, Seragam), total sebelum/sesudah diskon, cicilan 1–6 (tanggal + nominal), total dibayar. Lalu per bulan Juli–Juni: tanggal + nominal SPP, Katering, Jemputan, LSU. |
| **INV TK / INV PG** | Invoice tunggakan per siswa (template, diisi lewat KODE baris master) | Komponen tahunan, SPP per bulan, katering per bulan, jemputan, LSU, item lain; total; "Dapat dicicil hingga bulan September"; rekening BSI a.n. RA Lebah Madu; kontak Bu Fia (TK) / Bu Fitri (PG). Ada juga "INVOICE KHUSUS" dan daftar pesanan seragam/buku (Putih, Olga, Batik, Jilid 1/2, Pra + Prestasi) berstatus "sdh ditagih / blm ditagih". |
| **LSU** (8 siswa) | Paket layanan per pertemuan | Paket 8 pertemuan Rp 600.000 (ada 16 pertemuan Rp 1.100.000); jumlah pertemuan terpakai; rasio paket terpakai; hingga 17 pembayaran (tanggal + nominal). |
| **Biodata Siswa** | Data diri siswa | Sudah diimpor ke produksi 28/10 (Batch 5). |

## Temuan dari data

### Tarif dan biaya masuk

- **SPP per bulan** (nilai terbanyak per siswa):

  | Kelas | SPP | Jumlah siswa |
  |---|---|---|
  | TK A | Rp 1.350.000 | 38 |
  | TK B | Rp 1.300.000 | 33 |
  | PG Lebah | Rp 950.000 | 12 |
  | PG Lebah | Rp 900.000 | 5 |
  | PG Lebah | Rp 850.000 | 2 |
  | PG Kepompong | Rp 1.050.000 | 3 |

  Pengecualian:
  - 9 siswa punya SPP bervariasi antar bulan.
  - 4 siswa belum ada pembayaran SPP sama sekali.
  - Beberapa sel berisi nilai besar (Rp 2,95 jt, Rp 3,65 jt). Kemungkinan pembayaran beberapa bulan sekaligus, jadi tidak bisa dipakai sebagai tarif.
  - Ada SPP khusus Rp 500.000, Rp 562.500, Rp 700.000, dan Rp 800.000.
- **Biaya masuk tidak sama dengan daftar harga sistem (`tp_templates`).** Perlu divalidasi sekolah:

  | Komponen | Sheet 26/27 (terbanyak) | Daftar harga sistem |
  |---|---|---|
  | Kegiatan TK baru | Rp 5.000.000 (41 siswa) | Rp 4.500.000 |
  | Kegiatan TK lanjut | Rp 4.500.000 (36) | Rp 4.500.000 |
  | Kegiatan PG | Rp 2.500.000 (21) | Rp 2.500.000 |
  | Seragam TK | Rp 500.000 (45) | Rp 400.000 |
  | Seragam PG | Rp 250.000 (11) | Rp 200.000 |
  | Pengembangan TK / PG | Rp 1.650.000 / Rp 1.000.000 | sama |
  | Komite TK / PG | Rp 750.000 / Rp 375.000 | sama |
  | Uang Masuk TK / PG | Rp 3.200.000 / Rp 700.000 | sama |
  | Portofolio PG | Rp 300.000 (17), juga 200.000/100.000 | Rp 300.000 |

- **Kategori diskon di sheet:** UMUM 70, PG 11, SIB 10, SIPG 7, SBD 5, SIKBR 2, KHUSUS 2, PINDAHAN 1.
  - Sistem baru mengenal PG, SIPG, SIB, SIKBR. **SBD, KHUSUS, dan PINDAHAN belum ada.**
  - Nominal yang dipakai: SIPG −1,5 jt, PG −1 jt, SIB −0,5 jt.
  - SBD bernilai 0, tetapi komponennya lebih rendah (Uang Masuk 500 rb, Kegiatan 2,45 jt). Jadi SBD adalah tarif khusus, bukan potongan.
  - PINDAHAN memakai sekitar 75% tarif normal (prorata).
- **Rumus sheet konsisten.**
  - Total sebelum diskon = jumlah komponen: 107/108.
  - Sesudah diskon = sebelum + diskon: 105/108.
  - 91/108 siswa biaya masuknya sudah lunas.
- **Status siswa** (BARU 57, NAIK KELAS 32, LANJUTAN 12, MENGULANG 7). Di sistem ini tersebar di `tipe_tp` (baru/lama) dan `status` (aktif/naik/mengulang). Belum ada satu kolom yang setara, dan status ini menentukan tarif.

### Arus kas

- **Total per bulan** (jumlah siswa / rupiah):

  | Bulan | SPP | Katering | Jemputan | LSU |
  |---|---|---|---|---|
  | Juli | 101 / 126,7 jt | – | 11 / 2,3 jt | 2 / 1,2 jt |
  | Agustus | 101 / 127,0 jt | 82 / 19,6 jt | 15 / 3,3 jt | 3 / 1,8 jt |
  | September | 100 / 125,9 jt | 46 / 11,8 jt | 15 / 2,9 jt | 3 / 1,8 jt |
  | Oktober | 91 / 116,7 jt | 1 / 0,3 jt | – | 1 / 0,6 jt |
  | November–Desember | 7 siswa bayar di muka | – | – | – |

  Biaya masuk yang sudah dibayar sekitar Rp 1,40 M.
- **Sistem belum menjadi sumber kebenaran penerimaan.** Beranda produksi 2026/2027 mencatat Pendapatan Rp 6,7 jt dan hanya 7 tagihan, padahal sheet mencatat lebih dari Rp 1,9 M penerimaan Juli–Oktober.
- **Pembayaran di muka.**
  - Cicilan biaya masuk banyak dibayar Januari–Juni, sebelum tahun ajaran (Jan 7, Mar 8, Apr 8, Mei 5, Jun 28).
  - SPP Juli dibayar sebagian di Juni (11), Mei, dan April.
  - Secara akuntansi, uang ini masuk periode 2025/2026 sebagai pendapatan diterima di muka. Sistem perlu aturan untuk ini sebelum data historis dimasukkan.
- **Katering:** 129/129 nominal kelipatan Rp 22.000, sesuai tarif harian × hari makan. Ini cocok dengan perhitungan sistem (tarif katering × hari hadir dengan katering).
- **Jemputan:** nominal bervariasi (Rp 21 rb–108 rb dan seterusnya). Cocok dengan model sistem: tarif per siswa × perjalanan.
- **Cicilan:** hingga 4 cicilan terpakai (CIL 1 103 siswa, CIL 2 49, CIL 3 20, CIL 4 1). Batas "dicicil hingga September" belum ada di sistem.

## Kebutuhan di sheet dibandingkan dengan sistem

| Kebutuhan | Sistem sekarang | Status |
|---|---|---|
| Biodata siswa | Data Siswa + impor CSV (Batch 4–5) | Ada |
| Tarif SPP per siswa | `Siswa.spp_nominal`; 76 siswa baru masih Rp 0 | Ada, data belum terisi |
| Biaya masuk per siswa + diskon | Batch 3 (Uang Masuk, Pengembangan, Kegiatan, Seragam + PG/SIPG/SIB/SIKBR) | Sebagian: Komite dan Portofolio tetap dari daftar harga; kategori SBD/KHUSUS/PINDAHAN belum ada |
| Cicilan biaya masuk | Penerimaan sebagian per komponen | Ada; tanpa batas tanggal cicilan |
| Tagihan bulanan SPP + katering + jemputan | Generate tagihan per bulan/kelompok dari absensi | Ada, belum dipakai rutin (7 tagihan) |
| Catatan penerimaan per bulan (master) | Pembayaran tagihan → jurnal DRAFT → dicatat Keuangan | Ada, belum dipakai; data Juli–Okt masih di sheet |
| Invoice tunggakan per siswa | `InvoicePreview` per tagihan, Tunggakan Tagihan | Sebagian: belum ada invoice gabungan semua tunggakan siswa dengan rekening dan kontak |
| LSU (paket per pertemuan) | Belum ada | Belum |
| Pesanan seragam/buku tambahan (Putih/Olga/Batik, Jilid, Pra + Prestasi) dan ukuran seragam | Komponen LAIN di tagihan manual; ukuran tidak tersimpan | Sebagian |
| Status BARU/NAIK KELAS/LANJUTAN/MENGULANG | `tipe_tp` + `status` | Sebagian |
| Pembayaran di muka (sebelum periode) | Belum ada aturan | Belum |

## Usulan otomatisasi (urut dampak)

1. **Impor tarif dari tab master** (tier 3, uang). Alurnya sama dengan impor biodata: unggah CSV master, pratinjau per siswa, lalu Simpan.
   - Sumber nilai:
     - SPP diambil dari nilai SPP terbanyak.
     - Biaya masuk dan diskon langsung dari kolom komponen.
   - Nilai yang tidak bisa dipakai sebagai tarif ditandai untuk dicek manual: nominal di atas 2× tarif kelas, atau SPP berbeda antar bulan.
   - Ini sekaligus mengisi **SPP 76 siswa baru**.
2. **Mulai mencatat penerimaan di sistem** mulai satu bulan potong (mis. November 2026). Ada dua pilihan:
   - **Saldo awal per siswa** (rekomendasi): tagihan biaya masuk dibuat dengan penerimaan historis satu baris per siswa sampai Oktober, lalu tagihan bulanan dibuat normal mulai November.
   - **Migrasi penuh** Juli–Oktober (tagihan + semua pembayaran per tanggal): lebih lengkap, tetapi butuh keputusan akuntansi soal pembayaran di muka dan jurnal yang sudah dicatat manual.
3. **Invoice gabungan per siswa**: satu halaman cetak/WA berisi semua tunggakan (tahunan, bulanan, item lain), batas cicilan, rekening, dan kontak per jenjang. Ini menggantikan tab INV TK/PG.
4. **Kategori diskon dan tarif khusus**: tambah SBD, KHUSUS, PINDAHAN. Perlu aturan apakah PINDAHAN dihitung prorata otomatis dan SBD sebagai tarif khusus.
5. **Validasi daftar harga 26/27**: Kegiatan TK baru 5 jt, Seragam TK 500 rb, Seragam PG 250 rb, sesuai sheet.
6. **Modul LSU**: paket 8/16 pertemuan, sisa pertemuan, tagihan per paket, dan pencatatan pertemuan.
7. **Item tambahan dan ukuran seragam**: katalog item (seragam per jenis/ukuran, buku jilid, Pra + Prestasi) dengan status ditagih/belum, ditambah kolom ukuran seragam di siswa.

## Pertanyaan untuk sekolah

1. Daftar harga 26/27 yang benar: Kegiatan TK baru 5 jt atau 4,5 jt? Seragam TK 500 rb dan PG 250 rb?
2. Arti dan aturan SBD, KHUSUS, PINDAHAN (potongan tetap, tarif khusus, atau prorata).
3. LSU itu layanan apa? Apakah paketnya selalu 8 pertemuan Rp 600 rb, dan apakah sisa pertemuan hangus di akhir tahun?
4. Mulai bulan apa sekolah mau berhenti mencatat penerimaan di sheet dan pindah ke sistem?
5. Apakah pembayaran sebelum Juli sudah dicatat di pembukuan 2025/2026 (sebagai pendapatan diterima di muka)?
