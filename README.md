# BeeSmart Finance — SIA TK Lebah Madu

Sistem Informasi Akuntansi untuk TK Lebah Madu (skripsi). Stack: **Django REST + PostgreSQL** backend, **Vue 3 + PrimeVue 4 + Vite** frontend.

## Quick Start (Development)

### Prerequisites

- Python 3.13+
- Node.js 22+
- PostgreSQL 16+ (database `db_lebah_madu`)

### 1. Environment

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
# Edit .env — set DB_PASSWORD and DJANGO_SECRET_KEY
```

### 2. Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install .

cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 8000
```

API docs: http://localhost:8000/api/docs/

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### Demo Users (password: `LebahMadu2026!`)

| Username | Role | Home |
|----------|------|------|
| `admin.tu` | Administration (Bu Fitri) | `/siswa` |
| `keuangan` | Finance | `/dashboard` |
| `kepsek` | School Principal | `/dashboard` |
| `guru.kegiatan` | Teacher In Charge | `/kegiatan` |

---

## Docker Compose

Jalankan full stack (PostgreSQL + backend + frontend nginx):

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000/api/v1/ |
| API docs | http://localhost:8000/api/docs/ |

Backend otomatis `migrate` + `seed_demo` saat container start.

---

## Testing

### Backend

```bash
source .venv/bin/activate
cd backend
python manage.py test
```

### Frontend (Vitest)

```bash
cd frontend
npm run test        # single run
npm run test:watch  # watch mode
npm run build       # typecheck + production build
```

CI (GitHub Actions): `.github/workflows/ci.yml` — backend tests + frontend vitest + build.

---

### Automated UAT

```bash
source .venv/bin/activate
python backend/manage.py uat_walkthrough   # 31 checks — UJ-1/2/3
```

### UAT Checklist — 3 Persona (manual UI)

Gunakan password dev **`LebahMadu2026!`**. Centang setiap langkah setelah diverifikasi manual.

### UJ-1 — Bu Fitri (Administration) `admin.tu`

Operasional harian siswa & tagihan.

- [ ] Login → redirect ke `/siswa`
- [ ] **Absensi:** `/absensi-siswa` → pilih jenjang → kelompok → tandai hadir + flags katering/jemputan → Simpan
- [ ] **Rekap:** `/rekap-siswa` → lihat rekap bulan berjalan
- [ ] **Tagihan:** `/tagihan` → Generate → preview line items → Simpan → (opsional) Bayar → Cetak struk
- [ ] **Pendaftaran:** `/pendaftaran` → daftar calon → Bayar Sit-in → Finalisasi + set SPP
- [ ] **Katering / Jemputan:** cek modul terkait bila dipakai demo

### UJ-2 — Staff Keuangan `keuangan`

Jurnal, laporan, payroll (tidak bayar tagihan — SoD).

- [ ] Login → redirect ke `/dashboard`
- [ ] **Jurnal:** `/jurnal` atau nav Pemasukan/Pengeluaran → buat jurnal seimbang → Submit
- [ ] **Kegiatan:** (koordinasi guru) realisasi kegiatan tercatat
- [ ] **Approve flow:** minta kepsek approve jurnal PENDING
- [ ] **Laporan:** `/laporan` → neraca saldo / realisasi anggaran → export CSV / cetak
- [ ] **Tunggakan:** `/tunggakan-tagihan` read-only (tanpa tombol bayar)
- [ ] **Gaji:** `/gaji` → buat slip → posting

### UJ-3 — Pak Ali (Kepala Sekolah) `kepsek`

Governance & oversight.

- [ ] Login → `/dashboard` KPI terbaca
- [ ] **Approve jurnal:** `/jurnal` → approve jurnal PENDING → status POSTED
- [ ] **Audit log:** `/audit-log` → filter per tabel/tanggal → buka detail JSON
- [ ] **Periode:** `/periode` → (opsional) tutup periode tahun berjalan
- [ ] **Laporan:** review laporan keuangan untuk presentasi demo

---

## Project Structure

```
beesmartfinance-skripsi/
├── backend/           Django apps (accounts, accounting, operations)
├── frontend/          Vue 3 SPA
├── database/          SQL schemas + raw_data COA CSV
├── docker/            Dockerfiles + nginx config
├── docs/              Execution log, guides, checklists
└── _bmad-output/      Planning artifacts (PRD, epics, UX)
```

## Documentation

Panduan dan status deployment Cloudflare: [docs/18-CLOUDFLARE-DEPLOY.md](docs/18-CLOUDFLARE-DEPLOY.md).

| Doc | Purpose |
|-----|---------|
| [docs/10-EXECUTION-LOG.md](docs/10-EXECUTION-LOG.md) | Epic/story progress |
| [docs/11-FRONTEND-GUIDE.md](docs/11-FRONTEND-GUIDE.md) | Frontend modules |
| [docs/12-BACKEND-REFERENCE.md](docs/12-BACKEND-REFERENCE.md) | Backend API reference |
| [_bmad-output/planning-artifacts/epics.md](_bmad-output/planning-artifacts/epics.md) | Stories & acceptance criteria |

## License

MIT — see [LICENSE](LICENSE) if present.
