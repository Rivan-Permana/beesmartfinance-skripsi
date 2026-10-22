---
stepsCompleted: [1, 2]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-beesmartfinance-skripsi-2026-06-28/prd.md
  - _bmad-output/planning-artifacts/ux-designs/ux-beesmartfinance-skripsi-2026-06-28/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-beesmartfinance-skripsi-2026-06-28/EXPERIENCE.md
  - _bmad-output/implementation-artifacts/investigations/school-finance-standards-investigation.md
status: active
updated: 2026-06-28T3
---

# beesmartfinance-skripsi - Epic Breakdown

## Overview

Dekomposisi PRD v1 + UX spines menjadi epics & stories untuk menyelesaikan BeeSmart Finance dari **setengah matang → production-ready skripsi**. Digunakan sebagai **log implementasi & monitoring progress**.

**Baseline:** Backend ~85% | Frontend ~55% | UX/Deploy ~30%

## Requirements Inventory

### Functional Requirements

```
FR-1: Responsive App Shell (sidebar collapsible, drawer mobile)
FR-2: Role-aware navigation & home redirect per 4 role
FR-3: CRUD Siswa lengkap (jenjang, kelompok, tanggal lahir, wali, SPP)
FR-4: Absensi harian siswa (wizard jenjang→kelompok→grid, katering/jemputan flags)
FR-5: Rekapitulasi absensi siswa per periode
FR-6: Rekap katering dari absensi (tarif configurable)
FR-7: Menu katering mingguan (teks; upload gambar v1.1)
FR-8: CRUD armada jemputan
FR-9: Pendaftaran jemputan per siswa
FR-10: Rekap jemputan & data pendamping guru
FR-11: CRUD COA (golongan, sub-golongan, akun) + import CSV
FR-12: Anggaran golongan 9 + carry-over
FR-13: Jurnal maker-checker (existing + polish UX)
FR-14: Laporan keuangan + period picker tahun ajaran
FR-15: Export/cetak PDF laporan & struk
FR-16: Generate tagihan otomatis (SPP+katering+jemputan)
FR-17: Editor tagihan manual (line items, grand total)
FR-18: Cetak faktur ortu (layout mockup)
FR-19: CRUD Pegawai + work periode
FR-20: Absensi pegawai clickable grid
FR-21: Slip gaji lengkap + posting
FR-22: Audit log read-only UI
FR-23: Seed users 4 role + demo data script
FR-24: Pendaftaran siswa trial→admission UI (bayar-sitin, finalisasi)
FR-25: Master jenjang & kelompok CRUD
FR-26: Tunggakan tagihan read-only (Finance/Principal)
FR-27: Absensi siswa read-only (TeacherInCharge)
FR-28: seed_legacy — import roster/absensi/pegawai dari legacy-data CSV
FR-29: Template komponen biaya TP (tahunan, per jenjang, baru/lama)
FR-30: Katering differentiated (Sen–Kam vs Jumat; optional per jenjang)
FR-31: Jemput per-trip billing (datang/pulang × tarif)
FR-32: Batch generate tagihan per kelompok/jenjang/TA
FR-33: Payroll field mapping KAFALAH (tunjangan, transport, uang makan)
FR-34: Auto potong pinjaman pegawai ke gaji
FR-35: Import anggaran dari CSV legacy + realisasi
FR-36: Export rekap mirror format legacy (katering, jemput)
FR-37: Dashboard kepsek KPI operasional + keuangan (data legacy)
FR-38: validate_legacy — bandingkan hitung sistem vs CSV ground truth
```

### NonFunctional Requirements

