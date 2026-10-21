# Review kelengkapan dan kompatibilitas sistem desain BeeSmart 0.1

**Pembaruan penerapan:** [fondasi 0.2](../../design-artifacts/bee-design-system/README.md) sudah menghubungkan token/BeePreset dan shared components, menambah spesimen PrimeVue, serta menerapkan prioritas dashboard pada source lokal. Review di bawah menyimpan temuan **sebelum perubahan**; tautan baris source dapat bergeser. Kelengkapan seluruh modul/cetak tetap belum dinyatakan selesai.

**16 Oktober 2026, WIB. Verdict awal: fondasi tersedia; belum lengkap untuk rollout seluruh aplikasi.** Stack mendukung implementasinya tanpa rewrite, tetapi kesamaan teknologi tidak membuat spesimen otomatis menggantikan komponen produksi. Ada tiga pekerjaan utama sebelum migrasi luas.

Review ini tidak mengubah source aplikasi atau desain. Satu probe komponen dijalankan sementara di browser terisolasi, kemudian halaman dimuat ulang untuk membuang perubahan tersebut. Tidak ada request pembayaran, perubahan role, atau deployment.

## Design language

- **Audited surface:** sistem desain 0.1 dan jalur penerapannya pada Vue SPA BeeSmart: bootstrap → BeePreset/global CSS → AppShell/PageLayout → komponen serta halaman keuangan/operasional. Inventaris mencakup 23 `*View.vue`; pemeriksaan mendalam difokuskan pada shared components, dashboard, jurnal, tagihan, kegiatan, dan jalur print terkait.
- **Design sources:** permintaan pengguna tentang empat role, Phosphor, informasi yang relevan, dan fondasi sebelum rollout; `design-artifacts/bee-design-system/README.md` serta token/spesimen saat ini. Fondasi tersebut masih usulan dan belum mengatur hasil render aplikasi produksi.
- **Documented decisions:** IBM Plex Sans, navy untuk struktur, magenta untuk tindakan, madu untuk identitas; semantik status terpisah; nilai tak diketahui tidak menjadi nol; prioritas berbeda per role; reuse PrimeVue, route, API, dan komponen existing.
- **Governing owners and consumers:** aplikasi saat ini diatur `src/main.ts`, `core/theme.ts`, `assets/main.css`, `assets/primevue-overrides.css`, komponen bersama dan CSS scoped masing-masing. Spesimen mempunyai entry dan CSS terpisah. `navigation.ts`, router, auth store, predikat aksi, dan backend tetap mengatur akses.
- **Explicit exceptions:** spesimen sengaja memakai PrimeVue unstyled; form contoh hanya nominal rupiah bulat; data/role contoh tidak terhubung API; sidebar dokumentasi bukan shell produk final. Semua ini tertulis pada panduan 0.1, sehingga keberadaannya sendiri bukan bug produksi.

## Findings

P1 di sini berarti harus diselesaikan sebelum rollout luas, bukan insiden produksi yang ditemukan dari data asli.

