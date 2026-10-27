# Revisi dari spreadsheet pengguna — 28 Oktober 2026

Sumber: spreadsheet revisi per role dari pengguna (Google Sheets, 1 tab, 37 baris). Proyek tidak lagi terikat skripsi, jadi keputusan desain cukup mengikuti kebutuhan sekolah.

Status: **Batch 1 dan 2 selesai** di branch `codex/auto-deploy-fe-be` (belum di `main`/produksi). Batch 3 menunggu desain.

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

## Batch 2 — akses role dan aturan (tier 3) — selesai di branch kerja

Disetujui pengguna dengan semua rekomendasi (keputusan 1–9). Belum di produksi; rilis menjalankan migrasi `operations.0016`.

| Role | Perubahan |
|---|---|
| Kepala Sekolah | Menu baru: Pegawai (lihat), Absensi Pegawai (hanya tab rekap), Gaji (buat/ubah slip, tanpa posting), Kasbon (mengajukan). "Anggaran" dan "Kegiatan" digabung menjadi **Anggaran Kegiatan** (hanya lihat; tab Per kegiatan / Per akun). Tetap menyetujui/menolak jurnal dari Beranda. |
| Staf Keuangan | Menu baru: Data siswa dan Pendaftaran (hanya lihat), Jurnal (semua sumber). Anggaran Kegiatan: membuat/mengubah kegiatan + Guru PJ. Kasbon: mengubah dan mencairkan, tidak bisa mengajukan. Gaji: tetap satu-satunya yang membuat jurnal gaji. |
| Guru PIC | Absensi Siswa (isi dan ubah). Realisasi kegiatan tetap oleh Guru; Kepala Sekolah tidak lagi mencatat realisasi. |
| Staf TU | Pemasukan/Pengeluaran: membuat draf jurnal; hanya draf buatan sendiri yang bisa diubah/dihapus; pencatatan ke buku besar oleh Keuangan. |
| Semua | Status pegawai Aktif / Cuti / Non-aktif (`Pegawai.status`, migrasi `0016`; `status_aktif` tetap ada sebagai turunan). Cuti tidak masuk absensi harian, tetap bisa gaji/kasbon. |

Pengeluaran tanpa approval Kepsek sudah berlaku sebelumnya (Keuangan "Catat ke buku besar"); jurnal POSTED tetap dikoreksi lewat jurnal pembalik oleh Kepala Sekolah (keputusan 5).

**Pengecualian pemisahan tugas yang disetujui:** Kepala Sekolah mengajukan kasbon dan membuat slip gaji, lalu juga menyetujui jurnal pencairan/gaji yang dibuat Keuangan.

Verifikasi: tes matriks akses `operations/test_role_access.py`; 27 skenario API di DB UAT (kasbon, gaji, absensi Guru, kegiatan + PJ, draf jurnal TU, status Cuti, akses baca); migrasi `0016` diterapkan, dibalik, dan diterapkan ulang di UAT (backup `~/Backups/beesmartfinance/bee_uat_browser_20261020-20261028-052134-before-0016.dump`). Data uji UAT: kegiatan dan jurnal berawalan `UAT-B2`, plus satu kasbon (draf pencairan) dan satu slip gaji November 2026 untuk pegawai pertama.

**Belum:** `db_lebah_madu` lokal masih di `0015`, sehingga server demo :8000 dengan kode branch ini gagal pada endpoint pegawai sampai migrasi `0016` dijalankan (perlu izin + backup).

## Batch 3 — Data Siswa (tier 3, perlu desain)

- Checklist diskon PG/SIPG/SIB/SIKBR + nominal diskon manual.
- Input manual Uang Masuk, Uang Kegiatan, Uang Pengembangan, Uang Seragam.
- Aksi "Catat Penerimaan" dengan pembayaran sebagian per komponen, terhubung ke tagihan.

## Temuan saat verifikasi

- Periode `2026/2027` di DB demo lokal tersimpan 30/06/2026 – 29/06/2027 (bukan 01/07 – 30/06). Kemungkinan pergeseran zona waktu saat seed/impor. Perlu dicek di produksi sebelum filter Periode dipakai sebagai acuan.