```
NFR-1: UI Bahasa Indonesia; pesan error via core/errors.ts
NFR-2: JWT auth; RBAC enforced FE guard + BE permission
NFR-3: Responsive ≥768px tablet usable untuk absensi
NFR-4: WCAG AA contrast pada teks utama (audit Lighthouse ≥85)
NFR-5: Frontend vitest/component tests ≥60% modul kritis
NFR-6: Docker compose dev + prod template
NFR-7: CI: lint + test backend + build frontend on push
NFR-8: Audit trail: semua aksi approve/void tercatat (existing BE)
NFR-9: Nominal uang: hindari float; format id-ID konsisten
NFR-10: Performance: list 500 siswa <2s dengan pagination
NFR-11: Progressive disclosure — Admin tidak melihat modul akuntansi; istilah teknis hanya di Finance/Principal
```

### Business Config (confirmed 2026-06-28, updated 2026-06-30)

```
- Katering (resmi E10): Sen–Kam Rp 20.000/hari + Jumat Rp 10.000/hari (hadir + ikut_katering)
- Katering v1 kode: masih 22.000 flat sampai story 10.3
- PG: katering all-in semester — tidak auto-tagihan terpisah
- Jemputan: minimal Rp 20.000; E10 → per-trip 80% taksi online
- Portal ortu / WA / payment: v2 (setelah 3 role)
- Seed password dev: <password demo dari seed lokal>
```

### Additional Requirements

```
- PrimeVue 4 + existing BeePreset — extend tokens per DESIGN.md
- OpenAPI gen types: npm run gen:types setelah schema change
- Backend endpoints sudah ada — prioritas wiring FE, bukan rewrite BE
- PostgreSQL triggers immutable POSTED — UI must not offer edit on POSTED
- Seed dari result/T_*.csv dan diagrams COA CSV
```

### UX Design Requirements

```
UX-DR1: Sidebar grouped by domain (SISWA | KEUANGAN | PEGAWAI | KEGIATAN)
UX-DR2: Breadcrumb + page title di topbar setiap route
UX-DR3: AttendanceGrid component — chip toggles Hadir/Izin/Sakit/TH + katering/jemputan
UX-DR4: WizardStepper jenjang→kelompok→content untuk absensi/rekap/katering
UX-DR5: KPI cards dashboard pakai semantic colors (surplus green, defisit magenta)
UX-DR6: InvoicePreview component dengan @media print stylesheet
UX-DR7: PeriodPicker (bulan + tahun ajaran) shared di Laporan & Tagihan
UX-DR8: EmptyState component dengan ilustrasi lebah + CTA
UX-DR9: ConfirmDialog pattern untuk destructive actions
UX-DR10: Mobile drawer nav <768px; touch targets 44px min
UX-DR11: Login page selaras brand (existing — polish logo asset)
UX-DR12: DataTable loading skeleton rows
UX-DR13: Nav alias Pemasukan/Pengeluaran → Jurnal preset filter (Finance/Principal)
UX-DR14: SoD — Administration tidak punya route ke modul akuntansi
UX-DR15: Bahasa UI per role (operasional vs akuntansi) — lihat EXPERIENCE.md
UX-DR16: PageLayout wrapper — title, subtitle, actions, content card (semua halaman)
UX-DR17: formatRp() utility di core/format.ts — NFR-9, dilarang inline toLocaleString
UX-DR18: PrimeVue global skin — primevue-overrides.css (DataTable cream, Dialog lg, input 44px)
UX-DR19: KpiCard reusable component — dashboard + ringkasan
UX-DR20: Logo SVG assets — logo-lebah.svg, favicon; ganti emoji placeholder
UX-DR21: ListPage pattern — PageLayout + DataTable + Dialog + EmptyState (CRUD standar)
UX-DR22: E1 migration gate — semua view existing di-migrate sebelum E2+ merge
```

### FR Coverage Map

| FR | Epic |
|----|------|
| FR-1,2 | E1 |
| FR-3,4,5,25,27 | E2 |
| FR-6,7 | E3 |
| FR-8,9,10 | E4 |
| FR-11,12,13,14,15,26 | E5 |
| FR-16,17,18,24 | E6 |
| FR-19,20,21 | E7 |
| FR-22 | E8 |
| FR-23 + NFR5-7 | E9 |

## Epic List

