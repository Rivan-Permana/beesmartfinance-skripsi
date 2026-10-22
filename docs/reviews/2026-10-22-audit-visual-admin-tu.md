# Audit visual role Admin TU — 22 Oktober 2026

Audit browser pertama dari matriks route × role × viewport yang direncanakan pada [state analysis 21 Oktober](./2026-10-21-state-analysis.md). Dokumen ini hanya mencatat temuan; belum ada perbaikan.

## Cakupan dan metode

- Role: `admin.tu` (Bu Fitri, Staf TU) pada database demo lokal `db_lebah_madu`.
- Lingkungan: Vite `localhost:5173` → Django `127.0.0.1:8000`, branch `codex/auto-deploy-fe-be`.
- Viewport: desktop 1440×900 dan mobile 375×812 (emulasi Android Chrome).
- Route: `/siswa`, `/kelompok`, `/absensi-siswa`, `/rekap-siswa`, `/katering`, `/jemputan`, `/tagihan`, `/pendaftaran`, `/pegawai`, `/absensi-pegawai`.
- Hanya baca. Modal dibuka lalu ditutup tanpa simpan. Satu-satunya submit adalah form Tambah siswa dengan nama kosong untuk memicu validasi klien; tidak ada data yang berubah.
- Pemeriksaan otomatis per route: overflow horizontal, tombol/tautan tanpa nama aksesibel, input tanpa label, teks <12px, input <16px di mobile, target sentuh <24px (desktop) / <44px (mobile).
- Screenshot tersimpan di folder sesi lokal, tidak di repo, sesuai aturan handoff.

## Temuan

Tingkat: **Tinggi** mengganggu tugas inti atau demo; **Sedang** membingungkan atau melanggar pola bersama; **Rendah** polesan.

### Tinggi

**D1. Database demo berisi data uji UAT.**
Ada 6 siswa bernama `UAT-…`/`UAT Calon Demo` (tanpa NIS, status aktif) beserta tagihannya. Daftar Pendaftaran berisi 6 dari 6 entri UAT, semuanya "Perlu dicocokkan" dengan biaya "Belum diketahui".
Data ini muncul di baris teratas Tagihan dan di seluruh Pendaftaran, sehingga akan terlihat saat sidang. Temuan ini juga bertentangan dengan dokumen UAT yang menyebut alur tulis dijalankan di database terpisah.
Reproduksi: login `admin.tu` → `/tagihan` atau `/pendaftaran`; atau `GET /api/v1/siswa/?search=UAT` (count 6).

Status 22 Oktober: dibersihkan di database demo lokal setelah backup (`~/Backups/beesmartfinance/`). Dihapus: 7 siswa uji (6 `UAT-…` dan `rivan` NIS 1234), 42 absensi, 1 peserta jemputan, 7 tagihan, 6 pendaftaran, 2 kegiatan UAT beserta realisasinya, dan 10 jurnal draf. Sembilan jurnal POSTED dilindungi trigger, jadi dibalik dengan jurnal `REV-…` bertanggal sama (28 Juni dan 2 Juli 2026). Kas di dashboard turun dari Rp 202.250.000 menjadi Rp 200.350.000 (−Rp 1.900.000), sesuai dampak data uji.

**A2. Absensi siswa sulit dipakai untuk kelompok besar.**
Setiap siswa adalah kartu tinggi dengan 4 tombol kehadiran dan 3 checkbox layanan. "Simpan absensi" hanya ada di dasar halaman dan tidak sticky. Tidak ada aksi massal (mis. semua hadir) dan tidak ada pencarian di dalam daftar.

| Kelompok | Viewport | Tinggi halaman | Posisi tombol simpan |
| --- | --- | --- | --- |
| TKA Melati (77 siswa) | Desktop | ±17.400px | y ±17.290 |
| PG Merah (25 siswa) | Mobile | ±11.900px | y ±11.800 |

Sebagai pembanding, Absensi pegawai sudah punya kolom pencarian dan baris yang lebih ringkas.
Reproduksi: `/absensi-siswa` → TK A → TKA Melati → Tampilkan siswa.

