# Catatan implementasi paket transaksi — 14 Oktober 2026

Status: kode lokal diimplementasikan, 43 tes terarah berhasil pada PostgreSQL terisolasi setelah izin pengguna, migration berhasil diverifikasi pada salinan data VPS di server yang sama; belum deployment.

## Perilaku yang diimplementasikan

- Daftar jurnal menggunakan pagination server, 10 baris secara default, `page_size` maksimal 100. Filter `jenis=masuk|keluar` dan status diterapkan sebelum pagination. Tabel mengikuti jumlah record server dan kembali ke halaman pertama jika halaman lama sudah tidak tersedia.
- Finance memakai `POST /api/v1/jurnal/{id}/catat/` untuk MANUAL yang memuat pendapatan/beban, AUTO_BILLING, AUTO_PENDAFTARAN, dan AUTO_SITIN. DRAFT atau PENDING dapat dicatat. Payroll, kegiatan, kasbon, depresiasi, dan jurnal khusus tetap mengikuti kebijakan persetujuan sebelumnya.
- Jurnal lengkap dibangun sebagai DRAFT, kemudian diubah ke POSTED agar trigger periode dan anggaran tetap berjalan. Posting Finance tidak mengisi approved_by sebagai persetujuan diri. Aktor masuk audit log dan submitted_by; posted_at diisi.
- Endpoint submit lama mencatat langsung sumber yang termasuk cakupan Finance. Pesan sukses mengikuti status aktual. Sumber otomatis tidak dapat disamarkan melalui input tipe_sumber dan tidak dapat diedit/hapus sebagai jurnal manual.
- Pembayaran siswa disimpan sebagai PembayaranTagihan dan AlokasiPembayaranTagihan. Satu tagihan dapat memiliki beberapa penerimaan dan jurnal. Nilai tagihan asli tetap; status BELUM/SEBAGIAN/LUNAS diperbarui dari penerimaan valid.
- Dialog Bayar menampilkan komponen yang masih memiliki sisa, nominal pembayaran sekarang, tanggal, bukti, Kas/Bank, dan pilihan “Lunasi sisa”. Record pembayaran serta alokasi dapat dilihat pada Riwayat.
- Kunci request UUID dan bukti unik per tagihan mencegah pencatatan ulang. Permintaan dengan kunci yang sama harus memiliki payload yang sama. Payload kosong, nominal nol/negatif, akun tidak sesuai, komponen asing/berulang, alokasi tidak seimbang, dan kelebihan sisa ditolak.
- Draft penerimaan dapat dibatalkan Finance melalui `batal-penerimaan` dengan alasan. Penerimaan POSTED dikoreksi melalui pembalik oleh Principal. Pembatalan ikut mengembalikan sisa dan status tagihan; record lama tetap tersimpan.
- Tagihan dengan riwayat pembayaran dikunci dari edit/hapus biasa, termasuk pada admin. Data pembayaran pada admin hanya dibaca.
- Faktur menampilkan dibayar dan sisa. Halaman tagihan serta tunggakan mengikuti seluruh halaman API. Dashboard menghitung sisa BELUM + SEBAGIAN; rasio lunas hanya memakai record yang tidak ditandai perlu rekonsiliasi.

## Kontrak pembayaran baru

`POST /api/v1/tagihan/{id}/bayar/` wajib menerima:

```json
{
  "tanggal": "2026-02-01",
  "no_bukti": "BUKTI-CONTOH-001",
  "nominal": "2000000.00",
  "akun_kas": "1101",
  "request_id": "00000000-0000-4000-8000-000000000001",
  "alokasi": [{"detail": 1, "nominal": "2000000.00"}]
}
```

ID rincian dan akun dalam contoh adalah ilustrasi; klien mengambil nilai sebenarnya dari detail tagihan dan COA. Nilai uang dikirim sebagai string. Response berisi pembayaran, jurnal_id, serta tagihan dengan total_terbayar, sisa_tagihan, dan riwayat. Skema dan deklarasi tipe frontend telah diregenerasi.

## Migrasi dan data lama

Migration `operations.0012_historicaltagihan_perlu_rekonsiliasi_and_more` menambah struktur pembayaran, alokasi, history, constraint, dan penanda rekonsiliasi. Tagihan lama dengan jurnal atau status selain BELUM ditandai perlu rekonsiliasi; tidak dibuatkan record penerimaan nominal penuh berdasarkan dugaan.

Record tersebut menampilkan nominal dibayar/sisa sebagai null, bukan nol. Pembayaran baru, posting pendapatan billing lama, dan edit/hapus biasa diblokir. Jumlah record yang perlu rekonsiliasi muncul pada dashboard dan halaman tunggakan; nilai tidak diketahui tidak ikut total sisa terverifikasi.

Sebelum penerbitan: verifikasi migrasi pada database terpisah; cocokkan pembayaran lama dengan bukti kas/bank; tentukan koreksi jurnal yang keliru; kemudian rilis backend dan frontend yang sesuai kontrak baru. Jangan menjalankan klien lama yang mengirim pembayaran tanpa rincian. Jangan membalikkan migration setelah ada pembayaran baru tanpa strategi menjaga record tersebut.

Fasilitas rekonsiliasi pembayaran lama berdasarkan bukti nyata masih memerlukan data sekolah dan penetapan kasus koreksi; flag tidak boleh dihapus massal untuk membuka pembayaran.

## Batas yang masih berlaku

