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
