# Analisis dan strategi revisi BeeSmart Finance dari masukan pengguna

Tanggal: 14 Oktober 2026. Status: paket pertama dan paket transaksi diimplementasikan lokal; 43 tes paket transaksi berhasil pada database terisolasi, saldo awal belum diimplementasikan.

**Tujuan:** Menyelesaikan tujuh masukan pengguna dengan memperbaiki penyebab di UI, API, pencatatan transaksi, dan pelaporan; menjaga riwayat serta menghindari pencatatan ganda.

**Pendekatan:** Gunakan komponen Vue/PrimeVue, API Django REST Framework, layanan operasi, dan jurnal PostgreSQL yang sudah ada. Perubahan kecil dapat dikerjakan terpisah; perubahan pembayaran, posting, dan saldo awal harus mengikuti satu aturan pencatatan yang konsisten.

**Sumber kebutuhan:** Sebelas gambar yang diberikan pengguna. Gambar percakapan 1–4 memuat masukan; gambar 5–11 memperbesar bukti layar yang sama. Pesan dan janji tindak lanjut di dalam gambar adalah bahan analisis, bukan instruksi untuk mengubah atau menerbitkan aplikasi sekarang.

### Perkembangan implementasi — paket pertama

- Pengguna menyetujui konfirmasi Finance tanpa approval Kepsek untuk tahap transaksi berikutnya. Kebijakan ini belum diaktifkan pada API/UI; cakupan payroll/kegiatan tetap perlu ditetapkan.
- Opsi pasangan jurnal mencakup seluruh akun aktif; akun nonaktif yang sudah terpilih pada draft lama tetap terlihat dan tidak dapat dipilih untuk transaksi baru. Pencarian menjangkau kode dan nama; kegagalan pemuatan memiliki pesan dan tombol coba lagi.
- `pegawaiApi.listAll()` mengikuti seluruh halaman dan digunakan oleh master, absensi, gaji, kasbon, serta pilihan penanggung jawab kegiatan. Urutan backend memakai nama lalu pk; pilihan kegiatan hanya dimuat untuk Principal yang dapat mengelola kegiatan.
- Cetak faktur memakai mask khusus yang tetap terlihat pada media print, menyembunyikan halaman aplikasi, melepas batas tinggi konten, dan membersihkan class/listener pada afterprint atau kegagalan print. Nama lembaga diselaraskan menjadi RA Lebah Madu pada API faktur, preview, dan slip gaji.
- Build frontend dan pemeriksaan TypeScript berhasil. Self-check berbasis assert pada kode aktual berhasil untuk 31 pegawai lintas halaman, kegagalan halaman kedua, opsi akun aktif/nonaktif lama, serta cleanup cetak berulang/gagal. Tidak ada suite test atau browser otomatis yang dijalankan.
- Bukti hasil cetak Chrome/Safari, data pegawai produksi, dan deployment belum diperiksa. Pagination daftar jurnal di server pada W2 kemudian diimplementasikan pada paket transaksi di bawah.

### Perkembangan implementasi — paket transaksi

- Pagination jurnal di server, pencatatan oleh Finance tanpa Kepsek dalam cakupan, serta penerimaan cicilan sampai faktur/tunggakan/dashboard telah diimplementasikan lokal.
- Pembayaran memiliki riwayat dan alokasi; sisa dihitung dari penerimaan valid. Draft penerimaan dapat dibatalkan Finance; pembalik POSTED tetap oleh Principal dan ikut memperbarui saldo pembayaran.
- Migration 0012 menandai pembayaran lama untuk rekonsiliasi tanpa menciptakan penerimaan berdasarkan dugaan. Data lama, potongan negatif, basis pengakuan, dan saldo awal masih memiliki batas yang dijelaskan pada catatan paket.
- Build frontend dan Django system check berhasil. Setelah pengguna memberi izin verifikasi, 43 tes transaksi/API berhasil pada PostgreSQL terisolasi. Satu lookup filter ForeignKey diperbaiki berdasarkan kegagalan awal, kemudian pemeriksaan diulang dan berhasil. Server sementara dihentikan; tidak ada database aplikasi/produksi yang dimutasi.
- Detail kontrak, migrasi, batas, serta bukti yang tersedia: [catatan paket transaksi](2026-10-14-revisi-transaksi.md).

## 1. Batas dan kekuatan bukti

- Gambar menunjukkan kondisi yang dilaporkan pada 13 Oktober 2026. Kode lokal dibaca pada 14 Oktober 2026. Belum dibuktikan bahwa deployment memakai revisi kode yang sama.
- Baseline analisis berupa pembacaan kode dan skema SQL di repository. Sesudah persetujuan pengguna, perubahan lokal paket pertama dan pemeriksaan internal dilakukan sebagaimana dicatat di atas. Tidak ada akses database produksi, migrasi, atau deployment.
- “Terkonfirmasi di kode” berarti pola penyebab ada di repository. Itu tidak membuktikan setiap data produksi terkena masalah yang sama.
- Data nominal pada contoh faktur tidak boleh dianggap salah hanya dari screenshot. Tidak ada permintaan eksplisit mengubah tarif komite, SPP, katering, atau biaya tahunan.
- Gambar Anggaran pada gambar 2 tidak disertai komentar yang jelas. Jangan membuat kebutuhan revisi Anggaran dari gambar itu saja.
- Rencana menggunakan nama siswa dan pegawai generik; nomor kontak dalam percakapan tidak dibutuhkan untuk implementasi.

## 2. Inventaris masukan dan prioritas