- Pengakuan pendapatan tetap mengikuti penerimaan seperti sebelumnya; paket ini tidak menambah jurnal piutang pada penerbitan tagihan. Perubahan basis pengakuan dan saldo awal dikerjakan terpisah.
- Alokasi otomatis potongan negatif belum ditentukan. Tagihan dengan baris negatif diblokir dari pembayaran, dengan pesan agar memakai rincian netto yang benar. Ini mencegah jurnal kredit negatif dan tidak menebak pembagian diskon.
- Kas/Bank mengikuti kode COA yang saat ini dikenal proyek: 111, 112, 1011, 1101, dan 1102. Penambahan kode lain perlu penyelarasan pemetaan.
- Penyelarasan paket pendaftaran dan saldo awal belum masuk paket ini.

## Bukti verifikasi dan batasnya

- Build frontend dan pemeriksaan TypeScript berhasil pada kode lokal.
- Django system check dan pemeriksaan sintaks Python berhasil tanpa akses database aplikasi.
- Pemeriksaan model terhadap file migration tidak mendeteksi perubahan yang belum dibuat. Migration termasuk struktur pembayaran baru berhasil diterapkan saat membangun database tes terisolasi. History migration VPS diperiksa sampai `operations.0011`; kandidat `0012` kemudian berhasil pada salinan database VPS.
- Generator skema masih melaporkan metadata yang belum lengkap pada TarifKateringView dan dua serializer lain yang tidak diubah paket ini. Endpoint pembayaran/catat baru tercantum dalam schema dan deklarasi tipe hasil generator.
- Skenario regresi disiapkan untuk cicilan/pelunasan, permintaan berulang, input invalid, perubahan tagihan berbayar, rekonsiliasi, pembalik, periode tertutup, pagu, dan pagination.
- Pengguna kemudian memberi izin verifikasi. Sebanyak 43 tes pada `operations.test_payment_revision`, `accounting.test_api`, `operations.test_api`, dan `operations.tests` berhasil pada PostgreSQL sementara melalui socket lokal. Tes awal menemukan lookup prefix pada ForeignKey yang tidak didukung; filter diperbaiki untuk memakai field kode akun pada relasinya, lalu pemeriksaan diulang dan lulus. Server sementara dihentikan setelah selesai.
- Hasil tersebut mencakup cicilan/pelunasan, validasi dan idempotensi, penguncian edit/hapus, pembatalan, posting Finance, kontrol periode/pagu, dan pagination. Belum menjadi bukti pengujian beban/concurrency, cetak pada browser, atau rekonsiliasi pembayaran lama pada data sekolah.
- Belum ada migrasi pada database produksi, deployment, pemeriksaan browser, atau rekonsiliasi data produksi.

## Keputusan database dan pemeriksaan VPS

Pengguna memilih database VPS sebagai basis aplikasi online. Database lokal berisi dummy demo skripsi dan tidak akan diimpor untuk menggantikan atau digabungkan dengan data VPS. DBeaver merupakan klien untuk mengakses database; backend online saat ini sudah memakai PostgreSQL di VPS dan tidak bergantung pada database laptop. Migrasi ke Supabase tidak diperlukan untuk keputusan ini.

Audit VPS 14 Oktober 2026 menemukan 32 record siswa, 34 record pegawai, 5 tagihan, dan 5 jurnal, termasuk record yang tidak muncul melalui manager default karena soft-delete. Pada salinan setelah migration, manager default menampilkan 31 siswa dan 31 pegawai. Tiga tagihan berstatus LUNAS dari alur lama menjadi kandidat rekonsiliasi; dua tagihan berstatus BELUM. Jurnal lama terdiri dari dua AUTO_BILLING DRAFT, satu AUTO_BILLING PENDING, dan dua AUTO_PENDAFTARAN DRAFT.

Backup baru disimpan **di VPS yang sama**, di `/opt/beesmartfinance/backups/db-revision-e96fef6eda72.dump`, mode `0600`, ukuran 210.911 byte. Dump berhasil direstore ke database sementara dalam container PostgreSQL VPS. Kandidat kode dipasang ke container verifikasi terpisah; tidak menimpa source/container backend produksi. Database produksi tidak dimigrasi atau diubah.

Pada salinan tersebut, `operations.0012` dan Django system check berhasil. Pemeriksaan 48 tabel asli membandingkan seluruh nilai kolom sebelum dan sesudah migration. Nilai record lama tetap sama; metadata Django menambah tepat tiga content type dan 12 permission untuk model baru. Tiga tagihan mendapat penanda rekonsiliasi, tanpa membuat nominal penerimaan historis berdasarkan dugaan. Tabel pembayaran serta alokasinya masih kosong. Database dan direktori source verifikasi sementara dibersihkan setelah pemeriksaan.

Pemeriksaan awal sempat gagal karena membandingkan jumlah metadata Django sebelum dan sesudah penambahan model. Investigasi menemukan hanya dua tabel metadata tersebut yang bertambah; pemeriksaan berikutnya juga memastikan seluruh record metadata lama tetap ada dan tidak berubah, lalu berhasil. Ini bukan kegagalan migration atau perubahan record operasional.

Ekspor database penuh ke laptop sebelumnya ditolak automatic approval review karena penyimpanan seluruh data pada tujuan lokal itu belum diizinkan secara eksplisit. Ekspor tidak dijalankan. Pemeriksaan restore/migration akhirnya memakai salinan yang tetap berada di VPS, tanpa mengirim data operasional ke laptop atau penyedia database lain.

Backup ini melindungi proses revisi, tetapi belum menjadi backup di luar server. Kehilangan VPS masih membutuhkan strategi pemulihan di lokasi lain. Tiga tagihan lama tetap memerlukan bukti pembayaran dan rekonsiliasi sebelum pembayaran baru atau posting jurnal billing terkait diperbolehkan; jangan menghapus flag massal.
