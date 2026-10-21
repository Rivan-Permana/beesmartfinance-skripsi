# Revisi saldo awal dan foto katering — 15 Oktober 2026

## Permintaan dan keputusan

- Kolom Saldo Awal ditempatkan setelah Aktif pada Daftar Akun. Tambah/Edit Akun menerima nominal saldo awal.
- Pengguna menyatakan tanggal acuan saldo awal belum ditetapkan. Tanggal tidak ditebak atau diisi otomatis; wajib dipilih saat menyimpan saldo awal bukan nol. Akun lama tetap nol dengan tanggal kosong sampai sekolah mengisi data.
- Foto katering dapat disimpan tanpa keterangan teks. Menu tetap harus mempunyai keterangan, foto, atau keduanya.

## Implementasi

Saldo awal disimpan satu nilai bertanggal per akun di `ms_coa`, mengikuti posisi normal debit/kredit; nominal negatif menyatakan posisi berlawanan. Migration SQL `accounting.0003_opening_balance` menambah kolom, constraint tanggal, proteksi periode tertutup dan transaksi sebelum tanggal acuan, serta memperbarui view neraca saldo. Model core tetap `managed=False` dan state migration mengikuti DDL SQL.

Ini adalah saldo akun pada awal tanggal acuan sebelum transaksi hari itu. Tanggal acuan yang melewati transaksi POSTED pertama ditolak agar saldo awal tidak menghapus/menggantikan riwayat yang sudah dicatat. Posting sebelum tanggal acuan juga ditolak. Pembaruan dilakukan dalam transaksi dengan aktor audit; tidak membuat jurnal penerimaan/pengeluaran fiktif. Waktu pembuatan akun tidak ikut ditulis ulang saat mengubah saldo. Akun dengan saldo awal bukan nol tidak dapat dihapus.

Neraca saldo, posisi keuangan, buku besar dan saldo kas dashboard memasukkan saldo awal sesuai tanggal. Saldo akun neraca dibawa lintas tahun; buku besar menampilkan saldo bawaan ketika difilter ke bulan berikutnya. Saldo awal tidak dimasukkan sebagai pemasukan/beban operasional dashboard, realisasi anggaran, atau dataset prediksi kas. Tutup periode memperhitungkan saldo awal akun nominal yang ada dalam periode tersebut. Daftar akun memperingatkan selisih total debit dan kredit selama pengisian bertahap; angka laporan final tetap membutuhkan data lengkap dan seimbang dari sekolah.

Penyebab foto tidak dapat disimpan pada gambar pengguna adalah tombol Simpan dinonaktifkan ketika keterangan kosong meskipun foto sudah dipilih. Tombol kini aktif dan memvalidasi isi ketika ditekan. API menerima foto saja dan menolak menu tanpa isi serta file yang bukan gambar. URL pratinjau sementara dibersihkan saat diganti/komponen ditutup. Label input foto/keterangan terhubung ke kontrolnya dan pesan kesalahan ditampilkan dalam dialog.

## Bukti sebelum rilis

- 62 tes backend terarah berhasil: input saldo awal, audit aktor, ketelitian desimal, kontrol akses/periode, pembawaan saldo lintas tahun/bulan, jurnal sebelum tanggal acuan, tutup buku, upload JPEG tanpa keterangan, serta regresi transaksi/tagihan.
- Dua tes interaksi frontend berhasil: urutan kolom dan edit saldo awal dengan tanggal wajib, serta simpan foto tanpa keterangan dan penolakan menu kosong. Build frontend dan pemeriksaan TypeScript berhasil.
- Folder media backend VPS dapat dibaca/ditulis oleh user aplikasi (`uid=10001`). Folder katering belum ada saat audit; belum pernah ada foto yang tersimpan di folder tersebut.
- Backup VPS `/opt/beesmartfinance/backups/db-revision-d297be738f4b.dump` (230.974 byte) berhasil direstore ke database sementara pada VPS yang sama. Migration kandidat dan Django system check berhasil. Seluruh nilai kolom lama pada 48 tabel asli dan saldo view neraca saldo tetap sama. Seluruh saldo awal baru nol dan tanggalnya kosong. Database serta direktori verifikasi sementara dibersihkan.
- Tidak ada database VPS yang diekspor ke laptop, data dummy lokal yang diimpor, atau nominal saldo awal sekolah yang diisi.
- Skema API dan deklarasi TypeScript diperbarui. Generator skema masih memuat peringatan metadata lama pada Kelompok/MenuKatering serta TarifKateringView yang tidak terkait perubahan ini.

## Batas

Tanggal dan nominal saldo awal nyata masih menunggu sekolah. Bukti pembayaran 3 tagihan lama, paket pendaftaran, backup di luar server, dan pengujian beban bukan bagian perubahan ini. Saldo awal per akun dapat diisi bertahap; laporan belum menjadi angka final jika debit dan kreditnya belum seimbang. Pembalikan migration yang menghapus kolom saldo tidak disediakan karena dapat menghilangkan nilai yang sudah dimasukkan; pemulihan harus memakai backup dan strategi menjaga data tersebut.

## Hasil rilis dan pemeriksaan produksi

Revisi sudah diterbitkan ke `main` pada commit `f1690f8f2a25f0ae51e8c7a7b8b878ab2eb18e67`. State deployment backend dan frontend sama-sama menunjuk commit tersebut. Backend mulai dirilis pada 15 Oktober 2026 pukul 15:58 WIB, migration `accounting.0003_opening_balance` berhasil, dan Cloudflare menerbitkan versi `7d8f348b-14ca-4a15-9812-f094ea96f577`.

Backup produksi sebelum migration: `/opt/beesmartfinance/backups/db-20261015T085900Z.dump`, ukuran 230.974 byte, mode `0600`. Database VPS tetap digunakan; data dummy laptop tidak diimpor.

Pemeriksaan setelah rilis melalui API aplikasi dengan role yang sudah ada menghasilkan respons 200 untuk akun, neraca saldo, posisi keuangan, dan dashboard. Field saldo/tanggal tersedia, seluruh saldo awal masih nol dan tanggal kosong. Upload JPEG tanpa keterangan menghasilkan 201, penggantian gambar menghasilkan 200, dan byte gambar yang dibuka melalui server web cocok dengan file yang diunggah. Record uji berada dalam transaksi rollback; kedua berkas uji dihapus, dan jumlah menu tetap sama (0). Tidak ada transaksi keuangan atau saldo nyata yang ditambahkan untuk pengujian.

Probe gambar pertama dari dalam container tidak dapat mengakses origin HTTPS publik dan mendapat connection refused. Pemeriksaan disesuaikan agar pengambilan gambar dilakukan dari host VPS menggunakan curl, sedangkan unggah/penggantian tetap melalui API backend dan penyimpanan media sebenarnya; pemeriksaan berikutnya berhasil. Ini tidak memerlukan pelonggaran izin media, perubahan jaringan, atau perubahan TLS.

Halaman login serta aset JavaScript COA dan Katering terbaru di domain Cloudflare merespons 200 dari koneksi laptop. Berkas upload source/skrip verifikasi sementara di VPS sudah dibersihkan, sedangkan backup dipertahankan. PostgreSQL verifikasi sementara di laptop dihentikan. Penggunaan langsung pada Safari/iPad pengguna belum diperiksa; dua interaksi form diuji menggunakan komponen Vue/PrimeVue sebenarnya dalam lingkungan pengujian.

Bagian hasil rilis ini ditambahkan ke laporan lokal sesudah deployment; commit di atas adalah versi aplikasi yang diterbitkan.
