# Checklist rilis `codex/auto-deploy-fe-be` → `main` — 22 Oktober 2026

Merge ke `main` sama dengan deploy produksi: `scripts/poll_deploy_vps.sh` menarik `main`, lalu `scripts/deploy_vps.sh` melakukan `pg_dump` (deploy berhenti bila backup gagal), `migrate`, dan `collectstatic`, kemudian Worker Cloudflare dibangun ulang. Dokumen ini hanya persiapan; belum ada merge maupun deploy.

## Isi rilis

- 27 commit sejak `main` (`045bfdd`); 253 file berubah. Isinya revamp UI semua role, audit visual Admin TU/Keuangan, dan audit alur tulis beserta keputusan 1–5 ([audit](./2026-10-22-audit-alur-tulis.md)).
- `main` tidak punya commit yang belum ada di branch ini. `makemigrations --check` bersih.
- Migrasi baru (keduanya reversible, `operations`):
  - `0014_pinjaman_is_legacy`: kolom `is_legacy` dan backfill kasbon tanpa jurnal milik pegawai ber-NIP `KAF-…`.
  - `0015_gaji_kasbon_diselesaikan`: kolom `kasbon_diselesaikan`, tabel `PotonganKasbonGaji`, dan backfill `True` untuk slip yang sudah berjurnal.

## Cek read-only di produksi sebelum merge

Belum dijalankan: host key VPS belum ada di `known_hosts` Mac ini, dan SSH dari jaringan lokal memerlukan VPN (lihat `docs/18-CLOUDFLARE-DEPLOY.md`). Jalankan dari sesi SSH ke VPS:

```sh
cd /opt/beesmartfinance
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U beesmartfinance -d db_lebah_madu -At' <<'SQL'
SELECT 'kasbon KAF- tanpa jurnal (akan jadi legacy)', count(*) FROM operations_pinjamanpegawai p JOIN operations_pegawai g ON g.id = p.pegawai_id WHERE p.jurnal_id IS NULL AND g.nip LIKE 'KAF-%';
SELECT 'kasbon non-KAF tanpa jurnal (berhenti dipotong)', count(*) FROM operations_pinjamanpegawai p JOIN operations_pegawai g ON g.id = p.pegawai_id WHERE p.jurnal_id IS NULL AND coalesce(g.nip, '') NOT LIKE 'KAF-%' AND p.jumlah_pinjaman > p.sudah_terbayar;
SELECT 'slip berjurnal (ditandai selesai)', count(*) FROM operations_gajipegawai WHERE jurnal_id IS NOT NULL;
SELECT 'jurnal gaji/kasbon DRAFT/PENDING', count(*) FROM tr_jurnal WHERE tipe_sumber IN ('AUTO_PAYROLL', 'AUTO_KASBON') AND status IN ('DRAFT', 'PENDING');
SELECT 'jurnal DRAFT/PENDING di semua periode', count(*) FROM tr_jurnal WHERE status IN ('DRAFT', 'PENDING') AND NOT is_deleted;
SELECT 'periode tumpang tindih', count(*) FROM ms_periode_akuntansi a JOIN ms_periode_akuntansi b ON a.id < b.id AND a.tgl_mulai <= b.tgl_selesai AND b.tgl_mulai <= a.tgl_selesai;
SELECT 'akun laba ditahan 312/3102 aktif', count(*) FROM ms_coa WHERE kode_akun IN ('312', '3102') AND is_active;
SELECT 'migrasi operations terakhir', max(name) FROM django_migrations WHERE app = 'operations';
SQL
ls -lt /opt/beesmartfinance/backups | head -3
```

Cara membaca hasilnya:

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| kasbon non-KAF tanpa jurnal | 0, atau memang pengajuan yang belum dicairkan | Kasbon lama yang sebenarnya sudah cair di luar sistem akan berhenti dipotong. Tandai `is_legacy` secara manual setelah migrasi. |
| jurnal gaji/kasbon DRAFT/PENDING | 0 | Slipnya sudah berjurnal sehingga ikut ditandai selesai, dan saldo kasbonnya sudah dikurangi aturan lama. Aman, tetapi catat jumlahnya. |
| periode tumpang tindih | 0 | Validasi baru menolak perubahan pada periode itu. Rapikan sebelum ada yang menutup buku. |
| akun laba ditahan aktif | ≥ 1 | Tutup buku akan gagal dengan pesan "Akun COA untuk Laba Ditahan … belum dikonfigurasi". |
| migrasi operations terakhir | `0013_…` | Produksi tidak sinkron dengan branch; jangan merge sebelum diperiksa. |
| backup | Ada file `db-*.dump` | Deploy tetap membuat dump baru, tetapi backup harian di luar VPS belum dikonfigurasi. |