| Epic | Judul | Priority | Status |
|------|-------|----------|--------|
| E1 | Design System & App Shell | P0 | 🔲 |
| E2 | Modul Siswa & Absensi | P0 | 🔲 |
| E3 | Modul Katering | P0 | 🔲 |
| E4 | Modul Jemputan | P0 | 🔲 |
| E5 | Keuangan Lengkap (COA + Laporan) | P0 | 🔲 |
| E6 | Tagihan & Pendaftaran | P0 | ✅ |
| E7 | Pegawai & Payroll | P1 | 🔲 |
| E8 | Audit & Governance UI | P1 | ✅ |
| E9 | Quality, Seed & Deployment | P1 | ✅ |

---

## Epic 1: Design System & App Shell

**Goal:** Fondasi UI/UX selaras brand Lebah Madu; navigasi role-aware; responsif.

### Story 1.1: Design tokens & global styles

As a **developer**, I want centralized design tokens in theme + CSS variables, so that all modules look consistent.

**Acceptance Criteria:**
- **Given** DESIGN.md tokens
- **When** app loads
- **Then** all `--bee-*` variables in `main.css` match DESIGN.md CSS Variables section
- **And** Baloo 2 + Nunito Sans loaded
- **And** `primevue-overrides.css` imported; DataTable header cream, Dialog radius 18px
- **And** input min-height ≥44px on form controls

**Covers:** UX-DR18, NFR-3, NFR-9

### Story 1.2: Grouped sidebar navigation

As a **staff user**, I want menu grouped by domain, so that I find modules quickly.

**Acceptance Criteria:**
- **Given** logged-in user with role
- **When** viewing sidebar
- **Then** only permitted routes shown in groups SISWA/KEUANGAN/PEGawai/KEGIATAN
- **And** active route highlighted magenta

**Covers:** FR-2, UX-DR1

### Story 1.3: Topbar breadcrumb & page title

As a **user**, I want to know where I am, so that I don't get lost.

**Covers:** UX-DR2

### Story 1.4: Responsive shell (drawer + collapsible sidebar)

As a **admin TU with tablet**, I want usable navigation on smaller screens.

**Covers:** FR-1, UX-DR10, NFR-3

### Story 1.5: Shared components (EmptyState, PeriodPicker, PageLayout, KpiCard)

As a **developer**, I want reusable UX primitives, so that modules stay consistent.

**Acceptance Criteria:**
- **Given** `shared/components/`
- **Then** exports: `EmptyState`, `PeriodPicker`, `PageLayout`, `KpiCard`
- **And** `core/format.ts` exports `formatRp()` used by KpiCard and documented in DESIGN.md
- **And** ListPage pattern documented — no ad-hoc `.page-head` in new code

**Covers:** UX-DR7, UX-DR8, UX-DR9, UX-DR16, UX-DR17, UX-DR19, UX-DR21

### Story 1.6: Role-based nav labels & SoD route guard

As a **non-accountant staff user**, I want menus that match my daily tasks, so that I am not confused by accounting jargon.

**Acceptance Criteria:**
- **Given** user Administration
- **When** viewing sidebar
- **Then** no items for Jurnal, COA, Laporan, Tunggakan Tagihan
- **And** router guard redirects forbidden finance routes to role home

- **Given** user Finance or SchoolPrincipal
- **When** viewing sidebar group KEUANGAN
- **Then** items include **Pemasukan** and **Pengeluaran** (not raw "Jurnal" only)
- **And** both navigate to `/jurnal` with query `jenis=masuk|keluar` preset filter

**Covers:** FR-2, FR-13, NFR-11, UX-DR13, UX-DR14, UX-DR15

### Story 1.7: Logo SVG assets

As a **user**, I want professional branding (not emoji), so that the app feels production-ready.

**Acceptance Criteria:**
- **Given** login and sidebar
- **Then** `public/logo-lebah.svg` displayed (64px login, 40px sidebar)
- **And** `favicon.svg` updated to match brand
- **And** no emoji 🐝 in production shell/login

