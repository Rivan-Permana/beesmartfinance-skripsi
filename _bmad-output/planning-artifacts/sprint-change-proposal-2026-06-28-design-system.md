---
title: Sprint Change Proposal — Design System Docs Completion
date: 2026-06-28
author: Sinarivan-permananjung
status: approved
trigger: Investigate #6 — 5 gap DESIGN.md; user minta patch sebelum eksekusi FE
scope: Minor (docs only)
parent: sprint-change-proposal-2026-06-28.md
---

# Sprint Change Proposal — Design System Completion

## 1. Issue Summary

User ingin **design system docs jelas sepenuhnya** supaya saat eksekusi FE selesai tidak terasa kureng lagi. Investigasi #6 menemukan 5 gap spesifikasi di `DESIGN.md` yang belum explicit meski Epic E1 sudah ada.

**Trigger:** "patch dulu aja yang barusan" setelah audit DS.

## 2. Impact Analysis

| Epic | Change |
|------|--------|
| **E1** | 6 → **8 stories** (+1.7 Logo SVG, +1.8 Migrate views gate) |
| E1.1, E1.5 | Acceptance criteria expanded |
| E2–E9 | **Blocked** until E1.8 ✅ (explicit gate) |

| Artifact | Change |
|----------|--------|
| DESIGN.md | +PageLayout, KpiCard, ListPage, formatRp, PrimeVue skin, logo spec, CSS vars full, E1 DoD checklist |
| EXPERIENCE.md | +patterns PageLayout, ListPage, formatRp, KpiCard |
| epics.md | +UX-DR16–22, stories 1.7–1.8 |
| docs/11-FRONTEND-GUIDE.md | Rewritten around E1 gate + ListPage template |
| docs/10-EXECUTION-LOG.md | E1 0/8 |

**Technical:** No backend change. FE adds `core/format.ts`, `assets/primevue-overrides.css`, `shared/components/{PageLayout,KpiCard,EmptyState,PeriodPicker}.vue`, `public/logo-lebah.svg`.

## 3. Recommended Approach

**Direct Adjustment** — docs patch only; implementation unchanged order (E9.1 → E1 → E2…).

**Effort:** +1–2 hari dev for E1.7–1.8 (migration pass)  
**Risk:** Low  
**Benefit:** High — prevents "kureng" feeling from inconsistent CRUD pages

## 4. Changes Applied

### DESIGN.md
- PageLayout wireframe + slots
- KpiCard props
- ListPage CRUD pattern
- Logo asset table
- formatRp utility spec
- PrimeVue global skin table
- StatusTag semantic map
- Full CSS variables block
- **E1 Definition of Done** checklist (gate)

### Epics
- UX-DR16–22
- Story 1.7: Logo SVG
- Story 1.8: Migrate existing views (gate)
- Story 1.1, 1.5 AC expanded

## 5. Implementation Handoff

**Scope:** Minor — docs complete.

**Execution order:**
1. E9.1 seed
2. E1.1 → E1.6 (foundation)
3. E1.5 shared components
4. E1.7 logo
5. **E1.8 migrate all existing views** ← gate
6. E2+ only after E1.8 ✅

**Success criteria:** DESIGN.md E1 DoD checklist all checked; user UAT on siswa/tagihan/dashboard feels cohesive vs prototype.

**User approval:** "patch dulu aja yang barusan" (2026-06-28).