| # | Problem | Evidence | Proposed change | Scope | Confidence |
|---|---|---|---|---|---|
| 1 · P1 | Token baru belum mengendalikan komponen aplikasi; mengimpor CSS spesimen akan menghasilkan dua gaya | Kontrak integrasi ada pada panduan 0.1. [Entry spesimen](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/design-system/main.ts:7>) memakai unstyled; [entry aplikasi](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/main.ts:30>) memakai BeePreset. [Override tabel](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/assets/primevue-overrides.css:3>) dan font lama tetap masuk jalur render. Probe browser membuktikan tombol `#E5197F`, header krem `#F5EDD6`, font Nunito/Baloo, padahal token target `#B01862` dan IBM Plex Sans | Petakan token terpilih ke **BeePreset dan shared CSS existing**, lalu sesuaikan override yang berbenturan pada owner-nya; pertahankan styled mode | Seluruh aplikasi, terutama 20 file pengguna DataTable dan 16 file pengguna Dialog | Tinggi — source dan computed style probe |
| 2 · P1 | Spesimen belum mewakili komponen interaktif yang benar-benar digunakan produk | Panduan menjanjikan pola tabel/form/overlay yang konsisten. [Spesimen](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/design-system/DesignSystem.vue:3>) hanya mengimpor Dialog, InputNumber, Chart; tabel, tombol, select menggunakan HTML native. [Jurnal](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/features/jurnal/JurnalListView.vue:349>) memakai DataTable lazy/server pagination, [tagihan](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/features/tagihan/TagihanListView.vue:566>) DataTable client pagination. CSS `.bee-table` tidak menata `.p-datatable` | Lengkapi spesimen menggunakan **komponen PrimeVue yang sama dengan caller**, termasuk state dan paging yang dipakai produk | Tabel, filter, form, navigasi mobile, notifikasi, konfirmasi, status, ikon | Tinggi — impor dan komposisi template aktual |
| 3 · P1 | Prioritas role dan bahasa persetujuan pada dashboard belum tercermin pada view aplikasi | Spesimen Finance/Kepsek berbeda, tetapi [DashboardView](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/features/dashboard/DashboardView.vue:408>) menampilkan bagian operasional ketika `opsCards.length`, tanpa pemilahan Finance/Kepsek. Panel [“Jurnal Menunggu Approve”](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/features/dashboard/DashboardView.vue:452>) bersubjudul “Status draft”, sementara [load](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/frontend/src/features/dashboard/DashboardView.vue:299>) meminta DRAFT. [Backend approve](</Users/sinarivan-permananjung/Bismillah Skripsi/beesmartfinance-skripsi/backend/accounting/api.py:170>) memerlukan PENDING dan maker berbeda | Terapkan komposisi dashboard berbasis tugas role dan pisahkan **draf** dari **antrean persetujuan yang sah** pada DashboardView; pertahankan predikat/izin existing | Dashboard Finance/Kepsek; TU/Guru tetap memakai home existing | Tinggi untuk source; belum walkthrough dengan akun/data asli |

Temuan 3 bukan bukti kebocoran akses: Finance dan Kepsek memang diizinkan membuka route dashboard. Masalahnya adalah prioritas informasi dan label, yang tidak selesai hanya dengan mengganti warna. Tidak menyimpulkan semua PENDING dapat disetujui; rekonsiliasi, jenis sumber, `can_finance_post`, pembuat, dan status periode tetap berpengaruh.

## Improve first

**Temuan 1: jembatan token ke BeePreset/shared CSS.** Ini mencegah setiap layar mendapat override baru yang saling melawan. Jangan mengimpor `system.css` utuh ke `src/main.ts`, mengganti seluruh aplikasi menjadi unstyled, atau mengubah setiap view menjadi markup demo.

