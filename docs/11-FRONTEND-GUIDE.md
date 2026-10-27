# 🎨 Frontend Guide & Log — BeeSmart Finance v1

> Panduan implementasi frontend + log per-modul. **Area kerja utama** project saat ini.
>
> Master progress: [10-EXECUTION-LOG.md](./10-EXECUTION-LOG.md)

---

## Stack & Konvensi

| Item | Nilai |
|------|-------|
| Framework | Vue 3 + TypeScript + Vite |
| UI | PrimeVue 4 + `@primeuix/themes` (BeePreset) |
| State | Pinia (`stores/auth.ts`) |
| Router | Vue Router 5 + RBAC guard |
| API client | Axios → `/api/v1/` |
| Design ref | `_bmad-output/planning-artifacts/ux-designs/ux-beesmartfinance-skripsi-2026-06-28/DESIGN.md` |
| IA ref | `.../EXPERIENCE.md` |

**Jalankan dev:**

```bash
cd frontend
npm run dev          # http://localhost:5173
npm run gen:types    # sync OpenAPI → src/types/openapi.d.ts
```

---

## Struktur Folder (E1 ✅)

```
frontend/src/
├── core/
│   theme.ts          BeePreset
│   format.ts         formatRp() — WAJIB untuk nominal
│   api.ts, router.ts, errors.ts, config.ts
├── assets/
│   main.css          --bee-* tokens lengkap
│   primevue-overrides.css
├── stores/           auth.ts
├── types/            api.ts, openapi.d.ts
├── shared/
│   layout/AppShell.vue
│   components/
│       PageLayout.vue    ← wrapper semua halaman
│       KpiCard.vue
│       EmptyState.vue
│       PeriodPicker.vue
│       StatusTag.vue     (optional)
└── features/         <domain>/ api.ts + *View.vue
```

---

## Design System — E1 Gate ✅ (2026-06-28)

Referensi lengkap: `DESIGN.md` section **E1 Definition of Done**.

| # | Item | Story | Status |
|---|------|-------|--------|
| 1 | Full `--bee-*` tokens | E1.1 | ✅ |
| 2 | PrimeVue global skin | E1.1 | ✅ |
| 3 | `formatRp()` | E1.5 | ✅ |
| 4 | PageLayout | E1.5 | ✅ |
| 5 | KpiCard, EmptyState, PeriodPicker | E1.5 | ✅ |
| 6 | Grouped nav + SoD | E1.2, E1.6 | ✅ |
| 7 | Breadcrumb topbar | E1.3 | ✅ |
| 8 | Responsive drawer | E1.4 | ✅ |
| 9 | Logo SVG | E1.7 | ✅ |
| 10 | Migrate all existing views | E1.8 | ✅ |

**E2+ unblocked.** EmptyState di list view masih partial (siswa + tunggakan); sisanya pakai `#empty` text — polish nanti.

---

## Pola ListPage (CRUD standar)

```vue
<script setup lang="ts">
import PageLayout from "@/shared/components/PageLayout.vue"
import EmptyState from "@/shared/components/EmptyState.vue"
import { formatRp } from "@/core/format"
</script>

<template>
  <PageLayout title="Data Siswa" subtitle="Kelola siswa aktif">
    <template #actions>
      <Button label="Tambah Siswa" icon="pi pi-plus" @click="openCreate" />
    </template>
    <template #filters>
      <!-- search, PeriodPicker -->
    </template>
    <DataTable :value="rows" :loading="loading">
      <template #empty>
        <EmptyState message="Belum ada siswa." action-label="Tambah Siswa" @action="openCreate" />
      </template>
      <Column header="SPP">
        <template #body="{ data }">{{ formatRp(data.spp_nominal) }}</template>
      </Column>
    </DataTable>
  </PageLayout>
</template>
```

---

## Modul — Status & Target

### ✅ Sudah ada (E1.8 migrated)

