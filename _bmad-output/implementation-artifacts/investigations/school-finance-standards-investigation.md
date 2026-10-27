# Investigation: Evaluasi Standar Web Pengelolaan Keuangan Sekolah

## Hand-off Brief

1. **What happened.** Project BeeSmart Finance berhasil dijalankan (backend `:8000`, frontend `:5173`); backend kuat secara akuntansi/RBAC, frontend sudah menutup 12 modul inti, tetapi belum memenuhi standar web pengelolaan keuangan sekolah yang *production-ready*.
2. **Where the case stands.** Outcome 1 selesai — scope dan stronghold terpasang; evaluasi awal multi-aspek sudah dirangkum; login end-to-end ke dashboard belum diverifikasi (kredensial dev tidak tersedia di repo).
3. **What's needed next.** User mengirim file konteks tambahan (PRD, wireframe, kebutuhan sekolah); lalu lanjut Outcome 2 (perimeter evidence) atau Outcome 4 (trace gap FE↔BE per modul).

## Case Info

| Field            | Value                                                                      |
| ---------------- | -------------------------------------------------------------------------- |
| Ticket           | N/A                                                                        |
| Date opened      | 2026-06-28                                                                 |
| Status           | Active                                                                     |
| System           | macOS darwin 25.3.0; Python 3.13 + Django 5.2; Vue 3 + Vite 8 + PrimeVue 4 |
| Evidence sources | Runtime (runserver + vite dev), backend tests, source code, docs, OpenAPI schema |

## Problem Statement

User meminta: (1) jalankan project, (2) evaluasi apakah sudah memenuhi standar web pengelolaan keuangan sekolah yang baik, (3) elaborasi gap dari design, fungsionalitas, dll. User akan mengirim file konteks tambahan setelah evaluasi awal.

