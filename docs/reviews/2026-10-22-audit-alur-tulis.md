# Audit alur tulis — 22 Oktober 2026

Lanjutan [handoff 22 Oktober](./2026-10-22-handoff.md). Semua mutasi dijalankan di database UAT `bee_uat_browser_20261020` lewat API terpisah `127.0.0.1:8001` (`DB_NAME` diset di proses, `.env` tidak diubah) dan Vite `localhost:5175` (`API_PROXY_TARGET=http://127.0.0.1:8001`). `db_lebah_madu`, `main`, dan skrip deploy tidak disentuh.

## Cara uji

- Skrip API (68 langkah, empat role, login sekali per role): jurnal manual, pembayaran tagihan, kasbon, gaji, pendaftaran, tutup buku, dan laporan. Setiap langkah memeriksa kode HTTP dan status hasilnya.
- Browser: dialog periode (pembuatan periode yang tumpang tindih), cetak laporan dan faktur dengan media `print` yang diemulasi (diukur lewat DOM), serta tampilan saat API mati, membalas 500, atau saat POST pembayaran gagal di jaringan.

## Temuan dan perbaikan

| # | Temuan | Dampak | Perbaikan |
|---|---|---|---|
| 1 | Tutup buku selalu gagal karena memakai akun ekuitas `3102`, padahal COA Final memakai `312` (Laba Ditahan). Pengguna hanya melihat pesan "Akun COA … belum terdaftar". | Periode tidak bisa ditutup sama sekali | Akun sistem `LABA_DITAHAN` (kandidat `312`, lalu `3102`) di `coa_resolve` |
| 2 | Tutup buku tetap jalan walau masih ada jurnal DRAFT/PENDING di periode itu; jurnal tersebut tidak bisa diposting lagi | Jurnal tertunda terkunci selamanya | Tutup buku ditolak dengan jumlah jurnal tertunda yang masih ada |
| 3 | Jurnal manual dan auto-jurnal (pembayaran, pendaftaran, kasbon, gaji) bisa dibuat dengan tanggal di periode CLOSED; baru ditolak trigger saat dicatat | Draf yang tidak bisa diproses, error muncul terlambat | Ditolak saat input (`TrJurnalSerializer.validate`, `buat_jurnal`) |
| 4 | Periode boleh tumpang tindih atau tanggal selesai lebih awal dari tanggal mulai | Trigger memilih periode secara ambigu | Validasi rentang dan tumpang tindih di serializer periode |
| 5 | Periode CLOSED masih bisa diubah atau dihapus | Status tutup buku bisa dihapus diam-diam | Ubah dan hapus ditolak untuk periode CLOSED |
| 6 | Slip gaji dan kasbon yang sudah dijurnal masih bisa diubah atau dihapus lewat API (UI sudah menyembunyikan tombolnya) | Nominal slip berbeda dengan jurnalnya | `perform_update`/`perform_destroy` menolak bila `jurnal_id` sudah terisi |
| 7 | Respons `POST /periode/{id}/tutup/` mengembalikan status `OPEN` padahal periode sudah ditutup | Data respons menyesatkan | `refresh_from_db()` sebelum serialisasi; penutupan juga dijaga agar hanya mengubah periode yang masih OPEN |

Pendukung UAT: `frontend/vite.config.ts` membaca `API_PROXY_TARGET` (default tetap `:8000`).

## Yang sudah benar (tanpa perubahan)

- Jurnal: DRAFT → submit → PENDING → approve Kepala Sekolah → POSTED. Keuangan dan guru ditolak 403 saat approve atau void. Jurnal PENDING/POSTED tidak bisa diubah atau dihapus. Void menghasilkan `REV-…` dan void ulang ditolak. Jurnal tidak seimbang dan nomor bukti duplikat ditolak 400.
- Jurnal manual yang memakai akun 4/5 langsung tercatat saat Keuangan menekan submit; ini aturan `can_finance_post` yang memang disengaja.
- Tagihan: Keuangan ditolak bayar (pemisahan tugas). Pembayaran sebagian → SEBAGIAN, pelunasan multi-komponen → LUNAS, `request_id` idempoten, kelebihan bayar dan nomor kwitansi ganda ditolak. Pembatalan draf → VOID dan status kembali; void oleh kepsek atas pembayaran POSTED → BELUM. Tagihan yang punya riwayat pembayaran tidak bisa dihapus.
- Kasbon: cairkan → DRAFT → approve → POSTED, cairkan ulang ditolak. Gaji: posting ulang ditolak.
- Pendaftaran: sit-in, formulir (nominal harus cocok), batal → bayar ulang, finalisasi → REGISTERED + siswa (idempoten), Keuangan tidak bisa finalisasi.
- Cetak: laporan (sidebar dan tombol tersembunyi, dokumen dan brand tampil) dan faktur (hanya `#struk-print-area` yang tampil).
- Tampilan error: daftar tagihan saat API mati menampilkan "Tagihan belum berhasil dimuat…". Respons 500 menampilkan "Server sedang bermasalah…". POST pembayaran yang gagal di jaringan membiarkan dialog tetap terbuka dengan isian utuh.