**Covers:** UX-DR11, UX-DR20

### Story 1.8: Migrate existing views to design system (E1 gate)

As a **developer**, I want all existing pages on PageLayout + formatRp, so that UI feels cohesive before new modules.

**Acceptance Criteria:**
- **Given** DESIGN.md E1 Definition of Done checklist
- **When** E1.8 complete
- **Then** migrated: dashboard, siswa, tagihan, jurnal, pegawai, gaji, pinjaman, aset, kegiatan, anggaran, periode, laporan
- **And** each uses PageLayout; nominal uses formatRp; empty states use EmptyState
- **And** no duplicate scoped `.page-head`/`.toolbar` patterns remain

**Covers:** UX-DR22, UX-DR5, UX-DR12, NFR-9

**Gate:** E2+ stories **blocked** until E1.8 ✅

---

## Epic 2: Modul Siswa & Absensi

**Goal:** Menutup mockup MENU SISWA.

### Story 2.1: Extend Siswa CRUD fields

Fields: jenjang, kelompok, tanggal lahir, periode filter.

**Covers:** FR-3, FR-25

### Story 2.2: Master Jenjang & Kelompok pages

CRUD `/jenjang`, `/kelompok` API.

**Covers:** FR-25

### Story 2.3: Absensi harian — Wizard + AttendanceGrid

3-step wizard; chip toggles; bulk save ke `kehadiran-siswa` API.

**Covers:** FR-4, UX-DR3, UX-DR4, UJ-1

### Story 2.4: Rekapitulasi absensi siswa

Agregat per siswa; export CSV optional.

**Covers:** FR-5

### Story 2.5: Absensi read-only untuk TeacherInCharge

Guru koordinator melihat rekap absensi kelompok (read-only); tidak bisa edit.

**Acceptance Criteria:**
- **Given** user TeacherInCharge
- **When** opening `/rekap-siswa` or `/absensi-siswa`
- **Then** data visible but save/edit controls hidden
- **And** toast explains "Hubungi Admin TU untuk koreksi absensi"

**Covers:** FR-27, UX-DR15

---

## Epic 3: Modul Katering

**Goal:** Menutup mockup KATERING.

### Story 3.1: Rekap katering view

Filter bulan/jenjang/kelompok; tarif v1 flat Rp 22.000 (superseded → 20/10 di E10).

**Covers:** FR-6

### Story 3.2: Menu katering mingguan CRUD

Senin–Jumat text menu via `menu-katering` API.

**Covers:** FR-7

---

## Epic 4: Modul Jemputan

**Goal:** Menutup mockup JEMPUTAN.

### Story 4.1: Data armada jemputan CRUD

**Covers:** FR-8

### Story 4.2: Pendaftaran jemputan siswa

Link siswa + harga + alamat.

**Covers:** FR-9

### Story 4.3: Data pendamping & rekap jemputan

Assignment guru per armada/tanggal; rekap billing.

**Covers:** FR-10

---

## Epic 5: Keuangan Lengkap

**Goal:** Menutup mockup MENU KEUANGAN + coretan brief.

### Story 5.1: COA management UI ✅

CRUD golongan, sub-golongan, coa; import CSV referensi.

**Covers:** FR-11

### Story 5.2: Anggaran UI polish ✅

Kepala 9 pairing indicator dengan beban 5.x.

**Covers:** FR-12

### Story 5.3: Jurnal UX polish + Pemasukan/Pengeluaran entry ✅

Balance indicator, submit/approve flow clarity; preset filter from nav alias.

**Acceptance Criteria:**
- **Given** nav "Pemasukan"
- **When** page loads
- **Then** jurnal list filtered to akun pendapatan (4.x) and create form pre-selects pendapatan accounts
- **Given** nav "Pengeluaran"
- **Then** filter preset beban (5.x)

**Covers:** FR-13, UX-DR13

### Story 5.4: Laporan + PeriodPicker ✅

