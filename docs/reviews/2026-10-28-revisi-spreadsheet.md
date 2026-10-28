# Revisi dari spreadsheet pengguna — 28 Oktober 2026

Sumber: spreadsheet revisi per role dari pengguna (Google Sheets, 1 tab, 37 baris). Proyek tidak lagi terikat skripsi, jadi keputusan desain cukup mengikuti kebutuhan sekolah.

Status: **Batch 1–3 dirilis ke produksi 28/10/2026** lewat PR #22 (merge `23895b4`, 04:59 UTC). Deploy otomatis: backup `backups/db-20261028T050005Z.dump`, migrasi `operations.0016`/`0017` (05:00:22 UTC), backend aktif 05:00:54, Worker (`index-BO5I_TBs.js`) aktif 05:01:55. Cek pasca-rilis (read-only via web console): container running, pegawai 33 aktif + 1 nonaktif, 7 tagihan Bulanan, 18 jurnal dan 33 siswa sama dengan sebelum rilis, periode 2026/2027 01/07/2026 – 30/06/2027. Smoke test login per role dilakukan pengguna.

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

**Lokal:** `db_lebah_madu` sudah dimigrasi ke `0016` (28/10, backup `~/Backups/beesmartfinance/db_lebah_madu-20261028-070659-before-0016.dump`); 36 pegawai berstatus aktif.

## Batch 3 — Data Siswa: biaya masuk dan diskon (tier 3) — selesai di branch kerja

Disetujui pengguna dengan opsi A dan keputusan 1–6 sesuai rekomendasi. Rilis menjalankan migrasi `operations.0017`.

| Bagian | Perubahan |
|---|---|
| Form Data Siswa | Bagian **Biaya masuk**: Uang Masuk, Uang Pengembangan, Uang Kegiatan, Uang Seragam (input manual, tombol "Isi dari daftar harga" sesuai jenjang); checklist status diskon PG/SIPG/SIB/SIKBR (label, boleh lebih dari satu) + jumlah diskon manual. Ringkasan total, diskon, dan yang ditagihkan. |
| Tagihan | Simpan siswa membuat/memperbarui satu tagihan jenis **Biaya masuk** (`Tagihan.jenis`). Diskon dicatat netto, memotong Uang Masuk → Pengembangan → Kegiatan → Seragam, tercatat di keterangan baris. Tagihan biaya masuk tampil di menu Tagihan ("Biaya masuk · Bulan Tahun") dan hanya diubah lewat Data Siswa. |
| Daftar siswa | Kolom status biaya masuk (Belum dibayar / Sebagian / Lunas + sisa) dan aksi **Catat penerimaan** untuk Staf TU, memakai dialog pembayaran sebagian per komponen yang sama dengan menu Tagihan. Jurnal penerimaan DRAFT, dicatat ke buku besar oleh Keuangan. |
| Aturan | Komponen yang sudah ada penerimaannya terkunci nominalnya. Komponen yang sudah ditagih di tagihan bulanan 12 bulan terakhir ditolak (mencegah tagihan ganda); sebaliknya tagihan Juli dari daftar harga melewati komponen yang sudah ada di biaya masuk. Iuran Komite dan Portofolio tetap dari daftar harga. |
| Skema (`0017`) | Kolom `diskon_kategori`, `diskon_nominal`, `uang_masuk`, `uang_kegiatan`, `uang_pengembangan`, `uang_seragam` di siswa; `Tagihan.jenis` (BULANAN/BIAYA_MASUK); unik tagihan per siswa + bulan + tahun + jenis, hanya untuk tagihan yang tidak dihapus. Balik migrasi menolak jalan bila masih ada tagihan biaya masuk. |

