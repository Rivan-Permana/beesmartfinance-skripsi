# Standar UI/UX BeeSmart — preview dan studi arah visual

15 Oktober 2026. Standar untuk revamp yang sedang disusun; belum diterapkan ke seluruh aplikasi produksi.

## Batas cakupan yang jujur

Rencana revamp tetap mencakup 23 view. Preview sekarang mewakili empat peran melalui tujuh layar: dashboard, siswa, tagihan, tunggakan, jurnal, kegiatan, dan rekap siswa; dua alias pemasukan/pengeluaran menggunakan layar jurnal yang sama. Finance dan Kepsek mempunyai variasi dashboard. Ini belum berarti seluruh 23 view selesai atau terhubung ke backend.

Entry preview terpisah di `frontend/dashboard-preview.html` dan `frontend/src/design-preview/main.ts`. Entry produksi `src/main.ts`, router, auth, API, dan model data tidak diubah. Pilihan peran pada toolbar adalah alat review dengan fixture, bukan fitur untuk mengganti izin akun. Route/menu preview berasal dari `navForRoles` yang ada.

## Arsitektur informasi

| Peran | Home existing yang diikuti | Urutan kelompok navigasi preview | Fokus |
|---|---|---|---|
| Finance | `/dashboard` | Ringkasan; Transaksi; Perencanaan dan laporan; Pegawai dan aset; Pengaturan keuangan | Membaca kondisi kas, memeriksa draft, menindaklanjuti pencatatan |
| SchoolPrincipal | `/dashboard` | Ringkasan; Transaksi; Kegiatan; Perencanaan dan laporan; Pengaturan keuangan | Pengawasan, persetujuan yang berlaku, anggaran/kegiatan |
| Administration | `/siswa` | Siswa; Tagihan dan pendaftaran; Kehadiran dan layanan; Pegawai | Mengelola siswa, pembayaran dan layanan |
| TeacherInCharge | `/kegiatan` | Kegiatan; Kehadiran dan layanan | Realisasi kegiatan dan rekap baca-saja |

Kelompok adalah metadata presentasi, bukan role baru atau perubahan izin. Semua destination tetap memakai path/query existing. Item yang belum mempunyai layar contoh tidak menjadi tautan palsu; tersedia keterangan bahwa preview-nya belum dibuat. Navigasi, filter, tombol aksi, dan alat review dipisahkan secara visual.

Tidak ada dashboard baru untuk Admin/Guru pada tahap ini. Usulan baru semacam itu membutuhkan penetapan kebutuhan data dan hak akses; prioritas setara dicapai dengan memoles pekerjaan mereka pada home yang memang ada.

## Grafik berdasarkan pertanyaan

| Pertanyaan | Visual | Sumber aplikasi untuk integrasi berikutnya | Scope dan batas |
|---|---|---|---|
| Bagaimana kas masuk dan keluar berubah? | Garis dua seri | `dashboardApi.prediksiKas`, field arus kas historis | Per bulan; pisahkan historis dari proyeksi. Cash flow berbeda dari pendapatan akrual |
| Berapa pendapatan dan beban tiap bulan? | Batang berkelompok | `dashboardApi.labaRugiBulanan` | Bulan/tahun jelas; baseline nol; tidak menyebut beban sebagai kas keluar |
| Dari mana pendapatan atau beban berasal? | Donut dengan daftar nominal dan tabel | `laporanApi.labaRugi` | Kategori dijelaskan; nilai kategori menjumlah ke total periode; bukan jumlah transaksi |
| Berapa pagu dan realisasi per akun? | Batang horizontal berkelompok | `laporanApi.realisasiAnggaran` | Tahun anggaran disebut eksplisit; jangan terkesan ikut filter bulan bila endpoint tahunan |
| Bagaimana tren kehadiran? | Batang bulanan | `DashboardOperasional.absensi_sparkline` | Jumlah catatan hadir, bukan siswa unik atau persentase tanpa denominator |
| Bagaimana realisasi masing-masing kegiatan? | Batang horizontal pagu/realisasi | `kegiatanApi.list` dan hak akses yang berlaku | Scope kegiatan yang diizinkan, bukan seluruh anggaran sekolah |