## Belum diubah (perlu keputusan)

1. ~~Potongan kasbon menghitung kasbon yang belum dicairkan.~~ Selesai: lihat bagian "Keputusan 1" di bawah.
2. ~~Saldo kasbon berkurang saat jurnal gaji dibuat; void tidak mengembalikannya.~~ Selesai: lihat bagian "Keputusan 2". Slip yang jurnalnya di-void tetap terkunci dan belum bisa diposting ulang (butuh nomor bukti baru).
3. Kepala Sekolah tidak punya tindakan "tolak" untuk jurnal PENDING; jurnal hanya bisa disetujui.
4. Tidak ada kwitansi per pembayaran; yang bisa dicetak hanya faktur tagihan.

## Hasil verifikasi

- Backend `python manage.py test`: 118 OK (termasuk 5 tes regresi baru).
- Frontend `npm run test`: 131/131; `npm run build` (vue-tsc + build) bersih.
- Audit ulang di UAT dengan kode final (run `FE6AF6`, periode Juni 2026): 66/68 lulus; dua sisanya C2 dan C5, yaitu keputusan 1 dan 2 di atas.

Data uji di UAT: periode `UAT-C86B14-2026-09` (CLOSED), periode `UAT-FE6AF6-2026-06` (CLOSED), serta tagihan, pendaftaran, kasbon, dan slip gaji berawalan `UAT-`/`KW-`.

## Keputusan 1 — potongan hanya dari kasbon yang sudah cair

- Kolom baru `PinjamanPegawai.is_legacy` (migrasi `operations.0014`, reversible). Backfill: kasbon tanpa jurnal milik pegawai ber-NIP `KAF-…` ditandai legacy. Impor KAFALAH berikutnya langsung mengisi penanda ini.
- Potongan gaji dan pelunasan kasbon hanya memakai kasbon yang `is_legacy` atau jurnal pencairannya POSTED dan belum dibalik (`pinjaman_terpotong`).
- Kasbon legacy ditolak bila dicairkan (mencegah kas keluar dua kali). Di UI statusnya tampil "Saldo legacy" tanpa tombol Cairkan.
- Field read-only `is_legacy` dan `ikut_potongan` ditambahkan di API kasbon. Pratinjau potongan di form gaji memakai `ikut_potongan`, dan peringatannya kini menyebut pengajuan yang tidak ikut dipotong.
- Verifikasi: backend 121 OK, frontend 131/131, build bersih. Migrasi diterapkan di UAT dan diuji turun-naik (`0013` ↔ `0014`). Di UAT, slip November untuk Pak Rudi berpotongan 0 selama kasbonnya belum disetujui, lalu menjadi 200.000 setelah pencairan POSTED.
- Produksi: migrasi ikut jalan otomatis ketika branch ini di-merge ke `main`.

## Keputusan 2 — saldo kasbon mengikuti persetujuan jurnal gaji

- Migrasi `operations.0015` (reversible): kolom `GajiPegawai.kasbon_diselesaikan` dan tabel `PotonganKasbonGaji` (alokasi potongan per kasbon). Backfill: semua slip yang sudah berjurnal ditandai selesai, karena aturan lama sudah mengurangi saldonya; hal ini mencegah potongan ganda.
- Posting gaji hanya membuat jurnal DRAFT. Saat jurnal gaji POSTED (approve Kepala Sekolah), saldo kasbon dikurangi dan alokasinya dicatat dalam transaksi yang sama. Bila saldo tidak lagi cukup menutup potongan slip, persetujuan ditolak dan jurnal tetap PENDING.
- Void jurnal gaji mengembalikan saldo sesuai alokasi. Slip dari sebelum migrasi tidak punya alokasi, jadi saldonya tidak dikembalikan otomatis.
- Verifikasi: backend 123 OK (tes approve, void, dan saldo kurang), frontend 131/131, build bersih. Migrasi diuji turun-naik (`0014` ↔ `0015`) di UAT. Di UAT dengan slip #6: saldo tetap saat DRAFT, berkurang 200.000 setelah approve, kembali setelah void `REV-GJ-6-202611`.