Verifikasi: tes `operations/test_biaya_masuk.py` (7 tes); 13 skenario API di DB UAT (backup `~/Backups/beesmartfinance/bee_uat_browser_20261020-20261028-101907-before-0017.dump`; `0017` diterapkan, dibalik, diterapkan ulang); penerimaan sebagian lewat UI; cek DOM desktop dan 375 px. Lokal: `db_lebah_madu` dimigrasi ke `0017` (backup `~/Backups/beesmartfinance/db_lebah_madu-20261028-102237-before-0017.dump`). Data uji UAT: siswa Bima Sakti dengan tagihan biaya masuk (diskon SIB, tiga penerimaan berawalan `UAT-B3`) dan tagihan bulanan Oktober 2026.

**Cek sebelum rilis (selesai):** tidak ada siswa yang biaya masuknya sudah tertagih sejak Agustus 2025, jadi semua siswa aktif bisa diisi; periode 2026/2027 sudah dikoreksi.

## Cek read-only produksi — 28/10/2026 (persiapan rilis Batch 1–3)

Sesi `default_transaction_read_only = on`; tidak ada perubahan.

- Produksi = `main` `cec1df7`; branch kerja 7 commit di depan, 0 di belakang. Migrasi produksi di `operations.0015`; rilis menerapkan `0016` dan `0017`.
- Container backend/caddy/db berjalan, db healthy; disk 7% terpakai. Backup terakhir `backups/db-20261027T210503Z.dump` (hanya di VPS, belum ada salinan luar).
- Dampak migrasi: `0016` mengubah 1 dari 34 pegawai (`status_aktif=false`) menjadi `nonaktif`; `0017` memberi 7 tagihan jenis Bulanan, tidak ada tagihan dihapus atau kunci ganda.
- Biaya masuk: belum ada komponen Uang Masuk/Pengembangan/Kegiatan/Seragam/Komite/Portofolio yang tertagih sejak Agustus 2025, jadi ke-32 siswa aktif bisa diisi biaya masuknya tanpa bentrok.
- **Periode `2026/2027` di produksi juga tersimpan 30/06/2026 – 29/06/2027.** Penyebab: form periode lama (sebelum revamp `bf1a06a`) mengirim tanggal lewat konversi UTC; form sekarang sudah memakai `formatLocalDate`. Koreksi data perlu persetujuan terpisah. Cek lanjutan (lewat web console hPanel, sesi read-only, karena SSH dari WARP Singapura timeout di IPv4 walau VPS tidak memblokir): periode `id=1` OPEN, tanpa trigger; jurnal bertanggal 28/09–03/11/2026, tidak ada di 30/06/2026 atau sesudah 29/06/2027; 2 jurnal tertaut `fiscal_period=1` (16 lainnya kosong); 2 anggaran dan 33 siswa tanpa periode; tidak ada saldo awal. Jadi koreksi tanggal ke 01/07/2026 – 30/06/2027 tidak memindahkan data apa pun antarperiode. Disetujui pengguna; lokal `db_lebah_madu` sudah dikoreksi (backup `~/Backups/beesmartfinance/db_lebah_madu-*-before-periode-fix.dump`). DB UAT tidak punya periode 2026/2027 (hanya periode uji `UAT-*`), jadi tidak berubah. Produksi dikoreksi pengguna lewat web console pada 28/10/2026 04:57 UTC: backup `backups/db-20261028T045714Z-before-periode-fix.dump` (248 KB, 50 tabel data), `UPDATE 1`, periode `id=1` kini 01/07/2026 – 30/06/2027 OPEN. Rollback: UPDATE kembali ke 30/06/2026 – 29/06/2027 atau restore backup tersebut.

## Temuan saat verifikasi

- Periode `2026/2027` di DB demo lokal tersimpan 30/06/2026 – 29/06/2027 (bukan 01/07 – 30/06). Kemungkinan pergeseran zona waktu saat seed/impor. Perlu dicek di produksi sebelum filter Periode dipakai sebagai acuan.

## Batch 4 — masukan WA Staf TU + keputusan review (tier 3) — selesai di branch kerja