| ID | Sumber gambar | Masukan | Kategori | Temuan lokal | Prioritas |
|---|---|---|---|---|---|
| R1 | 1, 5 | Akun pada Buat Jurnal Pemasukan belum semua muncul; Pengeluaran juga | Bug fungsi jurnal | Opsi setiap baris dibatasi prefix 4 atau 5 | P1: menghambat jurnal berpasangan |
| R2 | 1, 6 | Tombol cetak faktur belum berfungsi | Bug keluaran | Handler ada; CSS print menyembunyikan mask dialog, berpotensi menyembunyikan faktur | P1: keluaran operasional |
| R3 | 2, 7 | Ada pegawai yang tidak tampil pada halaman 3 | Bug kelengkapan data, kemungkinan pagination | Frontend hanya memakai results halaman pertama; API PAGE_SIZE=25 | P1: merembet ke absensi/gaji |
| R4 | 2, 8 | Pemasukan/Pengeluaran tidak perlu approval Kepsek | Perubahan aturan bisnis | UI, API, dokumentasi memakai DRAFT → PENDING → POSTED dengan Principal | P1: perlu kebijakan lintas lapisan |
| R5 | 3, 9 | Bayar perlu rincian dan mendukung cicilan; belum lunas jika belum terbayar semua | Gap model transaksi | Endpoint tanpa nominal; service membayar seluruh tagihan dan langsung LUNAS; status SEBAGIAN sudah ada | P0: integritas nominal dan status |
| R6 | 3, 10 | Pendaftaran = formulir + sit-in/observasi; contoh total Rp850.000 | Penyelarasan istilah dan proses | Dua biaya dan dua aksi/jurnal terpisah; finalisasi langsung membuat penerimaan pendaftaran | P1: risiko pungutan/penerimaan ganda |
| R7 | 3, 4, 11 | Nama faktur TK perlu diganti; saldo awal akun belum terlihat | Dua kebutuhan berbeda | Nama TK ada di backend dan fallback frontend; fitur khusus saldo awal belum ditemukan | Nama P2; saldo awal P0 untuk keandalan laporan |

P0 berarti penghalang sebelum menggunakan hasil revisi untuk pencatatan/pelaporan riil. Ini bukan bukti bahwa seluruh data yang ada sudah rusak. R7 dipisah menjadi R7a identitas dan R7b saldo awal pada paket kerja berikut.

## 3. Diagnosis dan arah perbaikan

### R1 — Akun jurnal tidak lengkap

**Bukti:** `frontend/src/features/jurnal/JurnalListView.vue` memakai `coaOptionsForForm` yang hanya mengembalikan akun 4.x untuk Pemasukan dan 5.x untuk Pengeluaran. Pilihan itu dipakai pada setiap baris. `coaApi.list()` di `features/jurnal/api.ts` sudah mengambil semua halaman COA, sehingga filter UI merupakan penyebab yang lebih kuat daripada pagination COA.

Contoh jurnal pemasukan Rp100.000 memerlukan debit Kas/Bank dan kredit Pendapatan. Jika kedua baris hanya menerima akun pendapatan, pengguna tidak dapat memilih pasangan kas. Pengeluaran juga memerlukan pasangan Kas/Bank atau Utang, bukan hanya akun beban.

**Rancangan:** Semua baris jurnal dapat memilih seluruh akun aktif. Konteks Pemasukan/Pengeluaran tetap membantu pemilihan awal serta penyaringan daftar, tetapi tidak membatasi pasangan jurnal. Tampilkan kode dan nama akun; pencarian bisa menjangkau keduanya. Akun nonaktif dalam jurnal lama tetap dapat dilihat, tetapi tidak dipakai untuk transaksi baru.

**Batas:** “Pemasukan” sekarang bermakna jurnal yang mengandung akun pendapatan, belum tentu seluruh penerimaan kas. Penerimaan pinjaman atau pelunasan piutang tidak selalu mengandung pendapatan. Jangan mengganti definisi menjadi seluruh kas masuk tanpa keputusan tersendiri.

Ada masalah terkait: `load()` hanya mengambil halaman pertama jurnal, lalu `filteredRows` menyaringnya di frontend. Jurnal relevan pada halaman API lain tidak akan terlihat. Perbaiki kelengkapan daftar dengan filter jenis di server sebelum pagination dan navigasi halaman API, bukan hanya mengubah dropdown.

**Selesai bila:** Finance dapat menyimpan jurnal Kas/Pendapatan dan Beban/Kas yang seimbang; akun aktif di luar 4/5 tersedia; jurnal relevan dapat ditemukan pada seluruh halaman; kegagalan memuat COA ditampilkan dengan opsi coba lagi, bukan select kosong tanpa penjelasan.

### R2 — Cetak faktur

**Bukti:** `TagihanListView.vue::cetak()` menambahkan class `bee-print-struk` lalu memanggil `window.print()`. `assets/primevue-overrides.css:302` menyetel `.p-dialog-mask { display: none !important; }` saat print. Jika mask merupakan induk dialog, seluruh faktur ikut hilang; aturan yang menampilkan anak tidak dapat mengatasi induk yang disembunyikan. Struktur DOM runtime belum diperiksa. Handler `onafterprint` juga baru dipasang setelah `window.print()`.

**Rancangan minimum:** Pertahankan faktur yang sama untuk preview dan print; perbaiki aturan print agar mask menjadi wadah tanpa overlay, sementara konten faktur tetap terlihat. Sembunyikan halaman aplikasi, header/footer dialog, dan tombol. Hilangkan batas tinggi serta overflow dialog saat print agar seluruh rincian dicetak. Daftarkan pembersihan class/listener sebelum print dan pastikan cancel juga mengembalikan tampilan.

**Diagnosis saat implementasi:** Bedakan klik tidak bereaksi, dialog print terbuka tetapi kosong, dan isi terpotong. Screenshot hanya membuktikan laporan pengguna bahwa cetak belum bisa; belum menetapkan gejalanya. Jika browser mobile punya batas dukungan print, tentukan kebutuhan “Simpan sebagai PDF” dari dialog print sebelum menambah generator PDF server.

**Selesai bila:** Faktur pendek/panjang menampilkan nama, periode, rincian, total, dan status; halaman aplikasi tidak ikut tercetak; cetak/cancel/cetak ulang tidak merusak UI. Bukti penerimaan perlu Chrome Windows dan Safari desktop karena keduanya tampak di gambar; kebutuhan mobile ditentukan oleh perangkat pemakai aplikasi, bukan perangkat yang memotret percakapan.

### R3 — Pegawai hilang

**Bukti:** `PegawaiListView.vue::load()` mengambil `pegawaiApi.list().results` tanpa mengikuti `next`. API memakai `PAGE_SIZE=25`, sementara tabel lokal memecahnya menjadi 10 baris per halaman. Pola ini menghasilkan 10 + 10 + 5 baris, sesuai bentuk halaman 3 pada gambar. Jika data aktif yang tersedia melebihi 25, sisanya tidak dimuat. Belum diketahui jumlah atau identitas pegawai yang sebenarnya hilang.

