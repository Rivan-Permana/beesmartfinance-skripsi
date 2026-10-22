> Pembaruan 18 Oktober 2026: fondasi 0.11 mencakup Siswa dan Tagihan/pembayaran TU serta Kegiatan Guru/Kepsek, Jurnal Finance/Kepsek dan kelima laporan keuangan, Absensi siswa TU dan Rekap TU/Guru, serta Katering/Jemputan TU UI Pendaftaran calon, serta Gaji/Kasbon Finance melalui komponen aplikasi; spesimen tetap referensi pendamping. Review utama kini melalui aplikasi localhost. Termasuk interaksi shared, locale, recovery, dan tanggal lokal. Sudah diperiksa dengan build, tes terarah dan API fixture browser terisolasi; belum dideploy. Bukti dan batas backend: `design-artifacts/bee-design-system/README.md`. Berikutnya modul lain dalam inventaris 23 view. Pendaftaran diperiksa dengan fixture serta pembacaan data localhost setelah pengguna menyetujui backup dan migrasi existing 0011–0013; 160 tagihan lama ditandai untuk rekonsiliasi sesuai aturan migrasi.

# BeeSmart Finance — rencana implementasi revamp UI/UX

**Tanggal:** 15 Oktober 2026, WIB. **Status terbaru:** eksekusi lokal per modul berjalan; acuan sekarang [sistem desain 0.13](../../../design-artifacts/bee-design-system/README.md) dan [halaman fondasi interaktif](http://127.0.0.1:4173/design-system.html). Preview sebelumnya tersedia sebagai pembanding; fondasi tema/shell dan dashboard sudah masuk source aplikasi lokal; belum dideploy atau selesai untuk seluruh modul.

**Goal:** memoles keseluruhan UI/UX BeeSmart untuk empat peran secara seimbang, dengan identitas Lebah Madu yang lebih tertata dan informasi transaksi yang tetap akurat.

**Architecture:** pertahankan Vue SPA, route/RBAC, API, dan komponen PrimeVue. Perubahan bergerak dari token dan komponen bersama ke contoh layar empat peran, kemudian per kelompok modul. Tampilan baru meneruskan arsitektur yang ada; tidak memerlukan rewrite frontend atau perubahan skema data.

**Tech stack teramati:** Vue 3, TypeScript, Vite, PrimeVue 4/Aura melalui `@primeuix/themes`, PrimeIcons, Pinia, Vue Router, Chart.js. Versi di `package.json` adalah deklarasi dependency, bukan bukti versi yang sedang berjalan di produksi.

**Spec terbaru:** [sistem desain 0.13](../../../design-artifacts/bee-design-system/README.md), dengan [panduan implementasi dan pemetaan source](../../design-system.md). [Arah desain dan audit awal](../../../design-artifacts/revamp-2026-10-15/design-direction.md) menyimpan riwayat usulan. Inventaris route dan kontrak perilaku di bawah tetap berlaku; keputusan visual lama mengikuti fondasi baru setelah dinilai cocok. Checkbox wave di bawah adalah rencana awal, bukan tracker progres terkini; gunakan coverage 0.13. Catatan tanpa pemeriksaan pada tahap awal adalah catatan historis, bukan status pemeriksaan artefak terbaru.

## Batas pelaksanaan

- Saat rencana awal disusun, lingkupnya audit, referensi dan perencanaan. Pengguna kemudian mengotorisasi implementasi lokal dan verifikasi bertahap; coverage 0.10 dirangkum pada spesifikasi. Deployment belum dilakukan.
- Penyusunan rencana awal tidak menjalankan tes. Pemeriksaan implementasi berikutnya dicatat per versi pada spesifikasi; skenario di bawah tidak otomatis menjadi bukti lulus.
- Tidak memasang dependency, membuat branch/worktree/commit, login ke akun sekolah, mengubah data, atau mengatur layanan eksternal untuk menyusun rencana ini.
- Pertahankan perubahan lokal pengguna. Saat audit sudah ada perubahan/untracked pada dokumentasi, `_bmad-output`, dan skrip; dokumen revamp dibuat terpisah.
- Reuse `formatRp`, `notifyError`/`notifySuccess`, API modul, auth store, dan pola validasi existing. Tidak merombak service backend sebagai bagian polish.
- Nama route, query `jenis=masuk|keluar`, role home, HTTP payload, idempotensi pembayaran, aturan posting/reversal, dan scope laporan adalah kontrak yang dipertahankan.
- Jangan mengisi nominal/tanggal saldo awal atau tarif pendaftaran/SPP berdasarkan dugaan. `null` yang berarti belum diketahui tetap dibedakan dari nol.
- Jangan menghapus proteksi periode tertutup, alasan pembatalan, konfirmasi destruktif, penanda rekonsiliasi, atau riwayat transaksi untuk menyederhanakan layar.

## Cakupan seluruh route

Pemetaan berasal dari `frontend/src/core/router.ts` dan `navigation.ts`. F = Finance, A = Administration, P = SchoolPrincipal, G = TeacherInCharge. Semua path file pada tabel berikut relatif ke `frontend/src/features/`.

| Route | Akses route saat ini | File | Fokus desain | Wave |
|---|---|---|---|---|
| `/login` | Publik | `auth/LoginView.vue` | Identitas, form, label, error, loading | 1 |
| `/dashboard` | F/P | `dashboard/DashboardView.vue` | Hierarki metrik, cakupan, perhatian per peran | 2 |
| `/jurnal` | F/P | `jurnal/JurnalListView.vue` | Alias masuk/keluar, status, form baris, aksi sesuai izin | 2 |
| `/tagihan` | A | `tagihan/TagihanListView.vue` | Daftar, pembayaran/alokasi, rincian, riwayat, batch | 2 |
| `/kegiatan` | P/G | `kegiatan/KegiatanListView.vue` | Pengelolaan P, realisasi G/P, pagu dan laporan | 2 |
| `/absensi-siswa` | A | `absensi/AbsensiSiswaView.vue` | Konteks tanggal/kelompok, chip, simpan | 2 |
| `/siswa` | A | `siswa/SiswaListView.vue` | Daftar dan form profil | 3 |
| `/kelompok` | A | `kelompok/KelompokListView.vue` | Jenjang, kelompok, perpindahan | 3 |
| `/rekap-siswa` | A/G | `absensi/RekapSiswaView.vue` | Rekap terbaca dan akses G read-only | 3 |
| `/pendaftaran` | A | `pendaftaran/PendaftaranListView.vue` | Biaya, penerimaan, finalisasi yang terpisah | 3 |
| `/katering` | A | `katering/KateringView.vue` | Jadwal, foto/menu, tarif, rekap | 3 |
| `/jemputan` | A | `jemputan/JemputanView.vue` | Armada, pendaftaran, rekap/ekspor | 3 |
| `/tunggakan-tagihan` | F/P | `tagihan/TunggakanTagihanView.vue` | Sisa dan rekonsiliasi, read-only | 4 |
| `/coa` | F/P | `coa/CoaListView.vue` | Hirarki akun, saldo awal/tanggal, status aktif | 4 |
| `/anggaran` | F/P | `anggaran-periode/AnggaranListView.vue` | Pagu/realisasi dan periode | 4 |
| `/periode` | F/P | `anggaran-periode/PeriodeListView.vue` | Status dan konsekuensi tutup buku | 4 |
| `/laporan` | F/P | `laporan/LaporanView.vue` | Scope tiap laporan, tabel, print/CSV | 4 |
| `/audit-log` | F/P | `audit/AuditLogView.vue` | Ringkasan perubahan, filter, detail teknis | 4 |
| `/pegawai` | A/F | `kepegawaian/PegawaiListView.vue` | Profil dan masa kerja; menu F saat ini tersembunyi | 5 |
| `/absensi-pegawai` | A/F | `kepegawaian/AbsensiPegawaiView.vue` | Grid dan ringkasan; menu F saat ini tersembunyi | 5 |
| `/gaji` | F | `kepegawaian/GajiListView.vue` | Komponen, status posting, slip | 5 |
| `/pinjaman` | F | `kepegawaian/PinjamanListView.vue` | Kasbon, pencairan dan status | 5 |
| `/aset` | F | `aset/AsetListView.vue` | Identitas aset, nilai dan penyusutan | 5 |

Alias `/absensi` tetap mengarah ke `/absensi-siswa`. `/jurnal?jenis=masuk` dan `/jurnal?jenis=keluar` berbagi view, bukan dua route baru. Home kosong `/` tetap memakai `roleHome`.

## Urutan rollout dan tugas konkret

Urutan: `0 → 1 → 2 → 3 → 4 → 5 → 6`. Wave 2 mencakup contoh empat peran sebelum migrasi massal; wave selanjutnya tetap mendapat baseline bersama sejak wave 1. Wave berarti paket implementasi, bukan izin melakukan deployment otomatis.

### Wave 0 — tutup celah bukti dan pilih arah

**Files:** baca `core/router.ts`, `core/navigation.ts`, halaman pilot; perbarui `design-artifacts/revamp-2026-10-15/design-direction.md`. Artefak mockup selanjutnya ditempatkan pada folder desain yang sama.

- [ ] Pilih arah visual berdasarkan rekomendasi A dan respons pengguna; catat sidebar, tipografi, serta density yang disepakati.
- [ ] Lakukan walkthrough baca-saja pada lingkungan yang tersedia, dengan empat konteks role yang sah. Jika akses tidak tersedia, gunakan fixture lokal berlabel contoh; pisahkan bukti fixture dari bukti produksi.
- [ ] Catat baseline screenshot desktop/tablet/mobile untuk halaman pilot, state kosong/error, dan overlay. Jangan memakai kredensial dari laporan atau menerbitkan data siswa ke layanan referensi.
- [ ] Buat mockup empat konteks role dan absensi tablet: tabel tagihan + pembayaran, jurnal, dashboard Kepsek, kegiatan Guru. Gunakan struktur referensi Mobbin dalam spec.
- [ ] Putuskan dialog atau panel samping hanya dari mockup yang menunjukkan keuntungan nyata. Default implementasi tetap Dialog agar perubahan state dan print minimal.

**Hasil:** brief visual yang dapat direview dan daftar temuan runtime yang dibedakan dari audit sumber. Tidak mengasumsikan preferensi perangkat atau masalah pengguna sudah terbukti.

### Wave 1 — fondasi, shell, dan login

**Modify:** `frontend/src/core/theme.ts`, `frontend/src/assets/main.css`, `frontend/src/assets/primevue-overrides.css`, `frontend/src/shared/layout/AppShell.vue`, `frontend/src/shared/components/{PageLayout,SearchField,PeriodPicker,EmptyState,KpiCard,ChartPanel,RingGauge}.vue`, `frontend/src/shared/error/{CrashView,ErrorBoundary}.vue` bila markup pemulihannya memerlukan penyesuaian, `frontend/src/features/auth/LoginView.vue`, `frontend/index.html` bila pemuatan font berubah.

**Read/preserve:** `frontend/src/main.ts`, `frontend/src/App.vue`, `frontend/src/core/{navigation,router,format,errors}.ts`, `frontend/src/stores/auth.ts`.

**Interfaces:** pertahankan prop/emit existing komponen bersama. `PageLayout` tetap menerima `title`, `subtitle`, slot `actions`, `filters`, dan default; tambahkan hanya `surface?: boolean` dengan default `true`, lalu dashboard menggunakan `:surface="false"` untuk menghindari kartu luar. `SearchField` mempertahankan v-model/hint/block; `PeriodPicker` mempertahankan model bulan/tahun dan rentang tahun.

- [ ] Terapkan token yang dipilih pada BeePreset dan CSS aplikasi; gunakan semantic/component tokens PrimeVue untuk skin yang didukung. Pisahkan magenta brand dari danger. Pertahankan alias CSS lama selama caller belum dimigrasi.
- [ ] Tinjau seluruh bagian `primevue-overrides.css`, termasuk print; pindahkan hanya skin yang memang sudah terwakili token, jangan menghapus override secara massal.
- [ ] Rapikan shell, nav aktif, breadcrumb query jurnal, tooltip/nama aksesibel saat collapsed. Reuse `navForRoles`/`groupedNav`, tanpa mengubah daftar izin atau role home.
- [ ] Gunakan Drawer PrimeVue untuk navigasi mobile; label tetap terlihat walau state desktop collapsed. Focus-return, Escape, scroll, dan penutupan saat navigasi tetap jelas.
- [ ] Terapkan prop surface dan susunan filter; lebar search mengikuti ruang, bukan dipaksa penuh pada semua desktop.
- [ ] Rapikan komponen ringkasan/empty/chart dan pemulihan error; jangan membuat framework komponen baru. Pertahankan public props sampai semua caller diperiksa.
- [ ] Hubungkan label login dengan input, tetapkan hierarki brand/form, dan pertahankan autocomplete, loading, pesan gagal, serta redirect `next` yang ada.

**Hasil:** seluruh aplikasi memakai baseline visual baru; shell, dialog, tabel, login, dan pemulihan error konsisten. Hasil ini belum berarti semua flow modul sudah dipoles.

### Wave 2 — terapkan pola pada empat peran

**Modify:** `frontend/src/features/dashboard/{DashboardView.vue,chartTheme.ts}`, `frontend/src/features/jurnal/JurnalListView.vue`, `frontend/src/features/tagihan/TagihanListView.vue`, `frontend/src/features/kegiatan/KegiatanListView.vue`, `frontend/src/features/absensi/{AbsensiSiswaView,AttendanceGrid}.vue`.

**Interfaces:** payload dan endpoint existing tetap dipakai. Pertahankan `AttendanceRow`, prop `students/modelValue/readonly` dan emit `update:modelValue/delete`. Chart tetap memakai Chart.js. Predikat `canManage`, `canRealisasi`, `canCreate`, `canApprove`, serta `can_finance_post` tetap menjadi dasar aksi.

- [ ] Dashboard: tampilkan metrik inti satu kali, lalu panel perhatian dan analisis; visual Finance/Kepsek menonjolkan tugas yang memang diizinkan. Semua data analisis tetap dapat diakses tanpa memenuhi area pertama dengan setiap chart.
- [ ] Selaraskan label antrean jurnal dengan data: panel DRAFT bernama “Jurnal draf”; bila Kepsek membutuhkan panel persetujuan, gunakan query PENDING yang sudah didukung dan tampilkan konteks kelayakan approval. Jangan menyebut DRAFT sebagai PENDING atau membuat hitungan dari lima preview row.
- [ ] Nyatakan cakupan masing-masing metrik/chart. Dashboard memuat sumber tahunan, periodik, dan menu hari ini; jangan membuat satu label periode seolah mengubah semuanya. Pertahankan partial-failure handling dan tandai panel yang datanya gagal/masih dari cakupan lama.
- [ ] Tagihan: rapikan list dan susunan aksi tanpa menghilangkan pembayaran sebagian, batch, riwayat, editor, atau cetak. Pada form bayar, identitas siswa, periode, alokasi, total/sisa, dan bukti berada dalam satu konteks yang jelas.
- [ ] Jurnal: rapikan form multi-baris, label input, indikator balance dan aksi per status. Route alias tetap satu view; tooltip/copy menerangkan konsekuensi posting/pembatalan.
- [ ] Kegiatan: tampilkan PIC, tanggal, status, pagu, realisasi dan sisa dengan hierarki yang jelas. Guru melihat realisasi/laporan; pengelolaan kegiatan tetap milik Kepsek.
- [ ] Absensi: rapikan urutan pemilihan dan grid sentuh, penanda status, konteks tanggal/kelompok serta feedback simpan; jangan mengubah hubungan status hadir dengan flags layanan.

**Hasil:** lima halaman pilot dapat menjadi contoh pola yang lengkap, dengan satu konteks nyata untuk setiap peran. Usability dan perilaku belum dinyatakan lulus tanpa verifikasi tahap berikutnya.

### Wave 3 — operasional siswa dan pendaftaran

**Modify:** semua file view wave 3 pada inventaris; `frontend/src/shared/utils/tahunPelajaran.ts` hanya dibaca kecuali ada kebutuhan tampilan yang jelas. Caller terkait: `frontend/src/features/katering/legacyExport.ts`, API siswa/kelompok/absensi/katering/jemputan/pendaftaran, dan helper pencarian.

- [x] Terapkan pola toolbar/table/form ke siswa dan kelompok; pertahankan perpindahan kelompok dan riwayat yang tersedia.
- [ ] Rapikan rekap siswa tanpa membuka kontrol edit untuk Guru; label tanggal/jenis rekap dan ekspor harus jelas.
- [ ] Pendaftaran: bedakan status calon, komponen biaya, penerimaan, dan finalisasi. Record `perlu_rekonsiliasi` tidak diberi total/sisa palsu; biaya/SPP kosong tetap kosong sampai diisi.
- [ ] Katering: pertahankan simpan foto saja, teks saja, atau keduanya; jadwal mingguan, tarif, preview gambar, error upload, dan cleanup URL tetap bekerja seperti sebelumnya.
- [ ] Jemputan: pertahankan pemisahan armada, pendaftaran, dan rekap; navigasi tab, identitas siswa dan aksi menjadi konsisten.
- [ ] Samakan loading, empty, filtered-empty, error dan copy. Periksa scope search/pagination sebelum menambah filter; jangan menyebut search seluruh sekolah jika hanya menyaring halaman API aktif.

**Hasil:** seluruh operasional A dan rekap G konsisten dengan halaman pilot, tanpa mengganti aturan pembayaran/finalisasi atau tarif.

### Wave 4 — keuangan, laporan, dan governance

**Modify:** semua file view wave 4 pada inventaris; `frontend/src/features/audit/auditFormat.ts` hanya jika diperlukan untuk label presentasi. **Read:** `frontend/src/features/{laporan,coa,anggaran-periode,tagihan}/api.ts` serta tipe terkait.

- [x] Tunggakan: tampilkan sisa yang diketahui dan jumlah record perlu rekonsiliasi secara terpisah. Jangan menafsirkan null sebagai utang nol atau menambah tombol pembayaran untuk F/P.
- [x] COA: rapikan hierarki akun; urutan aktif/saldo awal, tanggal wajib untuk nilai bukan nol, saldo negatif, dan peringatan keseimbangan tetap terlihat.
- [x] Anggaran/periode: tampilkan periode, status dan konsekuensi aksi dengan jelas; tidak menghilangkan konfirmasi tutup buku atau memperluas akses.
- [x] Laporan: label cakupan masing-masing tab mengikuti endpoint aktual. Bedakan filter yang dipilih dengan hasil yang sudah diterapkan agar judul/cetak tidak mengklaim periode baru saat data masih lama.
- [x] Audit: utamakan siapa/mengubah apa/kapan dengan nilai sebelum-sesudah; detail teknis tetap bisa dibuka sesuai akses, tanpa menambah data pribadi ke ringkasan.

**Hasil:** Finance/Kepsek dapat membaca angka dan status dengan konsisten, termasuk data yang belum siap dianggap final.

### Wave 5 — pegawai, payroll, kasbon, dan aset

**Modify:** semua file view wave 5 pada inventaris dan `frontend/src/features/kepegawaian/StaffAttendanceGrid.vue`. **Read/preserve:** API kepegawaian/aset dan `frontend/src/features/kepegawaian/GajiSlipPreview.vue` untuk kontrak cetak wave 6.

- [x] Rapikan profil/masa kerja dan absensi pegawai dengan pola form/grid bersama, tanpa mengubah akses route/menu.
- [x] Slip gaji: kelompokkan komponen dan total; bedakan draft, edit dan posting. Alokasi/potongan pinjaman existing dipertahankan.
- [x] Kasbon: identitas pegawai, nominal, status dan pencairan jelas; aksi tetap mengikuti status dan validasi sekarang.
- [x] Aset: tampilkan nilai, tanggal, masa manfaat dan aksi penyusutan tanpa menyederhanakan perhitungan atau menghilangkan konfirmasi.

**Hasil:** modul pendukung mendapat kualitas yang sama dengan operasional siswa dan keuangan inti.

### Wave 6 — cetak, konsistensi akhir, dan kesiapan rilis

**Modify bila diperlukan:** `frontend/src/features/tagihan/InvoicePreview.vue`, `frontend/src/features/kepegawaian/GajiSlipPreview.vue`, `frontend/src/features/laporan/LaporanView.vue`, CSS print pada `frontend/src/assets/{main,primevue-overrides}.css`, serta dokumentasi desain/frontend yang akhirnya disepakati.

- [ ] Selaraskan invoice/slip/laporan dengan identitas baru tanpa mengubah rincian transaksi, total, atau penanda status/reconciliation.
- [ ] Pertahankan `bee-print-struk`, cleanup `afterprint`/unmount, dan pemisahan elemen screen/print. Pastikan perubahan Dialog tidak menghilangkan isi cetak.
- [ ] Lakukan inventaris ulang seluruh route dan state; samakan ejaan/copy, heading, icon-label, fokus, nominal dan empty state.
- [ ] Rekonsiliasi DESIGN/EXPERIENCE Juni dan frontend guide setelah arah baru disepakati. Jangan menandai dokumentasi lama sebagai baru/final pada tahap draft ini.
- [ ] Bila pengguna meminta verifikasi, jalankan pemeriksaan terarah di bawah; catat bukti dan batas perangkat. Bila pengguna kemudian meminta rilis, gunakan alur deployment proyek yang ada dengan pasangan versi frontend/backend yang kompatibel.

**Hasil:** paket revamp siap direview untuk rilis. Rollback perubahan UI memakai versi frontend sebelumnya yang kompatibel; tidak membutuhkan rollback database karena rencana ini tidak mengubah skema/API. Jangan mencampur rollback UI dengan rollback perubahan aplikasi lain yang belum terkait.

## Skenario verifikasi untuk tahap yang diotorisasi berikutnya

Daftar ini merupakan kriteria penerimaan rencana, bukan laporan pengujian. Tidak ada tes/build/browser automation yang dijalankan untuk menyusun dokumen ini.

| Fokus | Kondisi | Perilaku yang diharapkan | Pemilik wave |
|---|---|---|---|
| Route/role | Empat role, multi-role, link langsung/alias, role tanpa izin | Home/guard tetap benar; menu dan aksi tidak meluas | 1/2 |
| Navigasi | Jurnal masuk/keluar, sidebar collapsed, lalu viewport mobile | Breadcrumb tepat, label tersedia, Drawer fokus/Escape benar | 1 |
| Uang/transaksi | Nol, negatif, null, nominal besar, pembayaran sebagian/ulang | Tidak ada nilai palsu/truncation; validasi/idempotensi tetap berlaku | 2/3/4 |
| State | Gagal API sebagian, hasil filter kosong, data belum ada | Error berbeda dari nol/kosong; input tidak hilang; cakupan hasil jujur | Semua |
| Hak aksi | Finance posting, PENDING khusus, POSTED, rekonsiliasi, periode tertutup | Hanya aksi yang sah tersedia; data final tidak jadi editable | 2/4/5 |
| Pendaftaran | Finalisasi sebelum/sesudah penerimaan, biaya kosong, data lama | Tidak membuat penerimaan otomatis; null dan tarif tidak ditebak | 3 |
| Absensi | Tidak hadir, flag layanan, nama panjang, Guru read-only | State domain tetap benar; identitas tidak terpotong | 2/3/5 |
| Cakupan laporan | Pilih periode tanpa Terapkan; tab tahunan vs bulanan | Angka, judul, cetak dan ekspor menyebut scope data yang benar | 2/4 |
| Responsive/a11y | 1440/1024/768/390/360 px, keyboard, zoom 200% | Nominal/aksi tetap terbaca, scroll tabel lokal, label/focus/status jelas | Semua |
| Cetak | Invoice, slip, laporan panjang, cetak dibatalkan lalu diulang | Isi lengkap, shell tersembunyi, cleanup print benar | 6 |

**Pemeriksaan existing yang relevan bila nanti diminta:** `core/navigation.test.ts`, `core/router.guard.test.ts`, `core/format.test.ts`, `features/tagihan/api.test.ts`, `features/pendaftaran/PendaftaranListView.test.ts`, `features/coa/CoaListView.test.ts`, `features/katering/KateringView.test.ts`, `shared/composables/useTableSearch.test.ts`. Tidak mengubah assertion hanya agar perilaku lama yang rusak terlihat lulus. Build/typecheck: script existing `npm run build` dari `frontend/`. Skenario interaksi baru diarahkan hanya ke perilaku yang berubah, bukan snapshot semua CSS.

## Risiko dan keputusan yang perlu dibawa ke pelaksanaan

1. **Global CSS menjangkau semua halaman dan print.** Ubah token/shell terlebih dahulu, jangan menumpuk override baru tanpa memeriksa caller dan tampilan cetak.
2. **Label finansial dapat menyesatkan walaupun angka tidak berubah.** Cakupan tahunan/bulanan, DRAFT/PENDING/POSTED, serta null/rekonsiliasi harus mengikuti data aktual.
3. **Akses guru dan Finance berbeda dari sebagian dokumen lama.** Pertahankan kode/permission saat ini; usulan perubahan kewenangan dipisahkan dari revamp.
4. **Belum ada keluhan usability atau baseline terukur.** Rekomendasi hierarki dan panel detail merupakan hipotesis desain; ukur lewat walkthrough, jangan klaim hasil efisiensi.
5. **Belum ada review runtime/perangkat pada sesi ini.** Safari/iPad, keyboard ponsel, printer fisik, dan koneksi lambat tetap membutuhkan bukti terpisah saat verifikasi diminta.

Langkah berikut per 18 Oktober 2026: Gaji/Kasbon 0.11, Data pegawai/Absensi pegawai 0.12, dan Aset 0.13 sudah masuk aplikasi localhost. Lanjutkan modul administrasi/keuangan lain yang tersisa pada inventaris, lalu konsistensi dan cetak wave 6. Pendaftaran 0.10 dan migrasi localhost yang disetujui pengguna sudah selesai. Usulan awal memilih arah/mockup empat peran sudah dilanjutkan ke implementasi lokal. Tidak diperlukan rewrite stack atau dependency baru untuk meneruskan revamp.

## Perkembangan preview pertama

Bagian ini sampai akhir dokumen menyimpan riwayat preview 15 Oktober, bukan status integrasi terkini. Gunakan ringkasan 0.12 dan spesifikasi di atas untuk menentukan pekerjaan tersisa.

Pengguna meminta mengikuti plan dan langsung memperlihatkan hasil tanpa memerlukan Pen.dev. Arah A diterapkan pada [preview dashboard HTML](../../../design-artifacts/revamp-2026-10-15/dashboard-preview.html), dengan logo existing, sidebar terang, empat metrik tanpa pengulangan, arus kas, tindak lanjut, tabel tunggakan read-only, jurnal draf, dan rincian yang dapat dibuka melalui disclosure native.

Preview memakai angka/nama contoh yang diberi label, tidak memanggil API dan tidak melakukan transaksi. Halaman contoh memakai konteks Finance; home dan layar peran lain belum dibuat. Menu modul yang belum dibuat berupa teks noninteraktif; tautan dalam preview menuju bagian halaman. Periode masih statis. Belum ada integrasi ke router/theme/frontend produksi.

Preview dibuka dan dilihat secara visual melalui browser terisolasi pada 1440 px dan 390 px. [Screenshot desktop](../../../design-artifacts/revamp-2026-10-15/dashboard-desktop.png) dan [mobile](../../../design-artifacts/revamp-2026-10-15/dashboard-mobile.png) disimpan bersama mockup. Ini pemeriksaan visual mockup, bukan bukti fungsi aplikasi, browser matrix, aksesibilitas menyeluruh, atau hasil tes otomatis. Tidak menjalankan tes/build/deployment.

## Preview kedua dan arahan tambahan

Pengguna menekankan kelengkapan dashboard, empat peran, ikon Phosphor, copy, arsitektur informasi, dan standardisasi. Pengguna juga meminta empat sumber referensi baru dipelajari dan dimasukkan ke rules global; penambahan pada `~/.codex/AGENTS.md` sudah dilakukan tanpa menghapus aturan sebelumnya.

- Preview aktif sekarang memakai entry terpisah `frontend/dashboard-preview.html` dan Vue/PrimeVue/Chart.js existing. Entry produksi dan backend tetap utuh. Server development berjalan pada `http://127.0.0.1:4173/dashboard-preview.html`.
- Selector preview mencakup Finance, Kepsek, Staf Tata Usaha, dan Guru PIC. Ketujuh layar contoh beserta dua alias jurnal mengikuti metadata akses existing; ini belum menyelesaikan 23 layar produksi.
- Dashboard mencakup arus kas, pendapatan/beban, komposisi yang dapat dipilih, pagu/realisasi, tren kehadiran, dan anggaran kegiatan untuk Kepsek. Grafik memakai dataset fixture, tooltip dan tabel angka yang sama; tidak mengganti null dengan nol atau kas dengan pendapatan.
- Ikon preview memakai 38 SVG regular Phosphor resmi dengan lisensi lokal. Penggunaan PrimeIcons pada aplikasi utama belum dimigrasi; tambahkan pemetaan seluruh caller pada wave implementasi, lalu hapus dependency hanya setelah tidak dipakai.
- [Standar UI, IA, copy, ikon dan chart](../../../design-artifacts/revamp-2026-10-15/ui-standards.md) menjadi referensi tambahan wave 1–6. Metadata label/ikon/taxonomy dan token terpusat di folder preview untuk dipromosikan sesuai kebutuhan implementasi.
- Typecheck dan build berhasil setelah perbaikan tipe opsi Chart.js. Tidak menjalankan suite tes atau deployment. Peringatan chunk aplikasi utama >500 kB masih ada; performa runtime belum diukur.

Artefak screenshot versi kedua: `dashboard-finance-v2.png`, `dashboard-principal-v2.png`, `admin-siswa-v2.png`, `guru-kegiatan-v2.png`, dan `dashboard-mobile-v2.png`. HTML/screenshot versi pertama disimpan sebagai riwayat visual, bukan preview terkini.


### Pembaruan preview v3 — 15 Oktober 2026

Pengguna meminta pemisahan relevansi informasi per role dan komposisi yang lebih matang. Finance sekarang berfokus pada kas, jurnal draf, komposisi dan tunggakan; Kepsek pada persetujuan, kondisi keuangan dan anggaran/kegiatan. Kehadiran hanya di rekap TU/guru. Home TU/guru mendahulukan daftar tugas domain mereka. Penghitungan jumlah/nominal memakai fixture yang ditampilkan, tidak memakai jumlah dekoratif.

Detail kontrak role, bukti verifikasi, dan batas keamanan ada di `design-artifacts/revamp-2026-10-15/ui-standards.md` bagian revisi ketiga. Typecheck/build dan pemeriksaan browser role/mobile lulus. Preview tetap belum terintegrasi dengan API atau seluruh 23 view. Scope per-PIC pada backend belum dipastikan sebagai kebutuhan; jangan mengubah role/permission hanya untuk mengikuti mockup.


### Pembaruan alur jurnal v5 — 15 Oktober 2026

Preview Finance/Kepsek kini memakai shell navy konsisten. Dashboard dapat membuka draf tertentu; daftar jurnal menyediakan pencarian, bulan, status, rincian akun dan form debit/kredit. Simulasi buat/ubah draf, konfirmasi pencatatan dan hasil berjalan di memori. Jurnal otomatis dan jurnal tercatat tidak diberi edit; jalur jurnal khusus tetap berbeda dari pencatatan Finance. Mobile menampilkan nominal/status/tindakan tanpa perlu menggeser tabel daftar.

Typecheck/build dan pemeriksaan browser alur/role, nominal, validasi, penjagaan perubahan dan fokus telah dijalankan. Batas serta bukti ada di `design-artifacts/revamp-2026-10-15/ui-standards.md` bagian v5. Integrasi aplikasi/API produksi dan 23 view tetap belum dimulai.


### Pembaruan alur tagihan v6 — 15 Oktober 2026

Preview TU kini mempunyai pembayaran per komponen, pemeriksaan sebelum simpan, hasil dan riwayat yang berubah di memori. Pembayaran sebagian/pelunasan mengikuti sisa komponen; data yang belum terverifikasi diblokir. Finance/Kepsek tetap baca-saja. Siswa mempunyai tautan tagihan per NIS. Tema bersama sudah konsisten di home keempat role.

Stylesheet studi diganti menjadi `workspace-theme.css`; pola drawer/form/feedback/result dipakai bersama melalui `workflow-preview.css`. Build dan pemeriksaan browser alokasi, duplikasi, null, role, fokus dan mobile lulus. Detail bukti/batas ada pada bagian v6 di `design-artifacts/revamp-2026-10-15/ui-standards.md`. Realisasi kegiatan, perluasan sisa layar dan integrasi API produksi masih menjadi tahap berikutnya.
