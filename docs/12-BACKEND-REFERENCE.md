# ⚙️ Backend Reference & Log — BeeSmart Finance

> Backend **stabil (~85%)** — API production-ready untuk v1 (E1–E9 ✅).
> Dokumen ini: referensi endpoint, konfigurasi bisnis, dan log perubahan BE.
>
> **Master progress:** [10-EXECUTION-LOG.md](./10-EXECUTION-LOG.md)  
> **Status FE per route:** [11-FRONTEND-GUIDE.md](./11-FRONTEND-GUIDE.md) (sumber kebenaran UI)  
> **Legacy / E10:** [13-LEGACY-ALIGNMENT-GUIDE.md](./13-LEGACY-ALIGNMENT-GUIDE.md)

**Last synced:** 2026-06-30 — kolom FE di bawah diselaraskan dengan router + views yang sudah shipped.

---

## Status Ringkas

| Aspek | Status v1 | Catatan |
|-------|-----------|---------|
| API `/api/v1/` | ✅ | 30+ endpoints, Swagger `/api/docs/` |
| Akuntansi double-entry | ✅ | PostgreSQL triggers |
| Maker-checker jurnal | ✅ | submit / approve / void |
| RBAC 4 role | ✅ | Django Groups |
| Auto-posting | ✅ | tagihan, gaji, aset, kegiatan |
| Tests | ✅ ~35 passing | accounting, operations, accounts |
| Seed demo | ✅ E9.1 | `manage.py seed_demo` |
| Docker Compose | ✅ E9.3 | `docker-compose.yml` (db + backend + frontend) |
| CI | ✅ E9.3 | GitHub Actions |
| Tarif katering kode | ⚠️ v1 flat 22rb | Resmi 20/10 — **E10 story 10.3** |

**Checklist historis BE:** [09-BACKEND-PROGRESS-CHECKLIST.md](./09-BACKEND-PROGRESS-CHECKLIST.md)

---

## Jalankan Backend

```bash
source .venv/bin/activate
cd backend && python manage.py migrate
python manage.py runserver 8000
# API docs: http://localhost:8000/api/docs/
```

**Full stack (opsional):**

```bash
docker compose up --build
```

---

## Seed Users (E9.1 ✅)

| Username | Role | Password (dev) |
|----------|------|----------------|
| `admin.tu` | Administration | `<password demo dari seed lokal>` |
| `keuangan` | Finance | `<password demo dari seed lokal>` |
| `kepsek` | SchoolPrincipal | `<password demo dari seed lokal>` |
| `guru.kegiatan` | TeacherInCharge | `<password demo dari seed lokal>` |

> ⚠️ Password dev only — ganti saat deploy production.

```bash
python backend/manage.py seed_demo          # users + demo data
python backend/manage.py seed_demo --users-only   # users saja
python backend/manage.py uat_walkthrough    # smoke 31/31 ✅
```

**Command:** `backend/accounts/management/commands/seed_demo.py`

---

## API Map — Endpoint vs Frontend (v1)

Legend: **✅** wired di Vue · **⚠️** partial / tanpa halaman CRUD dedicated · **🔲** E10+ · **—** BE-only / Finance internal