**Hipotesis user (Hypothesis #1):** Project sudah/s belum memenuhi standar web pengelolaan keuangan sekolah yang baik.

## Evidence Inventory

| Source              | Status    | Notes                                                                 |
| ------------------- | --------- | --------------------------------------------------------------------- |
| Runtime backend     | Available | `manage.py check` OK; `runserver :8000` aktif; `/api/docs/` → 200   |
| Runtime frontend    | Available | `npm run dev` → `http://localhost:5173/`; halaman login render      |
| Backend tests       | Available | 35 test lulus (`accounting`, `operations`, `accounts`)                |
| Frontend tests      | Missing   | Tidak ada file test di `frontend/`                                    |
| Source code FE      | Available | 12 route/modul di `frontend/src/core/router.ts`                       |
| Source code BE      | Available | 30+ resource di `backend/config/urls.py`                              |
| OpenAPI schema      | Available | `frontend/src/types/openapi.d.ts` — endpoint BE > modul FE            |
| Docs planning       | Partial   | `docs/09-BACKEND-PROGRESS-CHECKLIST.md` backend ✅; FE checklist outdated |
| project-context.md  | Missing   | Glob tidak menemukan file                                             |
| Docker/deployment   | Missing   | Tidak ada Dockerfile                                                  |
| Login E2E           | Partial   | UI login tampil; kredensial dev tidak tersedia di repo                |
| User-provided files | Pending   | User akan kirim file konteks lanjutan                                 |

## Investigation Backlog

| # | Path to Explore | Priority | Status | Notes |
| - | --------------- | -------- | ------ | ----- |
| 1 | Gap FE vs BE endpoint | High | Open | COA, kehadiran, katering, jemputan, pendaftaran, audit-log |
| 2 | Login E2E semua role | High | Blocked | Butuh kredensial atau seed user dari user |
| 3 | User-provided context files | High | Open | PRD, kebutuhan sekolah, desain |
| 4 | Responsive/a11y audit | Medium | Open | AppShell tanpa breakpoint mobile |
| 5 | Deployment readiness | Medium | Open | No Docker, no CI visible |
| 6 | Compliance BOS/Permendikbud | Low | Open | Butuh dokumen kebutuhan sekolah |

## Timeline of Events

| Time        | Event                              | Source              | Confidence |
| ----------- | ---------------------------------- | ------------------- | ---------- |
| 2026-06-28  | Backend check passed               | `manage.py check`   | Confirmed  |
| 2026-06-28  | 35 backend tests OK                | test runner         | Confirmed  |
| 2026-06-28  | Frontend dev server ready :5173    | vite output         | Confirmed  |
| 2026-06-28  | 3 users in DB (keuangan, kepsek)   | Django shell        | Confirmed  |
| 2026-06-28  | No Administration/TeacherInCharge user | Django shell    | Confirmed  |

## Confirmed Findings

### Finding 1: Stack berjalan lokal tanpa error konfigurasi

**Evidence:** `backend/manage.py check` → 0 issues; HTTP 200 dari `/api/docs/` dan `/`.

**Detail:** Backend Django + PostgreSQL dan frontend Vite dapat dijalankan di environment dev saat ini.

### Finding 2: Backend memenuhi fondasi SIA sekolah yang kuat

**Evidence:** `backend/config/urls.py:53-97`, `database/schemas/01_init_schema.sql`, `docs/09-BACKEND-PROGRESS-CHECKLIST.md`

**Detail:** Double-entry jurnal, COA, anggaran, periode tutup buku, maker-checker (submit/approve/void), audit log DB trigger, auto-posting tagihan/gaji/aset, laporan neraca/laba rugi/realisasi anggaran, RBAC 4 role, JWT + throttle login.

### Finding 3: Frontend menutup 12 modul inti, BE punya lebih banyak endpoint tanpa UI

**Evidence:** `frontend/src/core/router.ts:27-99` vs `backend/config/urls.py:53-78`

**Detail:** FE: dashboard, jurnal, siswa, tagihan, pegawai, gaji, pinjaman, aset, kegiatan, anggaran, periode, laporan. BE tambahan tanpa halaman FE: `coa`, `golongan`, `sub-golongan`, `audit-log`, `kehadiran-siswa`, `absen-pegawai`, `menu-katering`, `armada-jemputan`, `pendaftaran-jemputan`, `pendaftaran-siswa`, `jenjang`, `kelompok`.

### Finding 4: Tidak ada test frontend dan belum ada artefak deployment

**Evidence:** glob `frontend/**/*test*` → 0; glob `Dockerfile*` → 0

### Finding 5: Desain brand konsisten tapi belum mobile-first

**Evidence:** `frontend/src/core/theme.ts`, `frontend/src/shared/layout/AppShell.vue:96-103` (sidebar fixed 250px, no `@media`); hanya `DashboardView.vue` punya breakpoint.

## Deduced Conclusions

### Deduction 1: Untuk skripsi/demo internal — sudah cukup kuat

**Based on:** Finding 2, Finding 3

**Reasoning:** Modul akuntansi inti + operasional sekolah TK sudah terimplementasi end-to-end di level API; FE sudah menutup alur utama finance staff.

**Conclusion:** Layak sebagai proof-of-concept / sistem informasi akuntansi sekolah swasta.

### Deduction 2: Untuk standar web production sekolah — belum memenuhi

**Based on:** Finding 3, Finding 4, Finding 5, gap deployment

**Reasoning:** Operasional harian (absensi → tagihan, katering, jemputan, pendaftaran) butuh UI; audit trail tidak bisa diakses staf; tidak ada export laporan massal; tidak ada portal orang tua/pembayaran digital; testing & deploy belum matang.

**Conclusion:** Masih gap signifikan vs standar web pengelolaan keuangan sekolah modern.

## Hypothesized Paths

### Hypothesis 1: Project belum memenuhi standar web pengelolaan keuangan sekolah yang baik (secara keseluruhan)

**Status:** Open (cenderung Confirmed untuk production; Refuted untuk MVP skripsi)

**Theory:** Backend sudah near-complete; frontend dan aspek non-fungsional (UX mobile, testing, deploy, integrasi) belum.

**Supporting indicators:** Gap FE↔BE, no frontend tests, no Docker, no parent portal.

**Would confirm:** UAT dengan staf sekolah + checklist kebutuhan resmi sekolah.

**Would refute:** User menetapkan scope hanya SIA internal tanpa portal orang tua.

**Resolution:** Menunggu file konteks user + verifikasi login E2E.

## Missing Evidence

| Gap                         | Impact                                      | How to Obtain                    |
| --------------------------- | ------------------------------------------- | -------------------------------- |
| Kredensial login dev        | Tidak bisa audit UX dashboard per role      | User berikan atau seed script    |
| File kebutuhan sekolah/PRD  | Evaluasi compliance domain tidak presisi    | User kirim file                  |
| UAT dengan pengguna nyata   | Validasi UX untuk staf kurang tech-savvy    | Observasi / wawancara            |
| Benchmark sistem sejenis    | Perbandingan standar industri               | Research / dokumen user          |

## Source Code Trace

| Element       | Detail |
| ------------- | ------ |
| Entry point FE | `frontend/src/main.ts` → `router.ts` |
| Entry point BE | `backend/config/urls.py` → `/api/v1/` |
| Auth flow     | `frontend/src/stores/auth.ts` → JWT `/auth/token/` |
| RBAC          | `frontend/src/core/router.ts:105-117`, `backend/accounts/permissions.py` |

## Conclusion

**Confidence:** Medium

Backend sudah memenuhi standar teknis SIA sekolah (double-entry, SoD, audit DB, laporan). Frontend sudah fungsional untuk modul inti finance, tetapi **belum** memenuhi standar web pengelolaan keuangan sekolah yang *baik* secara holistik — terutama modul operasional pendukung tagihan, master data COA, audit UI, mobile UX, testing, deployment, dan integrasi eksternal (pembayaran/portal orang tua).

## Recommended Next Steps

### Fix direction

Prioritas gap: (1) UI modul operasional BE-only, (2) export/print laporan, (3) responsive layout, (4) frontend tests, (5) deployment pipeline.

### Diagnostic

Login dengan semua role; bandingkan checklist user setelah file konteks diterima.

## Reproduction Plan

1. `source .venv/bin/activate && python backend/manage.py runserver 8000`
2. `cd frontend && npm run dev`
3. Buka `http://localhost:5173/login`
4. API docs: `http://localhost:8000/api/docs/`

## Side Findings

- DB hanya 3 user; tidak ada user `Administration` atau `TeacherInCharge` untuk uji role-based menu — **Confirmed** via Django shell.
- Docs `09-BACKEND-PROGRESS-CHECKLIST.md` section 6 masih menyebut frontend belum; `02-FRONTEND-MIGRATION.md` sudah claim semua modul selesai — **Confirmed** inkonsistensi dokumentasi.

## Follow-up: 2026-06-28 #2

### New Evidence

- 14/14 file referensi sempro confirmed di folder induk
- Mockup HTML extracted (5 files) — gap matrix vs Vue app
- COA CSV + T_JURNAL patterns extracted (golongan 1-5, 9; KL/AP budget flow)
- Coretan brief sistem.png — requirement baseline keuangan
- Exa benchmark: SAKOLA, Siswamedia, SIAS literature, ISAK 35 references
- Website sekolahlebahmadu.com — komponen biaya PG/TK

### Additional Findings

**Finding 6:** Mockup sempro defines 5 top-level modules (SISWA, PEGAWAI, KATERING, JEMPUTAN, KEUANGAN) vs Vue's flat Finance-centric nav — **Confirmed** via HTML extract.

**Finding 7:** Cross-module flow absensi→katering/jemputan→tagihan is designed in mockup but broken in current FE — **Confirmed**.

**Finding 8:** COA golongan 9 mirrors golongan 5 one-to-one (86 accounts each) — **Confirmed** via diagrams CSV.

### Updated Hypotheses

**Hypothesis #1:** Project belum memenuhi standar web pengelolaan keuangan sekolah — **Status: Confirmed** for production; gap documented in PRD.

### Backlog Changes

- Item 3 → Done (referensi located)
- PRD + UX + Epics created → `_bmad-output/planning-artifacts/`

### Updated Conclusion

**Confidence:** High for gap analysis. **Fix direction:** Execute epics E1→E6 priority. Planning artifacts ready for implementation tracking.

## Follow-up: 2026-06-28 #3 — Verifikasi komprehensif per role

### Pertanyaan user

Apakah setelah docs selesai, cakupan per user/role sudah komprehensif vs standar fungsional?

### Temuan (Confirmed)

- Mockup sempro 5 modul HTML → mapped ke FR/E1–E8 di epics.md — **Confirmed**
- Backend RBAC: tagihan/siswa/katering/jemputan = `IsAdministration`; jurnal/COA = Finance; approve = Principal — **Confirmed** via `backend/accounts/permissions.py`, `operations/api/*.py`
- FE router saat ini Administration hanya `/siswa` + `/tagihan` — **Confirmed** via `frontend/src/core/router.ts:44-50`
- Semua epic masih 🔲 Not started — **Confirmed** via `docs/10-EXECUTION-LOG.md`

### Verdict per layer

| Layer | Komprehensif? | Score |
|-------|---------------|-------|
| **Perencanaan docs (v1 scope)** | Ya, untuk mockup sempro + 3 role + website TK | ~90% |
| **Implementasi codebase** | Belum — FE operasional putus | ~45% |
| **Standar industri penuh** | Tidak — portal ortu/VA/WA sengaja v2 | ~65% |

### Gap perencanaan yang tersisa (bukan implementasi)

1. Finance tidak punya UI tagihan/tunggakan dedicated (hanya dashboard widget) — minor
2. Laporan arus kas formal (ISAK) tidak explicit di epic — v1.1
3. Pemasukan/Pengeluaran mockup → digabung ke Jurnal; perlu UX label ramah staf
4. TeacherInCharge absensi: opsional read — belum di epic

### Hypothesis #1 update

**Status:** Confirmed — planning v1 cukup komprehensif untuk skripsi; implementasi belum.

## Follow-up: 2026-06-28 #4 — Non-akuntan & apakah perlu ganti stack FE

### Pertanyaan user

1. User bisa non-akuntan; sistem tetap pakai standar akuntansi proper — apakah docs sudah handle?
2. FE UI terasa jelek/kurang — harus ganti stack atau docs UX sudah cover perbaikan?

### Stronghold (Confirmed)

- Stack FE: Vue 3 + Vite + PrimeVue 4 + Pinia — `frontend/package.json`
- Epic E1 (Design System) status 🔲 — `docs/11-FRONTEND-GUIDE.md:81-91` (checklist 0/8 done)
- AppShell saat ini: flat nav 12 item, tanpa grouping/breadcrumb/drawer — `frontend/src/shared/layout/AppShell.vue:19-32,67-83`
- DESIGN.md + EXPERIENCE.md status **final** — mendefinisikan target UI, belum diimplementasi penuh

### Temuan per layer

| Aspek | Docs | Kode sekarang | Gap |
|-------|------|---------------|-----|
| Brand tokens | DESIGN.md `--bee-*` | `main.css` + BeePreset partial | E1.1 belum selesai |
| Grouped nav SISWA/KEUANGAN | E1.2, EXPERIENCE IA | Flat list | **Belum diimplementasi** |
| Breadcrumb + page title | E1.3 | Topbar cuma user+logout | **Belum** |
| Responsive drawer | E1.4 | Fixed sidebar 250px | **Belum** |
| Shared UX primitives | E1.5 EmptyState, Wizard, AttendanceGrid | Tidak ada folder `shared/components` | **Belum** |
| Modul operasional Admin | E2–E4, E6 | Hanya siswa+tagihan | **~70% modul missing** |
| Pola view | List+Dialog CRUD | Generic DataTable semua modul | Prototype quality |

### Non-akuntan vs akuntansi proper

**Confirmed arsitektur sudah benar:**
- Admin TU: operasional (absensi, tagihan, bayar) — auto-jurnal di backend, user tidak input debit/kredit — `backend/operations/api/billing.py` IsAdministration
- Finance: jurnal, COA, laporan — standar akuntansi
- PRD persona Bu Fitri: "familiar Excel, tidak tech-savvy" — `prd.md:48`

**Gap docs minor untuk non-akuntan:**
- EXPERIENCE.md masih pakai istilah akuntansi penuh di modul Finance (wajar)
- Belum explicit: **Admin tidak pernah lihat layar jurnal**; Finance dapat alias "Pemasukan/Pengeluaran" di nav
- Progressive disclosure untuk Finance non-akuntan — **Hypothesized**, perlu 1 story E1/E5

### Hypothesis #2: FE jelek karena stack salah

**Status:** Refuted

**Evidence:**
- PrimeVue 4 + custom BeePreset sudah dipakai; DashboardView punya KPI+charts brand-aligned — `frontend/src/features/dashboard/DashboardView.vue:30-67`
- Masalah dominan = **implementasi E1–E6 belum jalan**, bukan limitasi framework
- Ganti stack (React+shadcn, Nuxt UI, dll) = rewrite ~13 views + router + auth tanpa menambah fitur; risiko tinggi untuk skripsi

### Hypothesis #3: Docs UX sudah cover perbaikan FE

**Status:** Confirmed (strategic), Partial (tactical non-akuntan)

**Confirmed covered:**
- DESIGN.md: colors, typography, layout, AttendanceGrid, InvoicePreview
- EXPERIENCE.md: IA, flows A/B/C, state patterns, anti-patterns
- epics E1–E8: acceptance criteria perbaikan
- docs/11-FRONTEND-GUIDE: gap table per modul

**Partial / belum explicit:**
- Role-based language (Admin vs Finance labels)
- Page-level wireframe/mock per screen
- Komponen "Pemasukan"/"Pengeluaran" sebagai entry point Jurnal

### Verdict

| Pertanyaan | Jawaban |
|------------|---------|
| Ganti stack? | **Tidak perlu** — stay Vue 3 + PrimeVue 4 |
| Docs UX cover perbaikan? | **Ya ~85%** — cukup sebagai kontrak implementasi E1→E6 |
| Kenapa FE terasa jelek? | **Prototype belum lewat E1** + modul operasional missing + pola CRUD generic |
| Non-akuntan handled? | **Ya di arsitektur**; perlu +1–2 UX decision di docs (alias nav Finance) |

### Rekomendasi (hold implementasi)

1. **Jangan ganti stack**
2. Optional patch docs: tambah subsection "Bahasa UI per role" di EXPERIENCE.md
3. Saat hold dilepas: E9.1 seed → **E1 wajib first** sebelum modul baru

## Follow-up: 2026-06-28 #5 — Correct Course docs patch applied

### Changes applied (Confirmed)

| Artifact | Patch |
|----------|-------|
| `prd.md` | §2.2 non-akuntan; FR-13 alias; FR-26/27; FR-14 v1.1; UJ-1 fix |
| `epics.md` | Stories 1.6, 2.5, 5.3 expand, 5.6, 5.7; NFR-11; UX-DR13–15 |
| `EXPERIENCE.md` | Bahasa UI per Role; SoD; Flow D; IA lock |
| `DESIGN.md` | Nav label rules |
| `docs/11-FRONTEND-GUIDE.md` | Checklist + tunggakan |
| `docs/10-EXECUTION-LOG.md` | Story counts |
| `sprint-change-proposal-2026-06-28.md` | Created |

### Status

Planning **ready for execution**. Stack unchanged (Vue 3 + PrimeVue 4).

## Follow-up: 2026-06-28 #6 — Audit Design System (docs vs kode)

### Pertanyaan user

Apakah design system sudah oke supaya FE ke depan tidak terasa kureng?

### Stronghold (Confirmed)

- DESIGN.md status **final** — tokens, typography, 3 komponen khusus, do/don't
- Epic E1 = 6 stories (1.1–1.6), UX-DR1–15 — **semua 🔲**
- `frontend/src/shared/` — hanya `layout/AppShell.vue` + error; **tidak ada** `components/`
- BeePreset hanya override `primary` magenta — `frontend/src/core/theme.ts:6-21`
- `--bee-*` partial di `main.css` (6 vars); DESIGN.md punya 10+ token termasuk success/warning/workspace mapped partial

### Scorecard: Docs vs Implementasi

| Layer | Siap? | Score | Catatan |
|-------|-------|-------|---------|
| **DESIGN.md (blueprint)** | Cukup | ~80% | Kurang: PageLayout template, KPI card reusable, PrimeVue global overrides, logo asset spec |
| **EXPERIENCE.md (patterns)** | Baik | ~85% | State/flow/role language lengkap |
| **Epics E1 (acceptance criteria)** | Baik | ~90% | 6 stories actionable |
| **Kode FE (delivered DS)** | Belum | ~25% | Fonts ✅, tokens partial ✅, shell prototype ❌, shared components ❌ |

### Gap DESIGN.md (planning, belum blocking eksekusi)

1. **PageLayout** — pola standar: page title + subtitle + toolbar + content card (setiap ListView reinvent sendiri)
2. **formatRp()** utility — saat ini duplikat inline di setiap view
3. **PrimeVue global skin** — DataTable header cream, dialog radius lg belum ada di `main.css`/preset guide
4. **Logo asset** — masih emoji 🐝; DESIGN sebut logo lebah tapi tidak spec file SVG
5. **KPI Card** — hanya inline di DashboardView, belum komponen shared

### Gap implementasi (penyebab "kureng")

| E1 Story | Target | Kode sekarang |
|----------|--------|---------------|
| 1.1 tokens | Full `--bee-*` + BeePreset extended | Partial |
| 1.2 grouped nav | SISWA\|KEUANGAN\|… | Flat 12 item |
| 1.3 breadcrumb | Topbar | Cuma user+logout |
| 1.4 responsive | Drawer + collapsible | Fixed sidebar |
| 1.5 shared | EmptyState, PeriodPicker, ConfirmDialog | Tidak ada |
| 1.6 role nav | Pemasukan/Pengeluaran, SoD | Tidak ada |

### Hypothesis #4: Design system docs belum cukup → FE akan kureng

**Status:** Partially Confirmed

- **Docs side:** Refuted untuk blocking — E1 stories + DESIGN/EXPERIENCE cukup mulai implementasi
- **Delivery side:** Confirmed — perasaan kureng **100% karena E1 belum diimplementasi**, bukan karena stack atau konsep DS salah

### Verdict

Design system **planning OK untuk eksekusi** (~80–85%). **Belum OK sebagai produk** (25%). User tidak akan merasa puas UI sampai **E1 selesai 6/6** — baru modul E2+ pakai shared components.

### Rekomendasi

1. **Jangan patch docs besar lagi** — optional +3 item ke DESIGN.md (PageLayout, formatRp, logo spec) via correct-course kecil
2. **Eksekusi E1 wajib gate** — jangan buat modul CRUD baru sebelum shared components ada
3. **Definition of Done E1:** semua halaman existing (siswa, tagihan, jurnal…) di-migrate ke PageLayout + EmptyState + grouped nav

## Follow-up: 2026-06-28 #7 — Design system docs patch (correct-course)

### Trigger

User minta pastiin docs DS jelas supaya post-FE tidak kureng; patch 5 gap dari #6.

### Changes applied (Confirmed)

| Item | Location |
|------|----------|
| PageLayout, KpiCard, ListPage | DESIGN.md |
| formatRp utility | DESIGN.md + epics E1.5 |
| PrimeVue global skin | DESIGN.md + epics E1.1 |
| Logo SVG spec | DESIGN.md + Story E1.7 |
| E1 DoD gate | DESIGN.md + Story E1.8 |
| UX-DR16–22 | epics.md |
| ListPage code template | docs/11-FRONTEND-GUIDE.md |
| Proposal | sprint-change-proposal-2026-06-28-design-system.md |

### Hypothesis #4 update

**Status:** Confirmed resolved (docs) — **Refuted** as blocking gap; **Confirmed** delivery still requires E1.8 gate.

### Verdict post-patch

| Layer | Score |
|-------|-------|
| DESIGN.md blueprint | **~95%** |
| E1 stories | **8** (E1.8 = gate before E2+) |
| Risk "kureng" after full FE | **Low** if E1.8 enforced |

**Status:** DS docs complete. Ready: E9.1 → E1.1–1.8 → E2+.
