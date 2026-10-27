# Lampiran Pemetaan SAK EMKM — BeeSmart Finance

> **Tujuan:** Bahan sidang / lampiran skripsi — menyelaraskan *Exposure Draft SAK EMKM* (IAI) dengan klaim skripsi dan fitur sistem BeeSmart Finance.  
> **Sumber:** `docs/draft_ed_sak_emkm_kompilasi.pdf` · `docs/SKRIPSI RIVAN (1).docx` · implementasi BeeSmart Finance  
> **Sikap ilmiah:** Sistem mengikuti **prinsip dan komponen laporan** SAK EMKM sebagai pedoman penyusunan LK sederhana; **bukan** pernyataan kepatuhan penuh terhadap seluruh persyaratan ED, dan **bukan** klaim bahwa sekolah yayasan secara formal masuk ruang lingkup UMKM.

---

## 1. Ringkasan untuk penguji (30 detik)

Penelitian ini merancang Sistem Informasi Akuntansi yang menghasilkan **Laporan Posisi Keuangan** dan **Laporan Laba Rugi** sesuai kerangka SAK EMKM, dengan Chart of Accounts yang dikelompokkan menjadi aset, liabilitas, ekuitas, pendapatan, dan beban, kemudian disesuaikan dengan transaksi operasional Sekolah Lebah Madu (SPP, katering, antarjemput, gaji, dan beban operasional).

Mekanismenya: transaksi operasional tercatat secara berpasangan (debit–kredit) ke daftar akun, melalui alur draft → pengajuan → persetujuan, lalu diagregasi menjadi laporan keuangan. Catatan atas laporan keuangan (CALK) secara otomatis belum menjadi keluaran sistem; dapat disusun secara manual dari data yang diekspor.

---

## 2. Tabel utama: paragraf ED → fitur BeeSmart → skripsi

| No | Acuan ED SAK EMKM | Isi pokok standar | Fitur / perilaku di BeeSmart Finance | Rujukan di skripsi |
|----|-------------------|-------------------|--------------------------------------|--------------------|
| 1 | Bab 1 Ruang lingkup | EMKM untuk entitas tanpa akuntabilitas publik signifikan yang memenuhi kriteria UMKM | Digunakan sebagai **pedoman desain pelaporan sederhana**, bukan sertifikasi status UMKM sekolah | Latar belakang & tujuan (Bab I); landasan teori 2.1.2 |
| 2 | Bab 2 — asumsi dasar | Akrual, kelangsungan usaha, konsep entitas bisnis | Transaksi diakui melalui jurnal ke akun yang relevan; kas sekolah dipisahkan dari pemilik/yayasan dalam pembukuan sistem | 2.1.1 SIA; 2.1.2 SAK EMKM |
| 3 | Bab 2 — pengukuran | Dasar pengukuran biaya historis | Nilai transaksi dicatat sebesar jumlah yang terjadi (tagihan, pembayaran, gaji, pengadaan) | 2.1.2; 2.1.3 COA |
| 4 | Bab 2 — unsur LK | Aset, liabilitas, ekuitas, penghasilan, beban | COA sekolah dikelompokkan sesuai lima unsur tersebut | 2.1.3 Chart of Accounts |
| 5 | Bab 3 — LK lengkap | Minimum: posisi keuangan, laba rugi, catatan atas LK | Menu laporan menyediakan posisi keuangan dan laba rugi (plus neraca saldo, buku besar, realisasi anggaran untuk operasional sekolah). CALK otomatis belum ada | Batasan & tujuan (Bab I); 2.1.2; pembahasan hasil |
| 6 | Bab 4 — posisi keuangan | Menyajikan aset, liabilitas, ekuitas; format/urutan tidak dipaksakan | Laporan posisi keuangan dari saldo akun POSTED | 2.1.2; tujuan menghasilkan neraca |
| 7 | Bab 5 — laba rugi | Menyajikan pendapatan dan beban periode | Laporan laba rugi / kinerja periode dari akun pendapatan dan beban | 2.1.2; tujuan menghasilkan laba rugi |
| 8 | Bab 6 — catatan atas LK | Pernyataan kepatuhan, kebijakan akuntansi, rincian akun | Belum otomatis; data pendukung tersedia lewat buku besar, jurnal, dan audit log | Gap yang jujur di sidang / saran pengembangan |
| 9 | Bab 8 — aset & liabilitas keuangan | Piutang/utang diukur pada harga transaksi (jumlah tagihan) | Tagihan siswa dan utang terkait (mis. gaji) tercermin lewat akun piutang/utang dan jurnal terkait | 2.1.3; modul tagihan & payroll |
| 10 | Bab 11 — aset tetap | Biaya perolehan; penyusutan (konsep) | Modul aset / pencatatan aset tetap sesuai COA sekolah (tingkat detail mengikuti kebijakan sekolah) | Kebutuhan operasional sekolah |
| 11 | Bab 14 — pendapatan | Diakui saat ada hak atas pembayaran; uang muka = liabilitas; belum bayar = piutang | Tagihan, pembayaran, pendaftaran, sit-in memicu jurnal ke akun pendapatan (SPP, pendaftaran, sit-in, katering, dll.) | 2.1.2; 2.1.3; modul tagihan & pendaftaran |
| 12 | Bab 14 — beban | Beban diakui saat penurunan manfaat ekonomi dapat diukur | Payroll, realisasi kegiatan, pengeluaran operasional menghasilkan jurnal beban | Modul gaji & kegiatan |
| 13 | Contoh ilustratif LK | Contoh pos: kas, piutang, aset tetap, utang, modal, saldo laba; pendapatan usaha; beban usaha | Struktur laporan mengikuti klasifikasi, bukan menyalin label contoh manufaktur di ED | 2.1.3 — penyesuaian akun sekolah tanpa mengubah klasifikasi EMKM |
| 14 | Dasar Kesimpulan — komponen LK | ED tidak mensyaratkan laporan arus kas dan perubahan ekuitas | Skripsi fokus pada posisi keuangan dan laba rugi — selaras dengan pertimbangan kemudahan ED | Batasan masalah: LPK + Laba Rugi |