| Resource | Path | FE Route / View | FE |
|----------|------|-----------------|-----|
| Auth | `auth/token`, `auth/me` | `/login` LoginView | ✅ |
| Dashboard | `dashboard/*` | `/dashboard` DashboardView | ✅ |
| Siswa | `siswa/` | `/siswa` SiswaListView | ✅ |
| Kehadiran siswa | `kehadiran-siswa/` | `/absensi-siswa`, `/rekap-siswa` | ✅ |
| Jenjang | `jenjang/` | Dipakai wizard absensi & pendaftaran (bukan CRUD page) | ⚠️ |
| Kelompok | `kelompok/` | Dipakai wizard absensi (bukan CRUD page) | ⚠️ |
| Menu katering | `menu-katering/` | `/katering` KateringView | ✅ |
| Tarif katering | `tarif-katering/` | `/katering` (config periode) | ✅ |
| Armada jemputan | `armada-jemputan/` | `/jemputan` JemputanView | ✅ |
| Pendaftaran jemputan | `pendaftaran-jemputan/` | `/jemputan` JemputanView | ✅ |
| Tagihan | `tagihan/` (+ generate, bayar, struk) | `/tagihan` TagihanListView | ✅ |
| Tunggakan | `tagihan/` (filter) | `/tunggakan-tagihan` | ✅ |
| Pendaftaran siswa | `pendaftaran-siswa/` (+ bayar-sitin, finalisasi) | `/pendaftaran` PendaftaranListView | ✅ |
| COA | `coa/`, `golongan/`, `sub-golongan/` | `/coa` CoaListView | ✅ |
| Jurnal | `jurnal/` (+ submit, approve, void) | `/jurnal` JurnalListView | ✅ |
| Anggaran | `anggaran/` | `/anggaran` AnggaranListView | ✅ |
| Periode | `periode/` (+ tutup) | `/periode` PeriodeListView | ✅ |
| Laporan | `laporan/*` | `/laporan` LaporanView | ✅ |
| Pegawai | `pegawai/` | `/pegawai` PegawaiListView | ✅ |
| Absen pegawai | `absen-pegawai/` | `/absensi-pegawai` AbsensiPegawaiView | ✅ |
| Gaji | `gaji/` (+ posting) | `/gaji` GajiListView | ✅ |
| Pinjaman | `pinjaman/` (+ cairkan) | `/pinjaman` PinjamanListView | ✅ |
| Aset | `aset/` (+ susutkan) | `/aset` AsetListView | ✅ |
| Kegiatan | `kegiatan/` (+ realisasi, laporan) | `/kegiatan` KegiatanListView | ✅ |
| Audit log | `audit-log/` | `/audit-log` AuditLogView | ✅ |

**Tidak ambigu lagi:** semua baris yang dulu ❌ (kehadiran, COA, katering, jemputan, pendaftaran, absen pegawai, audit) sudah ✅ di v1.

**Masih ⚠️ (bukan gap blocker):** CRUD master **jenjang/kelompok** — stories E2.1–E2.2 optional; data di-manage via seed + dipilih di wizard absensi/pendaftaran.

**Belum ada (E10 backlog):** `seed_legacy`, `validate_legacy`, batch tagihan, billing 20/10 — lihat [13-LEGACY-ALIGNMENT-GUIDE.md](./13-LEGACY-ALIGNMENT-GUIDE.md).

---

## Konfigurasi Bisnis Backend

**Tarif katering resmi (keputusan 2026-06-30):** Sen–Kam **Rp 20.000** + Jumat **Rp 10.000** per hari hadir + ikut katering.

**Kode v1** masih default lama sampai E10 story 10.3:

```python
# backend/operations/services/katering_tarif.py — v1 shipped
DEFAULT_TARIF_KATERING_HARIAN = Decimal("22000")  # superseded

# Target E10.3:
DEFAULT_TARIF_SEN_KAM = Decimal("20000")
DEFAULT_TARIF_JUMAT = Decimal("10000")
```

**Jemputan v1:** `PendaftaranJemputan.harga` flat bulanan di `billing.py` — E10.4 akan per-trip.

---

## Backend Change Log

| Date | Change | Files | Status |
|------|--------|-------|--------|
| 2026-06-28 | Reference doc created | `docs/12-BACKEND-REFERENCE.md` | ✅ |
| 2026-06-28 | `seed_demo` — 4 role + demo data | `accounts/management/commands/seed_demo.py` | ✅ E9.1 |
| 2026-06-28 | Katering tarif v1 flat 22.000 | `operations/services/katering_tarif.py` | ✅ v1 |
| 2026-06-28 | Docker compose full stack | `docker-compose.yml`, `docker/` | ✅ E9.3 |
| 2026-06-28 | UAT walkthrough 31/31 | `accounts/management/commands/uat_walkthrough.py` | ✅ |
| 2026-06-30 | Doc sync — FE map + deployment status | `docs/12-BACKEND-REFERENCE.md` | ✅ |
| — | Katering 20/10 differentiated billing | `katering_tarif.py`, `billing.py` | 🔲 E10.3 |
| — | `seed_legacy` + `validate_legacy` | management commands | 🔲 E10.1, E10.11 |

