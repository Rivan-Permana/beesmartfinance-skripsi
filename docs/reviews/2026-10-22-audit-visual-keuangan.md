# Audit visual role Keuangan — 22 Oktober 2026

Lanjutan [audit Admin TU](./2026-10-22-audit-visual-admin-tu.md). Semua temuan di bawah sudah diperbaiki pada 22 Oktober; lihat bagian Status perbaikan.

## Cakupan dan metode

- Role `keuangan` (Staff Keuangan), database demo lokal, branch `codex/auto-deploy-fe-be` (`485d967`).
- Route: `/dashboard`, `/jurnal`, `/jurnal?jenis=masuk`, `/tunggakan-tagihan`, `/gaji`, `/pinjaman`, `/aset`, `/anggaran`, `/periode`, `/coa`, `/laporan`, `/audit-log`. Pegawai dan Absensi pegawai sudah tercakup di audit Admin TU.
- Setiap route dimuat di iframe 1440px dan 375px, lalu diperiksa lewat DOM: overflow horizontal, tombol tanpa nama, target sentuh, teks <12px, kesejajaran kolom aksi, jenis paginator, error JavaScript. Halaman bermasalah diperiksa lebih dalam.
- Hanya baca; tidak ada data yang diubah.

## Lolos di semua route

Tidak ada overflow horizontal halaman, tidak ada tombol tanpa nama aksesibel, tidak ada error JavaScript, di kedua lebar.

## Temuan

### Tinggi

**K-L1. Neraca saldo menampilkan semua akun, termasuk ±177 dari 191 yang bersaldo nol.**
Laporan jadi sulit dibaca. Di 375px tabelnya setinggi ±17.300px dan bergeser horizontal (680px di wadah 303px); halaman Laporan total ±18.200px. Saat ini akun nol hanya disembunyikan ketika dicetak.
Usul: sembunyikan akun bersaldo nol secara bawaan dengan sakelar "Tampilkan akun bersaldo nol", dan kartu ringkas di mobile.

### Sedang

**K-A1. Kolom aksi Gaji tidak sejajar dengan header.**
Kolom memakai grid dua jalur (tombol + 44px untuk menu ⌄). Pada baris tanpa menu, jalur kedua kosong sehingga "Lihat slip" berhenti 56px sebelum tepi header "Tindakan" (tombol berakhir di 1327px, header di 1383px).

**K-A2. Header "Aksi" di Anggaran dan Daftar akun (COA) rata kiri, tombolnya di kanan.**
Anggaran: header 1239–1265px, tombol 1329–1370px. COA: header 1252–1278px, tombol 1341–1382px. Halaman lain memakai header "Tindakan" rata kanan.

**K-P1. Tiga daftar masih memakai paginator bawaan DataTable**, berbeda dari pager bersama: Anggaran, Periode akuntansi, Log audit.

### Rendah

- **K-T1.** Teks 11,7px (di bawah 12px) pada nomor bukti di Dashboard ("DFT-202610-02 · 2026"), keterangan "Tanpa saldo awal" di COA mobile, dan periode tagihan di Tunggakan mobile.
- **K-T2.** Tombol geser tab analisis di Dashboard mobile 40×50px, di bawah target sentuh 44px (komponen bawaan PrimeVue).
- **K-L2.** Locale PrimeVue belum menerjemahkan teks bantu komponen Password; layar login masih memuat "Enter a password".
- **K-N1.** Label kolom aksi belum seragam: "Tindakan" (sebagian besar), "Aksi" (Anggaran, COA, Periode), "Rincian" (Jurnal).

## Status perbaikan (22 Oktober)

| Temuan | Perbaikan | Bukti setelah perbaikan |
| --- | --- | --- |
| K-L1 | Neraca saldo menyembunyikan akun tanpa mutasi (debit, kredit, saldo nol); sakelar "Tampilkan N akun tanpa mutasi"; disembunyikan juga saat cetak | 191 → 16 baris; total tetap Rp 755.150.000 / Rp 755.150.000 sebelum dan sesudah sakelar; halaman 375px 2.323px |
| K-A1 | Tombol tunggal di kolom Gaji mengisi kedua jalur grid | Tepi tombol/ikon terakhir 1383px = tepi header |
| K-A2, K-N1 | "Aksi" → "Tindakan", rata kanan (aturan bersama untuk kolom `bee-col-actions`, COA) | Anggaran 1382px, COA 1382px vs header 1383px |
| K-P1 | Anggaran dan Log audit memakai pager bersama; Periode tanpa paginasi (satu baris per tahun pelajaran) | Tidak ada lagi paginator bawaan DataTable |
| K-T1 | `small` mengikuti token caption (13px), bukan `smaller` bawaan browser | Tidak ada teks <12px di Dashboard, COA, Tunggakan |
| K-T2 | Tombol geser tab 44px | 44×50px di 375px |
| K-L2 | Locale Password: "Masukkan kata sandi", Lemah/Sedang/Kuat | Layar login tidak lagi memuat teks Inggris |

Label "Rincian" di Jurnal dipertahankan: kolom itu memang hanya berisi tombol rincian.

## Kepala Sekolah dan Guru PIC (22 Oktober)

Route Kepala Sekolah (`/dashboard`, `/jurnal`, `/kegiatan`, `/tunggakan-tagihan`, `/anggaran`, `/periode`, `/coa`, `/laporan`, `/audit-log`) dan Guru PIC (`/kegiatan`, `/rekap-siswa`) diaudit dengan cara yang sama. Tidak ada overflow, tombol tanpa nama, atau teks <12px.

| Temuan | Perbaikan | Bukti |
| --- | --- | --- |
| Kolom "Tindakan" Kegiatan rata kiri, tombol di kanan (header 1167px, tombol 1378px) | Header dan tombol rata kanan | Ikon terakhir 1379px = tepi header (Kepala Sekolah dan Guru PIC) |
| Laporan dan Log audit sesekali melempar pengguna ke login | Penyebab: COA dimuat 25 baris per request (8 request) sehingga batas 120/menit tercapai, lalu `init()` menghapus token untuk error apa pun termasuk 429. Kini token hanya dihapus pada 401, dan semua loader daftar meminta 200 baris per request | COA 8 → 1 request; Laporan, Log audit, Kegiatan, COA dimuat tanpa dialihkan ke login |

## Belum dicakup

Cetak laporan, dialog tulis (jurnal baru, posting, slip gaji, tutup buku), state error API, Kepala Sekolah dan Guru PIC.