Status 22 Oktober (commit 41e4e95): diperbaiki dengan pencarian nama/NIS, dua aksi massal untuk siswa yang ditampilkan, bar simpan sticky, dan kartu yang lebih padat. Hasil untuk TKA Melati (77 siswa):

| Viewport | Tinggi kartu | Tinggi halaman |
| --- | --- | --- |
| Desktop 1440px | ±225 → 133px | ±17.400 → ±11.300px |
| Mobile 375px | ±435 → 205px | ±34.800 → ±17.200px |

### Sedang

**G1. Fokus input tidak bisa dibedakan dari error.**
Input yang fokus hanya mengganti border 1px ke primary `#B01862`, tanpa ring. Warna error `#B13447` nyaris sama, sehingga field kosong yang baru difokuskan terlihat seperti error. Ini berlaku di semua form karena berasal dari tema bersama.
Catatan: fokus tombol sudah baik (outline 3px, offset 3px).

Status 22 Oktober (belum di-commit): input, textarea, dan select yang fokus kini mendapat cincin 2px; field tidak valid tetap berbingkai merah, dan saat difokus cincinnya ikut merah.

**G2. Navigasi sidebar memakai `<button>`, bukan tautan.**
`nav.app-navigation` berisi `<button>` dengan `aria-current="page"`. Akibatnya menu tidak bisa dibuka di tab baru atau disalin tautannya, dan pembaca layar mengumumkannya sebagai tombol. Komponen bersama, jadi berlaku untuk semua role.

Status 22 Oktober (belum di-commit): menu diganti `RouterLink` (`<a href>`); navigasi tetap tanpa reload dan drawer mobile tetap menutup.

**S1. Paginasi menyembunyikan jumlah halaman.**
Paginator hanya menampilkan halaman 1–3 dan prev/next, tanpa halaman pertama/terakhir, total halaman, atau pilihan jumlah baris.
- Data siswa: 164 siswa, 10 per halaman, 17 halaman; butuh 16 klik untuk mencapai halaman terakhir.
- Katering: 162 siswa, 15 per halaman.

Ukuran halaman juga berbeda-beda: Siswa 10, Katering/Pegawai 15, Rekap 20.

**A1. Validasi filter Absensi siswa.**
Menekan "Tampilkan siswa" tanpa pilihan memberi error pada Jenjang dan juga pada Kelompok, padahal Kelompok masih disabled. Pesan error juga menggeser baris: label Tanggal dan tombol tidak lagi sejajar dengan Jenjang/Kelompok.

Status 22 Oktober (belum di-commit): baris filter memakai grid label/input/error bersama, jadi pesan error tidak menggeser field lain; error Kelompok baru muncul setelah Jenjang dipilih.

**K1. Siswa aktif tanpa kelompok tidak terlihat dari halaman Kelompok.**
Data siswa menghitung 164 siswa, Kelompok menghitung 157 "siswa aktif dalam kelompok", dan Rekap/Katering 162. Selisih 7 adalah siswa aktif tanpa kelompok (6 di antaranya data UAT dari D1).
Halaman Kelompok tidak menandai mereka, dan alur "Pindah siswa" mensyaratkan kelompok asal, sehingga siswa ini hanya bisa ditempatkan lewat edit profil.

**T1. Tombol chevron di Tagihan membuka menu aksi, bukan rincian.**
Tombol berikon chevron berlabel aksesibel "Rincian tagihan …" ternyata membuka menu (`role=menu`) berisi Riwayat pembayaran, Lihat faktur, Ubah tagihan, dan Batalkan tagihan. Ikon chevron mengesankan baris akan dibuka, padahal ada aksi destruktif di dalamnya.

**T2. "Simpan pembayaran" aktif saat nominal Rp 0.**
Di dialog Catat pembayaran, tombol simpan sudah aktif sebelum nominal apa pun diisi. Tombol tidak diklik, jadi respons validasinya belum diverifikasi.