---

## Minor BE Tasks (post-v1)

| Task | Trigger | Priority | Status |
|------|---------|----------|--------|
| Katering 20/10 + weekday split | E10.3 | P0 | 🔲 |
| Jemput per-trip billing | E10.4 | P1 | 🔲 |
| Batch generate tagihan | E10.5 | P1 | 🔲 |
| `seed_legacy` import CSV | E10.1 | P0 | 🔲 |
| Template komponen TP | E10.2 | P1 | 🔲 |
| CORS | — | — | ✅ sudah OK |
| Major refactor BE | — | — | ❌ tidak perlu v1 |

---

## Arsitektur Singkat

```
backend/
├── accounts/      User + Groups RBAC + seed_demo + uat_walkthrough
├── accounting/    COA, jurnal, anggaran, laporan (managed=False PG models)
├── operations/    siswa, tagihan, pegawai, katering, jemputan, kegiatan
└── config/        settings, urls
```

Database core accounting: raw SQL schemas `database/schemas/*.sql` + triggers.

### Koreksi COA lokal — 2026-10-20

Pada database pengembangan lokal, akun legacy `1011` (Kas di Bank), `1101` (Kas di Tangan), dan `1103` (Perlengkapan Sekolah) dipindahkan ke subgolongan `11` (Aset Lancar). Relasi sebelumnya berturut-turut `512`, `911`, dan `911`. Kode akun, saldo awal, dan baris jurnal POSTED tidak diubah. Laporan menghitung kategori dari awalan kode akun, sehingga koreksi relasi ini memperbaiki hierarki COA tanpa mengubah rumus atau nominal laporan.

Aturan `SISTEM/PIUTANG_KARYAWAN` sebelumnya menunjuk `1103` meski nama akun tersebut Perlengkapan Sekolah. Akun `114` (Piutang Karyawan/Kasbon) dibuat, aturan dialihkan ke `114`, dan dua baris jurnal `AUTO_KASBON` yang masih DRAFT (total debit Rp1.200.000) dipindahkan dari `1103` ke `114`. Resolver kini hanya memakai `1103` sebagai fallback legacy jika nama akunnya mengandung “Piutang”. Perubahan data ini hanya dilakukan pada database lokal; database lain perlu diaudit tersendiri sebelum koreksi.

Audit lanjutan menemukan `1103` tidak memiliki referensi di jurnal, anggaran, aturan posting, pembayaran, aset, kegiatan, maupun riwayat; saldo awalnya nol. Akun ini dinonaktifkan di database lokal agar pilihan Perlengkapan memakai akun COA Final `113`, yang tetap aktif. Baris `1103` tetap tersimpan untuk jejak audit.

---

## Docs Terkait

| Doc | Isi |
|-----|-----|
| [11-FRONTEND-GUIDE.md](./11-FRONTEND-GUIDE.md) | Status modul FE per route |
| [10-EXECUTION-LOG.md](./10-EXECUTION-LOG.md) | Epic & story log |
| [13-LEGACY-ALIGNMENT-GUIDE.md](./13-LEGACY-ALIGNMENT-GUIDE.md) | E10 backlog BE+FE |
| [03-API-DEVELOPMENT.md](./03-API-DEVELOPMENT.md) | Panduan API |
| [09-BACKEND-PROGRESS-CHECKLIST.md](./09-BACKEND-PROGRESS-CHECKLIST.md) | Checklist historis |