| Route | View | API | Catatan |
|-------|------|-----|---------|
| `/login` | LoginView | auth/token | Logo SVG ✅ |
| `/dashboard` | DashboardView | dashboard/* | KpiCard + PeriodPicker |
| `/siswa` | SiswaListView | siswa/ | PageLayout + EmptyState |
| `/absensi-siswa` | AbsensiSiswaView | kehadiran-siswa/ | E2.3 wizard |
| `/rekap-siswa` | RekapSiswaView | kehadiran-siswa/ | E2.4 + E2.5 read-only guru |
| `/katering` | KateringView | menu-katering/ + kehadiran | E3 |
| `/jemputan` | JemputanView | armada-jemputan/ + pendaftaran-jemputan/ | E4 |
| `/tagihan` | TagihanListView | tagihan/ + preview | E6: preview → editor → cetak |
| `/jurnal` | JurnalListView | jurnal/ | Pemasukan/Pengeluaran via `?jenis=masuk\|keluar` |
| `/tunggakan-tagihan` | TunggakanTagihanView | tagihan/ | Read-only outstanding |
| `/coa` | CoaListView | golongan/sub-golongan/coa | E5.1 ✅ |
| `/laporan` | LaporanView | laporan/* + PeriodPicker | E5.4–5.5 ✅ |
| `/pegawai` | PegawaiListView | pegawai/ | E7.1 periode kerja |
| `/absensi-pegawai` | AbsensiPegawaiView | absen-pegawai/ | E7.2 grid + rekap |
| `/gaji` | GajiListView | gaji/ | E7.3 slip + posting |
| `/pinjaman` | PinjamanListView | pinjaman/ | kasbon |
| `/pendaftaran` | PendaftaranListView | pendaftaran-siswa/ | E6.4 ✅ |
| `/audit-log` | AuditLogView | audit-log/ | E8 ✅ read-only |
| `/aset` | AsetListView | aset/ | |
| `/kegiatan` | KegiatanListView | kegiatan/ | |
| `/anggaran` | AnggaranListView | anggaran/ | |
| `/periode` | PeriodeListView | periode/ | |

### ⚠️ Optional / tanpa halaman dedicated (bukan gap v1)

| Item | API | Status | Catatan |
|------|-----|--------|---------|
| CRUD Jenjang | `jenjang/` | ⚠️ | E2.1 optional — dipakai via wizard absensi & pendaftaran |
| CRUD Kelompok | `kelompok/` | ⚠️ | E2.2 optional — dipakai via wizard absensi |

---

## Konfigurasi Bisnis

**Resmi (2026-06-30):** katering **Rp 20.000** Sen–Kam + **Rp 10.000** Jumat — implementasi kode di **E10.3**.

v1 UI/backend masih referensi flat 22.000 sampai E10:

```typescript
// Saat E10.3 — update config + tampilan rekap
export const KATERING_TARIF_SEN_KAM = 20_000
export const KATERING_TARIF_JUMAT = 10_000
```

---

## Frontend Implementation Log

| Date | Item | File(s) | Status | Notes |
|------|------|---------|--------|-------|
| 2026-06-28 | DS planning patch | DESIGN.md, epics E1.7-1.8 | ✅ | PageLayout, formatRp, gate |
| 2026-06-28 | E1.1 tokens + overrides | main.css, primevue-overrides.css | ✅ | |
| 2026-06-28 | E1.2–1.6 AppShell + nav | AppShell.vue, navigation.ts, router.ts | ✅ | SoD flash, grouped nav |
| 2026-06-28 | E1.5 shared components | shared/components/*, core/format.ts | ✅ | |
| 2026-06-28 | E1.7 logo SVG | public/logo-lebah.svg | ✅ | |
| 2026-06-28 | E1.8 migrate views | features/*/*View.vue | ✅ | `npm run build` pass |
| 2026-06-28 | E4 jemputan | features/jemputan/* | ✅ | |
| 2026-06-28 | E7 pegawai & payroll | features/kepegawaian/* | ✅ | |
| 2026-06-28 | E8 audit log | features/audit/* | ✅ | read-only Principal + Finance |
| 2026-06-28 | E6.4 pendaftaran | features/pendaftaran/* | ✅ | |
| 2026-06-28 | E9 vitest + CI | vitest, docker-compose, README | ✅ | 20 unit tests |

---

## Testing (E9 ✅)

```bash
cd frontend && npm run test      # Vitest — formatRp, auth, router, tagihan API
cd frontend && npm run build
cd backend && python manage.py test
docker compose up --build        # optional full stack
```

Target: login flow, router guard, formatRp, tagihan generate mock — **20 tests passing**.

---

## Referensi Mockup Sempro

Path lokal: `../Layout Website Lebah Madu(FIX).xlsx/*.html`

Cross-module flow: `_bmad-output/planning-artifacts/epics.md`