**G3. Pola antar halaman tidak konsisten.**
- Sub-navigasi: tab bergaris bawah (Kelompok, Absensi pegawai) vs kontrol segmen (Katering, Jemputan).
- Aksi header: tombol outline (Absensi siswa, Rekap, Pegawai) vs tautan teks berwarna primary (Katering, Jemputan "Buka absensi").
- Ikon hapus: abu-abu di Data siswa, merah di Jemputan.
- Pemilih periode: "Bulan rekap" satu select di Rekap absensi vs dua select bulan + tahun di Katering.
- Pencatatan kehadiran: Absensi siswa memakai grid 2×2 dengan latar merah muda dan ikon centang, opsi "Tidak hadir". Absensi pegawai memakai deret tombol ringkas berisi penuh, opsi "Terlambat"/"Tanpa catatan", dan punya pencarian.

### Rendah

- **M1.** Di mobile, tombol aksi header (Rekap: 3 tombol, terbungkus 2 baris) dan kartu filter menghabiskan layar pertama, sehingga data baru terlihat setelah scroll. Terjadi di Rekap absensi, Tagihan, dan Katering.
- **M2.** Di mobile, nama dan role pengguna (Bu Fitri, Staf TU) tidak tampil di header maupun drawer, padahal di desktop tampil di kanan atas.
- **M3.** Kartu Rekap absensi di mobile sekitar 310px per siswa (20 kartu per halaman), sehingga perbandingan antar siswa sulit.
- **L1.** Pendaftaran memakai marker native `▶` untuk "Alur calon, penerimaan, dan finalisasi", tidak seragam dengan ikon Phosphor.
- **L2.** Label rentang minggu di Menu mingguan Katering terpotong menjadi dua baris di kotak sempit.
- **L3.** Jenjang yang hanya punya satu kelompok (Playgroup → PG Merah, TK A → TKA Melati) tetap mewajibkan pilih kelompok manual.
- **L4.** Absensi siswa memuat siswa per 25 secara berurutan (77 siswa = 4 request), karena `page_size` diabaikan API. Lokal cepat (<50ms/request); dampaknya baru terasa di jaringan lambat.

## Yang diperiksa dan tidak bermasalah

- Tidak ada overflow horizontal di 10 route × 2 viewport.
- Tidak ditemukan tombol tanpa nama aksesibel, input tanpa label, teks <12px, maupun input <16px di mobile.
- Di mobile, kontrol utama (tombol kehadiran 151×44, hamburger 44×44, Keluar 44×44) sudah memenuhi target sentuh.
- Dialog Tambah siswa:
  - fokus otomatis ke field pertama, `aria-modal`, judul tertaut;
  - Escape menutup dan fokus kembali ke pemicu;
  - error memakai `aria-invalid` + `aria-describedby`;
  - di mobile footer tetap terlihat dan konten bisa di-scroll.
- Drawer navigasi mobile memindahkan fokus ke tombol tutup dan menandai halaman aktif.
- Tidak ada error console dari aplikasi. Dua 401 berasal dari probe audit; dua lainnya adalah token kedaluwarsa yang langsung di-refresh (200) oleh interceptor.

## Belum dicakup

- Cetak (faktur, struk) dan state error/kosong saat API mati.
- Tab Jenjang, Rekap jemputan, Pendaftaran siswa (Jemputan), rincian Pendaftaran, dan Rekap bulanan pegawai.
- Seluruh alur tulis (sengaja tidak disubmit di database demo).
- Safari/iPad, pembaca layar nyata, dan zoom 200%.
- Tiga role lain: Keuangan, Kepala Sekolah, Guru PIC.

## Usulan urutan perbaikan

1. D1 diputuskan terpisah: bersihkan data UAT dari database demo, atau reset dengan `seed_demo`. Keduanya mengubah data, jadi butuh persetujuan dan backup dulu.
2. A2, karena tugas harian inti dan paling terasa di mobile.
3. G1 dan G2 di komponen/tema bersama, karena memperbaiki semua role sekaligus.
4. S1, A1, T1, T2, K1.
5. G3 dan temuan Rendah setelah pola bersama diputuskan.
