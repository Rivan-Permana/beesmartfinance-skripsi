---
title: Sprint Change Proposal — UX Non-Akuntan & Gap Planning Patch
date: 2026-06-28
author: Sinarivan-permananjung
status: approved
trigger: Investigasi per-role (#3, #4) — gap perencanaan sebelum eksekusi
scope: Minor (docs only, no code)
---

# Sprint Change Proposal

## 1. Issue Summary

Setelah review komprehensif per role dan assessment FE UI, ditemukan **7 gap perencanaan** yang belum explicit di PRD/epics/UX — bukan bug implementasi, tapi keputusan produk yang perlu di-lock sebelum coding.

**Trigger:** User hold implementasi; minta patch docs dulu (investigasi #3 + #4 + correct-course).

**Evidence:**
- Investigation `school-finance-standards-investigation.md` follow-up #3, #4
- FE prototype quality vs DESIGN.md target (E1 belum jalan)
- Backend SoD: tagihan `IsAdministration`; Finance tidak bayar tagihan

## 2. Impact Analysis

### Epic Impact

| Epic | Perubahan |
|------|-----------|
| **E1** | +Story 1.6 (nav alias + SoD guard) — 5→6 stories |
| **E2** | +Story 2.5 (TeacherInCharge read-only absensi) — 4→5 stories |
| **E5** | +Story 5.6 (tunggakan read-only), +Story 5.7 (arus kas v1.1 deferred); Story 5.3 expanded — 5→7 stories |
| E3–E4, E6–E9 | Tidak berubah scope |

### Story Impact

- **Tidak ada story completed** yang perlu rollback (semua 🔲).
- **Tidak ada epic baru** — Direct Adjustment dalam struktur existing.

### Artifact Conflicts Resolved

| Artifact | Conflict | Resolution |
|----------|----------|------------|
| PRD FR-2 | Admin bisa lihat jurnal? | Explicit: Admin **tidak** punya route akuntansi |
| Mockup KEUANGAN | Pemasukan/Pengeluaran terpisah | Nav alias → satu JurnalListView + preset |
| EXPERIENCE IA | TeacherInCharge absensi "?" | Confirmed read-only (FR-27) |
| FR-14 | Arus kas ISAK | v1.1 deferred; dashboard prediksi kas cukup v1 |
| UJ-1 | Finance posting pembayaran | Fixed: Admin **Bayar** + Finance **Tunggakan** read-only |

### Technical Impact

- **No stack change** — Vue 3 + PrimeVue 4 confirmed.
- FE: route `/tunggakan-tagihan`, query param `jenis` on `/jurnal`, read-only mode flag on absensi views.
- BE: **no change required** for FR-26/27 (existing tagihan + kehadiran APIs).

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**

- Effort: **Low** (docs patched; implementation follows existing epic order)
- Risk: **Low**
- Timeline: +0 hari planning; +~2–3 story-days implementation spread across E1/E2/E5
- MVP: **unchanged** — arus kas formal explicitly v1.1

**Not chosen:**
- Option 2 Rollback — N/A (nothing shipped)
- Option 3 MVP Review — tidak perlu; scope v1 tetap

## 4. Detailed Change Proposals

### PRD (`prd-beesmartfinance-skripsi-2026-06-28/prd.md`)

| Section | Change |
|---------|--------|
| §2.2 | **NEW** Prinsip Non-Akuntan vs Akuntansi Proper |
| §2.4 FR-2 | Admin excludes finance routes; Finance nav alias Pemasukan/Pengeluaran + Tunggakan |
| §4.4 FR-13 | Nav alias → Jurnal preset filter |
| §4.4 FR-14 | v1.1 arus kas deferred note |
| §4.7 | **NEW** FR-26 Tunggakan read-only, FR-27 TeacherInCharge absensi read-only |
| §6.1 MVP | FR-1 s/d FR-27 in scope (except FR-14 v1.1) |
| UJ-1 | Admin Bayar + Finance monitor tunggakan |

### Epics (`epics.md`)

| Story | Change |
|-------|--------|
| 1.6 | Role-based nav labels & SoD route guard |
| 2.5 | TeacherInCharge read-only absensi |
| 5.3 | Jurnal + Pemasukan/Pengeluaran entry expanded |
| 5.6 | Tunggakan tagihan Finance read-only |
| 5.7 | Laporan arus kas v1.1 deferred |
| Inventory | +FR-26, FR-27, NFR-11, UX-DR13–15 |

### UX (`EXPERIENCE.md`, `DESIGN.md`)

| Doc | Change |
|-----|--------|
| EXPERIENCE | **NEW** Bahasa UI per Role; SoD; Flow D tunggakan; IA updated |
| DESIGN | Sidebar nav label rules per role |

### Execution docs

| Doc | Change |
|-----|--------|
| `docs/11-FRONTEND-GUIDE.md` | Checklist + tunggakan route |
| `docs/10-EXECUTION-LOG.md` | Story counts E1/E2/E5 updated |

## 5. Implementation Handoff

**Scope classification:** Minor — docs complete; ready for dev.

**Handoff:** Developer agent via `bmad-dev-story`

**Execution order (unchanged):**
1. E9.1 Seed users
2. **E1** (include 1.6 SoD + nav alias)
3. E2 → E3 → E4 → E6
4. E5 (include 5.3, 5.6; skip 5.7 until v1.1)
5. E7, E8, E9

**Success criteria:**
- [ ] Administration sidebar has zero finance accounting items
- [ ] Finance sees Pemasukan/Pengeluaran/Tunggakan Tagihan
- [ ] TeacherInCharge absensi is read-only with info banner
- [ ] UJ-1 end-to-end without manual API

**User approval:** Implicit via "patch aja dulu … baru abis itu bisa eksekusi" (2026-06-28).
