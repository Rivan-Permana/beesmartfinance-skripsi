---
name: BeeSmart Finance Experience
status: final
updated: 2026-06-28T3
design_ref: ./DESIGN.md
---

## Foundation

- **Form-factor:** Web SPA (Vue 3 + Vite), desktop-primary, tablet-secondary.
- **UI system:** PrimeVue 4 + custom `{colors.*}` preset (lihat DESIGN.md).
- **Users:** 3 persona operasional + 1 secondary (Guru Kegiatan).
- **Prinsip:** Backend & laporan mengikuti standar akuntansi proper; **UI disesuaikan per role** — staf operasional tidak perlu paham debit/kredit.

| Persona | Role DB | Home | Modul utama |
|---------|---------|------|-------------|
| Bu Fitri (Admin TU) | Administration | `/siswa` | Siswa, Absensi, Tagihan, Katering, Jemputan |
| Staff Keuangan | Finance | `/dashboard` | Pemasukan, Pengeluaran, COA, Anggaran, Laporan, Tunggakan |
| Pak Ali (Kepsek) | SchoolPrincipal | `/dashboard` | Approve + Dashboard + Tutup buku |
| Bu Desi (Guru) | TeacherInCharge | `/kegiatan` | Kegiatan, realisasi; absensi **read-only** |

## Bahasa UI per Role

Progressive disclosure: istilah dan layar akuntansi hanya untuk Finance/Principal.

| Role | Label nav (contoh) | Hindari | Catatan |
|------|-------------------|---------|---------|
| **Administration** | Siswa, Absensi, Tagihan, Bayar, Cetak Struk, Katering, Jemputan | Jurnal, COA, Neraca, Debit/Kredit | **Tidak ada route** ke modul keuangan akuntansi |
| **Finance** | Pemasukan, Pengeluaran, Anggaran, Laporan, Tunggakan Tagihan | — | "Pemasukan"/"Pengeluaran" → `/jurnal?jenis=masuk\|keluar` (satu komponen) |
| **SchoolPrincipal** | Sama Finance + Setujui Transaksi | — | Approve di layar jurnal |
| **TeacherInCharge** | Kegiatan, Realisasi | Input absensi | Read-only di rekap/absensi |

**Pesan khusus non-akuntan:**
- Bayar tagihan: "Pembayaran tercatat. Jurnal dibuat otomatis oleh sistem."
- POSTED (jika terlihat): "Transaksi sudah final. Hubungi Staff Keuangan untuk koreksi."
- Guru read-only absensi: "Hubungi Admin TU untuk mengubah absensi."

## Information Architecture

```
/login
/app (AppShell)
├── /dashboard              [Finance, Principal]
├── /siswa                  [Administration]
├── /absensi-siswa          [Administration write; TeacherInCharge read-only]
├── /rekap-siswa            [Administration write; TeacherInCharge read-only]
├── /tagihan                [Administration — generate, bayar, struk]
├── /katering               [Administration]
├── /jemputan               [Administration]
├── /pendaftaran            [Administration]
├── /coa                    [Finance, Principal]
├── /jurnal                 [Finance, Principal — also via Pemasukan/Pengeluaran alias]
├── /tunggakan-tagihan      [Finance, Principal — read-only, no bayar]
├── /anggaran               [Finance, Principal]
├── /periode                [Finance, Principal]
├── /pegawai                [Finance, Principal]
├── /absensi-pegawai        [Administration, Finance]
├── /gaji                   [Finance]
├── /pinjaman               [Finance]
├── /aset                   [Finance]
├── /kegiatan               [TeacherInCharge, Principal]
├── /laporan                [Finance, Principal]
└── /audit-log              [Principal, Finance read-only]
```

**SoD (Segregation of Duties):**
- Admin: operasional + **bayar tagihan** (auto-jurnal BE).
- Finance: jurnal manual + laporan; **tidak** bayar tagihan di UI.
- Principal: approve jurnal; tidak input operasional harian.

## Voice and Tone