---

## 3. Chart of Accounts: apa yang dimaksud “sesuai SAK EMKM”

### 3.1 Yang dimaksud standar (bukan daftar kode wajib)

ED SAK EMKM **tidak** menetapkan kode akun numerik wajib. Yang diwajibkan secara konsep adalah:

- klasifikasi unsur laporan keuangan (aset, liabilitas, ekuitas, pendapatan, beban);
- kemampuan menyusun Laporan Posisi Keuangan dan Laporan Laba Rugi;
- pengukuran berbasis biaya historis dan dasar akrual.

Contoh ilustratif di ED hanya **panduan penyajian**, misalnya kas, piutang, persediaan, aset tetap, utang, modal, dan saldo laba.

### 3.2 Yang dipakai Sekolah Lebah Madu

Sesuai tinjauan pustaka skripsi (§2.1.3), COA disusun mengacu klasifikasi SAK EMKM, lalu **disesuaikan** dengan aktivitas sekolah:

| Kelompok (SAK EMKM) | Contoh kebutuhan sekolah | Contoh akun operasional (nama umum) |
|---------------------|--------------------------|-------------------------------------|
| Aset | Kas, bank, piutang siswa, aset tetap | Kas di tangan, kas di bank, piutang terkait tagihan, aset tetap |
| Liabilitas | Kewajiban jangka pendek | Utang gaji / utang usaha terkait operasional |
| Ekuitas | Hak residual yayasan/sekolah | Ekuitas / saldo laba (defisit) |
| Pendapatan | Penerimaan operasional pendidikan | Pendapatan SPP, pendaftaran, sit-in, katering, antarjemput, dan pendapatan lain relevan |
| Beban | Pengeluaran operasional | Beban gaji, beban operasional, beban kegiatan, dan beban lain relevan |
| (Tambahan operasional) | Pengawasan anggaran sekolah | Golongan anggaran / realisasi — untuk manajemen internal, di luar template contoh EMKM murni |

Penyesuaian nama akun (SPP, katering, dll.) **tidak mengubah** kerangka klasifikasi lima unsur di atas — ini yang dijelaskan di skripsi sebagai “penyesuaian tanpa mengubah klasifikasi yang mengacu pada SAK EMKM”.

### 3.3 Jawaban lisan jika ditanya “COA-nya apa saja?”

> “Kami menggunakan Chart of Accounts sekolah yang dikelompokkan sesuai SAK EMKM: aset, liabilitas, ekuitas, pendapatan, dan beban. Isinya disesuaikan dengan transaksi Lebah Madu — misalnya pendapatan SPP, katering, antarjemput, beban gaji, dan beban operasional — sehingga Laporan Posisi Keuangan dan Laba Rugi dapat disusun dari klasifikasi yang sama, meskipun detail akunnya berbeda dari contoh manufaktur di standar.”

---

## 4. Mekanisme di sistem (tanpa jargon teknis berlebih)

Alur yang dibuktikan di demo sidang:

1. **Operasional** — Admin TU membuat tagihan, mencatat pembayaran, atau memproses pendaftaran.  
2. **Penjurnalan** — Sistem membentuk jurnal berpasangan (debit dan kredit seimbang) ke akun yang sesuai.  
3. **Pengendalian** — Staf keuangan mengajukan; kepala sekolah menyetujui (maker–checker).  
4. **Pelaporan** — Laporan keuangan hanya menghitung jurnal yang sudah disetujui (POSTED): neraca saldo, laba rugi, posisi keuangan, buku besar, serta realisasi anggaran.  
5. **Jejejak** — Perubahan penting dapat ditelusuri lewat riwayat / audit log untuk mendukung akuntabilitas.

