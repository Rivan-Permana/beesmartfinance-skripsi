# Pendaftaran: rincian biaya dan pemisahan penerimaan — 15 Oktober 2026

Pengguna belum bisa memastikan cakupan tarif Rp850.000 dan meminta pengerjaan diteruskan. Basis pekerjaan: rencana W5 pada `2026-10-14-revisi-masukan-user.md`; source awal `f1690f8`.

## Keputusan pelaksanaan

- Tidak menetapkan tarif global, diskon, refund, atau nominal SPP. Input biaya formulir, sit-in/observasi, dan SPP kosong sampai diisi pengguna; nilai nol harus merupakan input eksplisit.
- Rincian baru memakai `biaya_formulir` yang eksplisit. `biaya_pendaftaran` lama dipertahankan sebagai nilai historis, tidak disalin otomatis karena mungkin berarti formulir saja atau total paket. Nilai baru null pada record lama berarti perlu pencocokan data. Penerimaan lama tidak dianggap sudah benar hanya dari status/jurnal.
- Reuse dua FK jurnal yang ada untuk pembayaran komponen penuh. Satu aksi boleh membayar formulir, sit-in, atau keduanya; total hanya komponen yang dipilih dan belum diterima. Cicilan nominal bebas untuk pendaftaran belum ditambahkan karena kebutuhannya belum dikonfirmasi.
- Pembayaran wajib menyertakan tanggal, nomor bukti, Kas/Bank, nominal, dan komponen. Lock record pendaftaran mencegah dua request membuat penerimaan ganda; pengulangan dengan payload sama mengembalikan jurnal yang sama.
- Finalisasi hanya membuat siswa dan mengubah status, tidak membuat jurnal atau menganggap biaya lunas. Finalisasi berulang tidak membuat siswa kedua.
- Data lama dengan pemetaan biaya/penerimaan yang belum jelas tetap ditandai dan tidak ditagih/posting ulang. Tidak ada perubahan nilai historis atau rekonsiliasi tanpa bukti sekolah.
- Penerimaan DRAFT/PENDING baru dapat dibatalkan Finance dengan alasan; penerimaan POSTED mengikuti jurnal pembalik oleh Kepala Sekolah. Pembatalan tidak membatalkan status siswa secara otomatis.

## Urutan dan cakupan

1. Model, migration nullable, service pembayaran/finalisasi, serializer, permission, audit, dan pengamanan data lama.
2. Kontrak API serta seluruh caller yang dilacak Git, UI rincian/total/sisa, penghapusan tarif bawaan, dan pagination seluruh data.
3. Pengujian terarah, build, pemeriksaan migration pada salinan VPS, dan rilis sesuai alur deployment proyek dengan backup.

Paket ini tidak mengisi saldo awal sekolah, tidak merekonsiliasi tiga tagihan lama berdasarkan dugaan, dan tidak mengganti data VPS dengan dummy lokal. Cetak Safari/iPad tetap memerlukan pemeriksaan terpisah.

## Perkembangan