Konteks grafik dibagi berdasarkan pekerjaan peran. Finance menampilkan arus kas/laba rugi dalam satu panel yang dapat diganti serta komposisi pendapatan/beban. Kepsek menampilkan pagu/realisasi tahunan dan progres per kegiatan. Guru melihat perbandingan pagu/realisasi setelah daftar kegiatan. Kehadiran hanya ada di rekap siswa untuk TU/guru; tidak ada di dashboard Finance maupun Kepsek. Setiap chart memiliki judul, satuan/cakupan, deskripsi, tooltip, dan tabel angka yang dapat dibuka. Animasi chart dimatikan agar fokus pada pembacaan dan reduced motion terjaga.

Semua fixture diberi label. Data contoh kas sengaja terpisah dari pendapatan/beban. Jangan mengisi widget menggunakan data yang kebetulan tersedia tetapi mempunyai arti berbeda. Jangan menambah gauge, heatmap, atau sankey tanpa pertanyaan/data yang cocok.

## Ikon Phosphor

- Gunakan [Phosphor Icons](https://phosphoricons.com/) sesuai arahan pengguna; bobot regular, ukuran default 20–21 px, icon kontrol 18–20 px.
- Preview memakai subset 38 SVG resmi dari [repository Phosphor Core](https://github.com/phosphor-icons/core), commit `2b75f3ad12b420c9504ef05df8d2564a28f8500e`. Paths dipertahankan dalam sprite lokal. Source dan lisensi MIT ada pada `frontend/src/design-preview/icons/`.
- Semua ikon preview dirender melalui `PhosphorIcon.vue`, mewarisi `currentColor`, tanpa font ikon atau permintaan CDN runtime. Tidak mencampur gambar SVG buatan tangan dengan Phosphor.
- Ikon dekoratif `aria-hidden`; kontrol ikon memiliki nama yang menjelaskan aksi. Logo lebah existing tetap aset brand, bukan ikon navigasi.
- Migrasi PrimeIcons pada aplikasi utama dilakukan bersama rollout, termasuk pemetaan menu, tombol, empty/error state, dan slot ikon komponen yang terlihat. Jangan menghapus dependency PrimeIcons sebelum seluruh caller dimigrasi.

## Standar data, nama, dan kode

| Kebutuhan | Sumber standar | Aturan |
|---|---|---|
| Role, izin menu, home | `core/navigation.ts`, router/permission existing | Gunakan identifier `Finance`, `SchoolPrincipal`, `Administration`, `TeacherInCharge`; label manusia terpisah |
| Label, ikon, kelompok presentasi | `design-preview/fixtures.ts` → `screenInfo`, `navigationGroupOrder` | Metadata terpusat pada preview; promosikan bersama implementasi setelah arah disepakati |
| Nominal | `core/format.ts` → `formatRp` | Jangan menduplikasi formatter; null yang berarti belum pasti harus ditangani sebelum formatter |
| Data chart | Satu fixture per domain, lalu adapter Chart.js | Dataset yang sama dipakai chart, tooltip, legenda, dan tabel; jangan mengetik angka kedua kali pada ilustrasi |
| Panel chart | `design-preview/PreviewChart.vue` | Satu pola heading, deskripsi, scope, tooltip dan tabel angka; reuse PrimeVue Chart/Chart.js yang sudah terpasang |
| Tokens | `design-preview/preview.css` | Surface, teks, border, brand, status, radius, spacing didefinisikan sekali; belum mengganti token produksi |
| Status | API enum dan boolean existing, dengan label presentasi | Identitas status bisnis tetap; status siswa, pembayaran dan jurnal tidak disatukan menjadi satu enum universal |
| Mockup dan aplikasi nyata | Entry yang terpisah | Tidak memasukkan selector role/fixture/state simulator ke shell produksi |

Pemetaan label yang disarankan: `DRAFT` → “Draf”; `PENDING` → “Menunggu persetujuan”; `POSTED` → “Tercatat di buku besar”. `BELUM` → “Belum bayar”; `SEBAGIAN` → “Sebagian dibayar”; `LUNAS` → “Lunas”. Boolean `perlu_rekonsiliasi` ditampilkan sebagai “Perlu dicocokkan” dan tidak diterjemahkan menjadi lunas/nol. Penerapan harus tetap mengikuti data dan predikat tindakan existing.

Jangan membuat wrapper untuk semua hal. Komponen bersama dibuat ketika pola benar-benar berulang. Formatter, permission, validasi, dan caller existing lebih diutamakan daripada membangun ulang arsitektur.

## Copy dan interaksi

- Gunakan Bahasa Indonesia, sentence case, dan satu istilah konsisten: “Staf Tata Usaha”, “Catat pembayaran”, “Catat penerimaan”, “Finalisasi pendaftaran”, “Setujui”, “Ekspor CSV”. Label tidak menyamakan aksi bisnis yang berbeda.
- Draf dan menunggu persetujuan memiliki pesan berbeda. Finance tidak melihat semua draf sebagai antrean approval Kepsek.
- Nilai belum diketahui ditulis “Belum diketahui” atau “Perlu dicocokkan”, bukan Rp0. Kosong, loading, error, dan hasil filter kosong memiliki state terpisah.
- Field memiliki label tetap; placeholder hanya contoh. Tombol menyebut aksi, hasil sukses menyebut apa yang disimpan, pesan gagal memberi langkah pemulihan dan menjaga input.
- Filter pencarian/status pada list contoh benar-benar menyaring fixture; jumlah hasil menyebut total fixture, bukan seluruh siswa sekolah. Filter periode di header saat ini merupakan label statis, tidak berpura-pura memfilter chart.
- Popup pembayaran adalah contoh form tanpa penyimpanan; tanggal, bukti, Kas/Bank dan nominal mempunyai label. Simpan dinonaktifkan dan diberi keterangan bahwa ini preview. Alokasi/idempotensi actual belum diintegrasikan.
- Drawer dan Dialog memakai PrimeVue existing untuk focus/Escape; slot `closeicon` memakai Phosphor dengan tombol native PrimeVue agar referensi fokus tetap bekerja. Drawer mengembalikan fokus ke tombol pemicu setelah ditutup. Transaksi destruktif dan konfirmasi actual belum dibuat dalam prototype.
- Desktop memakai sidebar; mobile memakai satu drawer navigasi. Tabel lebar scroll lokal, angka tidak dipotong agar muat. Keyboard, kontras dan printer fisik tetap membutuhkan verifikasi menyeluruh pada implementasi.

## Sumber baru dan cara memakainya

| Sumber | Yang benar-benar dipelajari | Pemakaian BeeSmart |
|---|---|---|
| [Impeccable](https://impeccable.style/) | Situs menjelaskan panduan shaping/refinement/design system; skill terpasang serta panduan Operate/craft dibaca | Tugas operasional, hierarki, konsistensi kontrol/copy, state dan density mengarahkan desain |
| [SaaSpo](https://saaspo.com/) | Halaman resmi yang terindeks menyebut koleksi SaaS landing page dan section; direct fetch 403 | Sumber komposisi visual jika perlu; bukan bukti workflow dashboard. Tidak menyalin hero pemasaran ke ruang kerja |
| [Refero Styles](https://styles.refero.design/) | Library arah visual dan DESIGN.md dengan warna, typography, spacing, components | Rujukan menyusun token/standar; tidak menimpa identitas Lebah Madu dengan style pihak lain |
| [mkdir](https://mkdir.directory/) | Halaman dibuka melalui browser setelah fetch gagal; berisi direktori galeri/award/landing/section | Titik penemuan bila referensi kurang; ranking tidak dianggap bukti usability. Tidak membuka seluruh direktori |

Pembagian tersebut sudah ditambahkan pada `~/.codex/AGENTS.md` sebagai aturan global; detail BeeSmart tetap berada di dokumen proyek ini.

Referensi chart yang dibaca pada Mobbin: [Monarch](https://mobbin.com/screens/ad1708a5-829c-41b4-8aa1-621655218be9) untuk perbandingan tren dan kategori, [Quicken](https://mobbin.com/screens/946dd3b8-4164-447e-b55b-3083f45d841f) untuk komposisi dengan nominal, dan [Rocket Money](https://mobbin.com/screens/2c672084-8391-462c-b8d1-44fe11646973) untuk hubungan breakdown dengan daftar. Preview gambar benar-benar dilihat; tidak menyimpulkan perilaku aplikasi yang tidak terlihat.

## Bukti pengerjaan dan batas

- Preview Vue/PrimeVue menggunakan dependency proyek yang sudah terpasang. Tidak memasang package baru atau mengubah entry/route/backend produksi.
- Pemeriksaan TypeScript dan `npm run build` berhasil. Vite masih memperingatkan chunk aplikasi utama di atas 500 kB; build ini tidak membuktikan performa runtime atau kesiapan seluruh revamp.
- Tampilan Finance, Kepsek, Admin, dan Guru dibuka pada browser terisolasi. Screenshot desktop dan Finance mobile disimpan di folder artefak. Ini review visual, bukan pengujian end-to-end.
- Pemeriksaan copy Better Design pada teks viewport awal Finance lulus heuristik. Pemeriksaan awal yang menggabungkan copy beberapa layar menganggap terlalu banyak kata/aksi; hasil tersebut tidak diperlakukan sebagai audit seluruh dashboard. Label/header kemudian dipisahkan sesuai konteks.
- Self-check fixture mengecek jumlah breakdown dan kelengkapan metadata menu. Tidak menjalankan suite unit/E2E, tidak login ke sistem sekolah, dan tidak melakukan deployment.
- Seluruh 23 layar produksi, integrasi API, Safari/iPad, zoom/keyboard matrix, cetak, dan transaksi sebenarnya belum diverifikasi pada tahap preview ini.


## Revisi ketiga: fokus role dan polesan komposisi

15 Oktober 2026. Menindaklanjuti koreksi pengguna bahwa kehadiran tidak relevan di dashboard keuangan dan tampilan masih terasa template.

| Peran | Konten utama | Informasi yang sengaja tidak ditampilkan di home |
|---|---|---|
| Finance | Kas/bank, pendapatan/beban/surplus, arus kas atau laba rugi, jurnal draf, sisa tagihan terverifikasi, komposisi keuangan | Kehadiran, daftar kegiatan, antrean persetujuan Kepsek |
| SchoolPrincipal | Kondisi keuangan, antrean persetujuan, pagu/realisasi tahunan, pengawasan kegiatan | Jurnal draf sebagai antrean kerja, kehadiran siswa |
| Administration | Jumlah siswa sesuai fixture, status, pencarian siswa, akses tagihan | Saldo kas sekolah, laporan laba rugi, jurnal dan persetujuan |
| TeacherInCharge | Daftar kegiatan, pagu/realisasi kegiatan; rekap kehadiran terpisah | Keuangan sekolah, tagihan/pembayaran siswa, jurnal dan persetujuan |

Kesamaan KPI keuangan Finance/Kepsek disengaja karena keduanya membutuhkan data yang sama untuk tugas berbeda. Struktur home dan tindak lanjut berbeda. Semua tautan membawa role aktif; perpindahan role memuat ulang home peran dan membuang filter/state role sebelumnya. Ini adalah pemisahan presentasi fixture, bukan mekanisme otorisasi aplikasi.

Perubahan visual: angka ringkasan memakai satu baris dengan pemisah, tanpa empat kartu identik; analisis utama lebih lebar daripada antrean pekerjaan; grafik Finance tinggal dua pada satu waktu; tabel jurnal dekat analisis; persetujuan Kepsek lebih dulu daripada anggaran; daftar kegiatan guru lebih dulu daripada grafik. Copy dipangkas, petunjuk geser tabel tersedia pada mobile, ikon tetap Phosphor regular. Referensi Mobbin yang sudah didokumentasikan dipakai ulang untuk hierarki dan kepadatan; tidak menambah pencarian provider yang setara.

Jumlah draf, tagihan, dan kegiatan kini diturunkan dari fixture yang benar-benar ditampilkan. Sisa terverifikasi Rp1.300.000 menjumlah dua tagihan yang diketahui; satu tagihan bersisa null tetap ditandai belum diketahui. Persentase anggaran dihitung dari pagu/realisasi fixture. Tidak ada angka ringkasan 7 draf/12 tagihan yang tidak didukung baris contoh.

Verifikasi revisi ini:
- Typecheck dan build produksi lulus; entry preview tetap terpisah. Warning chunk produksi >500 kB masih ada.
- `check-role-preview.js` melalui Playwright MCP: empat pergantian role, isi yang tidak sesuai role absen, tautan mempertahankan role, enam permintaan layar di luar role kembali ke home. Pengujian di viewport 390 px juga tidak menemukan overflow halaman; tabel mempunyai scroll lokal.
- Desktop 1440 px ditinjau untuk empat role; mobile Finance 390 px ditinjau. Gambar `*-v3-*.png` ada di direktori ini.
- Toggle arus kas/laba rugi bekerja. State kosong/gagal/memuat menyembunyikan chart dan kembali menampilkan dua chart pada state normal.
- Fokus menu mobile masuk ke tombol tutup, Escape menutup dan fokus kembali. Dialog rincian juga menerima/mengembalikan fokus setelah transisi. Perbaikan mengganti slot seluruh tombol dengan slot ikon agar tidak memutus ref internal PrimeVue.
- Pemeriksaan ini hanya mencakup preview. Tidak menguji otorisasi endpoint, akun nyata, seluruh 23 layar, printer, atau backend.

Catatan integrasi: `KegiatanViewSet` saat diperiksa memiliki queryset semua kegiatan dengan filter PIC opsional, bukan pembatasan otomatis per pengguna. Jangan menamai daftar “kegiatan saya” atau mengklaim isolasi per PIC tanpa keputusan akses dan pemeriksaan backend. Izin existing tetap dipertahankan pada preview.

Langkah berikutnya: perluas pola ini ke form/rincian transaksi dan state per role, kemudian terapkan shell/tokens/komponen ke aplikasi utama sesuai gelombang rencana. Saat menghubungkan API, verifikasi permission endpoint dan scope data per pengguna; toolbar role/fixture tidak masuk produksi.


## Studi visual Finance v4 — 15 Oktober 2026

Pengguna belum puas dengan polesan v3 dan memilih gabungan karakter yang lebih kuat, ruang kerja terang, serta hierarki kerja yang lebih baik. Studi berikutnya dibatasi ke home Finance agar arah baru bisa dinilai langsung. Role lain tetap memakai komposisi v3; stylesheet `finance-direction.css` dibatasi oleh kelas pada home Finance. Ini belum menjadi keputusan visual final semua peran.

Perubahan: sidebar navy #282651, konten terang, aksen magenta untuk tindakan, saldo sebagai angka dominan, panel arus kas lebih terstruktur dengan angka Oktober dari fixture, daftar kerja berikon Phosphor, dan tabel draf yang lebih rapat. Desktop dua kolom, mobile satu alur: ringkasan, analisis, daftar kerja, jurnal, komposisi. Seluruh informasi tetap tersedia di mobile. Tombol Buka jurnal menuju daftar existing, tidak menyimulasikan penyimpanan.

Referensi Mobbin baru yang gambarnya benar-benar dibaca:
- [Mercury — overview](https://mobbin.com/screens/1409f3cf-aafe-4e2f-9045-b4bdb2c48484): pemisahan balance, pergerakan uang, dan transaksi; tidak menyalin fitur bank ke aplikasi sekolah.
- [Revolut Business — home](https://mobbin.com/screens/4685d9fc-3a0a-402c-bd67-620809b6376a): daftar transaksi padat dan navigasi kontras; tema gelap penuh tidak diadaptasi.
- [Xero — cash flow manager](https://mobbin.com/screens/1c9ccbcc-0900-4bd4-b86c-dd68aa8c96f6): pembeda kas masuk/keluar dan unit pada grafik; preview tetap historis, tidak mengadopsi proyeksi tanpa data.

Perbaikan detail: selector logo `.brand` sebelumnya bertabrakan dengan status `.status.brand`, membuat badge Pengeluaran mewarisi padding logo. Logo diganti menjadi `.school-brand` pada seluruh caller dan stylesheet; status bisnis tetap memakai class semantiknya.

Bukti: screenshot `finance-v4-desktop.png` (1440 px) dan `finance-v4-mobile.png` (390 px). Tidak ada overflow halaman di mobile, kedua chart tetap terlihat. Typecheck/build lulus; warning chunk produksi >500 kB masih ada. Tidak ada dependency, API, permission, deployment, atau data produksi yang diubah. Studi visual tidak berarti pemeriksaan keamanan akun nyata.


## Alur jurnal v5 — 15 Oktober 2026

Alur yang sekarang dapat dicoba: dashboard → baris draf tertentu → rincian akun → ubah/buat draf → simpan → periksa → konfirmasi pencatatan → hasil. Tautan baris dashboard membawa kode jurnal melalui `entry`; kode yang tidak cocok dengan daftar/peran diabaikan. Daftar juga tersedia lewat Pemasukan/Pengeluaran dan Semua jurnal.

Shell navy dan tokens studi v4 sekarang digunakan konsisten pada seluruh rute preview Finance dan Kepala Sekolah. Struktur konten dan akses role masing-masing tetap berbeda. Header jurnal tidak lagi mengulang judul di dalam panel dan tidak menampilkan label bulan statis; pemilih bulan benar-benar memfilter tanggal data. Pencarian mencakup bukti, keterangan, dan sumber. Status memiliki hitungan dalam cakupan jenis/bulan; hasil kosong memberi jalan reset. Desktop tabel, mobile daftar transaksi yang langsung menunjukkan nominal, status, tanggal, dan tombol periksa.

Implementasi preview:
- `JournalPreview.vue`: daftar, filter, Drawer rincian/form, konfirmasi, hasil, penjagaan perubahan yang belum disimpan, fokus keyboard.
- `journal-preview.ts`: fixture turunan dari data dashboard, subset akun dari CSV COA proyek, label status/sumber, validasi angka dan predikat tindakan demo. Tidak menjadi lapisan otorisasi produksi.
- `journal-preview.css`: satu pola daftar desktop/mobile serta panel rincian/form.
- PrimeVue Drawer dan InputNumber existing dipakai ulang. Ikon memakai sprite Phosphor existing. Tidak ada dependency baru.

Perilaku contoh mengikuti pola existing yang diperiksa pada `JurnalListView.vue`, `accounting/api.py`, `accounting/services.py` dan serializer:
- Finance membuat/mengubah draf manual. Draf otomatis hanya dibaca; koreksi diarahkan ke transaksi sumber.
- Pencatatan harian yang memenuhi syarat berbeda dari pengajuan jurnal khusus. Kepsek meninjau jurnal khusus yang menunggu persetujuan; tidak menyunting draf Finance.
- Setelah simulasi pencatatan, status contoh menjadi Tercatat; aksi edit/catat ulang hilang.
- Form memakai akun, tanggal, bukti, keterangan dan minimal dua baris debit/kredit. Total harus seimbang, positif, aman dalam rentang integer dan setiap baris hanya mempunyai salah satu debit/kredit positif. Nomor bukti duplikat ditolak.
- Batas demo: rupiah bulat, satu pengguna contoh per role. Integrasi wajib mengikuti kontrak desimal API, identitas `created_by` aktual, periode terbuka, rekonsiliasi, validasi sumber dan hak akses server.

Seluruh simulasi hanya di memori komponen, tanpa request API atau local/session storage. Memuat ulang/berpindah halaman mengembalikan fixture. Status di hasil selalu menjelaskan bahwa transaksi sekolah tidak berubah. Dashboard tetap merupakan ringkasan fixture terpisah, bukan hasil hitung ulang daftar jurnal contoh. Tidak ada hapus, void atau pembatalan penerimaan baru pada alur ini.

Fixture daftar mempunyai tiga draf Oktober yang sama dengan dashboard, dua jurnal khusus yang menunggu persetujuan, dan dua contoh tercatat September untuk menilai filter dan keadaan baca-saja. Contoh manual ketiga diberi nama Penerimaan lain-lain agar tidak menyiratkan perubahan pada penerimaan pendaftaran otomatis.

Pemeriksaan v5:
- Typecheck/build lulus. Warning chunk produksi >500 kB tetap ada; entry produksi tidak diganti.
- Browser: ubah draf, tolak saldo tidak seimbang, simpan, catat, kunci edit/catat ulang, pencarian setelah edit; semuanya lolos.
- Buat draf baru menambah baris; nomor bukti duplikat ditolak. Tutup/Escape formulir yang berubah meminta pilihan; lanjut mengisi mempertahankan input, buang perubahan mempertahankan jurnal sebelumnya.
- Finance tidak diberi aksi approve/catat pada jurnal khusus PENDING; Kepsek dapat menyimulasikan persetujuan dan tidak diberi edit. Predikat fixture juga mempunyai assert untuk jurnal tercatat, rekonsiliasi, pembuat sama, dan pengajuan khusus.
- Filter bulan/status, hasil kosong, reset, format nominal id-ID (125.000 tetap bernilai 125000), dan tautan dashboard ke kode jurnal tertentu lolos.
- Drawer menerima fokus; sesudah ditutup fokus kembali ke baris asal. Form dan halaman tidak overflow di 390 px dan 320 px; tombol simpan tetap terlihat. Screenshot desktop/rincian/form dan mobile ada di `journal-v5-*.png`.
- Pemeriksaan empat role dan enam permintaan route di luar role masih lolos. Ini memeriksa presentasi preview, bukan keamanan API.

Yang belum dicakup: data/API nyata, seluruh 23 view, uang desimal produksi, seluruh kombinasi permission/user, audit aksesibilitas menyeluruh, printer dan deployment. Layar pembayaran TU tetap contoh form tanpa simpan; belum diubah menjadi simulasi jurnal ini.


## Alur tagihan v6 — 15 Oktober 2026

Lanjutan preview menuntaskan siswa → tagihan → rincian komponen/riwayat → alokasi pembayaran → pemeriksaan → hasil. Tema navy kini dipakai di home keempat role dan seluruh tujuh layar preview yang tersedia. Informasi dan tindakan tetap memakai role/navigation existing. Halaman siswa mendapat tautan Tagihan per NIS. Kegiatan mengikuti tema bersama; form realisasi kegiatannya belum dibuat.

Standardisasi yang dipakai bersama:
- `workspace-theme.css` menggantikan nama studi `finance-direction.css`; `.workspace-theme` adalah presentasi semua role, bukan izin Finance.
- `workflow-preview.css` menggantikan `journal-preview.css`. Drawer, form, input rupiah, metadata, pesan, penjagaan perubahan, konfirmasi, dan hasil mempunyai kelas bersama (`detail-drawer`, `entry-form`, `entry-balance`, `record-metadata`, `preview-feedback`, dll.). Tidak dibuat wrapper komponen baru yang belum diperlukan.
- `BillingPreview.vue` mengelola interaksi preview. `billing-preview.ts` menyediakan fixture komponen/riwayat, total, status, predikat bayar dan validasi alokasi. Nominal, status dan ringkasan dihitung dari sumber yang sama.
- Form pembayaran lama yang tombol simpannya dinonaktifkan telah dihapus. Dialog generik profil/kegiatan tetap hanya untuk membaca contoh rincian.

Pola bisnis mengacu pada `TagihanListView.vue`, `TunggakanTagihanView.vue`, `operations/api/billing.py`, `operations/services/billing.py` dan permission existing yang diperiksa:
- Hanya TU mencatat pembayaran. Finance/Kepsek hanya membaca tagihan/tunggakan dan rincian pembayaran; Guru tetap tidak mendapat rute tagihan.
- Total diterima adalah jumlah alokasi komponen. Nilai positif, rupiah bulat dalam batas integer aman, komponen valid, alokasi tidak duplikat dan tidak melebihi sisa masing-masing komponen. Bukti, tanggal dan Kas/Bank wajib diisi.
- Tagihan dengan pembayaran lama yang belum terverifikasi mempertahankan paid/sisa null. Tidak dimasukkan sebagai nol ke total terverifikasi, tidak diberi aksi pembayaran, dan tidak ditandai lunas.
- Pembayaran sebagian memperbarui komponen dan riwayat; pelunasan mengubah status menjadi Lunas serta menghilangkan aksi pembayaran berikutnya. Bukti duplikat dalam contoh ditolak.
- Hasil menyebut jurnal draf contoh secara eksplisit. Tidak ada posting ke buku besar, pengiriman data ke Finance, atau integrasi otomatis ke daftar jurnal pada preview ini.

Fixture turunan mempertahankan nominal tiga tagihan sebelumnya. SPP memakai fixture siswa; sisa komponen contoh diberi label Katering. Ini data demonstrasi, bukan aturan penetapan tarif. Riwayat awal Siswa Contoh B berisi bukti Rp600.000 pada komponen SPP, sesuai jumlah diterima fixture. Siswa C tidak diberi riwayat nol sebagai pengganti pembayaran lama yang belum diketahui.

Pemeriksaan v6:
- Typecheck/build lulus. Warning chunk produksi >500 kB masih ada.
- Browser: alokasi berlebih ditolak; pembayaran sebagian Rp50.000 pada sisa Rp350.000 menghasilkan Rp300.000; pelunasan berikutnya menghilangkan aksi bayar; riwayat bertambah sesuai dua pembayaran. Bukti duplikat ditolak.
- Pembayaran pada tagihan belum cocok diblokir dan nilai Belum diketahui dipertahankan. Finance/Kepsek tidak mempunyai tombol pembayaran.
- Siswa → Tagihan membawa filter NIS; pencarian dan status lokal menyaring data yang sama. Ringkasan menyebut cakupan hasil filter.
- Form dan langkah konfirmasi sama-sama menjaga input saat Escape/tutup. Lanjut mengisi mempertahankan input; buang perubahan tidak mengubah tagihan; fokus kembali ke baris pemicu.
- Mobile 390 px menggunakan daftar per tagihan dengan total/diterima/sisa/status/tindakan terlihat. Form dan hasil dapat diselesaikan di 320 px tanpa overflow halaman/panel. Input 150.000 memakai locale id-ID.
- Pemeriksaan empat role/enam permintaan rute di luar role tetap lolos. Alur simpan jurnal juga lolos sesudah pemakaian kelas bersama. Tidak ada request API, axios/fetch, localStorage atau sessionStorage pada preview.
- Screenshot `billing-v6-desktop.png`, `billing-v6-detail.png`, `billing-v6-review.png`, `billing-v6-mobile-list.png` dan `billing-v6-mobile-form.png` tersedia di folder ini.

Batas tetap: simulasi di memori, hilang saat navigasi/muat ulang; belum ada API/data produksi, idempotency server, uang desimal produksi, pencocokan data lama, cetak struk, atau audit aksesibilitas lengkap. Implementasi harus mempertahankan kontrak alokasi, `request_id`, validasi dan permission server existing. Seluruh 23 view belum selesai.
