# BeeSmart Finance — sistem desain 0.18

Tangkapan layar dan hasil pemeriksaan visual yang memuat data contoh disimpan lokal dan tidak disertakan dalam handover GitHub publik. Tautan gambar di bawah adalah indeks untuk workspace asal; implementasi dan kesimpulan audit tetap dijelaskan dalam dokumen teks.

Pintu masuk implementasi dan pemetaan source: [panduan sistem desain](../../docs/design-system.md).

18 Oktober 2026. **Fondasi 0.18 sudah terhubung ke source aplikasi lokal**: token bersama, BeePreset styled, shell dan komponen bersama, dashboard Finance/Kepsek, direktori/form Siswa dan Tagihan untuk TU, Kegiatan/realisasi/laporan untuk Guru dan Kepsek, Jurnal serta kelima laporan keuangan untuk Finance/Kepsek, Absensi siswa TU, Rekap TU/Guru, Katering dan Jemputan TU. Pendaftaran calon juga sudah masuk source dan berhasil membaca database localhost setelah backup serta migrasi existing disetujui pengguna. Gaji/Kasbon Finance mencakup daftar, form, rincian, tindakan dan cetak slip. Data pegawai, Absensi pegawai, Aset tetap, Kelompok belajar, Tunggakan tagihan, Daftar akun, Anggaran, Periode, dan Log audit sudah terhubung ke source dan browser lokal; bukti 0.11–0.18 ada di bagian akhir. Belum dideploy dan belum merupakan penyelesaian seluruh 23 view. Artefak preview lama tetap pembanding; halaman ini memakai komponen PrimeVue aktual.

## Artefak dan cara membuka

