# Checklist rilis Batch 13 → `main` — 11 November 2026

Rilis kecil, satu perubahan, tanpa migrasi dan tanpa perubahan schema API. Pola sama dengan Batch 7–12 (cek read-only → backup bernama → PR → merge → cek pasca-rilis → smoke test), dengan cek dan backup digabung dalam satu blok. Dokumen publik: hanya lulus/gagal dan hitungan.

## Isi rilis

- `origin/main` (`0b749dc`, rilis Batch 12) `..codex/auto-deploy-fe-be`: `8aa18d4` plus merge `origin/main` dan commit dokumen.
- **Baca jurnal hanya untuk Keuangan, Kepsek, dan TU** (`accounting/api.py`). Guru dan penyusun anggaran ditolak (403) saat membaca daftar/rincian jurnal; menulis jurnal tidak berubah; daftar akun (COA) tetap terbuka karena dipakai layar Kegiatan Guru. Superuser tetap bisa membaca.
- Verifikasi: tes baru di `test_role_access` (gagal di kode lama, lulus di kode baru); backend 199 tes OK; `makemigrations --check` bersih; schema sama. UAT: `guru.kegiatan` dan `penyusun.anggaran` jurnal 403 / COA 200; `admin.tu`, `keuangan`, `kepsek` jurnal 200.
- Risiko: rendah. Frontend tidak berubah; rute jurnal di layar sejak awal hanya untuk tiga peran itu.

## 1. Cek read-only dan backup bernama (web console hPanel, satu blok)

```sh
cd /opt/beesmartfinance
echo "== SHA ter-deploy"; cat /home/deploy/.local/state/beesmartfinance/backend_sha /home/deploy/.local/state/beesmartfinance/frontend_sha
echo "== Container"; docker compose --env-file .env.vps -f docker-compose.production.yml ps --format 'table {{.Service}}\t{{.Status}}'
echo "== GitHub"; curl -sS -o /dev/null -w "github %{http_code}\n" https://github.com
echo "== Database"
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U beesmartfinance -d db_lebah_madu -At -v ON_ERROR_STOP=1' <<'SQL'
SET default_transaction_read_only = on;
SELECT 'migrasi terakhir', app, max(name) FROM django_migrations WHERE app IN ('operations', 'accounts') GROUP BY app ORDER BY app;
SELECT 'jurnal total / POSTED / VOID / belum POSTED', count(*), count(*) FILTER (WHERE status = 'POSTED'), count(*) FILTER (WHERE status = 'VOID'), count(*) FILTER (WHERE status IN ('DRAFT', 'PENDING')) FROM tr_jurnal WHERE NOT is_deleted;
SELECT 'tagihan / siswa aktif / COA', (SELECT count(*) FROM operations_tagihan WHERE NOT is_deleted), (SELECT count(*) FROM operations_siswa WHERE NOT is_deleted AND status = 'aktif'), (SELECT count(*) FROM ms_coa);
SQL
echo "== Backup bernama"
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch13.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

| Baris | Yang diharapkan | Bila tidak |
|---|---|---|
| SHA | `0b749dc…` (merge PR #30) | Produksi berubah sejak Batch 12. Hentikan. |
| Container, GitHub | Up/healthy; `github 200` | Pulihkan layanan atau tunda merge. |
| Migrasi | `accounts 0003`, `operations 0023` | Jangan merge. |
| Jurnal | 18 / 11 / 3 / 4 (bila Keuangan/TU belum mencatat apa pun sejak 11/11 pagi) | Catat angka sebenarnya sebagai pembanding; tidak menghalangi rilis. |
| Tagihan / siswa / COA | 4 / 108 / 206 | Catat. |
| Backup | ±288 KB, `TABLE DATA` = 53 | Ukuran 0 atau gagal: jangan merge. |

### Hasil — 11/11 (web console)

SHA `0b749dc` keduanya; backend Up 26 menit, db healthy; `github 200`. Migrasi `0003`/`0023`. Jurnal 18 / POSTED 11 / VOID 3 / belum POSTED 4. Tagihan 4, siswa aktif 108, COA 206. Backup `backups/db-20261111T043218Z-before-batch13.dump`, 289.016 byte, 53 `TABLE DATA`. Semua sesuai; tidak ada yang menghalangi merge.

## 2. Rilis

1. PR `codex/auto-deploy-fe-be` → `main`, merge (keputusan rilis pengguna 11/11).
2. Tunggu poller; backend dibuat ulang (kode backend berubah), Worker dibangun ulang tanpa perubahan isi.
3. Cek dari luar (Claude): `/login` 200; API tanpa token 401.
4. Cek pasca-rilis: blok bagian 1 **tanpa** bagian backup; SHA baru, hitungan sama.
5. Smoke test (pengguna login; Claude hanya membaca): Guru → API jurnal 403, layar Kegiatan tetap memuat daftar akun; TU, Keuangan, Kepsek → Pemasukan/Pengeluaran tetap tampil.

## Rollback

Revert merge commit di `main`, lalu push. Tidak ada migrasi dan tidak ada data yang berubah.