Ini mewujudkan semangat Bab 14 ED (pengakuan pendapatan dan beban) serta tujuan SIA di skripsi: dari pencatatan transaksi hingga laporan dalam satu sistem.

---

## 5. Batasan yang perlu dikatakan jujur di sidang

| Topik | Klaim yang aman | Klaim yang dihindari |
|-------|-----------------|----------------------|
| Status entitas | Sekolah memakai **prinsip pelaporan sederhana** SAK EMKM | “Sekolah Lebah Madu adalah UMKM sehingga wajib SAK EMKM” |
| Kepatuhan | Laporan inti LPK + Laba Rugi selaras kerangka Bab 3–5 | “Sistem sudah 100% compliant seluruh paragraf ED” |
| CALK | Belum otomatis; dapat dilengkapi manual | “Catatan atas laporan keuangan sudah lengkap di aplikasi” |
| Nirlaba | Substansi laporan (aset–kewajiban–ekuitas; surplus/defisit) dapat dibahas; acuan nirlaba khusus adalah ISAK 35 | Menyamakan SAK EMKM dengan ISAK 35 |
| Referensi | Skripsi mengutip SAK EMKM (IAI, 2018); ED 2016 dipakai untuk memahami struktur dan contoh ilustratif | Mengklaim dua dokumen itu dokumen yang sama secara formal |

---

## 6. Narasi siap pakai (salin saat ditanya)

### “Apa mekanisme SAK EMKM di sistem Anda?”

> “Sesuai kerangka SAK EMKM, laporan disusun atas dasar akrual dan biaya historis. Setiap transaksi operasional dicatat berpasangan ke Chart of Accounts, kemudian diagregasi menjadi Laporan Posisi Keuangan dan Laporan Laba Rugi. Itu komponen minimum yang menjadi fokus skripsi. Catatan atas laporan keuangan belum digenerate otomatis oleh sistem.”

### “COA-nya dari mana? Apakah sama dengan contoh di standar?”

> “Standar tidak menetapkan daftar kode akun wajib. Yang kami ikuti adalah klasifikasi lima unsur. Detail akun mengikuti COA Final Sekolah Lebah Madu agar mencerminkan SPP, katering, jemput, gaji, dan operasional sekolah, sebagaimana dijelaskan di tinjauan pustaka tentang Chart of Accounts.”

### “Kenapa pakai SAK EMKM, bukan ISAK 35?”

> “Skripsi memilih SAK EMKM karena fokus pada laporan sederhana yang relevan untuk entitas dengan transaksi relatif sederhana, dan itu yang disepakati dalam perumusan masalah: posisi keuangan dan laba rugi. Sekolah sebagai entitas nirlaba secara teori juga terkait ISAK 35; substansi yang kami tampilkan (aset, liabilitas, ekuitas, dan hasil periode) sejalan, tetapi klaim kepatuhan penuh ISAK 35 bukan ruang lingkup penelitian ini.”

### “Di mana buktinya di aplikasi?”

> “Alur demo: buat atau bayar tagihan / pendaftaran, buka jurnal yang terbentuk, setujui hingga POSTED, lalu buka menu Laporan — posisi keuangan dan laba rugi. Itu rantai dari transaksi ke laporan yang dimaksud skripsi.”

---

## 7. Checklist cepat sebelum sidang

- [ ] Bisa menjelaskan **lima kelompok akun** tanpa menghafal seluruh daftar akun.  
- [ ] Bisa menunjukkan **Laporan Posisi Keuangan** dan **Laba Rugi** dari data POSTED.  
- [ ] Bisa menyebutkan **satu contoh** jurnal operasional (misalnya bayar SPP: kas bertambah, pendapatan diakui).  
- [ ] Siap mengakui **CALK belum otomatis** dan **status UMKM bukan fokus formal**.  
- [ ] Mengetahui bahwa contoh di PDF ED adalah **ilustrasi**, bukan template wajib nama akun.

---

## 8. Daftar pustaka terkait (dari skripsi)

- Ikatan Akuntan Indonesia (2018). *Standar Akuntansi Keuangan Entitas Mikro, Kecil, dan Menengah (SAK EMKM)*. Jakarta: Dewan Standar Akuntansi Keuangan Ikatan Akuntan Indonesia.  
- Dewan Standar Akuntansi Keuangan IAI (2016). *Exposure Draft SAK EMKM* (dokumen kerja: `draft_ed_sak_emkm_kompilasi.pdf`).  
- Yuniar, S. et al. (2025). Analisis penerapan SAK EMKM pada laporan keuangan entitas pendidikan nirlaba.  
- Romney, M. B. & Steinbart, P. J. (2021). *Accounting Information Systems* (rujukan konsep SIA dan COA di skripsi).

---

*Dokumen ini melengkapi skrip demo sidang (`16-SIDANG-DEMO-SCRIPT.md`) dengan fokus argumentasi akuntansi SAK EMKM.*