- Halaman interaktif: [sistem desain lokal](http://127.0.0.1:4173/design-system.html).
- Hasil sebelumnya: [layar siswa interaktif](http://127.0.0.1:4173/design-system.html#layar-siswa), memakai komponen yang sama dengan `/siswa`; data contoh hanya berada di memori halaman.
- Alur TU: [tagihan dan pembayaran](http://127.0.0.1:4173/design-system.html#layar-tagihan), memakai komponen yang sama dengan `/tagihan`.
- Kegiatan: [Kegiatan Guru/Kepsek](http://127.0.0.1:4173/design-system.html#layar-kegiatan), memakai komponen yang sama dengan `/kegiatan`.
- Jurnal: [Jurnal Finance/Kepsek](http://127.0.0.1:4173/design-system.html#layar-jurnal), memakai komponen yang sama dengan `/jurnal` dan alias pemasukan/pengeluaran.
- Laporan: [Laporan pada aplikasi localhost](http://127.0.0.1:4173/laporan). Review utama memakai aplikasi dan login role, bukan spesimen HTML baru.
- Absensi: [Absensi siswa TU](http://127.0.0.1:4173/absensi-siswa) dan [Rekap TU/Guru](http://127.0.0.1:4173/rekap-siswa) pada aplikasi localhost.
- Layanan: [Katering](http://127.0.0.1:4173/katering) dan [Jemputan](http://127.0.0.1:4173/jemputan) pada aplikasi localhost.
- Hasil terbaru: [Data pegawai](http://127.0.0.1:4173/pegawai) dan [Absensi pegawai](http://127.0.0.1:4173/absensi-pegawai). Gaji/Kasbon tersedia di menu Finance.
- Struktur keuangan: [Daftar akun](http://127.0.0.1:4173/coa) pada aplikasi lokal dengan Finance atau Kepsek.
- Perencanaan keuangan: [Anggaran](http://127.0.0.1:4173/anggaran) dan [Periode](http://127.0.0.1:4173/periode) pada aplikasi lokal.
- Governance: [Log audit](http://127.0.0.1:4173/audit-log) pada aplikasi lokal.
- Entry terpisah: `frontend/design-system.html` dan `frontend/src/design-system/main.ts`.
- Sumber token: `frontend/src/core/design-tokens.json`.
- Pemetaan CSS: `frontend/src/core/designTokens.ts`; pemeriksaan kontras: `frontend/src/design-system/tokens.ts`.
- Spesimen: `frontend/src/design-system/DesignSystem.vue`, `ComponentWorkbench.vue`, dan `system.css`.

Dari `frontend`, jalankan server Vite existing pada port 4173. Halaman ini membutuhkan dev server; entry build produksi saat ini tetap `index.html`. Bootstrap aplikasi memuat variabel token yang sama. Tidak menambah dependency atau mengubah API, autentikasi, dan database. Preview lama tersedia melalui tautan pembanding.

## Keputusan visual

BeeSmart merupakan perangkat kerja sekolah: transaksi perlu terbaca, tugas berikutnya jelas, dan layar operasional tidak perlu bersaing dengan angka. Identitas Lebah Madu hadir melalui logo, navy yang dalam, magenta, serta aksen madu yang terbatas.

| Unsur | Peran | Batas pemakaian |
|---|---|---|
| Navy `color.nav` | Navigasi, struktur, cuplikan saldo utama | Hindari menjadikan semua panel gelap |
| Magenta `color.brand` | Tindakan utama, tautan tindakan, fokus | Bukan warna gagal atau semua metrik |
| Madu `color.honey` | Identitas sekolah dan aksen kecil | Bukan label status, teks putih kecil, atau warna sukses |
| Kanvas dan permukaan | Memisahkan ruang kerja dari isi | Panel hanya ketika ada kelompok/tugas yang jelas |
| Tinta dan muted | Hierarki teks | Keterangan tetap terbaca; jangan menggunakan opacity pada seluruh kelompok |
| Semantic positive/warning/critical/info | Kondisi dan pesan | Selalu bersama kata; warna tidak menentukan enum bisnis |

Tidak ada gradient, ilustrasi hias pada area data, kartu di dalam kartu, atau motion terus-menerus. Keunikan dibangun dari proporsi, angka, hierarki, dan identitas yang konsisten. Kesesuaian arah ini tetap perlu dinilai dari layar pekerjaan nyata; halaman fondasi bukan bukti usability.

## Token sebagai sumber tunggal

`core/design-tokens.json` menyimpan kelompok `primary`, `color`, `font`, `type`, `weight`, `leading`, `space`, `radius`, `size`, `layout`, `shadow`, dan `motion`. Nilainya menghasilkan custom property `--bee-{group}-{key}` saat entry aplikasi atau sistem desain dibuka. Contoh: `color.brand` menjadi `--bee-color-brand`.

- Gunakan semantic token, misalnya `color.critical`, alih-alih menyalin hex merah ke setiap komponen.
- Pakai token existing sebelum menambah variasi. Tambahkan hanya untuk kebutuhan berulang yang belum terwakili.
- Ukuran ilustrasi skala/wordmark atau geometri lokal tidak otomatis menjadi token produk.
- `layout.sidebar` adalah calon ukuran shell produk. Sidebar dokumentasi memiliki kebutuhan berbeda dan bukan spesimen AppShell final.
- Token sudah dipetakan ke BeePreset dan alias shared CSS existing. Aplikasi serta spesimen menggunakan **styled mode yang sama**. Jangan mengimpor stylesheet dokumentasi `system.css` ke entry aplikasi.
- Reuse komponen bersama existing. PageLayout menambah opsi `surface` dengan default perilaku lama; SearchField menambah `inputId` opsional. Props/model/emit caller existing dipertahankan.

## Tipografi, angka, dan ruang

IBM Plex Sans, bobot 400/500/600/700, digunakan pada seluruh spesimen. Fallback mengikuti system sans. Entry aplikasi dan spesimen saat ini memuat Google Fonts; keputusan menyimpan font secara lokal beserta lisensinya menjadi bagian integrasi produksi.

| Peran | Desktop | Aturan |
|---|---:|---|
| Keterangan | 13 px / 400 | Periode, satuan, sumber, bantuan |
| Kontrol dan tabel | 14 px / 500 atau 400 | Label, baris transaksi, tindakan rutin |
| Isi | 16 px / 400 | Instruksi dan paragraf yang perlu dibaca |
| Judul bagian | 20 px / 600 | Pengelompokan pekerjaan |
| Judul halaman | 32 px / 600 | Satu judul utama |
| Angka utama | 44 px / 500 | Sedikit metrik yang menjadi prioritas |
| Angka pendukung | 28 px / 500 | Hierarki kedua |

Ukuran 48 px hanya untuk presentasi arah desain, bukan default dashboard. Pada mobile gunakan token responsif; input menjadi 16 px. Nominal lengkap tetap terlihat, memakai tabular numerals, dan rata kanan pada tabel. Reuse `formatRp`; singkatan juta hanya untuk sumbu grafik, dengan nilai penuh di tooltip/tabel alternatif.

Skala ruang: **4, 8, 12, 16, 24, 32, 48, 64 px**. Jarak kelompok lebih besar daripada jarak elemen yang saling berhubungan. Gutter produk 32 px desktop/16 px mobile; panel 24 px; antarbagian 48 px desktop. Sesuaikan komposisi untuk data padat tanpa merapatkan semua elemen secara seragam.

Radius: kontrol 6 px, panel 10 px, overlay 14 px, status 4 px. Border memisahkan permukaan; bayangan terutama untuk overlay. Hindari pill pada setiap elemen.

## Komponen dan perilaku

| Pola | Standar |
|---|---|
| Tombol utama | Satu per area kerja, label kata kerja + objek, tinggi minimum 44 px |
| Sekunder | Border jelas untuk tindakan pendamping; text button untuk tindakan ringan |
| Ringkas | Minimum 36 px hanya pada kontrol sekunder desktop; mobile kembali minimum 44 px |
| Ikon | Phosphor Regular dari distribusi resmi yang sudah tersimpan; 20 px kontrol, 16 px pendukung, 24 px penanda bagian |
| Icon button | Target minimum 44 px, nama aksesibel wajib; ikon dekoratif tidak dibaca ulang |
| Form | Label persisten, bantuan dekat field, satuan tertulis, error menjelaskan pemulihan |
| Dialog | Judul dan cakupan, isi yang dapat digulir, tindakan tetap jelas, Escape/focus trap/focus return melalui PrimeVue |
| Tabel | Identitas di kiri, nominal di kanan, header bermakna, status teks, tindakan konsisten |
| Kepadatan tabel | Baris satu tingkat minimum 60/48 px; record dua tingkat pada spesimen 72/60 px |
| Mobile | Identitas, nominal, status, dan tindakan menjadi record bertumpuk; tanggal dan rincian tetap tersedia pada detail |
| Filter | Label menyatakan cakupan; jumlah hasil dan hasil kosong mengikuti filter yang dipakai |

Sumber 59 ikon Phosphor Regular beserta MIT tersedia di `frontend/src/shared/icons/`. `shared/components/PhosphorIcon.vue` dipakai shell, KPI, panel grafik, search, dan spesimen; preview lama meneruskan ke komponen yang sama. `core/icons.ts` memetakan prop PrimeIcons lama bagi consumer yang sudah memakai komponen SVG. Icon prop pada modul yang belum dimigrasi tetap perlu dikerjakan per modul. Nama akun, role, label navigasi, dan route menggunakan sumber existing bila sudah tersedia.

Contoh form memeriksa bukti, Kas/Bank, serta nominal positif hingga dua desimal sebelum menampilkan keadaan berhasil. Itu validasi spesimen, bukan pengganti validasi/idempotensi server. Form tidak mengirim atau menyimpan pembayaran; alokasi, idempotensi, serta guard rekonsiliasi pada form pembayaran aplikasi tetap dipertahankan. Tombol Periksa menampilkan record yang dipilih, bukan form pembayaran baru.

## Bahasa dan status

Gunakan bahasa Indonesia, sentence case, dan kata kerja konkret: “Catat pembayaran”, “Periksa jurnal”, “Pilih Kas/Bank”. Hindari pesan umum seperti “Terjadi kesalahan” ketika kondisi dan pemulihan diketahui. Sukses perlu menyebut hasil sebenarnya; jangan menyebut “tersimpan” ketika request belum berhasil.

| Kondisi | Label presentasi | Makna yang dipertahankan |
|---|---|---|
| `DRAFT` jurnal | Draf | Belum masuk buku besar |
| `PENDING` jurnal | Menunggu persetujuan | Sudah diajukan; tidak sama dengan draf |
| `POSTED` jurnal | Tercatat | Sudah masuk buku besar, penyuntingan biasa terkunci |
| Rekonsiliasi belum selesai | Perlu dicocokkan | Nominal/sisa belum tentu diketahui; bukan nol atau lunas |

Label tersebut bersifat per domain. Jangan memaksa status siswa, kegiatan, tagihan, dan jurnal menjadi satu enum baru. ID dan kode akun tetap menyimpan identitas yang sama; display label tidak mengganti payload. Hindari informasi implementation/debug pada alur pengguna.

Keadaan kosong menjelaskan belum ada data dan langkah berikutnya; hasil filter kosong meminta penyesuaian filter. Memuat tidak boleh menampilkan nol palsu. Gagal mempertahankan input dan menyediakan pemulihan. Disabled harus beralasan pada konteks produk. Spesimen menunjukkan kosong/memuat/gagal/berhasil dan disabled, tetapi belum mencakup semua state domain.

## Informasi dan prioritas empat peran

`frontend/src/core/navigation.ts` tetap sumber menu dan home; route guard serta backend tetap sumber izin. Pilihan role pada halaman sistem desain hanya mengganti contoh presentasi.

| Peran | Prioritas home | Batas |
|---|---|---|
| Finance | Kas/bank, jurnal, transaksi yang perlu ditindaklanjuti, laporan sesuai scope | Tidak menambahkan tren kehadiran siswa ke dashboard keuangan |
| SchoolPrincipal | Antrean keputusan yang benar-benar memenuhi syarat, kondisi keuangan, pagu/realisasi | Jumlah persetujuan tidak diambil dari seluruh DRAFT |
| Administration | Siswa, tagihan, penerimaan pembayaran, layanan operasional | Home mengikuti siswa; tidak menyalin dashboard buku besar |
| TeacherInCharge | Kegiatan, pagu, realisasi, rekap sesuai akses | Tidak mendapat pengelolaan atau laporan keuangan yang tidak diizinkan |

Satu peran dapat membutuhkan informasi lintas modul sesuai izin. Tujuannya menghilangkan informasi yang tidak membantu tugas, bukan melarang konteks yang sah. Navigasi, perintah, dan filter tidak dicampur. Alias jurnal masuk/keluar tetap satu route dengan query existing. Multi-role mengikuti aturan prioritas home existing, bukan pilihan visual baru.

## Grafik

- Tentukan pertanyaan, sumber, periode, unit, cakupan posting, dan baseline sebelum memilih bentuk.
- Garis untuk tren aktual; batang dengan baseline nol untuk perbandingan; horizontal untuk pagu/realisasi; komposisi memakai proporsi dengan denominator dan nominal.
- Donut bukan default. Tambahkan bentuk baru hanya jika membantu membaca pertanyaan yang berbeda.
- Pertahankan perbedaan arus kas dengan pendapatan/beban. Periode satu panel tidak dianggap otomatis mengubah seluruh dashboard.
- Data belum diketahui tetap `null`/penanda belum diketahui; jangan diubah menjadi nol atau diinterpolasi tanpa alasan.
- Garis spesimen memakai solid/dashed di samping warna. Kedua grafik memiliki judul, periode, satuan, label aksesibel, dan tabel angka HTML dari dataset yang sama.
- Palette empat seri bukan bukti kontras seluruh kombinasi. Pada integrasi, gunakan label/pola dan evaluasi chart aktual, termasuk kategori panjang dan nilai negatif.

## Aksesibilitas, responsif, dan cetak

Teks normal menargetkan rasio 4,5:1; batas kontrol 3:1 pada permukaan yang digunakan. Tujuh pasangan token yang ditampilkan berkisar **5,40–15,20:1**. Kalkulasi `contrastRatio` untuk pasangan warna opaque, bukan komposit alpha. Self-check token memeriksa bentuk warna, pasangan tersebut, batas kontrol, dan black/white 21:1. Ini tidak membuktikan kepatuhan seluruh aplikasi.

Fokus keyboard 3 px dengan offset, label native terhubung, error field menyertakan `aria-invalid`/deskripsi, status memakai live region sesuai konteks, tabel memakai heading, dan tombol toggle mengungkap `aria-pressed`. Hormati reduced motion. Konten harus tetap dapat diakses pada zoom, keyboard, perangkat sentuh, serta fallback font. Jangan menyembunyikan nominal untuk mempertahankan layout.

Cetak invoice/slip/laporan tetap memakai pola print existing: shell dan kontrol disembunyikan, identitas/periode/nominal/status penting dipertahankan. Halaman sistem desain tidak membuktikan print, scanner/pembaca layar, atau Safari/iPad sudah diverifikasi.

## Dasar referensi

Referensi Mobbin telah ditinjau pada fase revamp sebelumnya: [Mercury](https://mobbin.com/screens/1409f3cf-aafe-4e2f-9045-b4bdb2c48484) untuk hierarki kas dan aktivitas, [Revolut Business](https://mobbin.com/screens/4685d9fc-3a0a-402c-bd67-620809b6376a) untuk pemindaian angka/transaksi, dan [Xero](https://mobbin.com/screens/1c9ccbcc-0900-4bd4-b86c-dd68aa8c96f6) untuk struktur pekerjaan keuangan. Yang diadaptasi adalah prinsip komposisi; screenshot tidak membuktikan perilaku atau permission BeeSmart.

Skill `frontend-design` dipakai untuk arah visual dan implementasi terpisah; `better-typography` untuk hierarki huruf, angka, dan ukuran baca. Panduan Impeccable serta referensi lain yang sudah ditinjau tetap sebagai masukan, bukan alasan membuka semua provider atau menyalin gaya landing page ke dashboard operasional.

## Penerapan 0.2

- JSON dipindahkan ke core agar aplikasi tidak mengimpor artefak preview. Primary palette/hover dan semantic colors memiliki self-check kesesuaian.
- BeePreset mengatur primary, focus ring, form, DataTable, Tag, Message dan Toast. Override warna/font lama yang bertentangan dihapus; CSS print dan layout khusus tabel tetap dipertahankan.
- Shell memakai Phosphor, navigasi aktif menghormati query jurnal, dan menu mobile memakai Drawer dengan Escape/fokus kembali. Label tetap ada pada collapsed navigation.
- Dashboard Finance memprioritaskan kas dan draf; Kepsek persetujuan dan anggaran. Antrean hanya cuplikan halaman pertama, dengan filter kelayakan tinjauan. Backend tetap memutuskan apakah persetujuan dapat dilakukan.
- Filter ringkasan keuangan hanya bulanan/tahunan: source backend menghitung mutasi bulanan/tahunan dan saldo kas kumulatif akhir periode, bukan saldo harian. Label kas menyebut akhir periode secara eksplisit.
- Chart menggunakan font/palette bersama, garis aktual, baseline nol pada perbandingan, tanpa animasi berkelanjutan, serta tabel data alternatif. Filter cepat mengabaikan respons lama; panel gagal tidak mempertahankan data lama seolah baru.
- Spesimen memakai Button, InputText, Select, MultiSelect, DatePicker, InputNumber, Checkbox, ToggleSwitch, Textarea, Password, Tabs, DataTable/Column/paginator, Tag, Message, Toast, ConfirmDialog, Drawer dan Dialog dari PrimeVue. Tabel native bukan lagi acuan DataTable produk.
- TU dan Guru tetap memakai home yang diizinkan. Keduanya mendapat baseline tema/shell; pengaturan komposisi dan workflow modul masih dilanjutkan per modul. COA pada kegiatan hanya dimuat untuk pengelola yang memiliki form pengaturan akun.

## Lanjutan per modul

1. Direktori dan form siswa TU sudah dipoles pada 0.3. Daftar/pembayaran/riwayat/faktur Tagihan menyusul pada 0.4. Kegiatan Guru/Kepsek menyusul pada 0.5 dan Jurnal pada 0.6. Berikutnya modul lain sesuai inventaris, termasuk state domain dan cetak yang relevan.
2. Teruskan ke inventaris 23 view. Lengkapi pola foto/upload, tabel rekap yang padat, cetak invoice/slip/laporan, serta seluruh state domain. Jangan menganggap halaman fondasi sudah membuktikan semuanya.
3. Evaluasi hasil nyata bersama pengguna dan perangkat sekolah; setelah itu jalur rilis mengikuti proses deployment proyek yang diotorisasi.

Tidak membutuhkan rewrite stack atau library UI tambahan. Desain masih dapat diperbaiki berdasarkan review; penerapan lokal bukan persetujuan rilis.

## Bukti dan batas pemeriksaan

Pemeriksaan 16 Oktober 2026:

- 22 tes terarah lulus: prioritas/kelayakan tinjauan dashboard, kompatibilitas default PageLayout, navigasi, route guard, dan format uang existing. Tidak menjalankan seluruh test suite.
- Build/typecheck aplikasi dan build entry sistem desain berhasil. Peringatan ukuran chunk existing masih ada.
- Probe komponen styled menghasilkan primary `#B01862`, header `#F8F9FB`, dan IBM Plex Sans. DataTable multiline terukur 72/60 px untuk dua density; pagination menampilkan record berikutnya dan search kosong memberi pemulihan.
- Form contoh menerima Rp 1.250,5; konfirmasi bertipe alertdialog dapat dibatalkan dan Toast muncul. Ini bukan transaksi sekolah.
- Browser terisolasi memakai **fixture lokal untuk seluruh request API** pada empat home role; tidak mengirim mutasi. Finance tidak memuat panel kehadiran/kegiatan, Kepsek meminta PENDING dan mengeluarkan milik sendiri/direct-post/rekonsiliasi. Script reproducible: `checks/roles.js`.
- Desktop 1440 px, dashboard mobile 390 px, dan sistem desain 320 px diperiksa. Fokus menu kembali ke tombol setelah Escape. Kegagalan arus kas yang disimulasikan menghasilkan pesan khusus panel.
- Tujuh pasangan token opaque tetap 5,40–15,20:1. Screenshot terbaru berakhiran `-02`; screenshot tanpa akhiran menyimpan riwayat 0.1.

Belum memverifikasi data/akun sekolah asli, semua 23 halaman dan state, transaksi riil, pembaca layar, Safari/iPad, atau hasil print fisik/PDF. Belum ada deployment. Body role pada screenshot bertuliskan pengguna/data contoh karena fixture, bukan bukti akses akun sekolah.


## Penerapan 0.3 — direktori siswa dan interaksi bersama

Dua komponen domain dipakai langsung oleh aplikasi dan spesimen interaktif: `features/siswa/SiswaDirectory.vue` serta `SiswaFormDialog.vue`. `SiswaListView.vue` tetap memiliki request dan mutasi API; `design-system/StudentWorkbench.vue` hanya mengubah fixture di memori. Tidak ada cabang mode contoh dalam API aplikasi, token login contoh pada produk, atau library baru.

Direktori menyatukan nama/NIS, kelompok belajar, status berbahasa Indonesia, SPP rata kanan, serta tindakan yang sama pada tabel desktop dan record mobile. Pencarian mencakup teks yang ditampilkan (termasuk nama kelompok), bukan kontak/alamat orang tua. Pencarian dan filter berlaku atas seluruh daftar yang dimuat dengan `listAll`; setiap perubahan filter kembali ke halaman pertama. Filter, hasil kosong, data awal kosong, memuat, gagal memuat, dan gagal memuat kelompok dibedakan.

Form mengelompokkan data siswa dan kontak orang tua, menghubungkan label/bantuan/error dengan kontrol, memfokuskan input bermasalah, serta menerima dua desimal SPP. NIS kosong dikirim sebagai `null` sesuai field nullable existing. Kontak, kelompok dan string nominal yang tidak diedit dipertahankan. Server tetap memvalidasi data; kegagalan simpan menampilkan error di form tanpa membuang input. Selama simpan berlangsung, kontrol dan penutupan form dikunci. Penghapusan tetap membutuhkan konfirmasi existing.

Panduan `frontend-design` dipakai untuk struktur direktori dan komposisi; `emil-design-eng` untuk detail respons kontrol dan motion. [Gumloop di Mobbin](https://mobbin.com/screens/b191aef1-ec44-48ac-ad7f-c76673fed6f5) ditinjau untuk hubungan judul, pencarian, daftar orang, dan tindakan baris. Yang diadaptasi adalah hirarki direktori, bukan permission atau perilaku produk tersebut. Context7 memberi dokumentasi resmi [PrimeVue styled mode](https://primevue.org/theming/styled); detail token/slot diperiksa pada versi yang terpasang. Playwright dipakai pada browser terisolasi untuk meninjau hasil dan workflow.

| Before | After | Why |
|---|---|---|
| Durasi kontrol mengikuti default library | Semantic transition duration 120 ms dari token bersama | Kontrol memakai ritme yang sama |
| Tombol hanya berubah warna | Tekanan pointer 80 ms, skala 0,98; tidak diterapkan pada focus-visible/reduced motion | Feedback singkat tanpa menggerakkan layout |
| Dialog 300 ms dan Drawer 500 ms dari library | Masuk 180 ms, keluar 140 ms, kurva ease-out/drawer dari token | Mempercepat lapisan yang dibuka pengguna; keyframe posisi bawaan PrimeVue dipertahankan |
| Toast lebar 25 rem terpotong pada layar 320 px | Lebar maksimum mengikuti viewport minus 32 px | Pesan dan tombol tutup tetap terlihat |
| Nama/kode, filter dan status terpisah tanpa konteks hasil | Direktori, filter berlabel, hasil terhitung, status domain dan pemulihan yang jelas | Mengurangi tebakan saat mencari siswa |

Copy umum kontrol, calendar month/day names, serta label aksesibel pagination dipusatkan pada `core/primevueLocale.ts` dan dipakai kedua entry. Ini belum merupakan penerjemahan seluruh copy/komponen dalam aplikasi. Halaman sistem desain menampilkan versi 0.3 dan tautan langsung ke spesimen siswa.

### Bukti pemeriksaan 0.3

- 19 tes terarah / 4 file lulus: pencarian berdasarkan kelompok tanpa kontak privat, reset pagination, validasi nama, input setelah error, nominal desimal, PageLayout, navigasi dan route guard.
- Build/typecheck aplikasi dan build entry sistem desain lulus. Peringatan chunk aplikasi di atas 500 kB tetap ada; bukan regresi baru yang sudah diselesaikan.
- Direktori desktop terukur 72 px per record; kedua ikon tindakan berada dalam satu baris. Pagination 12 contoh menghasilkan 10 + 2 record; pencarian Melati menghasilkan 4 dan kembali ke halaman pertama.
- Form contoh menerima `1.250,50`; nama kosong ditolak dan fokus berpindah ke field nama. Escape menutup dialog dan mengembalikan fokus ke pemicu. Gerak dialog terukur 180 ms; tekanan pointer terukur skala 0,98 / 80 ms. Reduced motion meniadakan animasi pada pemeriksaan browser.
- Layar siswa dan dialog tidak meluber pada viewport 320 px; font input mobile 16 px. Toast pada viewport 320 px terukur lebar 288 px, batas kiri 12 px dan kanan 300 px.
- `checks/students.js` mengintersep **seluruh** API dan menangani PUT di fixture memori saja. Simulasi gagal simpan mempertahankan input; percobaan berikutnya berhasil pada fixture. Nominal `750000.25`, kelompok dan kontak yang tidak diedit tetap sama pada payload. Gagal memuat kelompok tetap menampilkan siswa; gagal memuat siswa menawarkan muat ulang dan tidak mengaku sebagai data kosong.
- `checks/roles.js` memeriksa empat home role dengan seluruh API diintersep. Finance/Kepsek tetap terpisah prioritasnya; Guru tidak meminta COA pengelolaan. Fokus menu mobile kembali setelah Escape, kegagalan arus kas tetap khusus panel, dan seluruh request pada pemeriksaan empat role adalah GET.
- Screenshot terbaru memakai akhiran `-03`; `-02` adalah riwayat fondasi sebelumnya. Semua screenshot peran memakai fixture, bukan akun/data sekolah asli.

Belum memverifikasi seluruh 23 halaman, semua state domain, API sekolah asli, pembaca layar, Safari/iPad atau cetak fisik/PDF. Belum ada deployment. Review dengan pengguna TU dan perangkat sekolah tetap diperlukan untuk menyatakan alur ini sudah intuitif dalam penggunaan nyata.


## Penerapan 0.4 — Tagihan dan pembayaran TU

Direktori `TagihanDirectory.vue`, form `TagihanPaymentDialog.vue`, riwayat `TagihanHistoryDialog.vue`, dan `InvoicePreview.vue` dipakai aplikasi serta spesimen interaktif yang sama. Pembuatan satu/banyak tagihan dan editor tetap berada pada controller existing `TagihanListView.vue`; spesimen tidak menyalin controller/API aplikasi. Pembuatan/perubahan komponen tagihan tidak disimulasikan penuh pada halaman sistem desain dan diberi penjelasan ketika dipilih.

Daftar memprioritaskan siswa/periode, total, dibayar, sisa, status, dan Catat pembayaran. Tindakan pendamping berada pada Menu bawaan PrimeVue dengan navigasi keyboard, fokus kembali, dan target item 44 px. Record desktop 72 px; mobile menampilkan nilai yang sama sebagai daftar bertumpuk. Pencarian, filter periode/status, pagination dan keadaan gagal/kosong dibedakan. Filter hanya menyaring daftar yang dimuat; tidak mengaku mengubah periode laporan/ledger.

Form pembayaran mengelompokkan bukti, akun penerimaan, dan alokasi komponen. Total selalu berada dekat tombol Simpan pada footer dialog, termasuk mobile. Validasi memberi pesan dan fokus pada field bermasalah; nominal positif, batas sisa per komponen, tanggal valid, dan akun/bukti tetap wajib. Nominal nol tidak disertakan pada alokasi yang dikirim. Error server tetap berada dalam form; request ID, tanggal lokal, bukti, dan input tidak dibuang saat mencoba ulang. Akun yang belum tersedia memiliki pesan dan tindakan muat ulang.

`payment.ts` memusatkan total dalam sen, validasi, serta bentuk payload pembayaran yang dipakai controller; API dan backend tidak diubah. `presentation.ts` memusatkan label status dan kelayakan tindakan; nilai `null` tetap belum diketahui meski flag rekonsiliasi tidak konsisten. Invoice tidak mengubah nilai tak diketahui menjadi Rp 0. Guard rekonsiliasi dan komponen negatif pada fetch rincian tetap dipertahankan. Tagihan yang sudah punya pembayaran tidak mendapat tindakan ubah/batalkan biasa.

Kontrol pembuatan tagihan mendapat label terhubung, sentence case, ikon Phosphor dari aset bersama, dan penguncian parameter ketika request sedang berjalan. Perubahan filter batch membatalkan hasil pemeriksaan sebelumnya; tombol pembuatan kembali membutuhkan pemeriksaan yang sesuai. Respons tarif hanya diterapkan pada form/periode yang masih aktif, sehingga hasil periode lama tidak menimpa pilihan baru. Seluruh jalur API, transaksi, akun Kas/Bank existing, idempotensi, permission, serta class/Teleport/afterprint invoice dipertahankan.

### Bukti pemeriksaan 0.4

- 23 tes terarah / 5 file lulus. Empat kasus tambahan memeriksa jumlah sen, payload/string dua desimal/tanggal lokal/request ID, nominal/tanggal/alokasi invalid, status belum diketahui, dan invoice yang tidak mengarang Rp 0. Tidak menjalankan seluruh suite.
- Build/typecheck aplikasi berhasil. Build entry sistem desain juga diperiksa terpisah. Peringatan ukuran chunk existing tetap ada.
- `checks/billing.js` mengintersep seluruh request API dengan fixture lokal: 0,10 + 0,20 menghasilkan `0.30`; server gagal lalu retry memakai ID yang sama; riwayat menampilkan bukti dan status pencatatan; rekonsiliasi, komponen negatif dan form kosong menahan pembayaran.
- Pemeriksaan batch menunjukkan perubahan periode menonaktifkan hasil pemeriksaan lama. Simulasi respons tarif Januari yang terlambat tidak menimpa tarif Februari yang sudah dipilih.
- Jalur cetak diuji dengan `window.print` diganti stub: mask invoice ada sebagai anak body, mode cetak aktif saat dipanggil, lalu class dibersihkan setelah event afterprint. Tidak membuka printer atau menghasilkan bukti cetak fisik/PDF.
- Pada viewport 320 px, halaman dan dialog pembayaran tidak meluber (dialog scroll/client 286 px). Total tetap terlihat di footer. Menu terukur 44 px setelah transisi selesai; Escape mengembalikan fokus ke pemicu.
- `checks/design-system.js` memeriksa create/edit/delete siswa contoh, pembayaran hingga lunas, riwayat, serta faktur dengan nominal belum diketahui. Seluruh aktivitas spesimen menghasilkan **nol request API**. Data contoh hanya di memori dan direset saat reload.
- Screenshot tagihan terbaru berakhiran `-04`; bukti Siswa/interaksi shared sebelumnya berakhiran `-03`. Screenshot aplikasi menggunakan fixture fiktif, bukan data sekolah.

Sumber prosedural tetap `frontend-design` dan `emil-design-eng`; Context7 dipakai untuk dokumentasi resmi [Menu](https://primevue.org/menu) beserta slot/command/aksesibilitas, dan Playwright untuk inspeksi alur. Tidak menambahkan library atau memasang seluruh plugin yang tersedia. Referensi Mobbin sebelumnya dipakai sebagai pembanding hierarki, bukan bukti permission atau backend.

Batas yang masih berlaku: belum seluruh 23 view dipoles, Kegiatan Guru masih tahap berikutnya, tidak ada deployment, mutasi API sekolah asli, review pengguna TU, pembaca layar, Safari/iPad, atau cetak fisik/PDF. Ikon pada modul yang belum dimigrasi masih dapat memakai PrimeIcons existing; dependency tersebut belum dihapus secara global.


## Penerapan 0.5 — Kegiatan Guru dan Kepsek

Layar kegiatan dipisahkan menjadi controller API existing dan komponen domain reusable: `KegiatanDirectory.vue`, `KegiatanFormDialog.vue`, `KegiatanRealisasiDialog.vue`, `KegiatanReportDialog.vue`, serta `KegiatanUsage.vue`. Aplikasi dan `ActivityWorkbench.vue` memakai komponen yang sama; spesimen memanipulasi fixture saja. Guru melihat kegiatan/laporan dan mencatat realisasi; pengelolaan tetap hanya untuk Kepsek melalui `auth.hasRole` existing. Guru tidak mengambil opsi COA atau pegawai pengelolaan.

Daftar menempatkan nama/tahun pelajaran/status, pagu, realisasi/persentase, sisa, dan tindakan peran dalam satu record. Tidak ada kartu KPI yang mengulangi seluruh tabel. Persentase menyebut denominator pagu, memakai satu desimal bila perlu, dan tidak dibulatkan menjadi 100% ketika aktualnya 99,6%. Pagu nol/rasio non-finite tidak dianggap sebagai persentase nol. Bar visual dibatasi 0–100, sementara label tetap menyebut persentase aktual jika melampaui pagu. Nominal sumber API tidak diganti dengan nilai bar yang dibatasi. Mobile menampilkan informasi yang sama sebagai record bertumpuk.

`kegiatanApi.listAll` mengikuti pola pagination existing Siswa/Tagihan agar pencarian serta jumlah daftar mencakup seluruh halaman pada filter tahun pelajaran yang diminta. Method `list` tetap kompatibel untuk dashboard yang mengambil cuplikan. Respons filter lama diabaikan agar tidak mengganti periode yang lebih baru. Pilihan tahun pelajaran yang gagal dimuat tidak menghapus daftar; kegagalan data kegiatan tidak ditampilkan sebagai data awal kosong.

Form menghubungkan label, bantuan/error, fokus, serta status memuat. Pembuatan memeriksa nama, akun, pagu positif dan urutan tanggal. Realisasi memeriksa tanggal valid, nominal positif dan batas sisa sesuai rule backend. Input/parameter dan penutupan dikunci saat menyimpan; input dipertahankan ketika server gagal. Catatan realisasi tetap menjadi jurnal DRAFT sesuai backend existing, bukan klaim sudah masuk buku besar. Form error menyediakan Periksa laporan sebelum kirim ulang; pembacaan laporan menyegarkan sisa pada target form.

`core/format.ts` menambahkan `formatLocalDate` untuk payload kalender Tagihan dan Kegiatan. Mengambil field tanggal lokal menghindari pergeseran hari akibat `toISOString()` pada tengah malam. Helper menolak Date invalid; `formatRp` dan kontrak null existing tidak diubah secara global. Pemeriksaan input manual menemukan PrimeVue mengembalikan tanggal lama setelah teks seperti `31/02/2026` gagal diparse. `calendarTextMatches` membandingkan input dengan nilai yang diterima kalender sebelum blur; tiga form menahan submit sampai tanggal dikoreksi/dipilih ulang. Tanggal opsional yang sengaja dikosongkan tetap diperbolehkan. SearchField bersama juga mempertahankan label terlihat sebagai nama aksesibel ketika diberi `inputId`; cakupan pencarian menjadi deskripsi terpisah, tanpa mengganti nama label dengan tooltip panjang.

### Bukti pemeriksaan 0.5

- 35 tes terarah / 8 file lulus: cakupan sebelumnya ditambah pagination kegiatan, payload tanggal lokal/Date invalid, rasio budget, guard realisasi, form tanggal terbalik/error/input, dan kontrak label/hint pencarian, dan input tanggal manual yang gagal diparse. Tidak menjalankan seluruh suite.
- Build/typecheck aplikasi dan build entry sistem desain diperiksa. Warning chunk existing masih ada. Tidak menambah dependency atau mengubah skema/API/backend.
- `checks/activities.js` mengintersep seluruh API. Guru memuat halaman kedua kegiatan tanpa COA/pegawai; tidak mendapat Buat/Ubah/Hapus. Nominal nol dan melebihi sisa ditahan. Input realisasi dipertahankan setelah error, laporan dapat dibaca, dan tanggal lokal/nominal 150000.25 tetap sesuai payload.
- Kepsek dapat membuat fixture dengan pagu `1250000.50` dan tanggal `2026-10-16` sampai `2026-10-31`; tanggal terbalik tidak dikirim. Penghapusan hanya ditawarkan pada kegiatan tanpa realisasi. Simulasi respons tahun pelajaran lama tidak menimpa pilihan terbaru. Pilihan periode gagal tetap membiarkan daftar tampil; data gagal menyediakan pemulihan.
- Viewport 320 px dan dialog realisasi memiliki scroll/client 286 px; tidak meluber. Screenshot terbaru kegiatan/empat home role memakai akhiran `-05`. Screenshot tetap memakai data fiktif.
- `checks/design-system.js` kini juga memeriksa Guru mencatat realisasi dan membuka laporan, serta Kepsek membuat/menghapus kegiatan contoh. Tanggal manual tidak valid pada pembayaran, realisasi dan tanggal kegiatan opsional juga diuji: ditolak, lalu koreksi valid diterima. Seluruh rangkaian Siswa, Tagihan dan Kegiatan pada sistem desain menghasilkan **nol request API**.
- `checks/roles.js` diperiksa ulang: empat home role tetap sesuai prioritasnya; Finance tanpa tren kehadiran, Kepsek dengan antrean layak tinjau, TU Siswa, Guru Kegiatan. Menu mobile kembali fokus setelah Escape; kegagalan arus kas tetap khusus panel.

### Batas yang belum ditutup

Belum seluruh 23 view direvamp, belum ada deployment, dan belum memeriksa API/akun sekolah asli, usability dengan pengguna, pembaca layar, Safari/iPad, atau cetak fisik/PDF. Pipeline cetak hanya diprobe dengan stub pada 0.4. Build masih memberi warning ukuran chunk.

**Realisasi Kegiatan berbeda dari pembayaran Tagihan:** endpoint existing tidak memiliki request ID/idempotensi backend. UI mencegah klik ganda saat pending dan mengarahkan pemeriksaan laporan ketika gagal, tetapi tidak menjanjikan retry bebas duplikasi jika server sudah menyimpan sementara respons hilang. Pemeriksaan API fixture tidak membuktikan jaminan transaksi/backend tersebut. Semua mutasi pada script review diintersep lokal; tidak mengubah data sekolah.


## Penerapan 0.6 — Jurnal Finance dan Kepsek, lokal

`JurnalListView.vue` tetap controller API. `JurnalDirectory.vue`, `JurnalFormDialog.vue`, `JurnalDetailDialog.vue`, `JurnalActionDialog.vue`, dan `presentation.ts` digunakan oleh aplikasi serta `JournalWorkbench.vue`. Tidak mengganti stack, memasang dependency, mengubah backend, atau melakukan deployment. Permintaan pengguna membatasi eksekusi ke lokal; tidak ada mutasi data sekolah.

Daftar mengelompokkan nomor bukti/keterangan, tanggal/sumber, nominal jurnal dan status. Nominal menyatakan total debit yang seimbang dengan kredit, bukan arus kas; rincian belum cocok/tidak valid tidak dianggap nol. Status dan sumber memakai bahasa produk. Tombol Periksa membuka rincian akun dan tindakan sesuai role/status; konfirmasi menampilkan bukti, tanggal, nominal, serta konsekuensi. Satu record mobile memuat informasi yang sama, dengan rincian akun dapat digulir secara lokal.

Pencarian memakai `search` backend atas nomor bukti/keterangan dengan pagination server 10 record. Alias `jenis=masuk|keluar` tetap query pada satu view; keduanya memfilter akun pendapatan/beban sesuai backend, bukan otomatis klasifikasi kas. Pilihan filter baru tidak mengubah klaim cakupan daftar sampai Terapkan ditekan. Filter kembali ke halaman pertama; respons lama diabaikan, halaman tak tersedia kembali ke awal, dan gagal data berbeda dari kosong. Gagal memuat COA tidak menghilangkan jurnal; nama akun yang belum dimuat dibedakan dari kode/nominal yang tersedia.

Form menghubungkan label dan error, memisahkan identitas bukti dari baris akun, dan menempatkan total/selisih dekat tindakan simpan pada footer tetap. Total dihitung dalam sen; payload mempertahankan dua desimal dan tanggal kalender lokal. Akun aktif, nomor bukti, tanggal, keseimbangan positif dan satu sisi nominal per baris diperiksa sebelum mengirim. Tanggal manual yang tidak valid diblokir dengan helper existing. Input tetap ada saat gagal; pending mengunci kontrol, tombol tutup dan Escape. Tidak memilih akun pendapatan/beban secara otomatis berdasarkan urutan COA.

Finance tetap membuat/mengubah/menghapus draf manual, mengajukan jurnal khusus, mencatat jurnal yang memenuhi syarat, dan membatalkan penerimaan sebelum posting dengan alasan. Kepsek menyetujui hanya PENDING yang memenuhi syarat dan bukan dibuatnya sendiri. Jurnal tercatat tidak mendapat edit draf; pembatalannya melalui endpoint pembalik existing, yang membuat serta mencatat jurnal pembalik sambil mempertahankan jurnal asli. Backend tetap menegakkan izin, periode tertutup, saldo, transaksi sumber dan pencegahan pembalikan berulang.

### Review layout

Skill `frontend-design` dipakai untuk implementasi mengikuti fondasi existing; `better-layout` khusus untuk grouping, reading order, prioritas informasi dan adaptivitas. Tidak membuka ulang semua provider referensi. Mobbin pada bagian referensi sebelumnya tetap pembanding komposisi. MCP Playwright digunakan pada browser terisolasi, dengan fixture untuk seluruh API aplikasi.

| Severity | Location | Before | After | Why |
|---|---|---|---|---|
| MEDIUM, diperbaiki | `frontend/src/features/jurnal/JurnalDirectory.vue:29`, `JurnalDetailDialog.vue:20` | Banyak tindakan transaksi bersaing dalam setiap baris | Identitas/nominal/status mudah dipindai; rincian dan aksi dipusatkan pada pemeriksaan satu bukti | Kelompokkan menurut pekerjaan dan dahulukan informasi penting |
| MEDIUM, diperbaiki | `frontend/src/features/jurnal/JurnalFormDialog.vue:48` | Form header horizontal dan tabel multi-baris tanpa susunan mobile khusus | Metadata, baris akun dan total membentuk kelompok; mobile menumpuk akun di atas debit/kredit | Pertahankan urutan baca serta tindakan dalam area yang tersedia |

Approve untuk layout yang diperiksa pada lebar 1440, 1024, 768, 390 dan 320 px; halaman spesimen tidak meluber dan hanya satu representasi record yang terlihat. Dialog/form/rincian spesimen dan halaman aplikasi diperiksa pada 320 px. Escape dari rincian kembali ke tombol Periksa. Not verified: zoom 200%, RTL, terjemahan/pseudo-localization, pembaca layar, Safari/iPad dan perangkat sekolah. Ini bukan persetujuan rilis atau bukti seluruh layar sudah konsisten.

### Bukti pemeriksaan 0.6

- 30 tes terarah / 5 file lulus: 8 kasus baru Jurnal ditambah format, navigasi dan route guard existing. Mencakup desimal 0,10 + 0,20 = 0,30, payload tanggal lokal, nominal invalid, akun nonaktif, status/role, larangan persetujuan sendiri, input/error dan pending. Tidak menjalankan seluruh suite.
- Build/typecheck aplikasi dan build entry sistem desain berhasil; peringatan ukuran chunk tetap ada. Spesimen menambah kode demonstrasi pada entry terpisah, bukan dependency baru produk.
- `checks/journal-system.js`: ubah draf desimal, tanggal manual invalid lalu koreksi, catat, immutable setelah posting, rekonsiliasi, alasan pembatalan, peran Kepsek, persetujuan sendiri/layak, pembalik dan mobile. Menghasilkan nol request API dan nol page error. Reload memulihkan fixture.
- `checks/journal-app.js`: seluruh API diintersep lokal. Memeriksa alias jenis, server pagination/search, filter belum diterapkan, gagal simpan/input tetap ada, gagal tindakan dengan pemeriksaan status melalui GET sebelum retry, pending Escape, payload `1250000.50`/`2026-10-16`, serta dispatch create/update/delete/submit/catat/batal-penerimaan/approve/void. Seluruh mutasi hanya mengubah fixture. Gagal COA tetap menampilkan jurnal; gagal daftar memberi retry, bukan data kosong. Tidak ada page error.
- Screenshot `jurnal-*-06.png`, `role-Finance-jurnal-06.png`, dan `role-Principal-jurnal-mobile-06.png` tersimpan bersama artefak. Semua memakai data fiktif.

### Batas implementasi Jurnal

Belum ada deployment, login/mutasi akun sekolah, backend integration test nyata, seluruh view, cetak fisik/PDF, audit aksesibilitas menyeluruh atau review pengguna. Backend/schema tidak diubah. Realisasi kegiatan tetap memiliki batas idempotensi yang dijelaskan pada 0.5. Jurnal tidak menambahkan request ID baru: setelah respons mutasi hilang, UI meminta pemeriksaan status melalui GET sebelum mencoba kembali; fixture bukan jaminan transaksi backend. Backend menolak pembalik berulang, sementara payload jurnal saat ini tidak menyertakan penanda bahwa sebuah jurnal sudah dibalik; aksi dapat tetap terlihat sampai server memeriksanya.


## Penerapan 0.7 — Laporan pada aplikasi localhost

Kelima laporan tetap tersedia di `/laporan`: Neraca saldo, Laba rugi, Posisi keuangan, Realisasi anggaran dan Buku besar. `LaporanView.vue` memiliki pengambilan data/snapshot; `LaporanContent.vue` dan `AccountReportTable.vue` berbagi penyajian akun. `presentation.ts` memusatkan cakupan dan hitungan sen. Tidak membuat preview HTML laporan baru, mengganti stack, menambah dependency, mengubah API/permission atau deploy.

Empat laporan menggunakan tahun. Buku besar menggunakan tahun, bulan dan akun, termasuk akun nonaktif untuk riwayat. Judul, kode/nama/posisi normal akun, cetak dan CSV mengikuti snapshot hasil, bukan pilihan yang belum diterapkan. Pindah tab memakai cakupan yang sudah diterapkan; respons terlambat diabaikan. Gagal muat menghapus angka lama, menyediakan retry dan menonaktifkan cetak/CSV. Gagal COA memiliki pemulihan tersendiri.

Saldo negatif dan desimal dipertahankan; nilai tidak valid/tidak diketahui tidak menjadi nol. Buku besar membawa baris SALDO-AWAL dari server, menghitung saldo berjalan menurut posisi normal, dan tidak mengarang saldo berikutnya ketika nominal tidak diketahui. Total Posisi keuangan memperhitungkan akun kontra berdasarkan posisi normal bucket. Selisih tetap ditampilkan; laba tahun berjalan tidak otomatis ditambahkan ke ekuitas yang tidak diberikan endpoint. Anggaran menampilkan persentase aktual (99,6%/150%), dengan bar visual terbatas dan pagu nol tanpa persentase palsu. CSV tetap khusus Neraca saldo sesuai fitur existing.

### Review layout dan bukti

`frontend-design` dipakai untuk implementasi sesuai fondasi; `better-layout` untuk grouping, prioritas dan adaptivitas. MCP Playwright dipakai pada aplikasi/router yang sebenarnya dalam browser terisolasi. Referensi visual sebelumnya tetap berlaku; tidak membuka ulang semua provider.

| Severity | Location | Before | After | Why |
|---|---|---|---|---|
| MEDIUM, diperbaiki | `frontend/src/features/laporan/LaporanView.vue:90`, `reports.css:1` | Tab aktif dapat tersembunyi saat layar menyempit | Pilihan Jenis laporan menggantikan tab saat lebar workspace di bawah 700 px | Lokasi aktif dan tujuan lain tetap terlihat, mengikuti ruang konten |
| MEDIUM, diperbaiki | `frontend/src/features/laporan/AccountReportTable.vue:12`, `reports.css:16` | Nominal tidak sejajar dan tabel/grid tidak mengatur ruang sempit | Angka rata akhir, saldo bertanda, kelompok laporan konsisten; tabel dapat digulir lokal dengan petunjuk/fokus | Perbandingan nominal tetap terbaca tanpa meluberkan halaman |

Approve untuk layout yang diperiksa pada 1440, 1024, 768, 390 dan 320 px. Not verified: zoom 200%, RTL/pseudo-localization, pembaca layar, Safari/iPad, perangkat sekolah dan printer fisik.

- 11 tes terarah / 2 file lulus: scope dan snapshot, CSV tahun diterapkan, stale response, gagal/retry, COA, akun kontra, kredit-normal ledger, desimal/negatif/unknown serta persentase. Tidak menjalankan seluruh suite.
- Build/typecheck aplikasi dan build entry dokumentasi diperiksa; warning ukuran chunk existing masih ada.
- `checks/reports.js` memeriksa aplikasi Finance/Kepsek dengan seluruh API diintersep fixture lokal. Tidak ada mutasi API dan tidak ada page error. Memeriksa filter pending, judul/CSV/cetak yang mengikuti hasil, respons terlambat, lima laporan, COA failure, saldo pembuka kredit, persentase, 320–1440 px dan pemulihan kegagalan.
- Cetak diperiksa melalui stub `window.print` dan CSS print: identitas sekolah/judul/periode/tabel tampil, kontrol dan navigasi tersembunyi. Belum merupakan bukti PDF/printer fisik. Screenshot memakai fixture `laporan-*-07.png` dan `role-Principal-laporan-07.png`.

### Penyesuaian lingkungan lokal

Pemeriksaan API localhost menemukan empat laporan HTTP 400 karena kolom saldo awal belum tersedia. Rencana menunjukkan tepat satu migrasi existing yang tertinggal: `accounting.0003_opening_balance`. Setelah memastikan host database localhost, tidak ada kedua kolom tersebut, dan membuat backup PostgreSQL privat (mode 0600 di temporary directory), migrasi existing diterapkan hanya pada database lokal. Tidak menulis aturan/skema baru di source backend atau mengisi saldo awal nonnol berdasarkan dugaan. Sesudahnya kelima laporan dan COA merespons HTTP 200 pada akun Finance lokal. Tidak mengubah transaksi bisnis atau mengakses database online.

Seluruh UI/state dalam browser masih menggunakan fixture; pembacaan backend nyata di atas terbatas ke endpoint localhost dan tidak membuktikan rekonsiliasi angka, semua role backend, seluruh view, atau kesiapan produksi. Backup lokal bukan artefak publik. Tidak ada deployment.


## Penerapan 0.8 — Absensi siswa TU dan Rekap TU/Guru, lokal

Review melalui aplikasi `/absensi-siswa` dan `/rekap-siswa`. `AbsensiSiswaView.vue` memiliki konteks, API, simpan/hapus dan guard perubahan; `AttendanceGrid.vue` mempertahankan kontrak props/event dan berbagi status/layanan melalui `presentation.ts`. `RekapSiswaView.vue` memiliki snapshot hasil, pencarian dan CSV; `RekapDirectory.vue` menyajikan tabel/kartu serta pagination. `attendance.css` memakai token existing dan terlingkup ke kedua workspace. API jenjang/kelompok menambah `listAll` tanpa mengubah caller `list` existing. Helper rekap untuk Katering/Jemputan dipertahankan.

Tanggal/jenjang/kelompok diterapkan eksplisit. Input konteks baru tidak mengubah tujuan Simpan sebelum daftar diterapkan. Semua halaman siswa, catatan, jenjang dan kelompok dibaca; catatan halaman kedua tidak kembali menjadi default Hadir. Default Hadir tanpa ID ditandai belum disimpan. Status bukan hadir menonaktifkan dan mengosongkan ketiga layanan pada payload. Pilihan status memiliki `aria-pressed`, nama siswa, dan target minimum 44 px; checkbox dibungkus label sentuh.

Simpan menunggu seluruh hasil, menyimpan ID yang berhasil dan mempertahankan input gagal. Sebelum retry, GET memeriksa ID/status aktual termasuk POST yang sudah diterima server tetapi responsnya hilang. Hanya catatan yang masih perlu disimpan dikirim kembali; pembalikan pilihan oleh pengguna setelah error tetap dihormati. Kontrol terkunci selama pending. Hapus hanya mengubah baris target; draft siswa lain tetap ada. Pergantian daftar, muat ulang dan navigasi memperingatkan perubahan manual/hasil belum terkonfirmasi. Default Hadir yang belum disentuh bukan perubahan manual.

Rekap memakai satu pilihan bulan+tahun yang sesuai TA Juli–Juni. Hasil dan CSV tetap pada cakupan diterapkan, termasuk saat filter berubah. Bulan berjalan dibatasi sampai hari ini; keterangan menyatakan jumlah hari, bukan persentase/tingkat kehadiran. Nol catatan tidak dianggap tidak hadir. Pencarian menjangkau seluruh hasil, toggle membuka siswa tanpa catatan, dan CSV mengekspor semua hasil filter, bukan satu halaman. Gagal data membersihkan angka lama dan menonaktifkan CSV; gagal nama kelompok memiliki retry terpisah dan label belum dimuat. Guru mendapat rekap baca-saja tanpa CTA Isi absensi. Izin backend existing tetap berlaku.

### Review layout dan bukti 0.8

`frontend-design` digunakan untuk menerapkan fondasi dan `better-layout` untuk grouping/urutan baca/adaptivitas. MCP Playwright digunakan pada browser terisolasi dengan seluruh `/api/**` diintersep fixture. Tidak membuka ulang provider referensi yang tidak dibutuhkan untuk pola existing.

| Severity | Location | Before | After | Why |
|---|---|---|---|---|
| MEDIUM, diperbaiki | `frontend/src/features/absensi/AbsensiSiswaView.vue`, `AttendanceGrid.vue` | Konteks berubah otomatis, ringkasan simpan jauh dari input dan hasil parsial hilang | Cakupan eksplisit, bar simpan tetap terlihat, status per siswa dan input gagal dipertahankan | Konteks dan akibat tindakan harus mudah diperiksa |
| MEDIUM, diperbaiki | `frontend/src/features/absensi/RekapSiswaView.vue`, `RekapDirectory.vue` | Tahun/bulan dapat tidak sesuai TA; tabel lebar; Guru melihat CTA isi absensi | Bulan terikat TA, kartu pada ruang sempit, judul/CSV terikat hasil dan CTA sesuai izin | Urutan baca dan tindakan mengikuti tugas serta ruang tersedia |

Approve untuk layout yang diperiksa pada 1440, 1024, 768, 390 dan 320 px. Tidak ada overflow halaman; tombol status minimal 44 px. Kalender terbuka juga diperiksa pada 320 px. Fokus pilihan dapat dicapai; ini bukan audit pembaca layar menyeluruh. Not verified: zoom 200%, RTL/pseudo-localization, Safari/iPad dan perangkat sekolah.

- **16 tes terarah / 3 file lulus**: default vs perubahan manual, ID, status/layanan, pagination/error, batas bulan/as-of, nol data, pending/allSettled, hasil POST ambigu, pembalikan input sebelum retry, hapus satu baris, Teacher read-only, snapshot CSV, gagal/retry dan nama kelompok. Tidak menjalankan seluruh suite.
- Build/typecheck aplikasi lulus; warning chunk existing di atas 500 kB tetap ada. Tidak menambah dependency, mengganti stack, mengubah backend/skema/permission atau melakukan deployment.
- `checks/attendance.js` memeriksa 34 siswa dan 32 catatan awal lintas halaman, partial save, respons hilang setelah commit fixture, retry tanpa POST duplikat, tanggal diterapkan, delete tetap mempertahankan draft lain, pembatalan pindah daftar, tanggal manual invalid, role Guru, CSV 33 hasil lintas halaman, search/pagination, toggle, error/recovery, dan viewport. Hasil ringkas `checks/attendance-result-08.json`; nol page error. Semua POST/PATCH/DELETE hanya mengubah fixture di memori, bukan database lokal/sekolah.
- Screenshot `absensi-desktop-08.png`, `absensi-mobile-08.png`, `absensi-calendar-mobile-08.png`, `rekap-teacher-desktop-08.png`, `rekap-mobile-08.png` memakai data fiktif dan telah dilihat saat review.
- Pembacaan backend nyata hanya di localhost: masing-masing GET jenjang, kelompok, siswa aktif dan kehadiran merespons HTTP 200 untuk `admin.tu` dan `guru.kegiatan` (8 GET). Larangan tulis Guru dikonfirmasi pada permission source existing; tidak mencoba mutasi data nyata. Tidak ada seed atau migrasi pada tahap 0.8.

### Batas absensi/rekap dan tahap berikut

Simpan massal masih per catatan; tidak atomik dan tidak memiliki optimistic locking/idempotency key backend. Pemeriksaan GET sebelum retry menutup skenario respons hilang yang diuji, bukan jaminan transaksi serentak/exactly-once. Unique siswa/tanggal tetap ditegakkan backend. Hapus setelah respons terputus dapat memerlukan muat ulang untuk memeriksa hasil. Arsip memakai siswa aktif/kelompok profil saat ini, bukan snapshot historis; keterangan ini tampil pada layar. Belum ada walkthrough pengguna sekolah, mutasi integrasi nyata, seluruh suite atau deployment. Berikutnya Katering/Jemputan TU, lalu sisa inventaris 23 view.


## Penerapan 0.9 — Katering dan Jemputan TU, lokal

18 Oktober 2026. Review menggunakan aplikasi `/katering` dan `/jemputan`, bukan HTML preview baru. Skill `frontend-design` digunakan untuk implementasi sesuai fondasi existing; MCP Playwright untuk browser terisolasi dan fixture seluruh API. Referensi sebelumnya tetap berlaku; tidak menambahkan referensi/provider tanpa kebutuhan baru. Tidak mengganti stack, menambah dependency, mengubah backend/permission/skema, seed, migrasi, atau deploy.

Katering memisahkan cakupan bulanan, tarif, dan hasil. Pengaturan tarif memakai disclosure native: ringkasan Senin–Kamis/Jumat tetap terbaca dan form dibuka bila diperlukan. Hasil/CSV tetap memakai tarif yang berhasil dimuat, bukan angka yang sedang diketik. Gagal tarif tidak diam-diam memakai tarif bawaan atau mempertahankan total lama; tarif bawaan hanya ditandai ketika endpoint memang mengirim `is_default`. Gagal simpan mempertahankan input; PUT tarif tetap memakai periode diterapkan. Jenjang/kelompok dan periode diterapkan eksplisit; CSV mengikuti hasil pencarian lintas halaman. Export format lama tetap tersedia dan menjelaskan cakupan endpoint bulanan yang berbeda dari filter layar.

Menu mingguan menjadi daftar lima hari dengan tanggal, isi, foto opsional, dan aksi jelas. Foto tanpa keterangan tetap dapat disimpan; keterangan/foto keduanya kosong ditolak. Keterangan maksimal 255 karakter sesuai model. Input termasuk file/preview dipertahankan setelah gagal; object URL dibersihkan. Pending mengunci form, Escape/tutup dan perpindahan minggu/bagian. Setelah hasil create ambigu, tanggal unik diperiksa sebelum POST ulang; jika sudah ada menu, pengguna diarahkan memuat ulang dan memeriksa record, bukan menimpanya diam-diam. Muat menu gagal berbeda dari hari yang belum diisi; respons minggu lama diabaikan.

Jemputan memiliki bagian Armada, Pendaftaran siswa, dan Rekap. Daftar dan pilihan dibaca sampai halaman terakhir; pencarian mereset pagination. Nama pengemudi, kendaraan/rute, kapasitas, siswa/alamat, armada dan tarif dikelompokkan sesuai tugas. Form mempunyai label, validasi panjang/angka, error inline, input tetap ada, dan pending yang mengunci simpan/tutup/Escape. Kapasitas dan tarif nol dipertahankan. Harga diberi label **per perjalanan**, sesuai backend, bukan per bulan. Menghapus armada menjelaskan konsekuensi penetapan armada pada pendaftaran; menghapus pendaftaran tidak menghapus absensi.

Ditemukan mismatch existing: helper rekap memilih tarif tertinggi dari beberapa pendaftaran, sedangkan `build_tagihan_komponen` memilih ID pendaftaran terbaru. `buildJemputanRekap` kini memilih ID terbaru beserta armada/tarifnya, termasuk nol, tanpa bergantung urutan API. Backend tidak diubah. Perkalian nominal kedua rekap menggunakan sen untuk mencegah ekor float pada tarif desimal. Muat armada ditunggu bersama data rekap sehingga label tidak bergantung urutan selesai request.

`shared/components/ServiceRecap.vue` dipakai kedua rekap: identitas siswa, unit hari/perjalanan, tarif, jumlah, total sesuai filter, pagination 15 baris, tabel desktop dan kartu pada ruang sempit. `school-services.css` mengatur dua workspace/dialog dengan token existing; tidak diimpor ke modul lain. `PeriodPicker.vue` mempertahankan props/model dan kini memakai caret Phosphor yang sama. Controller domain tetap memiliki API dan mutasi; tidak dibuat abstraksi CRUD lintas domain.

### Bukti dan batas 0.9

- **13 tes terarah / 3 file lulus**: foto tanpa teks/validasi kosong, hari kerja/Jumat/akhir pekan, kalender lokal, nominal sen, pendaftaran terbaru vs tertinggi, tarif nol, pagination/error, draft tarif vs CSV, kegagalan tarif, pending form, validasi kapasitas/nama, zero edit dan respons label armada. Tidak menjalankan seluruh suite.
- Build/typecheck aplikasi lulus; warning ukuran chunk existing di atas 500 kB tetap ada. Tidak menambah dependency.
- `checks/school-services.js` mengintersep **seluruh API**. Memeriksa 28 siswa/armada, 29 pendaftaran awal, pembacaan lintas halaman, pencarian/CSV seluruh hasil, periode belum diterapkan, tarif belum tersimpan, gagal/retry, foto menu, create/edit/delete Menu/Armada/Pendaftaran, pending Escape, kapasitas/harga nol, dan kecocokan pendaftaran terbaru. Semua mutasi hanya pada fixture di memori; tidak mengubah data lokal/sekolah. Nol page error. Hasil ringkas `checks/school-services-result-09.json`.
- Kelima area (rekap katering, menu, armada, pendaftaran, rekap jemputan) diperiksa pada lebar 1440, 1024, 768, 390 dan 320 px tanpa overflow halaman. Dialog foto menu juga diperiksa pada 320 px. Screenshot `katering-*-09.png` dan `jemputan-*-09.png` memakai fixture dan telah dilihat saat review. Ini pemeriksaan layout browser, bukan usability dengan pengguna sekolah.
- Empat GET backend **localhost** (tarif, menu mingguan, armada dan pendaftaran jemputan) merespons 200 dengan akun TU lokal. Tidak melakukan mutasi layanan nyata. Izin tetap Administration pada router/backend.

Rekap masih memakai profil siswa aktif, pendaftaran dan tarif saat ini pada arsip; bukan snapshot historis. Semua tanggal dalam bulan dihitung sesuai helper existing, termasuk catatan bertanggal sesudah hari ini; tidak mengklaim rekap sampai hari ini. Rekap merupakan perhitungan, bukan bukti tagihan dibuat/dibayar. Create armada/pendaftaran belum memiliki idempotency key backend; setelah hasil ambigu UI meminta pemeriksaan daftar sebelum mencoba menambah kembali, tanpa janji exactly-once. Belum diperiksa: seluruh suite, mutasi integrasi nyata, Safari/iPad, pembaca layar, zoom 200%, perangkat sekolah, dan validasi file oleh server melalui upload nyata. Tidak ada deployment. Berikutnya Pendaftaran siswa dan modul pegawai/administrasi yang tersisa.


## Penerapan 0.10 — Pendaftaran calon, terhubung ke localhost

18 Oktober 2026. Skill `frontend-design` dipakai mengikuti fondasi existing; MCP Playwright memeriksa aplikasi/router sebenarnya dalam browser terisolasi dengan seluruh `/api/**` diganti fixture. Source tidak menambah alur daftar ulang karena kontrak modul ini khusus calon baru/sit-in sampai menjadi siswa. Backend, permission dan aturan transaksi tidak diubah. Tidak ada deployment atau dependency baru.

Daftar memusatkan calon/jenjang/tanggal, status, total, diterima, dan sisa. Aksi per baris menjadi Rincian; desktop memakai tabel dan ruang sempit memakai kartu. Pencarian nama/jenjang/status meliputi semua halaman yang dimuat; filter/search kembali ke halaman pertama. Panduan alur dibuat disclosure agar tidak mendominasi pekerjaan. Gagal daftar menghapus data lama dan menyediakan retry; gagal jenjang tidak menghilangkan calon.

`PendaftaranDirectory.vue`, `PendaftaranFormDialog.vue`, `PendaftaranPaymentDialog.vue` dan `presentation.ts` memisahkan penyajian/validasi domain dari controller API `PendaftaranListView.vue`. `admission.css` memakai token dan terlingkup halaman/dialog. API menambah GET rincian untuk memeriksa data terbaru sebelum tindakan tersedia. Gagal rincian menonaktifkan tindakan sampai retry berhasil. Ubah/hapus hanya untuk TRIAL tanpa siswa/jurnal; finalisasi hanya TRIAL tanpa siswa; penerimaan mengikuti komponen positif yang belum diterima dan bukan BATAL/reconciliation.

Form mempertahankan biaya serta SPP kosong tanpa tarif dugaan; nol harus diisi eksplisit. Nilai historis `biaya_pendaftaran` tidak disalin ke formulir. Tanggal lokal/manual invalid, nama, nominal sen, safe integer dan field wajib diperiksa sebelum submit. Input tetap ada saat error. Pending mengunci field, tutup/Escape dan navigasi; kalender ditutup ketika form terkunci. Setelah create ambigu, calon tidak dibuat ulang sebelum daftar diperiksa. Kas/Bank aktif sesuai daftar kode backend dimuat terpisah dengan retry.

Penerimaan hanya mencakup nilai penuh komponen yang dipilih; komponen sudah diterima/nol/unknown tidak ditawarkan. Hasil ambigu mengunci rincian percobaan; Coba ulang memakai payload identik agar pemeriksaan idempotensi backend berlaku. Finalisasi terpisah dari penerimaan, memakai SPP eksplisit termasuk nol, dan retry ambigu mempertahankan SPP yang sama. Sukses finalisasi membuka rincian terdaftar dengan tautan Data siswa, tanpa membuat penerimaan. Riwayat menampilkan nomor bukti, tanggal, komponen, nominal dan status jurnal dengan bahasa produk; hanya jurnal terakhir tiap komponen yang tersedia pada kontrak existing. Data lama unknown tetap unknown, bukan nol/lunas.

### Bukti UI 0.10

- **9 tes terarah / 2 file lulus**: unknown vs nol, sen/unsafe/negatif, guard status/jurnal/siswa, eligible component, biaya/SPP kosong, payload desimal/tanggal lokal, pending, retry penerimaan identik, gagal rincian/Kas/Bank, legacy lock dan gagal daftar. Tidak menjalankan seluruh suite.
- Build/typecheck aplikasi lulus; warning chunk existing di atas 500 kB tetap ada.
- `checks/admission.js` memeriksa 28 record lintas halaman, pencarian/filter, create/edit/delete, biaya kosong/nol/desimal, tanggal manual invalid, input setelah error, pending Escape, rincian segar, legacy unknown, Kas/Bank failure, full unpaid component, respons hilang setelah commit fixture, retry penerimaan/finalisasi identik dan finalisasi tanpa penerimaan. Semua mutasi hanya pada fixture di memori. Nol page error; hasil ringkas `checks/admission-result-010.json`.
- Daftar, rincian, form calon, penerimaan dan finalisasi diperiksa pada lebar 1440, 1024, 768, 390 dan 320 px tanpa overflow halaman. Screenshot `pendaftaran-*-010.png` menggunakan data fiktif dan dilihat saat review. Ini bukti UI fixture, bukan integrasi database/mutasi nyata.

### Riwayat hambatan database localhost dan penyelesaiannya

Pemeriksaan awal GET pendaftaran localhost mengembalikan HTTP 400: kolom `operations_pendaftaransiswa.biaya_formulir` belum tersedia. GET jenjang dan COA merespons 200. Saat itu status migrasi menunjukkan 0011/0012/0013 belum diterapkan. Source existing 0013 menambah komponen biaya nullable; dependensinya 0012 menambah struktur penerimaan tagihan dan menjalankan pembaruan penanda `perlu_rekonsiliasi=True` pada tagihan lama tertentu, sedangkan 0011 menyesuaikan field histori kegiatan.

Percobaan awal backup+migrasi ditolak review persetujuan otomatis karena mutasi penanda bisnis oleh 0012 belum disetujui eksplisit. Perintah itu tidak dijalankan dan tidak dicoba lewat jalur lain. Pengguna kemudian menjawab **“boleh”** atas permintaan backup database localhost dan penerapan `operations.0011–0013`, termasuk penanda rekonsiliasi. Setelah izin ini, backup dan migrasi berhasil dijalankan sesuai rencana; tidak ada fake migration atau perubahan source backend. Database online tidak diakses atau diubah.

- Backup privat PostgreSQL: `/private/tmp/beesmart-local-before-registration-x4horco8.dump`, 476.569 byte, mode 0600. Katalog backup dapat dibaca dengan `pg_restore --list`; restore penuh belum dicoba. File backup tidak dimasukkan ke repository.
- Tepat tiga migrasi existing forward diterapkan. Sebanyak **160 tagihan lama** mendapat `perlu_rekonsiliasi=True`; jumlah dan kondisi penanda diperiksa terhadap aturan 0012.
- Fingerprint seluruh kolom yang sudah ada pada tabel pendaftaran, siswa, tagihan dan jurnal sama sebelum/sesudah. Perubahan penanda berada pada kolom baru; nilai formulir pendaftaran lama tetap null. Tidak mengisi biaya atau merekonsiliasi berdasarkan dugaan.
- Lima GET localhost (daftar pendaftaran, rincian satu record, jenjang, COA dan tagihan) merespons **200**. Kontrak rincian biaya/pembayaran tersedia.
- Browser Playwright terisolasi berhasil login akun TU lokal, membuka enam pendaftaran dan rincian satu record dengan API nyata localhost. Semua request bisnis selain GET diblokir pada pemeriksaan ini; autentikasi dilakukan hanya pada endpoint token lokal. Token dibersihkan sesudah pemeriksaan; tidak menyimpan screenshot data nyata atau kredensial. Hasil ringkas ada pada `checks/admission-local-result-010.json`.


Belum diverifikasi: mutasi bisnis dengan database nyata, seluruh suite, Safari/iPad, zoom 200%, pembaca layar, perangkat sekolah, dan kesiapan rilis. Idempotensi yang diuji browser adalah simulasi sesuai source backend, bukan uji transaksi nyata. Pendaftaran bukan layar cicilan bebas, rekonsiliasi historis lengkap atau pembuatan bukti cetak baru. Berikutnya modul pegawai/administrasi.


## Audit regresi 0.10 — 18 Oktober 2026

Sebelum rollout berikutnya, laporan screenshot dialog Siswa ditelusuri melalui skill `ui-skills-root`/`better-layout`, source PrimeVue terpasang, dan Playwright MCP lokal. Perbaikan mencakup 18 slot clear dengan `SelectClearButton`, pemisah/scroll footer dialog, serta penutupan enam kalender dan 23 dropdown saat kontrol dikunci. Model, payload dan izin role dipertahankan.

**81 tes terarah / 19 file, build/typecheck, sembilan runner alur fixture dan 265 pasangan layar/ukuran lulus.** Semua API browser diintersep; tidak ada mutasi database sekolah atau deployment. Batas cakupan dan bukti lengkap ada pada [audit regresi](../../docs/reviews/2026-10-18-ui-regression-audit.md), dengan hasil [JSON](checks/ui-audit-result-010.json). Ini tidak mencakup seluruh 23 view atau validasi rilis. Modul pegawai/administrasi belum mulai direvamp pada audit ini.


## Perapian kolom tindakan Gaji/Kasbon — 18 Oktober 2026

Pass ini hanya memperbaiki kolom tindakan pada `GajiListView.vue` dan `PinjamanListView.vue`, bukan revamp seluruh modul pegawai. Mengikuti `better-layout` dan pola Menu existing Kegiatan: Lihat slip tetap terlihat pada Gaji; Ubah slip, Posting ke jurnal dan Hapus slip berada dalam menu tambahan. Kasbon menampilkan Cairkan, dengan Ubah/Hapus di menu tambahan. Hapus tetap memakai konfirmasi existing dan warna kritis di dalam menu; tidak tampil berulang sebagai ikon merah di tabel. Ikon baru memakai Phosphor lokal.

`employee-actions.css` dipakai kedua view, dengan satu baris kontrol, posisi tombol utama tetap, target ikon 44 px dan tinggi area tindakan yang sama termasuk baris tanpa aksi. Kondisi Finance dan jurnal existing dipertahankan; baris dijurnal/dicairkan tidak menawarkan aksi tulis. API, payload, service keuangan dan izin router/backend tidak diubah.

Build/typecheck lulus; warning chunk existing tetap ada. Playwright MCP memeriksa fixture lokal pada 1440, 1024, 768, 390 dan 320 px: tanpa overflow halaman, kontrol tidak turun baris, tombol utama sejajar, dan tinggi baris fixture konsisten. Menu keyboard/Escape mengembalikan fokus; Ubah membuka form yang benar, Lihat slip berfungsi, konfirmasi Hapus serta Cairkan tetap muncul dan dapat dibatalkan. Nol page error/mutasi API. Runner [employee-actions.js](checks/employee-actions.js), hasil [JSON](checks/employee-actions-result-010.json), screenshot [Gaji](employee-actions-gaji-menu.png) dan [Kasbon](employee-actions-kasbon-menu.png) memakai data fiktif.

Belum mencakup posting/pencairan/hapus nyata, seluruh form pegawai, suite repository, Safari/perangkat asli atau cetak slip. Tidak ada deployment; kedua server localhost dinyalakan kembali untuk review.


## Penerapan 0.11 — Gaji dan Kasbon Finance

18 Oktober 2026. Skill `frontend-design` dipakai mengikuti token dan pola aplikasi existing. Mobbin diperiksa melalui MCP: [ringkasan pembayaran Fresha](https://mobbin.com/screens/8cb51590-8635-4e42-9f3d-b4450fadad45) untuk pembacaan komponen/total per pegawai, serta [review payroll Deel](https://mobbin.com/screens/b40eabc2-7df4-4356-8ed6-e60687aedaca) untuk pemisahan rincian review dari daftar. Adaptasi terbatas pada hierarki informasi; warna, tipografi, komponen serta izin tetap Bee. Screenshot referensi tidak dipakai sebagai bukti perilaku atau izin backend. Tidak ada dependency baru, perubahan backend, skema atau deployment.

`GajiListView.vue` dan `PinjamanListView.vue` tetap controller API masing-masing. `GajiFormDialog.vue`, `KasbonFormDialog.vue`, `GajiSlipPreview.vue`, `EmployeeActionDialog.vue` dan `payroll.ts` memisahkan form/rincian/konfirmasi dan aturan presentasi. CSS kedua modul dikonsolidasikan ke `employee-finance.css`; `employee-actions.css` dari pass kolom tindakan sebelumnya sudah digantikan. Bukti `employee-actions-*-010` adalah riwayat versi sebelumnya; runner terkini adalah `checks/payroll.js`. Daftar memakai seluruh halaman API, pencarian/filter status, pagination 15 baris, tabel pada ruang lebar dan kartu pada container sempit. Tidak menambah grafik atau kartu metrik dekoratif.

Form Gaji mencakup seluruh komponen API: gaji pokok, tunjangan jabatan/pengabdian/asuransi, uang makan, transport, bonus, THR, hari hadir, dan potongan asuransi. Potongan kasbon baca saja dan tidak dikirim sebagai angka manual: backend menghitung ulang setiap create/update. Perkiraan mengikuti service existing, yaitu minimum saldo/angsuran; angsuran nol memakai seluruh sisa. **Service existing juga menghitung pengajuan yang belum memiliki jurnal pencairan**; form menjelaskan batas ini, tanpa mengubah aturan server. Kegagalan data pendukung tidak diperlakukan sebagai potongan nol. Simpan membuka rincian respons server, sehingga pengguna dapat memeriksa hasil aktual, bukan hanya perkiraan.

Form Kasbon memakai tanggal kalender lokal, jumlah/angsuran desimal, tenor eksplisit dan nama pegawai yang dipertahankan saat edit. Angsuran nol tetap didukung dan dijelaskan akibatnya; tidak membagi pinjaman otomatis berdasarkan tenor. UI meminta jumlah pinjaman positif. Nilai kosong/invalid/unsafe tidak dikirim; backend tetap memvalidasi kontrak. Form existing dapat menampilkan pegawai nonaktif yang sudah terhubung, sedangkan pengajuan/slip baru menawarkan pegawai aktif.

Penyimpanan, pemeriksaan rincian, posting, pencairan dan hapus mengunci kontrol terkait dan navigasi selama request berjalan. Error penolakan mempertahankan input. Respons ambigu create/update tidak otomatis dikirim ulang: form mengarahkan pemeriksaan daftar. Posting/pencairan/hapus memeriksa rincian terbaru sebelum konfirmasi. Setelah respons ambigu, tombol konfirmasi terkunci sampai GET status terbaru selesai. Jika jurnal sudah tertaut, konfirmasi ditutup dan tindakan tidak dikirim kedua kali; data potongan kasbon juga dimuat ulang setelah posting terkonfirmasi. Ini bukan jaminan exactly-once atau perlindungan race backend.

Label **Jurnal dibuat/Jurnal pencairan dibuat** hanya menyatakan ID jurnal tertaut, bukan jurnal POSTED atau bukti uang sudah diterima pegawai. Endpoint sumber membuat jurnal Draf; alur persetujuan dan buku besar tetap pada Jurnal. UI tidak memperluas route Finance atau mengganti aturan penghapusan/pencatatan. Rincian kasbon menampilkan jumlah, tenor, angsuran, sudah dikurangkan dan sisa; kontrak tidak menyediakan riwayat cicilan per transaksi.

Slip gaji merinci komponen tersimpan, bruto, potongan dan netto. Nilai kosong tetap belum diketahui; string desimal besar diformat dengan integer presisi tanpa memaksa konversi float. Form membatasi nominal/sum pada sen yang aman direpresentasikan JavaScript. Footer form mempertahankan total saat konten digulir. Cetak memakai class body/mask khusus, sehingga shell, halaman latar dan tombol dialog tidak ikut tercetak; class dibersihkan setelah print/close/unmount.

### Bukti UI dan kompatibilitas 0.11

- **17 tes terarah / 4 file lulus**, termasuk 9 tes baru pada tiga file kepegawaian dan 8 regresi overlay existing. Mencakup pagination API, null/nol/unsafe/desimal besar, minimum sisa/angsuran nol, pengajuan belum dicairkan, komponen gaji lengkap, potongan server, tanggal lokal/manual invalid, pegawai nonaktif existing, pending/recovery dan penguncian hasil ambigu. Seluruh suite repository tidak dijalankan.
- Build/typecheck lulus. Warning chunk existing lebih dari 500 kB masih ada.
- Playwright MCP terisolasi memakai **28 record fixture lintas halaman**. `checks/payroll.js` memeriksa pencarian halaman terakhir, create/edit/delete kedua modul, validasi sebelum request, cents/tanggal lokal, input setelah penolakan, pending Escape/navigasi, respons server, status terbaru sebelum tindakan, respons hilang setelah commit fixture dan pembacaan status tanpa replay, serta kegagalan pendukung/daftar dan retry. Semua API diintersep; seluruh mutasi hanya pada memori fixture. Nol page error.
- **40 pasangan layar/ukuran**: daftar, form, slip/rincian dan konfirmasi kedua modul pada 1440, 1024, 768, 390 dan 320 px. Tidak ada overflow halaman/dialog; kolom terakhir dapat digulir di atas footer. Print diuji terpisah pada A4 794×1123 dengan fungsi print di-stub: aplikasi latar dan footer tersembunyi, slip terlihat, lebar sesuai kertas. Ini bukan uji printer fisik. Hasil [payroll-result-011.json](checks/payroll-result-011.json).
- Screenshot fiktif diperiksa visual: `payroll-salary-desktop-011.png`, `payroll-salary-form-*-011.png`, `payroll-salary-slip-*-011.png`, `payroll-salary-print-011.png`, serta `payroll-loan-list/form/detail/disbursement-*-011.png`. Tidak menyimpan screenshot data pegawai nyata.
- Pembacaan bisnis **localhost nyata** dengan akun Finance: lima GET (daftar/rincian Gaji, daftar/rincian Kasbon, dan Pegawai) merespons **200**. Aplikasi berhasil memuat 33 gaji dan lima kasbon; halaman Gaji menampilkan 15 record pertama dari seluruh hasil, Kasbon lima record. Request bisnis selain GET diblokir; hanya autentikasi token lokal yang dilakukan lewat POST. Token dibersihkan setelah pemeriksaan. Hasil [payroll-local-result-011.json](checks/payroll-local-result-011.json).

Belum diperiksa: create/update/posting/pencairan/hapus dengan database nyata, transaksi bersamaan dan idempotensi backend, seluruh suite, Safari/iPad, pembaca layar, zoom native 200%, keyboard perangkat sekolah dan printer fisik. UI tidak membuat riwayat cicilan yang belum tersedia pada API. Data pegawai dan Absensi pegawai belum direvamp pada paket ini. Tidak ada transaksi nyata atau web online yang diubah. Berikutnya Data pegawai, Absensi pegawai, lalu administrasi/aset sesuai inventaris.


## Penerapan 0.12 — Data pegawai dan Absensi pegawai

18 Oktober 2026. `frontend-design` dipakai untuk dua alur operasional ini, mengikuti token Bee, hierarki, menu dan Phosphor Regular lokal yang sudah ditetapkan. Tidak ada dependency, route, skema, aturan gaji atau backend baru. Kedua view tetap controller API domain; `PegawaiFormDialog.vue` memiliki validasi dan penyimpanan profil, `StaffAttendanceGrid.vue` mengelola pilihan status, `staff.ts` menyimpan transformasi presentasi kecil, dan `staff.css` hanya mengatur layout dua layar ini.

Data pegawai memuat seluruh halaman API, lalu menyediakan pencarian lintas hasil, filter status, halaman berisi 15 pegawai, tabel dan kartu responsif. Profil menampilkan NIP, kontak, masa kerja, status aktif dan status akun tertaut. Hubungan akun hanya informasi; endpoint profil tidak menyediakan nama akun untuk TU dan tidak mengubah relasi akun saat simpan. Tanggal kerja memakai kalender lokal dan dapat dikosongkan. Form memvalidasi nama serta urutan tanggal, mempertahankan isian setelah penolakan, dan meminta pemeriksaan daftar setelah respons simpan ambigu. Menu penghapusan memeriksa detail terbaru; penonaktifan dijelaskan sebagai pilihan ketika riwayat perlu mudah ditemukan.

Absensi pegawai memisahkan pemilihan tanggal dari daftar yang sedang disimpan. Seluruh halaman catatan pada tanggal terpilih dimuat, termasuk catatan pegawai yang kini nonaktif. Pegawai aktif tanpa catatan disiapkan sebagai Hadir, tetapi diberi label *belum disimpan*; pilihan `Tanpa catatan` menghapus catatan tersimpan melalui kontrak bulk existing. Catatan lama dengan beberapa flag tidak diratakan diam-diam: nilainya tampil sampai pengguna memilih satu status baru. Perubahan yang belum disimpan menjaga navigasi/tanggal; pencarian hanya mengubah tampilan, sedangkan Simpan mencakup semua pilihan. Bulk backend tidak atomik. Karena itu respons yang tidak pasti mengunci pengiriman ulang sampai GET seluruh catatan selesai; hasil yang telah tersimpan disandingkan dengan pilihan lokal. Rekap bulanan menampilkan jumlah catatan sesuai endpoint, tanpa menganggapnya persentase hari kerja atau menghitung ulang slip gaji.

### Bukti UI dan kompatibilitas 0.12

- **6 tes terarah / 2 file lulus** untuk pagination absensi per tanggal, detail pegawai, flag campuran lama, pilihan awal dan penghapusan catatan; build/typecheck lulus. Warning chunk existing masih muncul.
- Playwright MCP terisolasi memakai 28 profil fixture lintas tiga halaman, kemudian satu profil baru. Create/update profil menjaga tanggal lokal dan tidak mengirim field akun. Kegagalan direktori/absensi serta retry, penjagaan navigasi saat belum disimpan, respons bulk `503` setelah commit fixture, pemeriksaan GET tanpa POST kedua, dan rekap dua pegawai terverifikasi. **20 pasangan layar/ukuran** pada 1440, 1024, 768, 390, 320 px tidak menunjukkan overflow halaman/dialog; nol page error. Semua operasi bisnis diarahkan ke fixture. Runner [staff.js](checks/staff.js), hasil [JSON](checks/staff-result-012.json), screenshot `staff-*-012.png` memakai nama fiktif.
- API localhost nyata dibaca dengan akun TU: Pegawai 200 (36 record), Absensi pegawai 200 (53 record), rekap Oktober 2026 200 (0 record). UI lokal menampilkan 15 pegawai halaman pertama dan 36 baris absensi tanggal hari ini, tanpa alert. Token browser dibersihkan. Hasil [staff-local-result-012.json](checks/staff-local-result-012.json). Rekap berisi data diperiksa di fixture, sebab periode lokal yang dipilih tidak punya catatan.

Belum diperiksa: create/update/delete profil atau simpan absensi pada database nyata, seluruh suite, transaksi bulk yang gagal sebagian pada server nyata, Safari/iPad, pembaca layar, zoom native 200%, dan perangkat sekolah. Backend bulk belum menyediakan transaksi menyeluruh atau idempotency key; UI meminta verifikasi sebelum retry namun tidak menjanjikan exactly-once saat ada penulis bersamaan. Tidak ada deployment. Berikutnya Aset serta administrasi lain yang masih tersisa pada inventaris.


## Penerapan 0.13 — Aset tetap Finance

18 Oktober 2026. `frontend-design` digunakan untuk menata halaman sebagai register aset operasional, mengikuti token Bee dan pola daftar/detail/form Finance yang sudah ada. Menu Aset dipindah dari kelompok Pegawai ke Keuangan; route `/aset`, izin Finance, API, skema, dan service penyusutan tidak berubah.

`AsetListView.vue` memuat seluruh halaman API, menampilkan nama/akun, tanggal dan harga perolehan, akumulasi, penyusutan bulanan, dan masa manfaat. Pencarian mencakup semua hasil yang dimuat; tabel 15 baris beralih menjadi kartu pada ruang sempit. Satu tombol **Periksa** membuka rincian terbaru sebelum tindakan. `AsetFormDialog.vue` memisahkan data perolehan dari akun jurnal, memakai tanggal lokal, batas nominal yang aman, label persisten, dan pesan kegagalan yang mempertahankan input. Akun aktif ditawarkan; kode akun existing yang tidak ada pada daftar tetap ditampilkan agar pengguna dapat memeriksanya.

Konfirmasi penyusutan menyebut nominal dari respons server dan menjelaskan bahwa sistem menambah akumulasi serta membuat jurnal **Draf**. Tidak ada perhitungan ulang penyusutan di browser. Respons tindakan ambigu tidak otomatis dikirim ulang; jika akumulasi berubah setelah pembacaan terbaru, pengguna diarahkan memeriksa jurnal. Perbedaan akumulasi saja tidak membuktikan jurnal spesifik mana yang terbentuk. Hapus tetap ditawarkan hanya bila akumulasi nol, mengikuti perilaku layar sebelumnya.

Build/typecheck lokal lulus; warning ukuran chunk existing tetap ada. Preview Playwright terisolasi memakai 28 aset dan tiga akun fiktif, dengan semua request bisnis selain GET diblokir. Daftar, rincian, form, dan konfirmasi dilihat pada desktop 1440 px dan mobile 390 px; keduanya tidak menunjukkan overflow halaman/dialog. Bukti gambar: `asset-register-*-013.png`, `asset-detail-*-013.png`, `asset-form-*-013.png`, dan `asset-depreciation-mobile-013.png`. Ini adalah inspeksi visual, bukan uji transaksi atau izin akun sekolah nyata.

Belum diperiksa: penyimpanan/penghapusan/penyusutan dengan database nyata, respons gagal sebagian atau penulis bersamaan, Safari/iPad, pembaca layar, zoom 200%, dan seluruh suite. Tidak ada deployment.


## Penerapan 0.14 — Kelompok belajar Admin/TU

18 Oktober 2026. Halaman `/kelompok` memakai pola direktori operasional Bee, Phosphor lokal, dan token existing. Tiga tugas dipisah menjadi tab Kelompok, Jenjang, dan Pindah siswa. Ringkasan menyatakan jumlah jenjang, kelompok, dan siswa **aktif** dalam kelompok; kegagalan muat ditampilkan sebagai belum diketahui, bukan nol. Daftar jenjang dan kelompok membaca seluruh halaman API, dengan pencarian/filter, pagination, tabel desktop dan kartu mobile. Aksi per baris mengarahkan ke Ubah, Pindahkan siswa, atau Lihat kelompok yang relevan. Hapus kelompok hanya ditawarkan ketika tidak ada siswa aktif; backend tetap memeriksa lagi. Konfirmasi menjelaskan dampak pada siswa nonaktif atau penanda jenjang pendaftaran.

Form jenjang/kelompok memakai label terhubung, batas panjang sesuai model, validasi isian, dan mempertahankan input saat server menolak. Respons simpan yang tidak pasti meminta pemeriksaan daftar sebelum pengiriman ulang. Mengubah jenjang kelompok yang berisi siswa aktif memunculkan penjelasan dampak. Alur perpindahan memilih kelompok asal, siswa aktif, dan tujuan yang berbeda; daftar asal diambil lagi sebelum dialog review dan sebelum POST. Dialog menyebut jumlah, asal, tujuan, dan nama siswa. Teks layar menyatakan tagihan yang sudah dibuat dan tarif SPP tidak otomatis berubah. Respons jumlah pindah yang berbeda dari pilihan awal meminta pemeriksaan daftar siswa.

Build/typecheck lokal lulus; browser Playwright terisolasi membuka fixture fiktif pada desktop 1440 px dan mobile 390 px. Direktori, formulir, serta dialog review dibaca secara visual tanpa overflow horizontal; seluruh request bisnis selain GET diblokir. Tidak ada tes otomatis atau mutasi database sekolah pada pass ini. Batas backend existing: endpoint pindah siswa masih menerima ID tanpa mengikatnya ke kelompok asal; pemeriksaan UI memperkecil risiko pilihan usang tetapi tidak menjamin transaksi serentak. Safari/iPad, pembaca layar, zoom 200%, dan operasi tulis nyata belum diperiksa. Tidak ada deployment.


## Penerapan 0.15 — Tunggakan tagihan Finance/Kepsek

18 Oktober 2026. Layar `/tunggakan-tagihan` tetap baca-saja untuk Finance/Kepsek. Ringkasan memisahkan **Sisa yang diketahui** dari jumlah tagihan **Perlu dicocokkan**. Record dengan `sisa_tagihan = null` tidak dikonversi menjadi nol atau dijumlahkan; daftar tetap menampilkannya sebagai “Belum diketahui”. Bilangan desimal API dijumlahkan sebagai sen integer agar total tampilan tidak kehilangan pecahan. Tagihan dengan sisa nol dan tanpa rekonsiliasi tidak ikut daftar perhatian.

Pencarian meliputi nama siswa, periode dan status pada seluruh halaman API. Jenis perhatian dan periode adalah filter tersendiri; hasil, ringkasan dan pagination memakai cakupan filter yang sama. Layar membedakan memuat, gagal dengan tombol muat ulang, tidak ada tunggakan, dan hasil filter kosong. Tabel desktop serta kartu mobile memakai label/status yang sama; tidak ada kontrol pembayaran untuk role baca-saja. Penjelasan menyatakan angka yang diketahui belum mencakup record rekonsiliasi.

Build/typecheck lokal lulus. Playwright MCP terisolasi menampilkan lima tagihan fiktif, termasuk dua sisa belum diketahui dan pecahan rupiah, pada 1440 dan 390 px tanpa overflow horizontal. Semua request bisnis selain GET diblokir. Tidak ada tes otomatis, operasi tulis database nyata, atau deployment. Safari/iPad, pembaca layar, zoom 200%, dan rekonsiliasi historis pada database sekolah belum diperiksa.


## Penerapan 0.16 — Daftar akun Finance/Kepsek

18 Oktober 2026. `frontend-design` dipakai untuk menata `/coa` sebagai struktur kerja akuntansi, mengikuti token Bee dan Phosphor Regular lokal. Tab Akun, Subgolongan, dan Golongan memperlihatkan jumlah record serta hubungan induk; tombol jumlah pada dua tingkat induk membuka daftar turunan yang sudah terfilter. Finance tetap memiliki aksi tulis, sedangkan Kepala Sekolah membaca tanpa kontrol ubah/hapus. API, route, izin backend, dan skema tidak berubah.

Pencarian dan filter bekerja pada seluruh halaman yang telah dimuat, lalu daftar dipaginasi 15 record. Layar membedakan loading, kegagalan/retry, daftar kosong, dan hasil filter kosong. Tabel desktop berubah menjadi kartu pada ruang sempit; kode, nama, pengelompokan, status, posisi normal, saldo awal, tanggal acuan, dan aksi tetap terbaca. Form memakai label persisten, batas panjang sesuai model, pilihan induk eksplisit, serta validasi tanggal ketika saldo bukan nol. Nilai saldo awal negatif tetap dapat dimasukkan. Akun yang sudah memiliki saldo awal ditahan dari aksi hapus di UI; backend tetap menjadi pemeriksa akhir hubungan jurnal dan data turunan.

Ringkasan debit, kredit, dan selisih menghitung string desimal API sebagai sen integer. Cakupannya seluruh akun tanpa memisahkan tanggal acuan, sehingga layar menjelaskan bahwa saldo per periode tetap harus diperiksa di laporan. Nominal tak terbaca tidak dijadikan nol; ringkasan ditampilkan belum diketahui. Kegagalan memuat salah satu tingkat mengosongkan data tampilan agar jumlah lama tidak tampak sebagai data terkini.

Build/typecheck lokal lulus. Playwright MCP terisolasi menampilkan 19 akun, dua subgolongan dan dua golongan fiktif pada 1440, 390, dan 320 px; tidak ada overflow horizontal atau page error. Form mobile juga diperiksa dan konten dapat digulir di atas footer. Seluruh request bisnis selain GET diblokir fixture. Tidak ada tes otomatis, operasi tulis database nyata, atau deployment. Safari/iPad, pembaca layar, zoom 200%, dan saldo awal per tanggal pada data sekolah belum diperiksa.


## Penerapan 0.17 — Anggaran dan Periode Finance/Kepsek

18 Oktober 2026. Kedua layar memakai struktur informasi dan token Bee yang sama dengan modul keuangan lainnya. `api.ts` kini menyediakan pembacaan seluruh halaman untuk daftar Anggaran dan Periode; metode `list` existing tetap ada untuk caller Kegiatan. Anggaran menyediakan pencarian lintas semua record termuat, filter tahun, jumlah hasil, loading, retry, dan keadaan kosong. Form memberi label persisten, validasi nominal/tahun, serta menjaga isian saat server menolak. Finance tetap membuat/mengubah/menghapus; Kepsek membaca. Pilihan akun yang gagal dimuat menahan create/edit, tanpa menyembunyikan daftar anggaran.

Copy Anggaran kini mengikuti sumber laporan aktual: view `v_realisasi_anggaran` menjumlah seluruh baris pagu per akun pada **tahun kalender**, termasuk baris bulanan dan tahunan. Kolom bulan serta `carry_over` belum diterapkan sebagai pembatas atau pemindahan pagu dalam view tersebut. UI menyatakannya secara eksplisit; tidak ada perhitungan laporan atau skema baru. Tabel dapat digulir horizontal pada ruang sempit agar kolom aksi tetap dapat dicapai.

Periode menampilkan jumlah Terbuka/Tertutup, rentang tanggal lokal, dan aksi sesuai role. Form membuat tanggal `YYYY-MM-DD` dari komponen kalender lokal, bukan `toISOString()` yang dapat bergeser hari. Konfirmasi Kepala Sekolah menyebut jurnal penutup yang langsung diposting dan dampak irreversibel; sebelum POST, UI membaca ulang status periode. Respons yang tidak pasti meminta pemeriksaan status dan jurnal sebelum retry. Backend tetap memegang keputusan akhir dan aturan tutup buku.

Build/typecheck lokal lulus. Playwright MCP terisolasi memuat 21 anggaran dan 13 periode fiktif lintas halaman pada 1440, 390, dan 320 px, serta form mobile; tidak ada overflow halaman atau page error. Seluruh request bisnis selain GET diblokir fixture. Tidak ada tes otomatis, operasi tulis database nyata, atau deployment. Safari/iPad, pembaca layar, zoom 200%, dan penutupan periode pada data sekolah belum diperiksa.


## Penerapan 0.18 — Log audit Finance/Kepsek

18 Oktober 2026. `/audit-log` tetap baca-saja dengan filter serta pagination milik server. Daftar memprioritaskan pelaku, jenis data, tindakan dan waktu; ID record serta tombol rincian tetap tersedia. Filter memiliki label terlihat. Di ponsel filter dibuka sesuai kebutuhan supaya riwayat tampak lebih awal; tabel memberi petunjuk geser. Perbandingan nilai sebelum/sesudah pada dialog berubah menjadi baris bertanda di layar sempit, sehingga nilai baru tidak tersembunyi di luar bidang pandang. Nilai uang dan field COA/anggaran yang lazim diberi label Indonesia; record mentah tidak dikirim ke ringkasan.

Respons lama tidak menimpa filter terbaru. Rentang tanggal terbalik ditolak sebelum request, dan kegagalan API menampilkan pesan serta retry, bukan tabel lama. Pilihan pengguna dibangun dari endpoint label yang sudah ada, bukan hanya 20 entri halaman aktif. Seluruh API, izin, dan sumber data tetap existing; tidak ada pengiriman audit atau tindakan tulis baru.

Build/typecheck lokal lulus. Playwright MCP terisolasi menampilkan 25 record fiktif pada 1440, 390, dan 320 px; daftar, filter mobile, dan dialog sebelum/sesudah diperiksa tanpa overflow halaman atau page error. Semua request bisnis selain GET diblokir fixture. Tidak ada tes otomatis, pembacaan audit database nyata, deployment, Safari/iPad, pembaca layar, atau zoom 200% pada pass ini.
