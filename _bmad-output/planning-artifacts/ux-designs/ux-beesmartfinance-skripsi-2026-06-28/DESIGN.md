---
name: BeeSmart Finance
description: SIA web TK Lebah Madu — branded-professional admin dashboard on PrimeVue 4
status: final
updated: 2026-06-28T3
colors:
  primary: '#E5197F'
  primary-foreground: '#FFFFFF'
  secondary: '#2E2A6E'
  secondary-foreground: '#FFFFFF'
  accent: '#F5A623'
  accent-foreground: '#1A1208'
  sky: '#4FB0DB'
  cream: '#F5EDD6'
  workspace: '#F6F7FB'
  success: '#2E9E5B'
  warning: '#F5A623'
  danger: '#C4116B'
  text-muted: '#6B7280'
typography:
  display:
    fontFamily: 'Baloo 2'
    fontWeight: '700'
  body:
    fontFamily: 'Nunito Sans'
    fontWeight: '400'
  label:
    fontFamily: 'Nunito Sans'
    fontWeight: '600'
    fontSize: '0.85rem'
rounded:
  sm: 8px
  md: 10px
  lg: 18px
  pill: 999px
spacing:
  sidebar: 260px
  sidebar-collapsed: 72px
  content-padding: 1.5rem
  section-gap: 1.25rem
components:
  sidebar:
    background: '{colors.secondary}'
    foreground: '#FFFFFF'
    active-background: '{colors.primary}'
  kpi-card:
    radius: '{rounded.md}'
    border: '1px solid rgba(46,42,110,0.08)'
  data-table:
    header-background: '{colors.cream}'
  btn-primary:
    background: '{colors.primary}'
    foreground: '{colors.primary-foreground}'
  btn-accent:
    background: '{colors.accent}'
    foreground: '{colors.accent-foreground}'
---

## Brand & Style