- Formal ramah Bahasa Indonesia: "Gagal menyimpan data" bukan "Error 500".
- **Administration:** bahasa operasional — "Tagihan", "Bayar", "Cetak", bukan "Posting jurnal".
- **Finance/Principal:** istilah akuntansi asli — Jurnal, Neraca Saldo, Realisasi Anggaran.
- Empty state dengan arahan: "Belum ada absensi hari ini. Pilih kelompok lalu tandai kehadiran."

## Component Patterns

| Pattern | Behavior |
|---------|----------|
| **PageLayout** | Wrapper wajib: title + subtitle? + `#actions` + `#filters` + content card — lihat DESIGN.md |
| **ListPage (CRUD)** | PageLayout → DataTable (cream header) → Dialog form → EmptyState on empty |
| List + Dialog CRUD | DataTable + Dialog form (**via ListPage**, bukan layout ad hoc) |
| Wizard 3-step | Jenjang → Kelompok → Grid (absensi, rekap) |
| Jurnal entry alias | Nav "Pemasukan"/"Pengeluaran" → same JurnalListView with preset filter |
| Maker-checker actions | Submit (Finance) / Approve (Principal) / Void (Finance+confirm) |
| Period picker | Bulan + tahun ajaran di header laporan & tagihan |
| Print | `@media print` hide sidebar; show invoice/report body |
| Read-only overlay | TeacherInCharge on absensi: data visible, controls disabled |
| **formatRp** | Semua nominal via `@/core/format` — never inline `toLocaleString` |
| **KpiCard** | Dashboard metrics — tone navy/green/magenta/orange |

## State Patterns

| State | UX |
|-------|-----|
| Loading | Skeleton row di DataTable |
| Empty | Ilustrasi + CTA primary |
| Error | Toast + inline Message |
| Forbidden | Redirect role home + toast |
| POSTED immutable | Disable edit; show "Koreksi via jurnal pembalik" (Finance only) |
| Read-only role | Disabled inputs + info banner |

## Interaction Primitives

- Confirm dialog untuk void, hapus, tutup periode.
- Toast sukses dengan detail backend bila ada.
- Inline validation balance jurnal (debit = kredit) — **Finance/Principal only**.

## Accessibility Floor

- Semua input punya `<label>` atau `aria-label`.
- Focus ring visible pada nav & form.
- Kontras teks navy/cream ≥ WCAG AA untuk body text.
- Keyboard: Tab order logis di form jurnal multi-baris.

## Key Flows

### Flow A — Absensi → Tagihan (Bu Fitri)
1. `/absensi-siswa` → pilih PG/TKA/TKB → kelompok → grid
2. Sistem simpan `kehadiran-siswa` + flags katering/jemputan
3. `/tagihan` → Generate → preview line items → Simpan → **Bayar** (opsional) → Cetak

### Flow B — Realisasi kegiatan (Bu Desi + Keuangan)
1. `/kegiatan` → buat rencana + pagu
2. Realisasi → cek pagu 9.x vs 5.x
3. Finance submit jurnal → Principal approve

### Flow C — Tutup bulan (Pak Ali)
1. `/laporan` → review neraca & laba rugi
2. `/jurnal` → approve pending
3. `/periode` → tutup buku

### Flow D — Finance pantau tunggakan (read-only)
1. `/tunggakan-tagihan` → filter periode
2. Review siswa BELUM/SEBAGIAN
3. Koordinasi dengan Admin TU untuk follow-up (no bayar button)

## Responsive & Platform

| Breakpoint | Behavior |
|------------|----------|
| ≥1280px | Sidebar full + 2-col dashboard |
| 768–1279px | Sidebar collapsible |
| <768px | Drawer nav; stack KPI cards 1-col |

## Inspiration & Anti-patterns

**Inspirasi:** Mockup HTML sempro; brand [sekolahlebahmadu.com](https://sekolahlebahmadu.com/); clarity SAKOLA dashboard.

**Anti-patterns:** Menu flat 12 item tanpa grouping; form jurnal tanpa indikator balance; tagihan tanpa preview sebelum cetak; **Admin melihat menu Jurnal/COA**; Finance punya tombol Bayar tagihan (SoD violation); **page header/toolbar duplicate per view**; emoji logo di production.