## Hasil cek produksi — 22 Oktober 2026

Dijalankan read-only (`default_transaction_read_only = on`) lewat SSH dengan VPN. Host key VPS `SHA256:1e+IUd0Yb5upPGxv4u/Pe7R7MiErTTmV4Wn4LiYmVdw` dicocokkan dengan konsol Hostinger sebelum disimpan.

| Cek | Hasil | Penilaian |
|---|---|---|
| Versi ter-deploy | `045bfdd` (= `main`) | Sesuai |
| Migrasi `operations` terakhir | `0013_…` | Sesuai; `0014` dan `0015` belum diterapkan |
| Kasbon KAF- tanpa jurnal | 0 | Backfill `0014` tidak menandai apa pun |
| Kasbon non-KAF tanpa jurnal dan masih bersaldo | 1 (id 2, dibuat 22/10/2026, belum dicairkan, belum terpotong) | Aman: pengajuan baru; aturan baru baru memotongnya setelah pencairan disetujui |
| Slip berjurnal / slip dengan potongan kasbon | 0 / 0 | Backfill `0015` tidak mengubah apa pun |
| Jurnal gaji/kasbon DRAFT/PENDING | 0 | Aman |
| Jurnal DRAFT/PENDING lain | 7 (tagihan 3, pendaftaran 2, kegiatan 2; Sep–Okt 2026) | Tidak terkait migrasi. Tutup buku periode `2026/2027` (OPEN, s.d. 29/06/2027) akan menolak sampai jurnal ini diselesaikan |
| Periode tumpang tindih | 0 | Aman |
| Akun Laba Ditahan aktif | 1 | Tutup buku dapat berjalan |
| Backup terakhir di VPS | `db-20261015T093125Z.dump` (15/10/2026) | Deploy berikutnya membuat dump baru; backup harian ke luar VPS belum ada |

Kesimpulan: tidak ada temuan yang menghalangi merge dari sisi data dan migrasi.

### Cek ulang — 28 Oktober 2026

Semua hasil sama dengan 22 Oktober, kecuali kini ada 1 slip gaji berjurnal: `GJ-1-202610`, POSTED, dengan potongan kasbon Rp 0. Backfill `0015` hanya menandainya sebagai sudah diselesaikan tanpa mengubah saldo kasbon. Kasbon #2 masih belum dicairkan. Belum ada periode CLOSED. Versi ter-deploy tetap `045bfdd`, migrasi di `0013`, dan backup terakhir masih 15/10/2026. Kesimpulan tidak berubah.

## Rollback

- Kode: revert merge commit di `main` lalu push. Poller akan men-deploy ulang (backend membuat dump baru lebih dulu).
- Skema: sebelum revert, jalankan di VPS `docker compose … run --rm backend python manage.py migrate operations 0013`. Kolom `is_legacy`, `kasbon_diselesaikan`, dan tabel alokasi dihapus; data lain tidak tersentuh.
- Data: `pg_restore` dari `backups/db-<waktu>.dump` yang dibuat deploy, hanya bila ada kerusakan data.

## Keputusan sebelum merge

1. ~~Hasil cek read-only di atas sudah diperiksa dan dapat diterima.~~ Sudah dijalankan, lihat "Hasil cek produksi".
2. Stash `stash@{0}` di `main` ("periode close-by-kepsek + jurnal Rincian") dibiarkan (diputuskan 22/10/2026). Stash ini menyentuh area tutup buku yang sudah diubah di branch ini, jadi kemungkinan besar bentrok bila di-pop setelah merge.
3. Merge lewat PR ke `main`, bukan push langsung: draft PR #21 sudah dibuka.