Dokumentasi resmi [PrimeVue styled mode](https://primevue.org/theming/styled) mendukung preset berlapis primitive → semantic → component melalui `definePreset`. Aplikasi sudah memakai jalur ini. Integrasi perlu mengikuti struktur preset yang dipakai, termasuk color scheme, bukan sekadar menambahkan nama custom property baru.

## Matriks kelengkapan dan kompatibilitas

| Area | Yang sudah tersedia | Yang masih perlu dilengkapi sebelum penerapan terkait |
|---|---|---|
| Warna, huruf, angka, ruang | JSON token, skala, fungsi warna, tabular numbers, radius, shadow | Mapping preset/alias; font pada entry utama dan CSS scoped; state hover/pressed/invalid pada komponen aktual |
| Button/InputText/InputNumber | Arah visual, kontrol native, InputNumber nyata, disabled dan form error contoh | Button/InputText styled, loading/disabled saat request, error per field; jangan menyalin aturan integer demo ke pembayaran desimal |
| Select/MultiSelect/DatePicker | Native select dan aturan label | Search/filter/clear, popup yang diteleport ke body, pilihan kosong/gagal dimuat, kalender, keyboard, format tanggal lokal |
| DataTable/pagination | Record contoh, density 72/60, nominal kanan, filter kosong | DataTable styled, lazy/client paging, sorting jika caller memakainya, total record API, header/action alignment, record panjang, scroll lokal dan adaptasi mobile |
| Status/Message/Toast/ConfirmDialog | Bahasa status dan contoh pesan kosong/memuat/gagal/berhasil | `Tag` dan severity existing, VOID, sebagian bayar, konfirmasi destruktif, loading request, recovery tanpa menghapus input; Toast/ConfirmationService tetap terpasang |
| Shell/navigasi | Cuplikan menu per role memakai `navForRoles`/`roleHome` | AppShell nyata: expanded/collapsed/mobile, aktif berdasarkan route+query, label aksesibel, Escape/fokus/scroll pada menu mobile |
| Shared components | Sudah ada owner yang bisa dipakai | `PageLayout` dipakai 22 view dan selalu membuat outer card; jangan mengubah default untuk semua caller. `SearchField` 5 caller, `PeriodPicker` 7, `EmptyState` 9 memerlukan adaptasi yang menjaga props/model/emit |
| KPI/chart container | Spesimen saldo dan dua bentuk grafik | Skin `KpiCard`/`ChartPanel`/`RingGauge` masih lama, termasuk gradient, font dan motion; ubah owner existing, bukan tambah paket komponen paralel |
| Chart.js | Line/bar nyata, periode/unit, dashed line dan tabel angka dari dataset sama | `chartTheme.ts` masih palette/font lama, font sumbu 11 px dan animasi 500–800 ms; CSS reduced motion tidak menghentikan animasi canvas JavaScript. Tentukan reduced-motion di opsi chart dan tambahkan alternatif data per panel nyata |
| Informasi role | Empat cuplikan dengan prioritas berbeda | Komposisi home nyata, multi-role sesuai prioritas existing, scope/count API, serta kelayakan aksi. Cuplikan 4 siswa/2 jurnal bukan total sekolah |
| Ikon Phosphor | SVG lokal 38 symbol, Regular, MIT, komponen SVG | Inventaris menemukan 54 nama PrimeIcons unik pada Vue produk+navigation.ts; jumlah ini bukan perbandingan satu-banding-satu dengan symbol. Belum ada mapping lengkap menu/aksi/status maupun penggantian ikon internal PrimeVue |
| Foto/upload | Ada kebutuhan nyata pada input foto menu katering | Spesimen memilih, mengganti, menghapus, preview, format/ukuran gagal, pending upload, dan cleanup URL mengikuti implementasi existing |
| Nilai uang/status tidak diketahui | Aturan bahasa sudah membedakan nol dari belum diketahui | Pertahankan guard `null` pada tagihan; decimal payload dan alokasi; lihat batas kontrak uang di bawah |
| Print | Panduan menyebut invoice/slip/laporan dan reuse print existing | Belum ada spesimen cetak baru yang terverifikasi. Preserve `.bee-print-struk`, mask/dialog Teleport, cleanup `afterprint`, periode/nominal dan halaman panjang |
| Responsif/aksesibilitas | Fokus, label, contoh error, target kontrol, reflow halaman spesimen | Periksa komponen styled/overlay dengan keyboard dan zoom; tabel padat/rekap jangan dipaksa menjadi kartu jika tugas membandingkan kolom membutuhkannya; screen reader dan perangkat asli belum diperiksa |
| Build/distribusi | Typecheck dan dua build berhasil | `design-system.html` bukan input build produksi normal. Tautan token `/src/...` bergantung dev server; jika styleguide kelak diterbitkan, ekspor JSON sebagai asset dan tetapkan entry terpisah |

Jumlah caller berasal dari import statis pada file Vue produk, mengecualikan `design-preview` dan `design-system`; bukan jumlah semua instance, row, atau route. Inventaris ini tidak menyatakan seluruh state di setiap view sudah diuji.

## Kontrak implementasi yang perlu dipertahankan

### Token dan alias

Gunakan JSON sebagai sumber nilai, BeePreset untuk komponen PrimeVue, dan CSS shared untuk shell/layout. Kandidat mapping yang jelas:

| Consumer existing | Token calon sumber |
|---|---|
| Primary theme dan `--bee-primary` | `color.brand`, hover `color.brand-hover`; state lain perlu ditetapkan pada preset |
| `--app-bg`, `--app-surface`, `--app-border`, `--app-text` | `color.canvas`, `surface`, `border`, `ink` |
| `--app-text-muted`, `--bee-text-muted` | `color.muted` |
| `--bee-danger` | `color.critical`, terpisah dari primary |
| Navigasi | `color.nav`, `nav-text`, `nav-muted` dan `layout.sidebar` |
| Font body/judul/komponen | `font.body`, `type`, `weight`, `leading` |

Jangan memetakan semua alias secara buta: `--bee-radius-lg` dipakai panel dan dialog, padahal target radius berbeda. `--bee-orange` dipakai sebagai identitas sekaligus peringatan utilisasi; caller warning perlu makna warning, bukan otomatis honey. Pertahankan alias sampai consumer yang terpengaruh disesuaikan. Dokumentasi sidebar 212 px bukan kontrak sidebar aplikasi 232 px.

### Komponen dan ikon

- Pertahankan props/model/emit shared components. Opsi outer surface pada PageLayout, bila dibutuhkan dashboard, harus default ke perilaku lama sampai caller dimigrasi.
- InputNumber tetap memakai model angka untuk field yang sekarang memerlukannya, sedangkan payload uang tetap string desimal sesuai API. Jangan memperkenalkan format display sebagai nilai request.
- Button/icon slot dan SVG Phosphor kompatibel. Mengganti string `pi pi-*` dengan nama symbol saja tidak merender sprite SVG. Gunakan komponen SVG/slot, termasuk ikon navigasi, loading, kalender, paginator dan dialog yang memang berada dalam scope. Rujukan: [PrimeVue custom icons](https://primevue.org/customicons).
- Native select tidak membuktikan style/keyboard popup PrimeVue Select. Overlay harus diperiksa di luar wrapper halaman karena Teleport.
- Jangan menghapus registry/service Toast, ConfirmationService, error handling atau validasi untuk menyamakan bentuk spesimen.

### Uang dan data contoh

Backend `operations/models/billing.py` memakai DecimalField 18 digit/2 desimal. `BayarTagihanInput` di `features/tagihan/api.ts:44` memerlukan tanggal, bukti, kode akun, `request_id`, total dan alokasi string. Form aktual tagihan mendukung hingga dua desimal, validasi sisa dan idempotency key. Form spesimen hanya nominal bulat dan tidak memiliki alokasi: ini contoh visual, bukan pengganti flow pembayaran.

Pemeriksaan runtime `formatRp(null)` dan `formatRp('invalid')` sama-sama menghasilkan **Rp 0**; fungsi existing tidak memenuhi aturan “belum diketahui” dengan sendirinya. Counterevidence: template tagihan sudah memeriksa `total_terbayar === null` dan `sisa_tagihan === null` sebelum memanggilnya. Guard itu wajib dipertahankan. Jangan mengganti helper global tanpa memeriksa caller; jangan menyalin ekspresi demo ke nullable field. Nilai desimal besar dan presisi seluruh pipeline belum diaudit pada review desain ini.

### Dashboard dan hak aksi

`roleHome` tetap Finance/Kepsek → `/dashboard`, TU → `/siswa`, Guru → `/kegiatan`. Kualitas setara tidak mensyaratkan membuat dashboard baru yang identik bagi semua role. Kegiatan memakai `canManage` untuk Kepsek dan `canRealisasi` untuk Guru/Kepsek; jurnal menggunakan `canCreate`, `canApprove`, sumber, rekonsiliasi, serta `can_finance_post`. Semua itu dipertahankan.

Periode panel perlu mengikuti endpoint-nya. `loadDashboard` mencampur ringkasan terfilter, chart tahunan, daftar jurnal, dan menu hari tertentu. Satu label periode global tidak membuktikan seluruh panel berubah cakupan. Kegagalan sebagian harus terlihat pada panel terkait; angka lama atau tidak tersedia tidak diberi tampilan seolah sudah mengikuti filter baru.

## Bukti pemeriksaan pada review ini

1. **Build dan integrasi entry — lolos kompilasi.** `npm run build` menyelesaikan vue-tsc dan Vite. Ada peringatan chunk aplikasi 662,14 kB yang sudah berasal dari build existing; tidak dianggap disebabkan token baru. Entry `design-system.html` juga dibundle ke `/private/tmp/beesmart-design-review-entry` tanpa perubahan config produksi.
2. **Probe komponen styled — berhasil mount, gaya belum cocok.** Vue/PrimeVue/BeePreset dari modul proyek digunakan untuk Button, Select, DataTable/Column dengan dua record lokal. Setelah CSS aplikasi dan spesimen hadir bersama, computed style tetap primary `#E5197F`, header `#F5EDD6`, Nunito/Baloo. Pagination berpindah dari Jurnal A ke Jurnal B. Ini membuktikan komponen bekerja dan konflik styling; bukan end-to-end app/API atau usulan tampilan final. [Screenshot probe](01-theme-compatibility-probe.png).
3. **Spesimen terpisah — interaksi dasar lolos.** Search menghasilkan 0 record untuk kata kunci yang tidak ada; dua density multiline terukur 72/60 px. Form menolak nol, membuka fokus di nomor bukti, menampilkan sukses contoh Rp 250.000 dan mengembalikan fokus setelah Escape. Grafik laba rugi menyertakan label aksesibel dan tabel enam bulan. [Screenshot fondasi saat review](02-system-current.png).
4. **Role dan mobile spesimen — contoh berubah sesuai role.** Empat tombol menghasilkan judul/metrik masing-masing. Pada 320 px, scroll width halaman = viewport 320 px dan input berukuran 16 px. Ini bukan verifikasi 23 view produksi atau perangkat ponsel nyata.
5. **Kontras token dan console — terbatas, lolos.** Tujuh pasangan opaque berada pada 5,40–15,20:1; tidak ada error/warning pada sesi halaman bersih setelah probe dimuat ulang. Ini bukan audit aksesibilitas penuh, semua chart palette, alpha overlay, screen reader atau printer.

Screenshot di atas dibuka dan diperiksa pada review ini. Probe bersifat sementara di browser; halaman bersih tidak mengimpor CSS aplikasi.

## Urutan agar siap dieksekusi

1. Selesaikan mapping BeePreset + shared CSS dan benturan font/radius/severity. Nilai hasil pada komponen nyata, bukan hanya swatch.
2. Lengkapi spesimen komponen yang dipakai aplikasi, dimulai DataTable/paginator, Select/DatePicker, form/error/loading, Tag/Message/Toast/ConfirmDialog; lanjut shell, ikon dan cetak. Reuse owner existing.
3. Buktikan satu layar kerja tiap role dengan akses/scope sebenarnya, termasuk draf vs persetujuan. Jangan memperluas ke 23 view sebelum pola ini konsisten.
4. Migrasi per modul mengikuti inventaris rencana revamp. Verifikasi route/query, request/payload, validasi, mobile/keyboard dan cetak pada modul yang berubah. Deploy hanya sebagai pekerjaan terpisah yang diotorisasi.

Kriteria sebelum migrasi luas: komponen styled memakai sumber token yang sama; tidak ada font/ikon/severity yang tercampur pada layar pilot; semua perilaku domain tetap sama; empat role memiliki prioritas yang benar; state gagal/kosong/memuat serta cetak utama mempunyai bukti pemeriksaan. Tidak perlu stack baru atau library UI tambahan untuk memenuhi kriteria ini.

## Tooling dan batas bukti

`ui-skills-root` digunakan untuk memilih audit berbasis source `improve-ui`; Ponytail membatasi perubahan pada laporan dan bukti. Context7 MCP berhasil membaca dokumentasi resmi PrimeVue untuk preset dan SVG icons. Playwright MCP menjalankan probe/interaksi lokal dalam browser terisolasi. Tidak ada manfaat tambahan membuka Mobbin atau situs inspirasi lagi untuk membuktikan kompatibilitas kode.

Tidak menjalankan test suite, memasang dependency, mengubah source produk, mengakses akun sekolah, atau mengubah data. Belum memverifikasi integrasi live API, multi-role dengan akun asli, cetak/PDF nyata, Safari/iPad, pembaca layar, zoom seluruh view, atau semua state 23 halaman. Head teramati `045bfdd`; source desain/preview masih untracked dan review ini merujuk working tree, bukan hanya commit tersebut.