- Pembacaan caller selesai: form/API pendaftaran, dua service lama, serializer/model/history, posting/pembatalan jurnal Finance, tes API, serta management command UAT yang dilacak Git. Skrip UAT lokal yang belum dilacak adalah perubahan pengguna dan tidak disertakan.
- Temuan: finalisasi lama membuat penerimaan formulir tanpa aksi pembayaran, layanan belum mengunci record, UI berisi tarif bawaan tanpa dasar yang dikonfirmasi, dan daftar hanya membaca halaman API pertama.
- Implementasi lokal selesai: API `/pendaftaran-siswa/{id}/bayar/`, rincian penerimaan wajib, idempotensi per komponen yang sudah diterima, pembatalan draft oleh Finance, finalisasi tanpa jurnal, nullable `biaya_formulir`, dan UI total/penerimaan/sisa. Form biaya serta SPP tidak mempunyai tarif bawaan. Halaman mengikuti seluruh halaman API dan menampilkan pagination lokal.
- 72 tes backend terarah serta empat tes interaksi form berhasil. Pengujian mencakup contoh formulir Rp100.000 + sit-in Rp750.000, dua tahap penerimaan, permintaan berulang, finalisasi tanpa jurnal/siswa ganda, pencatatan Finance, pembalik, pembatalan draft, serta penanganan data lama. Angka tersebut adalah fixture pengujian, bukan tarif yang ditetapkan ke VPS.
- Build frontend, pemeriksaan TypeScript, dan konsistensi model/migration berhasil. Skema API/deklarasi tipe diperbarui; peringatan metadata skema lama pada Kelompok/MenuKatering/TarifKateringView tetap berada di luar revisi ini.
- Migration `operations.0013_historicalpendaftaransiswa_biaya_formulir_and_more` berhasil pada salinan database di VPS yang sama. Seluruh nilai lama pada 48 tabel dan saldo view neraca saldo tetap utuh. Dua record pendaftaran lama tetap tanpa pemetaan formulir; total biaya/penerimaan/sisanya tidak ditebak. Backup verifikasi tersimpan di VPS: `/opt/beesmartfinance/backups/db-revision-e17580b737b2.dump` (236.514 byte). Database/direktori verifikasi sementara sudah dibersihkan.
- Biaya yang sudah memiliki riwayat penerimaan dikunci dari perubahan; data tersebut tidak dihapus. Jurnal lama dengan rincian belum terverifikasi ditandai perlu rekonsiliasi dan diblokir dari posting, termasuk jalur approval Kepala Sekolah. Koreksi penerimaan POSTED memakai jurnal pembalik yang sudah ada, tanpa membatalkan status siswa otomatis.
- Batas riwayat: dua FK menunjuk penerimaan terakhir tiap komponen; jurnal lama serta historical pendaftaran tetap tersimpan setelah koreksi. Paket ini tidak menambahkan buku penerimaan dengan cicilan bebas atau layar rekonsiliasi historis lengkap.

## Hasil rilis dan pemeriksaan web

- Rilis aktif 15 Oktober 2026, mulai sekitar 16.31 WIB. Backend dan frontend sama-sama menunjuk commit `045bfdd7229e0b7672dd0e4643ea6e96c4b9fc36`; migration operations.0013 sudah diterapkan. Versi Cloudflare: `1fada413-1a08-4335-adb4-3b24ef88963a`.
- Backup sebelum deployment berada di VPS: `/opt/beesmartfinance/backups/db-20261015T093125Z.dump`, 236.514 byte, mode 0600. Tidak ada pemindahan database operasional ke laptop atau penggantian dengan data dummy lokal. Backup terpisah dari VPS belum dikonfigurasi.
- Pemeriksaan API langsung di VPS berhasil: dua komponen penerimaan terpisah, pengulangan memakai jurnal yang sama, finalisasi tidak membuat penerimaan atau siswa kedua, dan penerimaan terverifikasi memenuhi aturan posting Finance. Seluruh fixture pendaftaran/siswa/jurnal dibatalkan melalui rollback transaksi; tidak ada data percobaan tertinggal. Dua pendaftaran lama tetap ditandai untuk pencocokan data.
- Halaman login dan asset pendaftaran terbaru dapat diakses dengan HTTP 200. Berkas sementara rilis/verifikasi di VPS sudah dibersihkan.
- Cetak diperiksa pada frontend yang sudah terbit melalui Chromium terisolasi, dengan respons API contoh di browser dan semua permintaan perubahan data diblokir. Tidak memakai akun sekolah atau data siswa asli. Klik tombol Cetak memanggil fungsi cetak satu kali; saat media print aktif, faktur terlihat, navigasi serta tombol dialog tersembunyi, dan penanda cetak dibersihkan sesudah event afterprint.
- PDF A4 hasil media print dibuka secara visual: identitas RA Lebah Madu, rincian, total, pembayaran, dan sisa terlihat utuh pada contoh satu halaman. Artefak lokal: `/tmp/beesmartfinance-invoice-print-verification.pdf`. Ini membuktikan layout Chromium dengan data contoh, bukan keluaran printer fisik atau Safari/iPad.
- Yang masih menunggu bukti sekolah: tarif sebenarnya, tanggal/nilai saldo awal, pencocokan dua pendaftaran lama, serta tiga tagihan lama. Angka Rp850.000 dalam pemeriksaan tetap hanya data contoh. Laporan final belum dapat dinyatakan siap sebelum data awal dan transaksi lama selesai dicocokkan.