Sumber: 4 screenshot WA dari Staf TU (Bu Fitri). Screenshot diambil dari **versi sebelum rilis 28/10** (tab "Menu Mingguan" minggu 19–23/10, kolom "Harga / bulan"), jadi dua masukan sudah terpenuhi di produksi. Disetujui pengguna: opsi 1 untuk Kelompok, migrasi `0018`, keputusan review 3a dan 3b ya, 3c dan 3d ditunda.

| Masukan / keputusan | Hasil |
|---|---|
| Gbr 1 · Data Siswa berisi data diri lengkap | Kolom baru **Nama panggilan, Jenis kelamin (L/P), Tempat lahir** (migrasi `operations.0018_siswa_data_diri`, tiga kolom boleh kosong, tanpa ubah data). Form disusun: NIS, status, nama lengkap, panggilan, jenis kelamin, tempat/tanggal lahir (tanggal lahir kini bisa diisi; sebelumnya tidak ada di form), kelompok, SPP; lalu alamat dan orang tua. Daftar siswa menampilkan "Panggilan · Laki-laki/Perempuan · NIS"; pencarian ikut nama panggilan. |
| Gbr 2 · Kelompok bisa diklik untuk cek nama | Nama kelompok (tabel dan kartu ponsel) membuka Data Siswa yang sudah terfilter kelompok itu (`/siswa?kelompok=<id>`); nama yang salah bisa langsung diubah. |
| Gbr 3 · Menu katering per bulan | Sudah ada sejak Batch 1 (tab **Menu bulanan**). Tidak ada perubahan. |
| Gbr 4 · Jemputan per hari, beda per anak, kadang antar saja | Sudah begitu sejak revamp: tarif per siswa per perjalanan, datang/pulang dicentang terpisah di absensi. Katering juga dicentang per hari, tapi tarifnya satu untuk semua anak. Tidak ada perubahan; perlu konfirmasi apakah katering juga perlu tarif per anak. |
| 3a · Guru tidak melihat nominal | `SiswaSerializer` menghapus SPP, biaya masuk, diskon, dan ringkasan biaya masuk dari respons untuk pengguna di luar Staf TU/Keuangan/Kepsek. Absensi Guru tidak memakai field itu. |
| 3b · Pesan ubah diskon | Bila diskon diubah setelah ada penerimaan: "Diskon tidak bisa diubah karena Uang Masuk sudah ada penerimaan dan diskon ikut memotong komponen itu. Minta Keuangan membatalkan penerimaan itu dulu bila diskon memang perlu diubah." |
| 3c, 3d | Ditunda (laporan diskon per kategori; biaya masuk kedua). |

Verifikasi: backend 149 tes OK (3 tes baru di `operations/test_biaya_masuk.py`); `makemigrations --check` bersih; frontend 33 berkas / 143 tes (2 tes baru di `SiswaWorkspace.test.ts`); `vue-tsc` + build bersih (peringatan chunk >500 kB tetap). Migrasi `0018`: backup `~/Backups/beesmartfinance/*-20261028-125413-before-0018.dump`; UAT diterapkan, dibalik, diterapkan ulang; lokal diterapkan. 9 skenario API UAT: TU ubah data diri 200, jenis kelamin salah 400, ubah diskon setelah penerimaan 400 dengan pesan baru, Guru GET daftar/detail tanpa field nominal, Guru PATCH 403, Keuangan tetap melihat nominal, Guru absensi 200. Data uji UAT: siswa Bima Sakti diberi panggilan "Bima", L, tempat lahir `UAT-B4 Bandung`, tanggal lahir 01/07/2021. Cek DOM lokal (Staf TU): klik "PG Merah" membuka `/siswa?kelompok=1` dengan filter terisi; form siswa tanpa overflow di desktop dan 375 px (satu kolom); tautan kelompok di kartu ponsel tinggi 44 px; halaman tanpa scroll horizontal.

Rilis: ikut rilis berikutnya bersama perbaikan 400 `siswa/biaya-masuk-default`; rilis menjalankan migrasi `0018`.

## Batch 5 — impor biodata siswa dari spreadsheet kelas (tier 3, data) — selesai di branch kerja