All tabs + tahun ajaran filter.

**Covers:** FR-14, UX-DR7

### Story 5.5: Export/print laporan ✅

Print CSS + optional PDF lib.

**Covers:** FR-15

### Story 5.6: Tunggakan tagihan (Finance read-only) ✅

Daftar tagihan outstanding; filter periode/siswa; link ke siswa; **no** bayar button.

**Covers:** FR-26

### Story 5.7: Laporan arus kas formal (v1.1 — deferred)

ISAK 35 arus kas report tab; **out of v1 MVP** — track as backlog after SM-1/SM-2.

**Covers:** FR-14 v1.1

---

## Epic 6: Tagihan & Pendaftaran

**Goal:** Alur tagihan end-to-end sesuai mockup & website sekolah.

### Story 6.1: Generate tagihan enhanced ✅

Pull absensi bulan lalu + SPP from siswa.

**Covers:** FR-16

### Story 6.2: Invoice editor & line items ✅

Edit/delete lines; sections TAHUNAN/BULANAN/LAIN.

**Covers:** FR-17

### Story 6.3: InvoicePreview + cetak faktur ✅

Print layout for parents.

**Covers:** FR-18, UX-DR6

### Story 6.4: Pendaftaran siswa UI ✅

Trial → bayar-sitin → finalisasi.

**Covers:** FR-24

---

## Epic 7: Pegawai & Payroll

**Goal:** Menutup mockup MENU PEGAWAI.

### Story 7.1: Pegawai work periode field ✅

**Covers:** FR-19

### Story 7.2: Absensi pegawai grid ✅

**Covers:** FR-20

### Story 7.3: Gaji slip fields lengkap ✅

Asuransi, lunch, loan, grand total breakdown.

**Covers:** FR-21

---

## Epic 8: Audit & Governance

### Story 8.1: Audit log viewer

Read-only DataTable `audit-log` API; filter by table/user/date.

**Covers:** FR-22, NFR-8

---

## Epic 9: Quality, Seed & Deployment

### Story 9.1: Seed script 4 roles + demo data

Management command: users, siswa sample, COA from CSV.

**Covers:** FR-23

### Story 9.2: Frontend vitest setup + critical tests

Login, router guard, tagihan generate mock.

**Covers:** NFR-5

### Story 9.3: Docker compose + CI workflow

**Covers:** NFR-6, NFR-7

### Story 9.4: README runbook & UAT checklist

3 persona walkthrough UJ-1/2/3.

**Covers:** SM-1, SM-2

---

## Implementation Log (Monitoring)

