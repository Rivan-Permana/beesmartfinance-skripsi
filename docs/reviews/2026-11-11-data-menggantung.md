# Data menggantung di produksi sebelum cut-over — 11 November 2026

Dokumen publik: tanpa nama dan nominal. Sumber: cek read-only produksi lewat web console (11/11).

## Temuan

| Kelompok | Isi | Kenapa menggantung |
|---|---|---|
| A. Jurnal pendaftaran | `REG-1`, `REG-2` (DRAFT sejak akhir Sep/awal Okt, 112 D / 415 K) | Catatan pendaftarannya masih "Perlu dicocokkan" (biaya formulir/sit-in kosong), jadi Keuangan tidak bisa mencatat |
| B. Jurnal realisasi kegiatan | `KG-1-1`, `KG-1-2` (PENDING, 5112 D / 112 K) | Diinput akun Kepsek; Kepsek tidak boleh menyetujui/menolak jurnal buatannya sendiri (SoD) dan hanya ada satu Kepsek → macet permanen |
| C. Tagihan lama + jurnalnya | Tagihan 1, 2, 3 (BULANAN Sep/Okt, "perlu dicocokkan"); jurnal `BL-1-202610` (PENDING), `BL-2-202610`, `BL-3-202609` (DRAFT) | Dibuat sebelum ada pencatatan per pembayaran. Tidak ada jalur di aplikasi untuk mencocokkan atau membatalkannya. Semua baris "LAIN" dikreditkan ke 411 SPP; `BL-1` mendebit akun pendapatan 412, bukan kas, dan nilainya tidak sama dengan total tagihan. Komponennya juga akan ditagih ulang oleh impor biaya masuk saat cut-over |

## Keputusan (pengguna, 11/11)

1. A diselesaikan lewat layar oleh TU dan Keuangan sesuai bukti.
2. B: Keuangan boleh mencatat jurnal realisasi kegiatan (sama seperti pengeluaran manual). SoD tetap: Kepsek tetap tidak bisa menyetujui jurnalnya sendiri. Konsekuensi yang dikonfirmasi pengguna 11/11: berlaku juga untuk realisasi berikutnya yang diinput Guru PJ, jadi Kepsek tidak lagi menyetujui realisasi kegiatan; kontrolnya dua orang (Guru, Keuangan) dan pagu kegiatan.
3. C: tiga tagihan lama dipensiunkan (jurnal → VOID, tagihan dihapus lunak dengan alasan di riwayat); ketiga siswa ikut alur cut-over biasa. Kas tetap benar karena uangnya ada di saldo sheet dan masuk lewat jurnal selisih 112.
4. B dan alat C ikut rilis berikutnya bersama perbaikan impor ulang biaya masuk dan pemasangan backup.

## Perubahan kode (branch, belum dirilis)

- `accounting/services.py`: `AUTO_KEGIATAN` masuk `FINANCE_POST_SOURCES`. UI menampilkan tombol Catat lewat `can_finance_post`, tanpa perubahan frontend.
- `operations/management/commands/pensiunkan_tagihan_lama.py`: default hanya rencana; `--terapkan` untuk menyimpan; wajib `--alasan` dan `--oleh` (pelaku di log audit). Seluruh perintah dibatalkan bila satu tagihan tidak bertanda perlu dicocokkan, sudah punya penerimaan baru, atau jurnalnya bukan AUTO_BILLING DRAFT/PENDING.
- Verifikasi: tes baru `test_kegiatan_posting` (gagal di kode lama, lulus di kode baru) dan `test_pensiun_tagihan` (rencana tidak mengubah; terapkan; tolak semua bila satu tidak memenuhi). Backend 195 tes OK, `makemigrations --check` bersih, schema sama. Di UAT (trigger asli): dua tagihan tiruan dengan jurnal DRAFT dan PENDING → rencana tidak mengubah, tagihan biasa ditolak tanpa perubahan, terapkan → VOID + dihapus lunak; log audit mencatat pelaku `keuangan`, riwayat tagihan mencatat alasan. Backup UAT sebelum uji: `~/Backups/beesmartfinance/bee_uat-20261111-014658-before-pensiun.dump`.

## Langkah setelah rilis

1. **TU** — menu Pendaftaran: dua catatan berlabel "Perlu dicocokkan" → isi biaya formulir dan sit-in sesuai bukti → simpan. **Keuangan** — Pemasukan: Catat `REG-1` dan `REG-2` (nilai jurnal harus sama dengan biaya yang diisi; kalau tidak, aplikasi menolak).
2. **Keuangan** — Pengeluaran: periksa bukti DP, lalu Catat `KG-1-1` dan `KG-1-2`.
3. **Superuser** — web console, rencana dulu:

   ```sh
   cd /opt/beesmartfinance
   docker compose --env-file .env.vps -f docker-compose.production.yml exec -T backend \
     python manage.py pensiunkan_tagihan_lama 1 2 3 --alasan "Tagihan uji coba Sep-Okt; diganti alur cut-over Jan 2027" --oleh keuangan
   ```

   Diharapkan tiga baris `tagihan … -> dihapus; jurnal BL-… -> VOID` dan "Rencana saja (3 tagihan)". Bila cocok, jalankan ulang perintah yang sama dengan `--terapkan` di akhir.
4. Cek read-only: tagihan tidak terhapus 7 → 4, perlu dicocokkan 3 → 0, jurnal DRAFT+PENDING 7 → 0.