Sumber: spreadsheet biodata kelas (tab "RA Lebah Madu": Kelas, No., Nama Siswa, JK, Tempat, Tanggal Lahir, Usia, Alamat, Nama Ayah + No. Tlp, Nama Bunda + No. Tlp). Semua kolom sudah ada di `Siswa` setelah `0018`, jadi **tidak ada migrasi skema**. Data anak tidak dimasukkan ke git (bukan migrasi data); impor dijalankan Staf TU dari aplikasi. Disetujui pengguna dengan keputusan 1–4 sesuai rekomendasi, ditambah perapian alamat.

| Bagian | Hasil |
|---|---|
| Impor | Data Siswa → **Impor biodata** (Staf TU): unggah CSV (Google Sheets → File → Download → CSV), pratinjau tanpa menyimpan, pasangkan tiap nilai Kelas ke kelompok (saran otomatis dari nama kelompok; bisa "Jangan ubah kelompok"), lalu Simpan. Satu transaksi; riwayat siswa bertanda "Impor biodata CSV". Endpoint `POST /siswa/impor-biodata/` (multipart, `simpan=false` untuk pratinjau). |
| Aturan | Siswa dicocokkan lewat nama (tanpa beda huruf besar/kecil dan spasi); penulisan nama di sistem dipertahankan. Kolom biodata ditimpa isi berkas, sel kosong tidak menghapus data lama. Siswa baru: status aktif, SPP Rp 0, ditandai **Belum diisi** di kolom SPP. Data keuangan (SPP, biaya masuk, diskon) tidak disentuh; SPP 0 tidak menghasilkan baris tagihan. Nama ganda di berkas/sistem, JK selain L/P, tanggal tidak valid atau di masa depan, dan teks >100 karakter menjadi baris bermasalah yang dilewati. Impor ulang tidak membuat duplikat. |
| Perapian | Alamat: spasi/koma, `Jl.`, `Gg.`, `No.`, `Kel.`, `Kec.`, `RT 004/RW 003`, kapitalisasi per kata (singkatan seperti TNI dan nomor blok seperti C6 tetap huruf besar). HP: hanya angka, `62`/`+62` → `0`, angka 0 di depan yang dibuang spreadsheet ditambahkan lagi; nomor janggal ditandai "perlu dicek". Tanggal: `24-Nov-21`, `4-Agu-21`, `dd/mm/yyyy`, `yyyy-mm-dd`. Tempat lahir kapital di awal kata. |
| Usia | Dihitung otomatis dari tanggal lahir ("4 tahun 11 bulan"), tidak disimpan: tampil di bawah isian tanggal lahir dan di baris kedua nama pada daftar siswa. |

Verifikasi: backend 155 tes OK (6 tes baru `operations/test_impor_biodata.py`, data rekaan); frontend 34 berkas / 145 tes (`SiswaImport.test.ts` baru); `vue-tsc` + build bersih; `makemigrations --check` bersih. Pratinjau terhadap spreadsheet asli (tanpa menyimpan; hanya hitungan dibaca; salinan dihapus): **104 siswa** terbaca (8 kelas TK + Lebah 1, Lebah 2, Kepompong), baris rekap "Laki-laki/Perempuan/Jml" dilewati, 0 baris bermasalah, semua punya JK dan tanggal lahir, 2 nomor HP perlu dicek, 104 alamat dirapikan. 4 skenario API UAT dengan data rekaan `UAT-B5`: pratinjau, simpan (2 baru, 1 dilewati), impor ulang (2 sama), Keuangan 403. Cek DOM lokal (Staf TU, pratinjau CSV rekaan, tanpa simpan): tombol Impor biodata, dialog tanpa overflow di desktop dan 375 px, tombol dan pemilih berkas 44 px.

Belum dilakukan: impor ke produksi. Langkahnya setelah rilis: backup DB produksi → Staf TU unggah CSV → periksa pratinjau (terutama pemetaan kelas) → Simpan → isi SPP siswa baru sebelum tagihan November.
