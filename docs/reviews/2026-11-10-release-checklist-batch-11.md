# Checklist rilis Batch 11 → `main` — 10 November 2026

Merge ke `main` = deploy produksi (poller `scripts/poll_deploy_vps.sh`: dump → migrate → backend → Worker). Dokumen ini publik: hasil cek dicatat sebagai lulus/gagal dan hitungan saja, tanpa nominal dan tanpa nama orang.

## Isi rilis

- `origin/main` (`242d519`, rilis Batch 10) `..codex/auto-deploy-fe-be`: `5423343` plus commit dokumen.
- **Hanya tampilan, tanpa migrasi dan tanpa perubahan API.** Kode pengeluaran aktif tanpa akun tetap (STR TK/PG, Sentra) ditampilkan sebagai "Akun per transaksi", bukan peringatan "Belum dipetakan":
  - form Pengeluaran: petunjuk netral "STR TK (Sentra) tidak punya akun tetap. Pilih akun Sentra yang sesuai untuk transaksi ini.";
  - panel kode di COA: label abu-abu "Akun per transaksi" untuk kode aktif, "—" untuk kode nonaktif tanpa akun.
- Keputusan pengguna 10/11: STR tetap tanpa akun tetap; akun Sentra dipilih per transaksi.
- **Sudah diverifikasi:** frontend 165 tes OK, build bersih. UAT: petunjuk netral di form Pengeluaran (form ditutup tanpa simpan); panel COA STR "Akun per transaksi | Aktif", FUN nonaktif "— | Nonaktif".

## Pekerjaan data yang menyertai (bukan bagian kode)

1. **User penyusun anggaran** dibuat superuser di VPS (bagian 4). Password diketik pengguna sendiri di prompt, tidak lewat chat.
2. **Plafon tahunan TP 2026/2027** diisi Keuangan di menu Anggaran (tanpa bulan = plafon). Nominal dari anggaran sekolah; tidak dicatat di repo.

## 1. Cek read-only produksi (web console hPanel)

```sh
cd /opt/beesmartfinance
echo "== SHA ter-deploy"; cat /home/deploy/.local/state/beesmartfinance/backend_sha /home/deploy/.local/state/beesmartfinance/frontend_sha
echo "== Container"; docker compose --env-file .env.vps -f docker-compose.production.yml ps --format 'table {{.Service}}\t{{.Status}}'
echo "== Disk"; df -h / | tail -1
echo "== GitHub"; getent hosts github.com; curl -sS -o /dev/null -w "github %{http_code}\n" https://github.com
echo "== Database"
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U beesmartfinance -d db_lebah_madu -At -v ON_ERROR_STOP=1' <<'SQL'
SET default_transaction_read_only = on;
SELECT 'migrasi terakhir', app, max(name) FROM django_migrations WHERE app IN ('operations', 'accounts') GROUP BY app ORDER BY app;
SELECT 'anggota grup BudgetPlanner', count(*) FROM accounts_user_groups ug JOIN auth_group g ON g.id = ug.group_id WHERE g.name = 'BudgetPlanner';
SELECT 'username penyusun.anggaran sudah ada', count(*) FROM accounts_user WHERE username = 'penyusun.anggaran';
SELECT 'anggaran bulanan / plafon', count(*) FILTER (WHERE bulan IS NOT NULL), count(*) FILTER (WHERE bulan IS NULL) FROM tr_anggaran;
SELECT 'kode aktif tanpa akun', string_agg(kode || '/' || unit, ' ' ORDER BY kode, unit) FROM operations_kodepengeluaran WHERE aktif AND kode_akun IS NULL;
SELECT 'COA / kode aktif', (SELECT count(*) FROM ms_coa), (SELECT count(*) FROM operations_kodepengeluaran WHERE aktif);
SELECT 'siswa aktif / jurnal / tagihan', (SELECT count(*) FROM operations_siswa WHERE NOT is_deleted AND status = 'aktif'), (SELECT count(*) FROM tr_jurnal WHERE NOT is_deleted), (SELECT count(*) FROM operations_tagihan WHERE NOT is_deleted);
SQL
```

