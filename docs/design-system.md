# BeeSmart Finance — panduan implementasi UI/UX

18 Oktober 2026 · Fondasi 0.18 · Implementasi lokal bertahap, belum rilis.

## Mulai dari sini

Dokumen ini menjadi pintu masuk implementasi, bukan salinan token atau spesifikasi baru. Baca sumber berikut sesuai pekerjaan:

| Kebutuhan | Sumber yang digunakan |
|---|---|
| Aturan visual, tipografi, layout, copy, state, grafik, aksesibilitas, motion, referensi dan bukti pemeriksaan | [Spesifikasi sistem desain 0.18](../design-artifacts/bee-design-system/README.md) |
| Inventaris 23 view, role, kontrak perilaku dan paket rollout | [Rencana revamp](superpowers/plans/2026-10-15-ui-ux-revamp.md) |
| Nilai token yang dipakai aplikasi | [design-tokens.json](../frontend/src/core/design-tokens.json) |
| Penerapan token ke CSS dan PrimeVue styled mode | [designTokens.ts](../frontend/src/core/designTokens.ts), [theme.ts](../frontend/src/core/theme.ts) |
| Contoh interaktif komponen aplikasi dengan data fiktif | [Halaman sistem desain lokal](http://127.0.0.1:4173/design-system.html) |
| Kontrak data dan izin aktual | API/tipe modul, [router.ts](../frontend/src/core/router.ts), [navigation.ts](../frontend/src/core/navigation.ts), serta permission backend terkait |

Jika desain meminta aksi atau data yang tidak didukung kontrak aktual, catat perbedaannya; jangan memperluas izin, mengarang data, atau mengubah transaksi untuk menyesuaikan mockup. Perbaikan desain mengikuti kontrak aplikasi dan keputusan pengguna.

`_bmad-output/planning-artifacts/ux-designs/ux-beesmartfinance-skripsi-2026-06-28/DESIGN.md` adalah desain Juni yang historis. Font/palet di sana berbeda dari fondasi Oktober; jangan menjadikannya acuan skin baru. `frontend/src/design-preview/` dan `dashboard-preview.html` juga merupakan studi sebelumnya. Spesimen terkini memakai komponen aplikasi dari `features/` dan `shared/`.

## Review lewat aplikasi lokal

Mulai 16 Oktober 2026, review alur utama dilakukan pada [aplikasi localhost](http://127.0.0.1:4173/), bukan katalog spesimen. Frontend Vue memakai entry `index.html`, router dan autentikasi aplikasi; backend Django berjalan hanya pada `127.0.0.1:8000`, menggunakan PostgreSQL lokal existing. Konfigurasi frontend existing `/api/v1` diteruskan oleh proxy Vite ke backend lokal. Server perlu tetap berjalan agar tautan tersedia.

Login menentukan home dan kewenangan role. Tidak ada selector role contoh pada aplikasi. Berbeda dari spesimen memori, tindakan simpan pada aplikasi menggunakan API dan mengubah database lokal. Menyalakan server tidak otomatis menjalankan seed, migrasi atau deployment. Pada penerapan Laporan 0.7, satu migrasi existing `accounting.0003_opening_balance` yang tertinggal diterapkan hanya ke PostgreSQL localhost setelah backup privat; tidak ada transaksi bisnis yang diubah. Kelima endpoint laporan dan COA kemudian merespons HTTP 200. Halaman `design-system.html` tetap referensi komponen; label coverage 0.10 tidak berarti seluruh 23 view selesai direvamp.

Pendaftaran 0.10 sudah terhubung ke database localhost. Setelah pengguna menyetujui backup dan migrasi existing `operations.0011–0013`, backup PostgreSQL privat dibuat dan ketiganya diterapkan. Sebanyak 160 tagihan lama mendapat penanda rekonsiliasi sesuai aturan 0012; kolom bisnis yang sudah ada pada pendaftaran, siswa, tagihan, dan jurnal terverifikasi tetap sama. Biaya formulir lama tetap null. Lima GET (daftar/rincian pendaftaran, jenjang, COA, tagihan) merespons 200; aplikasi berhasil membuka enam pendaftaran dan rincian satu record dengan akun TU dalam browser terisolasi. Pemeriksaan browser nyata hanya membaca data; mutasi UI sebelumnya tetap memakai fixture.

## Reuse dan kepemilikan kode

Audit regresi 18 Oktober sudah memperbaiki kontrol hapus pilihan, batas/scroll footer dialog, serta popup kalender/dropdown yang tertinggal ketika form dikunci. Lihat [temuan, perbaikan, cakupan dan bukti](reviews/2026-10-18-ui-regression-audit.md). Gunakan `shared/components/SelectClearButton.vue` dengan slot props PrimeVue; kontrol ber-overlay harus menutup popup ketika disabled, sambil mempertahankan model form.

Semua path kode pada tabel ini relatif terhadap `frontend/src/`.

| Bagian | Pemilik existing | Kontrak implementasi |
|---|---|---|
| Shell dan navigasi | `shared/layout/AppShell.vue`, `AppNavigation.vue`, `core/navigation.ts` | Reuse metadata menu/home; route guard dan backend tetap menentukan akses. |
| Struktur halaman | `shared/components/PageLayout.vue` | Pertahankan props/slot; default `surface=true`, gunakan `false` pada workspace yang mengatur permukaannya sendiri. |
| Pencarian dan periode | `shared/components/SearchField.vue`, `PeriodPicker.vue` | Dengan `inputId`, sediakan label terlihat yang terhubung. Jelaskan scope pencarian/filter aktual dan reset pagination saat filter berubah. |
| Ringkasan dan grafik | `shared/components/KpiCard.vue`, `ChartPanel.vue`, `ChartDataTable.vue`, `RingGauge.vue` | Reuse sesuai pertanyaan data; nominal, periode, baseline dan tabel alternatif mengikuti dataset yang sama. |
| Ikon dan bahasa kontrol | `shared/components/PhosphorIcon.vue`, `core/icons.ts`, `core/primevueLocale.ts` | Pakai Phosphor Regular resmi beserta lisensi lokal; jangan menambah keluarga ikon. Migrasi caller lama per modul. |
| Format dan error | `core/format.ts`, `core/errors.ts` | Reuse format uang/tanggal dan error existing. Jangan mengubah nilai null menjadi nol atau tanggal lokal menjadi tanggal UTC. |
| Siswa | `features/siswa/SiswaDirectory.vue`, `SiswaFormDialog.vue`, `presentation.ts` | Komponen domain dipakai aplikasi dan spesimen; controller `SiswaListView.vue` memiliki API/mutasi. |
| Kelompok belajar | `features/kelompok/KelompokListView.vue`, `kelompok.css`, `features/absensi/api.ts` | Admin/TU mengelola jenjang, kelompok, dan perpindahan siswa. Semua halaman API dibaca; perpindahan meninjau siswa aktif asal sebelum konfirmasi. |
| Tagihan | `features/tagihan/TagihanDirectory.vue`, `TagihanPaymentDialog.vue`, `TagihanHistoryDialog.vue`, `InvoicePreview.vue`, `payment.ts`, `presentation.ts` | Pertahankan alokasi, nominal desimal, request ID, rekonsiliasi dan cetak; controller tetap memiliki API. |
| Tunggakan tagihan | `features/tagihan/TunggakanTagihanView.vue`, `presentation.ts` | Finance/Kepsek memantau sisa yang diketahui dan jumlah record rekonsiliasi secara terpisah. Nilai null tidak masuk total rupiah; tidak ada aksi bayar pada layar ini. |
| Daftar akun | `features/coa/CoaListView.vue`, `coa.css` | Finance mengelola tiga tingkat akun; Kepsek membaca. Pencarian/filter lintas data termuat, saldo awal debit/kredit memakai sen integer, form tidak memilih induk otomatis. |
| Anggaran dan periode | `features/anggaran-periode/AnggaranListView.vue`, `PeriodeListView.vue`, `api.ts` | Daftar semua halaman, copy tahun kalender dan carry-over sesuai laporan existing, status/konsekuensi tutup buku, tanggal lokal tanpa konversi UTC. |
| Log audit | `features/audit/AuditLogView.vue`, `auditFormat.ts` | Filter server dan pagination, urutan pelaku/data/aksi/waktu, rincian nilai lama/baru, filter mobile ringkas dan label nominal yang terbaca. |
| Jurnal | `features/jurnal/JurnalDirectory.vue`, `JurnalFormDialog.vue`, `JurnalDetailDialog.vue`, `JurnalActionDialog.vue`, `presentation.ts` | Daftar server-paginated dan alias query dipertahankan; controller memiliki API, konfirmasi dan guard aksi sesuai role/status. |
| Laporan | `features/laporan/LaporanView.vue`, `LaporanContent.vue`, `AccountReportTable.vue`, `presentation.ts`, `reports.css` | Hasil memiliki snapshot jenis/periode/akun; filter belum diterapkan tidak mengubah judul/cetak/CSV. Tabel akun digunakan bersama antar laporan. |
| Absensi dan rekap | `features/absensi/AbsensiSiswaView.vue`, `AttendanceGrid.vue`, `RekapSiswaView.vue`, `RekapDirectory.vue`, `presentation.ts`, `attendance.css` | TU mengisi absensi; Guru membaca rekap. Tanggal/kelompok diterapkan eksplisit, ID diperiksa sebelum retry simpan, input gagal dipertahankan, CSV memakai hasil yang diterapkan. |
| Pendaftaran calon | `features/pendaftaran/PendaftaranListView.vue`, `PendaftaranDirectory.vue`, `PendaftaranFormDialog.vue`, `PendaftaranPaymentDialog.vue`, `presentation.ts`, `admission.css` | Biaya/SPP eksplisit, rincian terbaru sebelum tindakan, penerimaan terpisah dari finalisasi, retry ambigu memakai payload sama. UI/fixture diperiksa; daftar dan rincian database localhost juga sudah dibaca setelah backup+migrasi disetujui. |
| Layanan sekolah | `features/katering/KateringView.vue`, `MenuMingguan.vue`, `features/jemputan/JemputanView.vue`, kedua `api.ts`, `shared/components/ServiceRecap.vue`, `school-services.css` | Rekap memakai periode diterapkan; tarif yang belum disimpan tidak mengubah angka; pendaftaran jemputan terbaru mengikuti billing. CRUD tetap di controller domain, tabel/kartu rekap dipakai bersama. |
| Kegiatan | `features/kegiatan/KegiatanDirectory.vue`, `KegiatanFormDialog.vue`, `KegiatanRealisasiDialog.vue`, `KegiatanReportDialog.vue`, `KegiatanUsage.vue`, `presentation.ts` | Guru mencatat/membaca sesuai izin, Kepsek mengelola; controller tetap memiliki API. |
| Gaji dan kasbon | `features/kepegawaian/GajiListView.vue`, `PinjamanListView.vue`, `GajiFormDialog.vue`, `KasbonFormDialog.vue`, `GajiSlipPreview.vue`, `EmployeeActionDialog.vue`, `payroll.ts`, `employee-finance.css` | Finance tetap memiliki akses. Daftar lintas halaman, tabel/kartu, komponen gaji lengkap, potongan server, tanggal lokal, rincian terbaru sebelum tindakan, pending/recovery dan cetak slip terisolasi. Mutasi browser memakai fixture; API localhost diperiksa read-only. |
| Data dan absensi pegawai | `features/kepegawaian/PegawaiListView.vue`, `PegawaiFormDialog.vue`, `AbsensiPegawaiView.vue`, `StaffAttendanceGrid.vue`, `staff.ts`, `staff.css` | Profil dengan masa kerja/status dan akun sebagai informasi; absensi per tanggal, catatan campuran lama, rekap, serta verifikasi GET setelah hasil bulk ambigu. Mutasi browser memakai fixture; API localhost dibaca tanpa operasi tulis. |
| Aset tetap | `features/aset/AsetListView.vue`, `AsetFormDialog.vue`, `api.ts`, `asset.css` | Finance membaca semua halaman aset, mencari nama/akun/tanggal, memeriksa rincian terbaru, lalu mengubah atau mencatat penyusutan lewat konfirmasi. Perhitungan tetap milik server. |

Reuse PrimeVue dan pola modul sebelum menambah komponen. Jangan membuat form/tabel generik lintas domain jika kebutuhan bersama belum terbukti. Fixture, role selector contoh, dan CSS dokumentasi `design-system/system.css` tidak diimpor ke entry aplikasi.

## Cakupan saat ini dan berikutnya

- **Sudah masuk source lokal:** token/tema, shell, komponen bersama, dashboard Finance/Kepsek, Siswa dan Kelompok belajar, Tagihan/pembayaran serta Tunggakan Finance/Kepsek, Kegiatan Guru/Kepsek, Jurnal Finance/Kepsek, Daftar Akun, Anggaran, Periode, Log audit, kelima laporan keuangan, Absensi siswa TU, Rekap absensi TU/Guru, Katering dan Jemputan TU, UI Pendaftaran calon, Gaji/Kasbon Finance, Data pegawai/Absensi pegawai, dan Aset tetap. Detail coverage dan batas pemeriksaan ada pada spesifikasi 0.18; ini bukan klaim seluruh alur selesai.
- **Berikutnya:** modul administrasi/keuangan lain yang tersisa sesuai inventaris rollout, lalu konsistensi lintas layar dan cetak. Jurnal masuk/keluar tetap alias query pada satu view, bukan implementasi terpisah.
- **Belum selesai:** sisa view dan state domain, migrasi seluruh ikon lama, walkthrough pengguna/perangkat sekolah, serta validasi rilis. Baseline tema pada sebuah modul tidak berarti workflow modul itu sudah direvamp.

Tetap gunakan Vue 3, TypeScript, Vite, PrimeVue, Pinia dan API Django existing. Migrasi Next.js belum diputuskan dan bukan prasyarat revamp.

## Cara mengerjakan satu modul

1. Baca view, caller, API/tipe dan permission terkait. Catat tindakan per role, status, sumber angka, scope filter/search, serta perilaku cetak bila ada.
2. Susun hierarki pekerjaan dan informasi sebelum skin. Pisahkan navigasi, filter dan perintah; adaptasi pola domain yang sudah ada.
3. Terapkan token dan komponen bersama. Pertahankan kontrak props/emit, route/query, payload, validasi, error handling dan izin.
4. Lengkapi state awal kosong, hasil filter kosong, loading, gagal/retry, pending, disabled beralasan dan sukses sebenarnya. Error simpan mempertahankan input; respons lama tidak menimpa filter baru.
5. Tinjau desktop/mobile, teks panjang, nominal lengkap, label/error, keyboard/fokus, reduced motion dan print yang relevan. Jalankan tes/build saat verifikasi diminta; catat hasil aktual dan batas pemeriksaan, bukan status lulus dari contoh visual.
6. Perbarui coverage dan bukti pada spesifikasi. Bedakan implementasi lokal, fixture browser, API nyata dan hasil deployment.

## Batas yang harus dibawa ke implementasi

- Tidak mengubah izin role, skema/API, aturan posting/reversal, periode tertutup, rekonsiliasi, atau idempotensi hanya untuk polish.
- Pembayaran Tagihan mempertahankan request ID existing. Realisasi Kegiatan belum memiliki idempotensi backend; setelah respons hilang, periksa laporan sebelum kirim ulang. Jangan menjanjikan retry bebas duplikasi.
- Pemeriksaan terakhir memakai fixture lokal, bukan akun/data sekolah. Seluruh 23 view, pembaca layar, Safari/iPad, printer fisik dan kesiapan produksi belum terverifikasi menyeluruh. Warning ukuran chunk masih ada.
- Implementasi UI lokal tidak mengotorisasi deployment atau mutasi data sekolah.


Gaji/Kasbon 0.11 terhubung ke aplikasi localhost. Potongan kasbon tetap ditentukan server dan juga mencakup pengajuan yang belum dicairkan sesuai service existing; form menjelaskan hal ini. Pembuatan jurnal sumber menghasilkan Draf, bukan langsung memasukkan angka ke buku besar. Respons ambigu meminta pembacaan status sebelum pengiriman ulang; tidak mengklaim idempotensi transaksi. Bukti ada pada bagian penerapan 0.11 di spesifikasi.

Data pegawai dan Absensi pegawai 0.12 sudah terhubung ke aplikasi localhost. Data pegawai memakai daftar lintas halaman, pencarian, filter, form tanggal lokal, status aktif dan status akun tertaut sebagai informasi. Absensi memuat seluruh halaman per tanggal, menjaga catatan campuran lama sampai pengguna memilih status baru, serta menahan pengiriman ulang bulk saat hasil respons ambigu. Bukti di bagian penerapan 0.12 pada spesifikasi.

Aset tetap 0.13 terhubung ke aplikasi localhost untuk Finance. Daftar membaca seluruh halaman, menampilkan perolehan/akumulasi/penyusutan bulanan dan rincian akun; form memakai tanggal lokal serta validasi nominal/masa manfaat. Aksi penyusutan memakai nilai server dan menghasilkan jurnal Draf sesuai service existing. Preview browser memakai data fiktif dan seluruh request bisnis ditahan dari API nyata.
