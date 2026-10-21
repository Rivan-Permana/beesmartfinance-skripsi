# BeeSmart Finance — arah revamp UI/UX

Tanggal: 15 Oktober 2026, WIB. Status: **usulan desain untuk dibahas, belum diimplementasikan**.

Pembaruan: pengguna meminta preview nyata, dashboard lebih lengkap, perwakilan empat peran, Phosphor Icons, dan standar UI/IA/copy. Preview kedua tersedia melalui entry Vue terpisah di `frontend/dashboard-preview.html`; implementasi produksi belum dimulai. Lihat [standar versi kedua](./ui-standards.md) untuk arahan terbaru, cakupan yang sudah dibuat, serta evaluasi Impeccable, SaaSpo, Refero Styles dan mkdir. Arahan ikon Phosphor menggantikan pilihan ikon preview sebelumnya.

## Brief yang sudah dikonfirmasi

- Revamp mencakup seluruh UI/UX; tahap sekarang adalah deep planning.
- Admin TU, Finance/bendahara, Kepala Sekolah, dan Guru PIC mendapat perhatian setara.
- Pengguna belum menyebut keluhan alur tertentu; motivasinya membuat produk lebih terpoles.
- Pengguna meminta rekomendasi arah visual dan referensi Mobbin.
- Prioritas perangkat belum dipilih. Usulan: desktop untuk tabel/transaksi, tablet untuk absensi, mobile tetap dapat menyelesaikan tugas yang diizinkan.

Konsekuensi: pemerataan kualitas empat peran menjadi syarat cakupan. Perubahan urutan kerja harus punya alasan dari audit atau walkthrough; tidak menambahkan fitur hanya agar hasil terlihat baru.

## Rekomendasi visual

**Profesional, tenang, dan tetap terasa Lebah Madu.** Pertahankan logo dan pengenalan brand; bangun keteraturan dari tipografi, ruang, tabel, dan hierarki aksi. Identitas paling kuat ada pada navigasi aktif serta CTA magenta, sementara isi halaman menonjolkan nama, angka, periode, dan status.

| Opsi | Karakter | Implikasi | Penilaian |
|---|---|---|---|
| A — profesional dengan aksen sekolah | Surface putih, navy untuk teks/struktur, magenta terkontrol, garis tabel ringan | Cocok untuk seluruh peran; banyak komponen lama bisa dipakai | **Rekomendasi** |
| B — sekolah yang hangat | Lebih banyak warna madu, font judul playful, bidang berwarna | Identitas sekolah kuat; perlu menahan dekorasi di tabel keuangan | Alternatif bila kehangatan brand lebih diprioritaskan |
| C — enterprise netral | Abu/slate dominan, warna brand sangat sedikit, tabel lebih rapat | Efisien untuk Finance, tetapi identitas sekolah lebih lemah | Kurang cocok sebagai arah utama empat peran |

Pilihan A adalah rekomendasi, bukan persetujuan pengguna yang diasumsikan.

### Token usulan A

| Peran token | Nilai | Pemakaian |
|---|---|---|
| Workspace | `#F7F8FC` | Latar halaman |
| Surface | `#FFFFFF` | Sidebar, tabel, form, panel |
| Navy brand | `#2E2A6E` | Brand, heading, struktur penting |
| Magenta aksi | `#B51268` | CTA dan navigasi aktif; versi lebih dalam dari magenta logo |
| Teks sekunder | `#64748B` | Keterangan, metadata |
| Border | `#E2E8F0` | Pemisah dan batas kontrol |

Teks utama `#17243B`; magenta logo `#E5197F` tetap boleh tampil di aset brand. Status memakai palet terpisah: sukses `#166534`, peringatan `#92400E`, kesalahan/destruktif `#B91C1C`, informasi `#1D4ED8`, dengan latar tint yang ditentukan saat mockup. Warna pengeluaran tidak sekaligus berarti error. Kontras pasangan foreground/background belum diukur; nilai di atas merupakan kandidat.