| Baris | Yang diharapkan |
|---|---|
| SHA | `242d519…` (merge PR #28) |
| Container, disk, GitHub | Up/healthy, disk ±9%, `github 200` |
| Migrasi | `accounts 0003`, `operations 0023` |
| Anggota BudgetPlanner / username | `0` / `0` |
| Anggaran bulanan / plafon | `2` / `0` |
| Kode aktif tanpa akun | `STR/PG STR/TK` |
| COA, kode aktif, siswa, jurnal, tagihan | `206`, `60`, `108`, `18`, `7` |

### Hasil cek — 10/11 (web console, read-only)

SHA `242d519` keduanya; backend Up 42 menit, caddy/db Up 3 minggu (db healthy); disk 9%; `github 200`. Migrasi `accounts 0003`, `operations 0023`. Anggota BudgetPlanner 0, username `penyusun.anggaran` 0. Anggaran bulanan 2, plafon 0. Kode aktif tanpa akun `STR/PG STR/TK`. COA 206, kode aktif 60, siswa 108, jurnal 18, tagihan 7. Semua sesuai; tidak ada yang menghalangi backup dan merge.

## 2. Backup manual sebelum merge

```sh
cd /opt/beesmartfinance
f=backups/db-$(date -u +%Y%m%dT%H%M%SZ)-before-batch11.dump
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$f" \
  && chmod 600 "$f" && ls -l "$f" \
  && docker compose --env-file .env.vps -f docker-compose.production.yml exec -T db pg_restore --list < "$f" | grep -c "TABLE DATA"
```

Diharapkan: sekitar `…before-batch10` (288.196 byte), `TABLE DATA` = 53.

Hasil 10/11 17:14 UTC: `backups/db-20261110T171421Z-before-batch11.dump`, 288.263 byte, 53 `TABLE DATA`. Titik pulih rilis Batch 11.

## 3. Rilis

1. PR `codex/auto-deploy-fe-be` → `main`, merge (atas instruksi pengguna).
2. Tunggu Worker baru; cek dari luar: bundle COA memuat "Akun per transaksi", `/login` 200, API tanpa token 401.
3. Cek read-only ulang: SHA baru, semua hitungan sama.

### Hasil rilis — 10/11

- PR #29 di-merge ke `main` 17:15:02 UTC (`39d06c5`) atas instruksi pengguna, setelah cek read-only dan backup `before-batch11`.
- Worker baru terlihat 17:21:23 UTC, bundle `index-CsH51xwj.js`; chunk CoaListView memuat "Akun per transaksi". `/login` 200, API tanpa token 401.
- Cek read-only pasca-rilis: SHA backend dan frontend `39d06c5`; backend Up 57 menit (kode backend tidak berubah, jadi image sama dan container tidak dibuat ulang), db healthy, disk 9%, `github 200`. Migrasi tetap `0003`/`0023`. Anggota BudgetPlanner 1, username `penyusun.anggaran` 1 (dari langkah 4). Tidak berubah: anggaran 2/0, kode tanpa akun `STR/PG STR/TK`, COA 206, kode aktif 60, siswa 108, jurnal 18, tagihan 7.

## 4. User penyusun anggaran (superuser, web console)

Langkah ini menulis data (1 user). Password acak dibuat di VPS (`secrets.token_urlsafe`) dan hanya dicetak sekali di web console; jangan ditempel ke chat atau dicatat di repo. Kalau user sudah ada, password tidak diubah.

```sh
cd /opt/beesmartfinance
docker compose --env-file .env.vps -f docker-compose.production.yml exec -T backend python manage.py shell -c "
import secrets
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
U = get_user_model()
u, dibuat = U.objects.get_or_create(username='penyusun.anggaran', defaults={'first_name': 'Penyusun', 'last_name': 'Anggaran'})
pw = None
if dibuat:
    pw = secrets.token_urlsafe(12)
    u.set_password(pw)
u.is_staff = False
u.is_superuser = False
u.save()
u.groups.set([Group.objects.get(name='BudgetPlanner')])
print('dibuat' if dibuat else 'sudah ada', u.username, list(u.groups.values_list('name', flat=True)))
if pw:
    print('PASSWORD (catat sekarang, jangan ditempel ke chat):', pw)
"
```

Diharapkan: `dibuat penyusun.anggaran ['BudgetPlanner']` dan satu baris PASSWORD. Simpan password di pengelola password; saat menempel hasil ke chat, hapus baris PASSWORD.

Hasil 10/11: `dibuat penyusun.anggaran ['BudgetPlanner']`; password acak dicetak di console dan disimpan pengguna (tidak lewat chat). Pesan "9 objects could not be automatically imported" adalah info auto-import shell Django 5.2 untuk model Historical*, bukan galat.

Smoke test penyusun (pengguna login, Claude memeriksa tanpa menyimpan): `/` → `/anggaran`; menu hanya Anggaran; jurnal, tagihan, aset, laba rugi 403; panel anggaran bulanan tampil; form tambah tanpa pilihan plafon.

Hasil smoke test penyusun (10/11, produksi): login `penyusun.anggaran` (grup BudgetPlanner); `/` → `/anggaran`; menu hanya "Anggaran bulanan"; panel "Anggaran bulanan dan realisasi" tanpa error; API anggaran 200, jurnal/tagihan/aset/laba rugi 403; form Tambah anggaran hanya Bulan + Tahun kalender + Anggaran, tanpa pilihan plafon (ditutup dengan Batal). Lulus; lalu logout.

## 5. Plafon tahunan (Keuangan)

Menu Anggaran → Tambah anggaran → kosongkan Bulan → pilih TP 2026/2027 → isi Plafon per akun beban. Nominal dari anggaran sekolah. Setelah itu penyusun bisa mengisi anggaran bulanan di bawah plafon tersebut.

## Rollback

- Kode: revert merge commit di `main` (tidak ada migrasi).
- User: nonaktifkan lewat Django admin atau `u.is_active = False`.
- Plafon: hapus/ubah baris di menu Anggaran (Keuangan).
- Total: `pg_restore` dari `before-batch11`.
