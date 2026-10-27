# Revisi dari spreadsheet pengguna — 28 Oktober 2026

Sumber: spreadsheet revisi per role dari pengguna (Google Sheets, 1 tab, 37 baris). Proyek tidak lagi terikat skripsi, jadi keputusan desain cukup mengikuti kebutuhan sekolah.

Status: **Batch 1 selesai** di branch `codex/auto-deploy-fe-be` (belum di `main`/produksi). Batch 2 dan 3 menunggu keputusan pengguna.

## Batch 1 — selesai

| Role · menu | Permintaan | Hasil |
|---|---|---|
| Kepsek/Keuangan · Beranda | Tampilan per Hari/Bulan/Periode; periode mengikuti tahun ajaran | Filter Hari / Bulan / Periode, default periode akuntansi yang memuat hari ini. Backend `dashboard/ringkasan`, `laporan/laba-rugi`, `dashboard/laba-rugi-bulanan`, `dashboard/prediksi-kas` menerima `?periode=<id>`; ringkasan per hari kini benar-benar per tanggal (sebelumnya angka keuangan memakai bulan). |
| Beranda (masukan tambahan) | Lebih berwarna dan interaktif | KPI berwarna dan bisa diklik (Pendapatan → Pemasukan, Beban → Pengeluaran, Surplus → Laporan); baris operasional (siswa aktif, catatan hadir + sparkline, tagihan belum lunas, tingkat pelunasan); klik batang grafik bulanan membuka bulan itu; serapan kegiatan berwarna; realisasi melewati pagu ditandai merah. |
| Admin TU · Absensi Pegawai | Nama urut abjad; rekap bulanan bisa diunduh Excel | Harian dan rekap urut abjad (locale `id`); tombol **Unduh Excel** membuat `.xlsx` asli tanpa dependensi baru (`core/export.ts`). |
| Admin TU · Katering | Menu mingguan → bulanan | Tab **Menu bulanan**: semua hari Senin–Jumat dalam bulan, dikelompokkan per minggu, ringkasan "x dari y hari terisi". |
| Admin TU · Pendaftaran | Belum ada aksi Edit/Hapus di daftar | Tombol Ubah/Hapus di tiap baris (desktop dan kartu ponsel) untuk calon yang belum punya penerimaan/siswa. Aturan kunci tetap: setelah ada penerimaan, ubah/hapus tidak tersedia. |
| Kepsek/Keuangan · Gaji | Jabatan diambil otomatis dari Data Pegawai | Form slip menampilkan "Jabatan: … · diambil otomatis dari Data Pegawai"; daftar slip menampilkan jabatan di bawah nama. |
| Guru · Absensi Siswa | "Ya, dijemput" → "Ya" | Teks tersebut tidak ada di kode versi revamp (label kini "Jemput datang/pulang" berupa centang). Kemungkinan dilihat dari versi lama sebelum rilis 28/10. Perlu konfirmasi layar yang dimaksud. |
| Admin TU · Jemputan | Harga per bulan → per 1 kali jalan | Sudah begitu di versi revamp: "Tarif / perjalanan", tagihan = (datang + pulang) × tarif. Tidak ada perubahan. |

## Batch 2 — akses role dan aturan (tier 3, belum dikerjakan)

- Menu per role mengikuti spreadsheet: Guru → Absensi Siswa; Kepsek → Data/Absensi Pegawai hanya-lihat; Anggaran + Kegiatan digabung menjadi "Anggaran Kegiatan" (Kepsek hanya-lihat); Keuangan → Data Siswa, Pendaftaran, Jurnal; Admin TU → Pemasukan/Pengeluaran.
- Kasbon: diajukan Kepsek, dicairkan Keuangan; Keuangan tidak bisa mengajukan.
- Kepsek membuat slip gaji.
- Pengeluaran tanpa approval Kepsek, dengan aksi edit/hapus (POSTED dikoreksi lewat reversal).
- Status pegawai Aktif / Cuti / Non-aktif (migrasi `status_aktif` → `status`).

## Batch 3 — Data Siswa (tier 3, perlu desain)

- Checklist diskon PG/SIPG/SIB/SIKBR + nominal diskon manual.
- Input manual Uang Masuk, Uang Kegiatan, Uang Pengembangan, Uang Seragam.
- Aksi "Catat Penerimaan" dengan pembayaran sebagian per komponen, terhubung ke tagihan.

## Temuan saat verifikasi

- Periode `2026/2027` di DB demo lokal tersimpan 30/06/2026 – 29/06/2027 (bukan 01/07 – 30/06). Kemungkinan pergeseran zona waktu saat seed/impor. Perlu dicek di produksi sebelum filter Periode dipakai sebagai acuan.