- **Tipografi:** reuse Nunito Sans yang sudah dimuat; body 15–16 px, label 14 px, heading halaman 26–28 px/700, heading bagian 18–20 px/700. Baloo 2 hanya pada identitas brand bila masih diperlukan; keluarkan dari header tabel, angka, dan judul form. Tidak perlu font baru.
- **Angka:** `formatRp`, tabular numbers, rata kanan pada tabel, tanda minus terlihat. Nilai null yang berarti belum diketahui tidak ditampilkan sebagai Rp0.
- **Ruang:** skala 4/8/12/16/24/32 px. Desktop padding 24–32 px, tablet 20 px, mobile 16 px.
- **Bentuk:** kontrol 8 px, panel 12 px, dialog 16 px. Shadow hanya untuk elemen mengambang. Hilangkan hover mengangkat kartu yang tidak bisa diklik.
- **Kontrol:** tinggi target sentuh 44 px; tombol ikon tetap memiliki nama aksesibel. Tabel nyaman dibaca, tanpa density switch baru.
- **Motion:** transisi interaksi singkat 120–180 ms; hormati reduced motion. Tidak perlu animasi pembuka atau dekorasi bergerak.

### Komposisi workspace

Sidebar terang dengan logo dan teks navy; item aktif memakai tint magenta serta indikator yang tidak bergantung warna saja. Navigasi tetap dikelompokkan per domain dan per role. Topbar berisi konteks halaman dan identitas pengguna; filter periode berada di halaman yang memang memakai periode tersebut.

```text
┌──────────────────┬─────────────────────────────────────────────────────┐
│ Lebah Madu       │ Siswa / Tagihan                 Nama · Peran       │
│                  ├─────────────────────────────────────────────────────┤
│ Kelompok menu    │ Tagihan siswa                   [Buat tagihan]     │
│ • item aktif     │ Keterangan singkat              Buat sekaligus     │
│ • item lain      │                                                     │
│                  │ [Cari siswa…]  [Status]  [Periode]  Reset filter    │
│                  │ Cakupan hasil dan filter aktif                     │
│                  ├─────────────────────────────────────────────────────┤
│                  │ Siswa    Periode   Total   Dibayar   Sisa   Aksi    │
│                  │ …        …         Rp…     Rp…       Rp…    Detail  │
│                  ├─────────────────────────────────────────────────────┤
│                  │ Jumlah hasil                         Pagination    │
└──────────────────┴─────────────────────────────────────────────────────┘
```

Wireframe menunjukkan susunan, bukan komponen yang sudah dibangun. Nominal dan ringkasan hanya ditambahkan jika sumber data dan cakupannya jelas. Jangan menghitung total sekolah dari satu halaman API.

## Bukti dan batas audit

Sumber utama adalah kode lokal per 15 Oktober 2026. Inventaris statis menemukan **23 view: 22 halaman aplikasi dan login, 30 deklarasi DataTable, 30 deklarasi Dialog**. Jumlah deklarasi tidak berarti semuanya tampil sekaligus. Tidak ada listener lokal pada port 5173/8000/8080 saat diperiksa; UI BeeSmart belum ditinjau dalam browser pada sesi ini.