| Date | Story | Status | Notes |
|------|-------|--------|-------|
| 2026-06-28 | DS patch | ✅ | PageLayout, formatRp, KpiCard, logo, E1 gate |
| 2026-06-28 | Planning patch | ✅ | FR-26/27, UX non-akuntan, nav alias |
| 2026-06-28 | E9.1 Seed | backend/accounts/management/commands/seed_demo.py | ✅ | 4 users, <password demo dari seed lokal> |
| 2026-06-28 | E1.1–1.8 | frontend/src/* | ✅ | Gate passed — E2 unblocked |
| | E2.3 | 🔲 | Absensi wizard — next |

**Legend:** ✅ Done · 🔄 In Progress · 🔲 Todo · ⏸ Blocked

---

## Recommended Execution Order

1. **E9.1** Seed users (unblock UAT)
2. **E1** Shell & design system (**8 stories — E1.8 gate wajib sebelum E2**)
3. **E2 → E3 → E4** Operational chain (absensi → tagihan inputs)
4. **E6** Tagihan complete
5. **E5** COA + laporan export
6. **E7, E8, E9** Polish
7. **E10** Legacy alignment (v1.1 — post-v1, **on hold** sampai give go)

**Next action (v1):** ✅ E1–E9 selesai. **E10** — lihat [13-LEGACY-ALIGNMENT-GUIDE.md](../../docs/13-LEGACY-ALIGNMENT-GUIDE.md) (planning done, coding on hold).

---

## Epic 10: Legacy Alignment & Real Data Foundation (v1.1)

> **Satu epic unified** — menggabungkan semua item prioritas hijau + kuning dari investigasi `legacy-data/`. Bukan per-item epic terpisah.
>
> **Guide eksekusi:** [docs/13-LEGACY-ALIGNMENT-GUIDE.md](../../docs/13-LEGACY-ALIGNMENT-GUIDE.md)  
> **Investigasi:** `_bmad-output/implementation-artifacts/investigations/legacy-data-fit-investigation.md`  
> **Referensi tarif PDF:** `legacy-data/biaya masuk PG 2025-2026.pdf`, `legacy-data/Brosur Pricelist RA 2526.pdf`

**Goal:** Selaraskan aturan billing, seed data riil, payroll, anggaran, export, dan dashboard dengan spreadsheet operasional TK — demo sidang dengan grafik & angka yang masuk akal.

**Dependency chain:** L0 seed → L1 billing rules → L2 batch tagihan → L3 payroll → L4 anggaran/rekap/dashboard → L5 validasi

### Story 10.1: `seed_legacy` management command

Import roster siswa, absensi pilot (anchor Jul-2024), pegawai, armada dari CSV matrix. Idempotent; `--dry-run` + log unmatched rows. NIS sintetis jika CSV hanya nama.

**Covers:** FR-28  
**Sources:** `Absen siswa (3).xlsx - TK A/B.csv`, `KAFALAH APRIL '2025.xlsx - Salary Table.csv`, `Website_Lebah Madu.xlsx - JEMPUTAN.csv`

### Story 10.2: Template komponen biaya TP (tahunan)

Model `KomponenBiayaTemplate` + seed dari TP CSV + PDF pricelist. **Seed values dari PDF:** PG Sem I Rp 5.375.000; RA tahun 1 Rp 10.950.000; potongan PG→RA Rp 1jt, kakak RA Rp 500rb.

**Covers:** FR-29  
**Sources:** `TP 2025-2026.xlsx - *.csv`, `biaya masuk PG 2025-2026.pdf`, `Brosur Pricelist RA 2526.pdf`

### Story 10.3: Katering differentiated

Implement keputusan resmi 2026-06-30: **Rp 20.000/hari Sen–Kam + Rp 10.000 snack Jumat**; billing per weekday dari absensi; PG skip auto-tagihan. Extend `TarifKatering` (dua field) + `billing.py`. Validasi vs `laporan katering.csv`.

**Covers:** FR-30

### Story 10.4: Jemput per-trip billing

Ganti flat bulanan → `jemput_datang` + `jemput_pulang` × tarif per hari hadir. UI rekap selaras legacy.

**Covers:** FR-31  
**Sources:** `Absen Jemputan 2023-2024 … - *.csv`

### Story 10.5: Batch generate tagihan

API `POST /tagihan/generate-batch/` + UI: pilih jenjang/kelompok/TA, preview, commit. Integrasi komponen TP tahunan (10.2).

**Covers:** FR-32

### Story 10.6: Payroll KAFALAH field mapping

Mapping kolom Salary Table → `GajiPegawai`: tunjangan jabatan, transport, uang makan (jam × Rp), potongan. Slip preview mirror `Slip.csv`.

**Covers:** FR-33

### Story 10.7: Auto potong pinjaman ke gaji

Service link `PinjamanPegawai` → potongan otomatis saat posting gaji; saldo pinjaman decrement.

**Covers:** FR-34  
**Sources:** `KAFALAH APRIL '2025.xlsx - Pinjaman.csv`

### Story 10.8: Import anggaran CSV + realisasi

Load `realisasi anggaran sekolah.xlsx - Sheet1.csv` + rencana pemasukan; sinkron dashboard realisasi vs anggaran.

**Covers:** FR-35

### Story 10.9: Export rekap mirror legacy

Download CSV layout seperti `laporan katering.csv` dan rekap jemput bulanan (kolom & urutan legacy).

**Covers:** FR-36

### Story 10.10: Dashboard kepsek — KPI operasional

Extend `DashboardRingkasan`: collection rate, absensi/katering headcount, pending jurnal approval, sparkline terisi dari data legacy (bukan dummy kosong).

**Covers:** FR-37

### Story 10.11: `validate_legacy` command

Compare tagihan/katering/jemput/gaji hitung sistem vs CSV; report diff ± toleransi; input Bab IV skripsi.

**Covers:** FR-38

### Story 10.12: Tooling & UAT extend

Scripts `seed-legacy.sh`, `validate-legacy.sh`; extend `uat_walkthrough --legacy-month`; CI smoke optional.

**Covers:** NFR-12 (runbook legacy)

---

## Implementation Log (Monitoring) — E10

| Date | Story | Status | Notes |
|------|-------|--------|-------|
| 2026-06-30 | E10 planning | ✅ | Guide + PRD §10 + epics; implement on hold |
| | 10.1–10.12 | ✅ | E10 complete — lihat execution log |

**Legend:** ✅ Done · 🔄 In Progress · 🔲 Todo · ⏸ Blocked

---

## Epic E11: UAT Dosen — COA Final, CRUD & UX Humanis

> **Trigger:** Feedback UAT dosen akuntansi (2026-07-02). Guide: [14-DOSEN-FEEDBACK-GUIDE.md](../../docs/14-DOSEN-FEEDBACK-GUIDE.md)

**Goal:** COA selaras COA Final (~187 akun); pesan error/sukses humanis; CRUD fleksibel (jurnal draft, kelompok, absensi); filter & banner informatif per halaman.

### Story 11.1: Import COA Final CSV

**Covers:** FR-11 (revised)  
**AC:** ≥180 akun; hierarki golongan/sub; resolver untuk anggaran/jurnal legacy

### Story 11.2: Human error messages

**Covers:** NFR-1 (revised)  
**AC:** FK/constraint → bahasa Indonesia; tidak tampil nama PostgreSQL constraint

### Story 11.3: COA RBAC & copy Kepsek

**Covers:** NFR-11  
**AC:** Kepsek read-only + banner jelas; Keuangan full CRUD

### Story 11.4: Jurnal draft CRUD + akun lengkap

**Covers:** FR-13  
**AC:** Edit/hapus draft; dropdown akun dari COA penuh

### Story 11.5: Fix katering UI kolom

**Covers:** FR-6  
**AC:** Tarif & Total tidak overlap

### Story 11.6: Rekap absensi filter + tahun arsip

**Covers:** FR-5  
**AC:** Tahun 2024+ dari data; filter bulan benar

### Story 11.7: CRUD kelompok & pindah siswa

**Covers:** FR-25  
**AC:** Halaman kelola jenjang/kelompok; update kelompok siswa

### Story 11.8: Absensi siswa CRUD

**Covers:** FR-4  
**AC:** Edit/hapus absensi per tanggal

### Story 11.9: Dashboard filter periode

**Covers:** FR-37 (extend)  
**AC:** Filter hari/bulan/tahun; KPI refresh

### Story 11.10: Katering upload gambar + dashboard widget

**Covers:** FR-7  
**AC:** Foto menu per hari; tampil di dashboard

### Story 11.11: Kegiatan + tahun pelajaran + posting akun

**Covers:** FR-12 (extend)  
**AC:** Periode TA; kegiatan link akun penanggung jawab

### Story 11.12: Arsip rekap absensi

**Covers:** FR-5 (extend)  
**AC:** TA lama archived; default TA aktif

---

## Implementation Log (Monitoring) — E11

| Date | Story | Status | Notes |
|------|-------|--------|-------|
| 2026-07-02 | E11 planning | ✅ | Investigation + sprint proposal + guide 14 |
| | 11.1–11.12 | 🔲 | P0 first: 11.1–11.4 |