**Rancangan minimum untuk master sekolah:** Tambahkan `pegawaiApi.listAll()` mengikuti pola `siswaApi.listAll()` yang sudah ada. Pertahankan `list()` untuk pemanggil yang memang memerlukan pagination. Gunakan listAll pada tabel master serta pilihan pegawai di absensi, gaji, kasbon, dan penanggung jawab kegiatan. Urutkan stabil dengan nama lalu id. Jangan mengubah pagination global atau sekadar memperbesar PAGE_SIZE.

**Jika pegawai masih hilang setelah data lengkap:** Bandingkan daftar resmi terhadap record aktif dan soft-deleted, tanpa membuat record duplikat atau memulihkan data otomatis. `SoftDeleteManager` memang menyembunyikan record terhapus. Cek juga kegagalan impor dan NIP duplikat sebagai kemungkinan, bukan kesimpulan.

**Selesai bila:** Semua record yang berhak terlihat muncul tepat sekali, termasuk setelah record ke-25; jumlah cocok dengan sumber resmi; pegawai yang sama tersedia pada pemanggil terkait sesuai kebijakan aktif/nonaktif masing-masing. Jika skala nanti membesar, server pagination menjadi pengganti listAll, bukan bagian perluasan sekarang.

### R4 — Tanpa approval Kepsek

**Bukti:** `accounting/api.py` membatasi submit pada Finance dan approve pada Principal; laporan hanya menghitung POSTED. `database/schemas/02_governance.sql` memiliki `chk_sod`, kontrol anggaran/periode saat UPDATE menjadi POSTED, dan perlindungan detail POSTED. Pemasukan dan Pengeluaran sebenarnya dua tampilan satu modul jurnal melalui query `jenis`.

**Interpretasi kebutuhan:** Yang jelas diminta adalah menghapus ketergantungan approval Kepsek pada kedua menu. Belum jelas apakah semua jurnal otomatis di dalamnya juga termasuk, apakah konfirmasi Finance tetap dibutuhkan, atau apakah cukup sekali klik simpan langsung tercatat final.

**Rekomendasi awal:** Pertahankan draft yang dapat diedit, lalu Finance menekan “Catat ke Buku Besar” untuk DRAFT → POSTED pada transaksi yang masuk cakupan. Principal tetap dapat memantau. Jurnal yang berasal dari pembayaran TU tetap bisa menunggu pencatatan Finance tanpa perlu Kepsek; jika sekolah meminta otomatis langsung POSTED saat TU menerima uang, jadikan keputusan eksplisit.

| Kelompok | Usulan sementara | Catatan keputusan |
|---|---|---|
| MANUAL pemasukan/pengeluaran | Finance mencatat langsung dari draft | Definisi transaksi manual yang memenuhi cakupan ditetapkan di server |
| AUTO_BILLING, AUTO_PENDAFTARAN, AUTO_SITIN | Konfirmasi Finance tanpa Kepsek | Otomatis oleh TU merupakan alternatif, belum dianggap disetujui |
| AUTO_KEGIATAN, AUTO_PAYROLL, AUTO_KASBON, AUTO_DEPRESIASI | Pertahankan kebijakan saat ini sementara | Tampil di menu yang sama tidak otomatis berarti kebijakannya berubah |
| OPENING, CLOSING, REVERSAL | Kebijakan terpisah dengan otorisasi sesuai tugas | Jangan terikut pengecualian jurnal kas harian |

**Cara implementasi:** Pusatkan proses transisi posting di layanan accounting; endpoint Finance dan endpoint approval lama menggunakannya sesuai kebijakan. Allowlist kecil di server lebih tepat daripada mesin workflow baru. Jangan menentukan hak posting dari query frontend, prefix akun saja, atau `tipe_sumber` yang bebas diisi klien. Saat ini serializer menerima tipe_sumber; sumber otomatis dan pengecualian harus ditetapkan/dibatasi server.

Bangun jurnal sebagai DRAFT, simpan semua detail, lalu UPDATE menjadi POSTED dalam transaksi atomik agar trigger posting yang ada dijalankan. INSERT jurnal langsung POSTED berpotensi melewati `trg_post_rules`, karena trigger itu hanya BEFORE UPDATE. Untuk posting tanpa approval, `approved_by` tetap kosong; aktor pencatatan ditelusuri lewat audit dan posted_at. Jangan memalsukan persetujuan diri atau menghapus chk_sod secara global.

Validasi harus tetap mencakup akun aktif, nilai nonnegatif, satu sisi tiap baris, debit=kredit > 0, nomor bukti unik, periode, dan pagu yang berlaku. Gunakan penguncian transaksi untuk klik berulang. Jurnal final dikoreksi melalui pembalik, bukan edit/hapus. Pembalik juga harus memperbarui record pembayaran yang terkait agar kas dan status tagihan tidak berbeda.

**Data lama:** Inventaris DRAFT/PENDING dan kaitannya ke operasi. Jangan mengubah semuanya menjadi POSTED dengan SQL massal. Sediakan cara transisi untuk item dalam cakupan setelah rekonsiliasi, dengan aktor dan waktu tercatat. Jangan menjalankan ulang 02_governance.sql sebagai migrasi revisi: file itu memuat penyesuaian historis dan operasi lain yang tidak relevan.

**Selesai bila:** Transaksi dalam cakupan masuk laporan tanpa aksi Kepsek; kontrol periode/anggaran tetap berlaku; transaksi di luar cakupan tidak memperoleh jalan pintas; pesan, tombol, audit, dokumentasi, dan antrean lama konsisten.

### R5 — Pembayaran cicilan dan rincian

**Bukti:** `tagihanApi.bayar(id)` mengirim POST kosong. `post_pembayaran_tagihan()` mengambil semua detail, membuat penerimaan sebesar total, mengubah status LUNAS, dan menolak pembayaran berikutnya bila satu FK jurnal sudah terisi. Tidak ditemukan model riwayat pembayaran siswa. Enum SEBAGIAN saja belum cukup untuk mendukung cicilan.

**Model minimum yang diperlukan:**