| Temuan kode | Implikasi desain | Penanganan usulan |
|---|---|---|
| `AppShell.vue:27` mengembalikan judul route sebelum memeriksa alias; pemeriksaan `jenis=…` memakai `route.path` | Breadcrumb tidak mengikuti Pemasukan/Pengeluaran | Baca `route.query.jenis` sebelum fallback judul jurnal |
| Label menu disembunyikan saat collapsed tanpa nama aksesibel eksplisit pada button | Navigasi ikon berisiko sulit dipahami | Nama aksesibel, tooltip saat collapsed, `aria-current`, dan tautan navigasi semantik |
| Drawer shell berupa aside/backdrop; belum ada pengelolaan focus/Escape eksplisit | Risiko keyboard dan screen reader pada mobile | Gunakan Drawer PrimeVue yang sudah tersedia, pertahankan nav dan role filter |
| `PageLayout` selalu membungkus isi dengan satu kartu | Dashboard panel berpotensi bertumpuk di dalam kartu luar | Varian tanpa surface untuk dashboard; default lama tetap berlaku |
| SearchField dipaksa satu baris penuh oleh CSS global | Toolbar sulit disesuaikan dengan konteks | Search fleksibel di desktop; full width saat sempit |
| Dashboard mengulang metrik di hero strip dan KPI | Hierarki perhatian kurang jelas | Satu ringkasan inti, kemudian bagian tindakan dan analisis |
| Dashboard mengambil DRAFT tetapi panel berjudul “Jurnal Menunggu Approve” | Draft dan antrean persetujuan terkesan sama | Selaraskan nama panel dan query; DRAFT dan PENDING tidak digabung secara semu |
| Token danger memakai keluarga magenta brand | Aksi rutin dan destruktif sulit dibedakan | Pisahkan warna brand dan status destruktif |
| Label login/jurnal belum terhubung eksplisit ke input; beberapa tombol ikon turun ke 32–36 px | Perlu perbaikan aksesibilitas bersama dengan polish | Hubungkan label/input, target sentuh, focus, error inline |
| EmptyState ada di sebagian view; view lain memakai teks kosong sederhana | Pengalaman kosong belum konsisten | Bedakan data belum ada, hasil filter kosong, gagal muat |
| UX Juni menjelaskan approval seragam dan guru membuat rencana; kode sekarang berbeda | Mengikuti dokumen lama dapat mengubah kewenangan | Ikuti guard/predicate saat ini; guru realisasi, Kepsek mengelola kegiatan |

Masalah visual di atas merupakan interpretasi struktur/CSS, bukan hasil pengamatan langsung pada perangkat atau keluhan pengguna. Temuan aksesibilitas kode merupakan risiko yang perlu walkthrough, bukan klaim sertifikasi audit.

## Referensi Mobbin yang benar-benar dilihat

Preview dibaca dari dua pencarian terbatas: tabel invoice dan daftar kerja. Tautan berikut menuju screen kanonis; gambar tidak disalin atau disimpan ke repository.