BeeSmart Finance mewujudkan identitas [Sekolah Lebah Madu](https://sekolahlebahmadu.com/) dalam **dashboard admin profesional** — bukan klon landing page. Brand masuk sebagai aksen (logo lebah, magenta primary, navy sidebar) sementara workspace terang menjaga keterbacaan angka keuangan untuk staf harian yang tidak tech-savvy.

**Prinsip:** Clarity over decoration. Setiap layar harus menjawab "apa yang harus saya lakukan sekarang?" dalam 5 detik.

## Colors

| Token | Hex | Pemakaian |
|-------|-----|-----------|
| Navy `{colors.secondary}` | #2E2A6E | Sidebar, heading |
| Magenta `{colors.primary}` | #E5197F | CTA, active nav, brand |
| Orange `{colors.accent}` | #F5A623 | Badge, highlight KPI |
| Cream `{colors.cream}` | #F5EDD6 | Table header, card accent |
| Workspace `{colors.workspace}` | #F6F7FB | Main background |

**Semantic money colors:** hijau = masuk/surplus, magenta = keluar/defisit — konsisten di dashboard & laporan.

## Typography

- **Baloo 2** — judul halaman, brand title (selaras web compro).
- **Nunito Sans** — body, label form, angka tabel.
- Angka nominal: `tabular-nums`, locale `id-ID`, prefix `Rp`.

## Layout & Spacing

- Desktop-first (staf TU di PC); tablet-friendly (absensi di kelas).
- Sidebar `{spacing.sidebar}`; collapsible icon-only `{spacing.sidebar-collapsed}`.
- Topbar: breadcrumb + nama user + role badge + logout.
- Konten: max-width none; padding `{spacing.content-padding}`.

## Elevation & Depth

- Card level 1: shadow-sm + border halus.
- Dialog/modal: PrimeVue default + radius `{rounded.lg}`.
- Toast: kanan atas, auto-dismiss 5s sukses / persist error.

## Shapes

- Button/input: `{rounded.sm}`.
- Login card: `{rounded.lg}`.
- Avatar/logo lebah: `{rounded.pill}`.

## Components

### Sidebar Nav Item
- Icon PrimeIcons + label.
- Active: `{components.sidebar.active-background}`.
- Group header untuk modul: SISWA, KEUANGAN, PEGAWAI, KEGIATAN.
- **Finance group labels:** gunakan **Pemasukan** / **Pengeluaran** (bukan hanya "Jurnal"); **Tunggakan Tagihan** untuk outstanding read-only.
- **Administration:** hanya group SISWA + PEGAWAI (absensi pegawai); tidak render group KEUANGAN akuntansi.

### Attendance Grid (khusus)
- Grid siswa dengan chip Hadir/Izin/Sakit/TH.
- Sub-row: Katering Ikut/Tidak, Jemput Ikut/Tidak (toggle chips, bukan dropdown panjang).

### Invoice Preview
- Header sekolah + periode + tabel line items + grand total + tombol Cetak.

### PageLayout (wajib semua halaman app)

Wrapper standar agar setiap modul terlihat konsisten — **jangan** buat header/toolbar ad hoc per view.

```
┌─────────────────────────────────────────────────┐
│ [breadcrumb dari AppShell topbar]               │
├─────────────────────────────────────────────────┤
│ PageLayout                                      │
│  ├─ header row: title (h1) + subtitle? + actions│
│  ├─ optional: filter bar / PeriodPicker         │
│  └─ content card (surface putih, radius md)     │
└─────────────────────────────────────────────────┘
```

| Slot / prop | Isi | Contoh |
|-------------|-----|--------|
| `title` | Judul halaman (Baloo 2) | "Data Siswa" |
| `subtitle` | Opsional, muted | "Kelola siswa aktif PG/TK" |
| `#actions` | Tombol primary kanan | "Tambah Siswa" |
| `#filters` | Search, PeriodPicker | toolbar siswa/tagihan |
| default slot | Isi card | DataTable, form, chart |

**File target:** `frontend/src/shared/components/PageLayout.vue`  
**CSS class:** `.bee-page`, `.bee-page__header`, `.bee-page__card`

### KpiCard (dashboard & ringkasan)

Kartu metrik reusable — ekstrak dari inline `DashboardView`.

| Prop | Tipe | Contoh |
|------|------|--------|
| `label` | string | "Kas & Bank" |
| `value` | string | `formatRp(1350000)` |
| `icon` | PrimeIcon class | `pi pi-wallet` |
| `tone` | `navy \| magenta \| orange \| green` | semantic money color |

Layout: icon bulat kiri + label kecil + value besar (`tabular-nums`, navy).  
Border: `{components.kpi-card.border}`; radius `{components.kpi-card.radius}`.

**File target:** `frontend/src/shared/components/KpiCard.vue`

### ListPage pattern (CRUD standar)

Semua modul list (siswa, tagihan, pegawai, …) **wajib** pakai:

1. `PageLayout` dengan title + `#actions` (CTA tambah)
2. `#filters` → search + filter dropdown
3. `DataTable` di dalam `.bee-page__card` dengan global skin (cream header)
4. `Dialog` form create/edit — lebar `32rem` (siswa) / `40rem` (tagihan/jurnal)
5. `EmptyState` jika `#empty` — jangan plain text "Belum ada data"

**Anti-pattern:** copy-paste `.page-head` + `.toolbar` scoped di tiap view.

### Logo & brand assets

Ganti emoji placeholder dengan asset SVG konsisten.

| Asset | Path | Ukuran | Pemakaian |
|-------|------|--------|-----------|
| Logo mark (lebah) | `frontend/public/logo-lebah.svg` | 64×64 login, 40×40 sidebar | Login, sidebar brand |
| Logo full (opsional) | `frontend/public/logo-lebah-madu.svg` | — | Struk/faktur cetak |
| Favicon | `frontend/public/favicon.svg` | 32×32 | Browser tab (existing, update artwork) |

**Sumber visual:** honeybee + orange circle selaras [sekolahlebahmadu.com](https://sekolahlebahmadu.com/); v1 boleh SVG sederhana (flat), bukan foto.

**Fallback dev:** emoji 🐝 hanya jika SVG belum ada — hapus setelah Story E1.7.

## Utilities

### formatRp (wajib, NFR-9)

Satu helper nominal uang — **dilarang** inline `Number(x).toLocaleString` di view.

**File:** `frontend/src/core/format.ts`

```typescript
/** Format nominal IDR — hindari float di display layer. */
export function formatRp(value: string | number | null | undefined): string {
  const n = Number(value ?? 0)
  if (Number.isNaN(n)) return "Rp 0"
  return "Rp " + n.toLocaleString("id-ID")
}
```

Gunakan di template: `{{ formatRp(row.spp_nominal) }}` — import dari `@/core/format`.

## PrimeVue Global Skin

Override global di `frontend/src/assets/primevue-overrides.css` (import dari `main.ts` setelah `main.css`).

| Komponen | Override | Token |
|----------|----------|-------|
| DataTable header | background cream, text navy, font-weight 600 | `{colors.cream}`, `{colors.secondary}` |
| DataTable body | striped-rows, hover highlight halus | — |
| Dialog | border-radius `{rounded.lg}` | 18px |
| Dialog header | navy title, Baloo 2 optional | — |
| Button primary | sudah via BeePreset primary | magenta |
| Input | min-height 44px (tablet touch, NFR-3) | — |
| Tag status | map ke semantic: success/warn/danger | lihat StatusTag di bawah |

### StatusTag semantic map (shared)

| Domain | Value | Severity | Label UI |
|--------|-------|----------|----------|
| Siswa | aktif | success | Aktif |
| Siswa | lulus | secondary | Lulus |
| Tagihan | lunas | success | Lunas |
| Tagihan | belum | warn | Belum Bayar |
| Jurnal | POSTED | success | Posted |
| Jurnal | PENDING | warn | Menunggu Approval |

**File target:** `frontend/src/shared/components/StatusTag.vue` atau constant map di `core/status.ts`.

## CSS Variables (lengkap — Story E1.1)

Semua token di `:root` (`frontend/src/assets/main.css`):

```css
:root {
  --bee-primary: #e5197f;
  --bee-primary-foreground: #ffffff;
  --bee-secondary: #2e2a6e;
  --bee-accent: #f5a623;
  --bee-accent-foreground: #1a1208;
  --bee-sky: #4fb0db;
  --bee-cream: #f5edd6;
  --bee-success: #2e9e5b;
  --bee-warning: #f5a623;
  --bee-danger: #c4116b;
  --bee-workspace: #f6f7fb;
  --bee-text-muted: #6b7280;
  /* legacy aliases (keep during migration) */
  --bee-magenta: var(--bee-primary);
  --bee-navy: var(--bee-secondary);
  --bee-orange: var(--bee-accent);
  --app-bg: var(--bee-workspace);
  --app-surface: #ffffff;
  --app-border: #e5e7eb;
  --app-text: #1f2430;
  --app-text-muted: var(--bee-text-muted);
  --bee-sidebar-width: 260px;
  --bee-sidebar-collapsed: 72px;
  --bee-radius-sm: 8px;
  --bee-radius-md: 10px;
  --bee-radius-lg: 18px;
}
```

## E1 Definition of Done (gate sebelum modul baru)

Epic E1 **belum selesai** sampai:

- [ ] Semua `--bee-*` di atas terpasang
- [ ] `primevue-overrides.css` aktif
- [ ] `PageLayout`, `KpiCard`, `EmptyState`, `PeriodPicker` ada di `shared/components/`
- [ ] `formatRp` dipakai di **semua** view yang tampilkan nominal
- [ ] Logo SVG mengganti emoji di Login + AppShell
- [ ] **Migrate** view existing: login, dashboard, siswa, tagihan, jurnal, pegawai, gaji, pinjaman, aset, kegiatan, anggaran, periode, laporan → PageLayout

Modul E2+ **dilarang** merge sebelum checklist gate ✅.

## Do's and Don'ts

**Do:** Bahasa Indonesia di UI; pesan error ramah (`core/errors.ts`); konfirmasi sebelum hapus/void; **selalu** `PageLayout` + `formatRp`.

**Don't:** Gradient penuh di workspace; font <14px untuk label form; sidebar hilang total di mobile tanpa drawer; **duplicate** page header/toolbar per view; inline `toLocaleString` untuk Rp.