- `PembayaranTagihan`: tagihan, tanggal pembayaran, nomor bukti/referensi, nominal Decimal, akun kas/bank aktif, pembuat, jurnal, kunci permintaan unik, dan penanda pembatalan beserta alasannya. Satu tagihan memiliki banyak pembayaran; satu pembayaran memiliki satu jurnal penerimaan.
- `AlokasiPembayaranTagihan`: pembayaran, detail tagihan, nominal Decimal. Ini diperlukan agar cicilan dapat dikaitkan dengan komponen yang dibayar, bukan hanya total global.
- `total_terbayar` dan `sisa_tagihan` dihitung server dari pembayaran valid. `Tagihan.total` tetap nilai tagihan, bukan ditimpa nominal cicilan. `Tagihan.jurnal` lama dipertahankan sementara untuk kompatibilitas/histori, tetapi bukan sumber saldo pembayaran baru.
- Relasi, pilihan akun, dan id detail divalidasi server. Nominal nol/negatif, alokasi lintas tagihan, kelebihan terhadap sisa komponen, jumlah alokasi berbeda dari nominal bayar, dan kelebihan bayar ditolak. Uang muka/kelebihan bayar memerlukan kebutuhan terpisah.
- Komponen POTONGAN/diskon perlu aturan khusus: bukan komponen positif yang dibayar. Jangan menghasilkan kredit negatif karena skema jurnal melarangnya. Tentukan sisa komponen setelah diskon sebelum membuka pembayaran.

**Kontrak yang direncanakan:** `POST /api/v1/tagihan/{id}/bayar/` menerima tanggal, referensi bukti, nominal, akun kas/bank, kunci permintaan, dan alokasi berdasarkan id detail. Payload kosong ditolak dengan pesan jelas; jangan mempertahankan perilaku pembayaran penuh secara diam-diam. Response menyertakan pembayaran, jurnal, total_terbayar, sisa_tagihan, dan status. Detail tagihan dan data faktur menambahkan nilai dibayar/sisa per komponen serta ringkasan keseluruhan. Skema API dan tipe frontend ikut diperbarui.

**Layar Bayar:** tampilkan siswa/periode; komponen; nilai tagihan; sudah dibayar; sisa; nominal bayar sekarang. Pengguna memasukkan cicilan per komponen atau memilih “Lunasi sisa”. Total pembayaran dihitung dari alokasi, lalu pengguna mengonfirmasi tanggal, bukti, dan kas/bank. Riwayat tidak hilang setelah dialog ditutup.

**Status:**

| Kondisi | Status API | Label pengguna |
|---|---|---|
| Belum ada pembayaran valid, total positif | BELUM | Belum dibayar |
| 0 < terbayar < total | SEBAGIAN | Belum lunas — dibayar sebagian |
| terbayar = total | LUNAS | Lunas |

Contoh penerimaan untuk tagihan Rp6.350.000: cicilan Rp2.000.000 membuat sisa Rp4.350.000 dan status SEBAGIAN; pembayaran sisa membuat LUNAS. Ini ilustrasi perilaku, bukan catatan pembayaran riil siswa pada gambar. Tagihan bernilai nol akibat diskon perlu kebijakan penyelesaian tanpa jurnal penerimaan nol; tidak dipaksa melewati tombol bayar.

**Konsistensi:** Kunci tagihan ketika memvalidasi sisa dan membuat pembayaran, alokasi, serta jurnal. Kunci permintaan yang sama mengembalikan transaksi yang sama; permintaan berbeda yang melebihi sisa ditolak. Pembayaran yang dibatalkan tidak masuk agregat; jurnal POSTED dibalik dan subledger dikoreksi dalam proses yang konsisten. Status pembayaran operasional dan status pencatatan jurnal ditampilkan terpisah jika Finance masih harus memposting.

**Dampak wajib:** `TunggakanTagihanView.vue` sekarang menjumlahkan total asli untuk BELUM/SEBAGIAN; ganti ke sisa. Dashboard sekarang hanya menghitung BELUM dan nominal total; masukkan SEBAGIAN dengan nilai sisanya. Agregasi tunggakan harus menjangkau semua record sesuai filter, bukan hanya halaman UI yang sedang dimuat. Collection rate lama berbasis jumlah tagihan lunas harus diberi label jelas; jangan diam-diam mengubahnya menjadi rasio nominal.

**Keputusan pengakuan akuntansi:** Kode saat ini membuat debit kas/kredit pendapatan ketika pembayaran, belum pada penerbitan tagihan. Jangan menambahkan jurnal piutang saat penerbitan sambil tetap mengkredit pendapatan saat bayar; itu menggandakan pengakuan. Pilih salah satu aturan yang disetujui:

1. Perbaikan operasional minimum: pertahankan mekanisme penerimaan yang ada, jurnal hanya sebesar cicilan yang benar-benar diterima; kebutuhan penyesuaian pelaporan dijelaskan terpisah.
2. Jika akrual menjadi kebutuhan revisi: hak pendapatan yang sudah memenuhi syarat dicatat melalui piutang; pembayaran mengurangi piutang. Uang muka dan biaya untuk layanan mendatang perlu diperlakukan sesuai substansinya, bukan otomatis menjadi pendapatan saat tagihan dibuat.