| Referensi | Yang terlihat pada preview | Adaptasi untuk BeeSmart |
|---|---|---|
| [Mercury](https://mobbin.com/screens/a06d508c-cdb8-4973-8f0b-3be7db44b351) | Sidebar terang, ringkasan invoice, filter dekat tabel, detail invoice di samping | Detail pembayaran tetap punya konteks siswa/periode; uji panel samping pada mockup sebelum mengganti dialog |
| [Midday](https://mobbin.com/screens/f2a4a414-3111-4357-a01c-0cb2933ecb92) | Tabel berjarak rapi, status ringan, menu aksi terbuka | Satu aksi utama terlihat; aksi sekunder dikelompokkan tanpa menyembunyikan aksi penting |
| [QuickBooks](https://mobbin.com/screens/ad2852b2-dee4-4a9f-a815-0f2ba340f3b0) | Status/tanggal dekat daftar invoice, CTA jelas, pagination | Toolbar dekat data; copy lokal seperti “Buat tagihan” dan “Catat pembayaran” |
| [Asana](https://mobbin.com/screens/1581c115-af0d-4a78-bccb-8aa03522e097) | Daftar tugas dengan assignee/tanggal dan pengaturan tampilan di samping | Kegiatan menonjolkan PIC, waktu, pagu, realisasi, status; tetap memakai model kegiatan yang ada |
| [Motion](https://mobbin.com/screens/0955ab12-2387-492c-a404-07d7f4b55f1d) | Daftar dikelompokkan, status dan deadline menjadi kolom yang mudah dipindai | Kelompokkan informasi tugas yang ada; tidak menambahkan task manager atau kanban |

Better Design juga mengembalikan preview alur Acctual, Deel, dan Harvest; digunakan sebagai pembanding awal pemisahan form/ringkasan. Mobbin menjadi referensi utama setelah arahan pengguna. Tidak mengambil kit React/shadcn atau memasang library desain baru.

Untuk implementasi theme, dokumentasi resmi [PrimeVue Styled Mode](https://primevue.org/theming/styled), diambil lewat Context7, mendukung meneruskan preset Aura dengan `definePreset` dan token semantic/component. Utamakan jalur itu daripada menambah override `!important`; CSS print yang memang diperlukan tetap dipertahankan.

## UX empat peran

| Peran | Home saat ini | Pekerjaan yang harus terasa rapi | Hal yang wajib tetap benar |
|---|---|---|---|
| Administration | `/siswa` | Data siswa, absensi, tagihan/pembayaran, pendaftaran, katering/jemputan, pegawai | Bahasa operasional; tidak diberi menu akuntansi |
| Finance | `/dashboard` | Pemasukan/pengeluaran, tunggakan, akun/saldo awal, laporan, payroll | Tunggakan tetap read-only; posting mengikuti `can_finance_post` |
| SchoolPrincipal | `/dashboard` | Ringkasan, persetujuan yang memang diperlukan, kegiatan, laporan, periode | Tidak semua jurnal perlu approval; tutup buku dan pembalikan tetap sesuai akses |
| TeacherInCharge | `/kegiatan` | Realisasi kegiatan dan rekap siswa | Bukan pembuat/pengelola kegiatan pada kode sekarang; rekap read-only |

Home, URL, guard, dan kewenangan tidak perlu diubah untuk memoles empat peran. Finance saat ini bisa mengakses route pegawai/absensi pegawai tetapi item menu disembunyikan; ini dicatat sebagai perbedaan navigasi yang perlu keputusan tersendiri, bukan alasan membuka menu saat revamp.

### Alur prioritas dan copy

1. **Tagihan:** daftar → rincian → catat pembayaran → hasil → riwayat/cetak. Siswa, periode, total, diterima, sisa tetap terlihat pada langkah pembayaran. Alokasi per komponen, pembayaran sebagian, `request_id`, dan validasi existing dipertahankan.
2. **Pendaftaran:** daftar calon → rincian biaya; penerimaan uang dan finalisasi siswa adalah dua aksi terpisah. Biaya formulir, sit-in, dan SPP tidak diberi tarif asumsi. Status siswa dan status penerimaan disajikan sebagai informasi berbeda.
3. **Jurnal:** Finance menyimpan draft, lalu mencatat jurnal yang diizinkan; jurnal khusus mengikuti pengajuan/persetujuan yang berlaku. Tampilkan “Draf”, “Menunggu persetujuan”, “Tercatat di buku besar” sebagai label presentasi bila cocok dengan status aktual; nilai API tetap DRAFT/PENDING/POSTED.
4. **Kegiatan:** Kepsek membuat/mengelola kegiatan; Guru PIC mencatat realisasi sesuai akses. Ringkasan pagu/realisasi dan validasi batas anggaran dekat aksi, tidak tenggelam di dekorasi.
5. **Absensi:** pilih jenjang → kelompok → tanggal/grid → simpan. Tanggal/kelompok selalu jelas. Chip bisa disentuh, status tidak hanya dibedakan warna, indikator simpan jujur. Perubahan status tidak hadir tetap membersihkan flag katering/jemputan seperti implementasi sekarang.
6. **Laporan/tutup periode:** pilih cakupan → terapkan → baca → cetak/ekspor. Jelaskan laporan yang tahunan versus bulanan. Penutupan periode tetap terpisah dan terkonfirmasi.

Usulan copy: “Buat tagihan sekaligus” untuk Batch Generate, “Setujui” untuk Approve, “Ekspor CSV”, “Catat penerimaan”, dan “Jadikan siswa aktif” hanya bila tetap jelas bahwa aksi tersebut merupakan finalisasi. Detail akuntansi untuk Admin ditempatkan sebagai penjelasan singkat yang sesuai tugas; status penerimaan tidak boleh disembunyikan.

### Dua susunan khusus

```text
Pembayaran di desktop                   Dashboard Finance/Kepsek
┌──────────────────┬────────────────┐  ┌─────────────────────────────────┐
│ Siswa + periode  │ Ringkasan       │  │ Judul + cakupan waktu           │
│ Komponen/alokasi │ Total           │  │ Kas | Pendapatan | Beban | Hasil │
│ Tanggal + bukti  │ Sudah diterima  │  ├───────────────────┬─────────────┤
│ Kas / Bank       │ Sisa            │  │ Tren keuangan     │ Perlu       │
│ Error inline     │                 │  │                   │ perhatian   │
├──────────────────┴────────────────┤  ├───────────────────┴─────────────┤
│ Batal          Simpan pembayaran  │  │ Analisis tambahan dan detail    │
└───────────────────────────────────┘  └─────────────────────────────────┘
```

Pada mobile, ringkasan pembayaran tampil sebelum form; tombol akhir tidak menutupi input/keyboard. Dashboard tidak menambah antrean atau KPI bila data/API dan hak akses belum mendukungnya. Prediksi tidak boleh diberi label sebagai saldo aktual.

## Pola bersama dan responsive

- Satu judul halaman dan satu CTA utama. Aksi destruktif terpisah dari aksi rutin; aksi penting tidak tersembunyi hanya di hover.
- Reuse DataTable, Dialog, Drawer, Button, Select, DatePicker, InputNumber, Message, Tag, dan Toast PrimeVue. Tidak menulis ulang focus management modal sendiri.
- Form pendek tetap dialog; form panjang memakai dialog lebar dengan area isi yang bisa digulir. Panel detail samping adalah opsi mockup, belum keputusan mengganti seluruh dialog.
- Filter punya label aksesibel dan reset yang jelas; hasil kosong menyebut filter aktif. Periode bulan, tahun kalender, tahun ajaran, serta periode akuntansi tidak dipaksa menjadi satu filter global.
- Loading bukan nol; error bukan kosong; record lama belum terverifikasi bukan lunas. Sukses menyebut aksi yang benar-benar selesai; error tetap dekat form dan mempertahankan input.
- `≥1280 px`: sidebar penuh dan layout dashboard dua kolom. `768–1279 px`: sidebar collapsible, kolom menyesuaikan. `<768 px`: Drawer berlabel lengkap, konten bertumpuk.
- Pada layar sempit, tabel akuntansi tetap tabel dalam area scroll lokal dengan identitas baris jelas. Daftar sederhana boleh memakai susunan bertumpuk bila tidak menduplikasi state/data. Tidak menyembunyikan total/sisa atau izin aksi untuk mengejar tampilan ringkas.
- Target rancangan: 1440, 1024, 768, 390, dan 360 px; keyboard dan zoom 200% diperhatikan. Focus visible, label terhubung, status terbaca tanpa warna, escape/focus-return pada overlay, reduced motion.
- Cetak invoice, laporan, dan slip gaji punya kontrak sendiri: isi transaksi lengkap dan shell/tombol disembunyikan; perubahan screen CSS tidak boleh merusak print CSS.

## Review desain sebelum diperluas

Mockup berikut perlu dibuat pada tahap desain selanjutnya dengan data contoh yang diberi label:

| Peran | Layar contoh | State wajib |
|---|---|---|
| Admin TU | Tagihan + pembayaran, absensi tablet | Pembayaran sebagian, data perlu dicocokkan, simpan/gagal |
| Finance | Jurnal pemasukan/pengeluaran | Draf, saldo seimbang/tidak, tidak diizinkan mencatat |
| Kepsek | Dashboard + konteks persetujuan | Data kosong, gagal sebagian, jurnal PENDING yang valid |
| Guru | Kegiatan + realisasi | Read-only pada pengelolaan, pagu tersisa, rekap siswa read-only |

Semua peran harus terwakili sebelum pola visual dibawa ke seluruh modul. Review memutuskan palet A/B/C, sidebar terang, penggunaan Baloo, kepadatan tabel, dan kelayakan dialog versus panel samping. Tidak perlu membuat dashboard baru untuk tiap peran.

## Keberhasilan dan keputusan terbuka

Keberhasilan adalah seluruh route mendapat kualitas desain yang sama; pengguna bisa mengidentifikasi halaman, cakupan waktu, status, dan aksi utamanya; angka dan hak akses tetap benar. Tidak mengklaim perbaikan waktu kerja/persentase usability tanpa baseline dan pengamatan pengguna.

Belum diputuskan: penerimaan rekomendasi A, perangkat yang paling sering dipakai tiap peran, referensi pilihan pengguna, serta hasil walkthrough aplikasi yang berjalan. Arah visual dapat dilanjutkan sebagai draft, tetapi rollout produksi belum diotorisasi dalam permintaan ini.