Dokumen lokal `docs/17-SAK-EMKM-MAPPING.md` memuat narasi akrual/piutang yang lebih luas dari perilaku billing yang dibaca. Klaim itu perlu diperiksa dan diselaraskan. [SAK EMKM Bab 2 paragraf 2.19 dari IAI](https://www.iaiglobal.or.id/v03/files/file_sak/emkm/files/basic-html/page17.html) menjelaskan pengakuan berdasarkan kriteria unsur pada dasar akrual. [Penjelasan resmi ruang lingkup SAK EMKM](https://web.iaiglobal.or.id/SAK-IAI/Tentang%20SAK%20EMKM) juga menunjukkan bahwa pemilihan kerangka bergantung kondisi entitas. Rencana ini tidak menyimpulkan sekolah wajib menggunakan kerangka tertentu.

**Selesai bila:** cicilan mengurangi sisa dengan benar; jurnal hanya mencatat penerimaan aktual atau pelunasan piutang sesuai keputusan; pembayaran ulang tidak menggandakan transaksi; faktur, riwayat, tunggakan, dan dashboard menyajikan angka yang sama.

### R6 — Paket pendaftaran Rp850.000

**Yang diketahui:** Pengguna menjelaskan formulir + sit-in/observasi = Rp850.000, dengan contoh input Rp100.000 dan Rp750.000. Ini mendukung adanya total paket. Belum membuktikan tarif universal semua jenjang/periode atau bahwa klasifikasi akun 415 dan 416 harus digabung.

**Rekomendasi minimum:** Pertahankan dua komponen yang sudah ada untuk pencatatan; ubah label menjadi “Biaya formulir” dan “Biaya sit-in/observasi”, tampilkan “Total biaya pendaftaran” sebagai jumlah keduanya. Input contoh menghasilkan Rp850.000, bukan Rp950.000 atau penerimaan ganda. Jangan menyamakan biaya ini dengan Uang Masuk tahunan pada faktur tanpa dasar.

**Masalah proses yang perlu dipisahkan:** `post_bayar_sitin()` mencatat penerimaan sit-in; `finalisasi_pendaftaran()` langsung mencatat penerimaan formulir saat calon menjadi siswa. Finalisasi administrasi tidak membuktikan uang diterima. Penerimaan harus didukung transaksi pembayaran, sedangkan finalisasi hanya memindahkan status dan membuat siswa. Jika ada paket sekali bayar, satu aksi dapat mencatat kedua komponen dengan jurnal per akun; pembayaran sebelumnya diperhitungkan, bukan ditagih lagi.

Bila sekolah mempertahankan pembayaran dua tahap, tampilkan total paket, sudah dibayar, dan sisa; finalisasi tidak menganggap sisa lunas. Tidak perlu engine biaya baru: reuse field/model yang ada sejauh cukup. Tambahkan riwayat penerimaan hanya jika dua FK jurnal sekarang tidak dapat menampung cara pembayaran yang disetujui.

**Data lama:** Nilai `biaya_pendaftaran` saat ini bisa berarti formulir saja atau total paket tergantung cara pengguna mengisinya. Inventaris sebelum mengganti makna; label baru tidak boleh mengubah angka historis secara otomatis. Kasus sit-in sudah dibayar, calon batal, dan formulir belum dibayar memerlukan aturan operasional yang jelas, bukan asumsi refund otomatis.

**Selesai bila:** paket terlihat jelas; dua komponen tidak ditagih ulang; kas bertambah hanya karena pembayaran; finalisasi ulang tidak membuat siswa/jurnal ganda; alur lama dipetakan tanpa kehilangan bukti.

### R7a — Nama lembaga pada faktur

**Urutan masukan:** Awalnya diminta “PG–RA Lebah Madu”; setelah itu ada klarifikasi “RA Lebah Madu” bila PG dan TK tidak dibedakan. Gunakan **RA Lebah Madu** sebagai usulan nama utama berdasarkan klarifikasi terakhir. Ini tetap keputusan nama untuk disahkan pemilik lembaga, bukan dasar mengubah kode jenjang PG/TKA/TKB.

**Bukti:** `services/billing.py::struk_tagihan()` mengirim “TK Lebah Madu”; `InvoicePreview.vue` juga memakai string itu sebagai fallback. Mengubah salah satunya belum lengkap.

**Rancangan:** Selaraskan backend, fallback frontend, preview, dan print menjadi nama yang disepakati. Tidak diperlukan sistem multi-lembaga atau pengaturan branding baru. Jenjang/kelompok siswa tetap tampil pada metadata. Jangan mengganti semua istilah TK dalam data historis atau kode master.

**Selesai bila:** faktur siswa PG dan RA menampilkan identitas yang disepakati pada preview/print, tanpa mengubah jenjang dan rincian biaya.

### R7b — Saldo awal akun

**Bukti dan batas:** Model COA tidak menyimpan nilai saldo awal; tidak ditemukan layar/API khusus saldo awal. Jurnal manual dapat menampung jurnal awal, tetapi menu saat ini menyulitkan jurnal aset/liabilitas/ekuitas. `scripts/populate_rich_dashboard.py` berisi contoh saldo awal/demo, bukan bukti saldo awal sekolah sudah diinput. Script itu juga menghapus data dengan prefix tertentu; jangan dijalankan untuk kebutuhan ini.

Ada masalah pelaporan: `_saldo_tahun()` hanya menjumlahkan transaksi dalam tahun pilihan. Posisi keuangan dengan filter tahun dan kas dashboard berpotensi kehilangan saldo yang berasal dari tahun sebelumnya. Menambah kolom saldo awal pada COA saja tidak menyelesaikan ini.

**Rancangan minimum:** Saldo awal disimpan sebagai jurnal khusus `OPENING`, menggunakan master akun dan detail jurnal yang sama. Beri akses khusus yang dapat ditemukan dari Daftar Akun atau Periode, dengan tanggal mulai pembukuan, nominal debit/kredit per akun, bukti asal, dan preview keseimbangan. Kebijakan pencatatan ditentukan terpisah dari jurnal pemasukan harian.

**Langkah data:** Tentukan tanggal cutover dan sumber neraca/saldo yang disepakati. Inventaris saldo Kas, Bank, Piutang, Aset, Akumulasi Penyusutan, Utang, dan Ekuitas sesuai kebutuhan riil. Saldo awal piutang siswa harus cocok dengan daftar sisa tagihan per siswa; pembayaran berikutnya tidak boleh mengakui pendapatan lama dua kali. Jangan memaksa seluruh selisih ke akun modal atau membuat angka penyeimbang tanpa sumber.

**Aturan periode:** Pilih satu jalur: sejarah lengkap dihitung kumulatif, atau jurnal cutover menggantikan saldo sebelum tanggal awal pembukuan. Jangan menjumlahkan riwayat lama plus opening yang mewakili riwayat itu. Untuk pembukuan setelah cutover, akun neraca dihitung sampai tanggal laporan, sedangkan pendapatan/beban memakai rentang periode yang dipilih. Opening bukan penerimaan kas operasional tahun berjalan dan tidak ikut metrik/prediksi arus kas sebagai pemasukan baru. Jangan membuat opening tahunan berulang di atas ledger kumulatif.

**Contoh pemeriksaan, bukan data sekolah:** saldo awal kas Rp10 juta + penerimaan Rp2 juta − pengeluaran Rp1 juta menghasilkan kas Rp11 juta; laba rugi periode tidak memasukkan Rp10 juta saldo awal sebagai pendapatan. Saldo tahun berikutnya membawa kas tersisa tanpa mengulang jurnal awal.

**Selesai bila:** saldo didukung sumber; debit=kredit; tidak duplikat terhadap impor/riwayat; laporan posisi keuangan, kas dashboard, dan buku besar dapat direkonsiliasi termasuk lintas tahun. Data pendukung belum tersedia, sehingga tahap ini dapat membangun fasilitas tetapi tidak dapat menetapkan nominal final sendiri.

## 4. Paket kerja, dependensi, dan file terdampak

Daftar ini menentukan batas pekerjaan; bukan instruksi untuk mengubah semua file sekaligus. Nomor migration baru ditentukan dari keadaan repository saat implementasi.

### W0 — Tetapkan aturan dan baseline data

- [ ] Catat revisi kode deployment yang sedang dipakai dan gejala cetak pada perangkat pengguna.
- [ ] Cocokkan daftar pegawai resmi, transaksi tagihan yang pernah ditekan Bayar, pendaftaran, jurnal DRAFT/PENDING/POSTED, dan sumber saldo awal melalui pembacaan yang dibatasi ke kebutuhan ini.
- [ ] Putuskan cakupan posting tanpa Kepsek, pengakuan tagihan, makna paket pendaftaran, nama lembaga, dan tanggal cutover.

Keluaran: tabel keputusan serta daftar data yang perlu diperbaiki, tanpa mutasi produksi. Tidak semua keputusan menghalangi W1/W2.

### W1 — Identitas faktur dan cetak

Files: `backend/operations/services/billing.py`; `frontend/src/features/tagihan/InvoicePreview.vue`; `frontend/src/features/tagihan/TagihanListView.vue`; `frontend/src/assets/primevue-overrides.css`.

- [x] Selaraskan dua sumber nama lembaga berdasarkan keputusan; nama pada slip gaji juga diselaraskan.
- [x] Perbaiki print visibility, tinggi konten, dan lifecycle cetak dengan komponen faktur yang ada.
- [ ] Siapkan bukti penerimaan untuk rincian panjang, cancel, dan cetak ulang ketika verifikasi diminta.

Keluaran: faktur dengan identitas benar dan konten lengkap pada media cetak. Dapat dikirim terpisah dari perubahan pembayaran.

### W2 — Kelengkapan pegawai dan opsi akun jurnal

Files: `frontend/src/features/kepegawaian/api.ts`; `PegawaiListView.vue`; `AbsensiPegawaiView.vue`; `GajiListView.vue`; `PinjamanListView.vue`; `frontend/src/features/kegiatan/KegiatanListView.vue`; `backend/operations/api/staff.py`; `frontend/src/features/jurnal/JurnalListView.vue`; `features/jurnal/api.ts`; `backend/accounting/api.py`.

- [x] Tambahkan dan pakai listAll pada pemanggil pegawai yang memerlukan seluruh master; pertahankan kontrak list yang lama.
- [x] Beri urutan pegawai stabil dengan nama lalu pk.
- [ ] Bedakan record produksi yang hilang karena paging versus soft-delete/impor dengan daftar resmi.
- [x] Buka seluruh akun aktif untuk pasangan jurnal dan perjelas kegagalan memuat pilihan.
- [x] Terapkan penyaringan jenis jurnal sebelum server pagination; sambungkan tabel ke jumlah/halaman server dan reset halaman saat filter berubah.

Keluaran: master lengkap dan pembuatan/penelusuran jurnal tidak terpotong oleh filter/paging. Tidak mengubah kebijakan POSTED.

### W3 — Posting Finance tanpa Kepsek dalam cakupan

Files: `backend/accounting/services.py`; `api.py`; `serializers.py`; `utils.py` hanya bila audit memerlukan perubahan; `frontend/src/features/jurnal/api.ts`; `JurnalListView.vue`; `frontend/src/core/errors.ts`; `features/audit/auditFormat.ts`; `backend/accounting/reports.py` untuk definisi antrean; skema/migration hanya jika perlu perubahan struktur nyata.

- [x] Tambahkan proses posting bersama dan aksi API Finance dengan allowlist kebijakan yang diputuskan pada W0.
- [x] Gunakan detail lengkap dalam transaksi atomik, validasi dan audit, baru transisi POSTED; pisahkan metadata posting dari approval.
- [x] Batasi tipe_sumber dari klien; pastikan jalur approve lama tetap hanya untuk kelompok yang relevan.
- [ ] Ubah tombol, teks bantuan, pesan sukses, antrean, dan penanganan item PENDING lama.

Keluaran: satu jalur pencatatan sah tanpa Kepsek untuk kelompok yang disepakati. Pengaturan global Finance menjadi approver semua transaksi bukan bagian rencana.

### W4 — Pembayaran cicilan sampai pelaporan

Dependensi: W0 tentang pengakuan; W3 bila pembayaran memakai jalur posting baru.

Files: `backend/operations/models/billing.py`; `models/__init__.py`; migration baru termasuk history jika diaktifkan; `serializers.py`; `api/billing.py`; `services/billing.py`; `services/__init__.py` bila ekspor berubah; `admin.py` untuk melihat record pembayaran; `backend/accounting/services.py` untuk sinkronisasi reversal; `reports.py`; `frontend/src/features/tagihan/api.ts`; `TagihanListView.vue`; `InvoicePreview.vue`; `TunggakanTagihanView.vue`; `frontend/src/features/dashboard/DashboardView.vue` dan `api.ts` bila kontrak berubah; `frontend/src/types/api.ts`; `backend/schema.yml`; `frontend/src/types/openapi.d.ts`.

- [x] Buat pembayaran dan alokasi sebagai sumber agregat, dengan proteksi relasi, kelebihan bayar, dan permintaan ganda.
- [x] Ganti service penerimaan penuh menjadi penerimaan berdasarkan payload; jangan menimpa total tagihan.
- [x] Bangun dialog rincian/cicilan, riwayat, dan ringkasan dibayar/sisa pada faktur.
- [x] Sinkronkan edit/hapus tagihan di backend: tagihan dengan pembayaran tidak boleh dihapus/diubah melalui endpoint biasa meskipun tombolnya disembunyikan; koreksi lewat prosedur tersendiri.
- [x] Ubah tunggakan dan dashboard ke sisa riil, termasuk seluruh halaman data; tambahkan agregat server bila dibutuhkan untuk ringkasan lengkap.
- [ ] Migrasikan data lama hanya dengan bukti nominal pembayaran; daftar pengecualian tetap terlihat sampai rekonsiliasi, tidak otomatis dianggap lunas.

Keluaran: pembayaran sebagian benar pada seluruh jalur; perubahan FK lama dan tipe API tidak meninggalkan pemanggil memakai asumsi satu tagihan=satu jurnal.

### W5 — Paket pendaftaran dan pemisahan finalisasi/penerimaan

Files: `frontend/src/features/pendaftaran/PendaftaranListView.vue`; `api.ts`; `backend/operations/models/registration.py` dan migration hanya jika dibutuhkan oleh aturan pembayaran; `serializers.py`; `api/registration.py`; `services/registration.py`; `services/coa_resolve.py` hanya bila mapping disepakati berubah; `frontend/src/types/api.ts`; skema API.

- [ ] Tetapkan makna field formulir dan sit-in dari W0; tampilkan total paket sebagai penjumlahan tanpa angka tarif global yang belum disahkan.
- [ ] Pisahkan pembayaran dari finalisasi, atau gunakan transaksi gabungan yang secara eksplisit menyatakan keduanya dilakukan.
- [ ] Perhitungkan sit-in/formulir yang sudah dibayar; jangan menghasilkan pembayaran otomatis kedua.
- [ ] Petakan record lama yang field pendaftarannya berarti formulir saja versus total paket; jangan ubah massal tanpa bukti.

Keluaran: proses administratif dan penerimaan uang selaras, dengan paket yang jelas bagi TU.

### W6 — Saldo awal dan perhitungan saldo pada tanggal laporan

Dependensi: W0 sumber/cutover; W4 bila saldo piutang siswa masuk ruang lingkup pengakuan.

Files: `backend/accounting/services.py`; `api.py`; `serializers.py`; `reports.py`; `frontend/src/features/coa/CoaListView.vue` dan `api.ts` atau halaman Periode yang dipilih sebagai titik masuk; komponen form jurnal yang ada/reuse seperlunya; `frontend/src/features/laporan/api.ts`; `LaporanView.vue`; `features/dashboard/api.ts`; `types/api.ts`; migration/skema baru bila memerlukan metadata/keunikan opening. Model core accounting memakai `managed=False`; perubahan struktur tabel core harus memakai mekanisme SQL migration yang berlaku, bukan menganggap ORM membuat tabel otomatis.

- [ ] Buat fasilitas opening dengan sumber bukti dan tanggal cutover, reuse jurnal/detail.
- [ ] Tolak opening duplikat yang mewakili saldo yang sama; koreksi tetap dapat ditelusuri.
- [ ] Pisahkan saldo kumulatif akun neraca dari mutasi periode dan keluarkan opening dari metrik arus kas operasional/prediksi.
- [ ] Cocokkan saldo kas/bank/piutang/utang terhadap sumber serta pastikan tidak menghitung sejarah dan opening dua kali.

Keluaran: fasilitas saldo awal tersedia; nominal final hanya dimasukkan berdasarkan data sekolah yang sah.

### W7 — Penyelarasan dokumentasi dan penerimaan

Files yang ditinjau: `docs/03-API-DEVELOPMENT.md`; `12-BACKEND-REFERENCE.md`; `15-UAT-DEPLOY-READINESS.md`; `16-SIDANG-DEMO-SCRIPT.md`; `17-SAK-EMKM-MAPPING.md`; `docs/10-EXECUTION-LOG.md` bila log perubahan memang diminta.

- [ ] Sesuaikan narasi alur, permission, pembayaran, pengakuan, dan saldo awal dengan implementasi final, bukan rencana sementara.
- [ ] Tandai bukti lama UAT yang tidak lagi mewakili workflow baru; jangan mengklaim lulus dari hasil versi sebelumnya.
- [ ] Siapkan demonstrasi TU mencatat cicilan → Finance mencatat tanpa Kepsek → faktur/tunggakan/laporan cocok, dengan aturan yang sudah dipilih.

Keluaran: pengguna dan penguji menerima penjelasan yang sama dengan perilaku aplikasi.

## 5. Urutan pelaksanaan yang disarankan

1. **Mulai W0, lalu W1 dan W2:** perbaikan yang cepat terlihat, minim risiko migrasi, dan membuka penggunaan aplikasi. Nama lembaga memakai usulan terakhir bila sudah disahkan.
2. **W3 + W4:** prioritas integritas transaksi. Bangun aturan posting bersama sebelum menghubungkan cicilan ke ledger; lengkapi semua konsumen angka sisa.
3. **W5:** selaraskan paket pendaftaran dengan jalur penerimaan yang sudah jelas, supaya tidak mengulang rancangan pembayaran.
4. **W6:** fasilitas saldo awal dapat disiapkan setelah keputusan cutover; rekonsiliasi nominal menjadi penghalang penggunaan laporan final dan dapat berlangsung sejak W0.
5. **W7:** penyelarasan dokumentasi dilakukan mengikuti setiap paket, kemudian penerimaan lintas modul.

Tidak ada estimasi hari yang dipaksakan: perubahan cetak/nama lebih kecil; pembayaran dan saldo awal bergantung kualitas data serta keputusan pengakuan. Memisahkan paket menghasilkan hasil yang dapat ditinjau tanpa menjanjikan laporan final sebelum data awal selesai.

## 6. Strategi penanganan data lama dan penerbitan

- Buat inventaris read-only dan backup yang relevan sebelum migrasi yang nanti disetujui. Pembacaan snapshot tidak sama dengan persetujuan mengubah produksi.
- Pisahkan: belum dibayar; pembayaran penuh terbukti; cicilan terbukti; LUNAS hanya karena klik Bayar lama; jurnal DRAFT/PENDING; jurnal POSTED; jurnal yang sudah dibalik.
- Jangan menyimpulkan pembayaran penuh hanya dari status LUNAS atau FK jurnal. Sistem lama selalu membuat nominal penuh; cocokkan bukti kas/bank, audit, dan riwayat.
- Jika jurnal salah masih draft, koreksi melalui proses yang dapat ditelusuri; jika sudah POSTED, pembalik dan transaksi pengganti. Jangan edit detail POSTED atau hapus jurnal untuk merapikan tampilan.
- Tambah struktur pembayaran dahulu, petakan record terbukti, lalu gunakan API/frontend baru. Cegah klien lama mengirim POST kosong yang menganggap pembayaran penuh.
- Versikan perubahan database terpisah dari file schema bootstrap. Jalankan pada lingkungan yang sesuai hanya setelah implementasi dan verifikasi diotorisasi.
- Rollback UI saja tidak mengembalikan skema satu-tagihan-satu-pembayaran. Setelah cicilan baru tercatat, rollback harus mempertahankan record pembayaran dan menahan penulisan dari klien lama bila kontraknya tidak aman.

## 7. Skenario penerimaan yang perlu dibuktikan saat verifikasi diminta

Bagian ini adalah rancangan bukti selesai. Tidak ada test otomatis yang ditulis atau dijalankan pada tahap analisis ini. File test yang sudah ada dicantumkan sebagai lokasi calon penyesuaian setelah implementasi/verification diminta, bukan kewajiban menjalankan sekarang.

| Area | Kondisi | Hasil yang harus terlihat | Lokasi bukti yang tersedia |
|---|---|---|---|
| Akun jurnal | Kas/Pendapatan; Beban/Kas; akun nonaktif | Pasangan tersedia; draft seimbang; akun nonaktif tidak untuk transaksi baru | UI jurnal; `accounting/test_api.py` |
| Daftar jurnal | Jenis/status relevan pada halaman API kedua | Filter tidak hanya berlaku pada 25 data pertama | UI jurnal/API |
| Pegawai | 31 record valid, nama sama, beberapa soft-deleted | Seluruh record valid tampil tepat sekali; pemanggil konsisten | UI master/absensi/gaji/kasbon/kegiatan |
| Cetak | Faktur panjang; cancel; cetak ulang | Semua rincian terlihat; halaman aplikasi tersembunyi; UI normal kembali | Print preview Chrome/Safari |
| Posting | Finance dalam/di luar cakupan; periode CLOSED; pagu terlampaui | Posting sesuai kebijakan; batas tetap ditolak tanpa mutasi parsial | `accounting/tests.py`, `test_api.py` |
| Cicilan | Rp6.350.000 dibayar Rp2.000.000 lalu Rp4.350.000 | SEBAGIAN/sisa Rp4.350.000 lalu LUNAS/sisa nol; nominal jurnal tepat | `operations/tests.py`, `test_api.py` |
| Input uang | Nol, negatif, overpayment, id komponen tagihan lain, diskon | Ditolak atau ditangani dengan aturan diskon yang sah; tidak ada jurnal negatif | API pembayaran |
| Duplikasi | Double-click, retry setelah timeout, dua kasir bersamaan | Satu penerimaan per permintaan; tidak melebihi sisa | Service/API pembayaran |
| Pembatalan | Pembayaran sudah POSTED dibatalkan | Pembalik tercatat; saldo pembayaran/status/tunggakan kembali cocok | Layanan reversal, riwayat pembayaran |
| Penghapusan | Tagihan dengan pembayaran dihapus via API langsung | Ditolak walaupun pengguna melewati UI | API tagihan |
| Tunggakan | BELUM + SEBAGIAN pada beberapa halaman | Agregat menggunakan sisa seluruh data sesuai filter | Dashboard dan Tunggakan |
| Pendaftaran | Rp100.000 formulir + Rp750.000 sit-in; sit-in sebelumnya dibayar | Total Rp850.000; tidak ditagih dua kali; finalisasi tidak menciptakan kas fiktif | Service/API pendaftaran |
| Saldo awal | Cutover, riwayat impor, batas tahun | Neraca/kas kumulatif benar; opening tidak menjadi pendapatan/arus kas baru; tidak duplikat | `accounting/reports.py`, buku besar |
| Migrasi | LUNAS lama dengan nominal pembayaran tidak diketahui | Ditandai perlu rekonsiliasi; tidak diciptakan pembayaran penuh berdasarkan dugaan | Daftar pengecualian data |

## 8. Keputusan bisnis yang belum terjawab oleh gambar

| Keputusan | Usulan awal | Bukti/konfirmasi yang dibutuhkan sebelum perubahan terkait |
|---|---|---|
| Nama faktur | RA Lebah Madu | Klarifikasi terakhir sebagai acuan; pengesahan nama resmi |
| Rp850.000 | Total formulir Rp100.000 + sit-in Rp750.000 pada contoh | Tarif resmi per jenjang/periode; pembayaran sekali atau dua tahap |
| Pencatatan tanpa Kepsek | Disepakati: draft → Catat ke Buku Besar oleh Finance | Jalur Finance disetujui pengguna; cakupan payroll/kegiatan masih perlu ditetapkan |
| Bayar cicilan | Pengguna mengalokasikan per komponen, dengan pilihan lunasi sisa | Prioritas pembayaran jika sekolah meminta alokasi otomatis; aturan diskon |
| Pengakuan | Jangan mengubah basis secara terselubung | Kebijakan akrual/penerimaan, piutang awal, dan uang muka yang diakui sekolah |
| Saldo awal | Jurnal cutover yang bersumber dari saldo sah | Tanggal mulai; daftar saldo; riwayat yang sudah dimigrasikan |
| Data pegawai hilang | Selesaikan pemuatan seluruh halaman dahulu | Daftar nama/NIP resmi jika paging ternyata bukan satu-satunya sebab |

Keputusan ini tidak menghambat penyelesaian analisis. Sebelum implementasi bagian yang bergantung padanya, catat jawaban pemilik proses; keputusan teknis rutin seperti mengikuti next atau memperbaiki CSS tidak memerlukan rapat bisnis tersendiri.

## 9. Batas perubahan

Gunakan dependency dan pola yang sudah ada. Tidak diperlukan redesign menyeluruh, engine workflow generik, akun multi-lembaga, pengubahan tarif massal, regenerasi data demo, atau penggantian ledger. Fokusnya: setiap pembayaran bisa ditelusuri, setiap saldo memiliki sumber, dan setiap angka pada layar/laporan memakai aturan yang sama.

Perubahan lokal kedua paket belum membuktikan perilaku deployment, kelengkapan data produksi, hasil cetak pada browser pengguna, atau nominal saldo awal. Risiko utama pada paket transaksi berikutnya adalah status lunas keliru, pendapatan ganda, dan laporan kehilangan saldo awal/lintas tahun.
