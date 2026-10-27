# 📋 Execution Log — BeeSmart Finance v1

> **Log utama** untuk memantau eksekusi penyelesaian project. Update setiap story selesai.
>
> **Keputusan produk (2026-06-28):**
>
> - ~~Tarif katering: **Rp 22.000/hari** (website TK)~~ → **superseded** lihat 2026-06-30
> - Portal ortu / WA / payment: **v2** (setelah 3 role)
> - Seed password dev: **`<password demo dari seed lokal>`**
> - **Planning patch (2026-06-28 #2):** FR-26/27, UX non-akuntan, nav Pemasukan/Pengeluaran
> - **Design system patch (2026-06-28 #3):** PageLayout, formatRp, KpiCard, logo SVG, **E1.8 gate** sebelum E2+
> - **Legacy alignment (2026-06-30):** Epic **E10** — satu paket hijau+kuning; data riil `legacy-data/` + 2 PDF pricelist; guide [13-LEGACY-ALIGNMENT-GUIDE.md](./13-LEGACY-ALIGNMENT-GUIDE.md)
> - **UAT dosen (2026-07-02):** Epic **E11** — perbaikan pasca-feedback dosen akuntansi; COA Final + human errors + CRUD fleksibel; guide [14-DOSEN-FEEDBACK-GUIDE.md](./14-DOSEN-FEEDBACK-GUIDE.md)
>
> **Keputusan produk (2026-06-30) — tarif katering resmi:**
>
> - **Sen–Kam (makan siang):** Rp **20.000** / hari hadir + ikut katering
> - **Jumat (snack):** Rp **10.000** / hari hadir + ikut katering
> - Sumber: PDF Brosur RA 2526 + wireframe KATERING + validasi `laporan katering.csv` Jul-2024
> - **PG:** katering biasanya all-in semester — tagihan auto katering fokus **TK A/B** (optional di PG)
> - **v1 kode** masih default 22.000 flat sampai story **10.3** diimplement

---

## Status Ringkas


| Area                | Progress                 | Dokumen                                                                                        |
| ------------------- | ------------------------ | ---------------------------------------------------------------------------------------------- |
| **Backend**         | ~85% stabil              | [12-BACKEND-REFERENCE.md](./12-BACKEND-REFERENCE.md)                                           |
| **Frontend**        | ~95% (E1–E8 ✅, E9 tests) | [11-FRONTEND-GUIDE.md](./11-FRONTEND-GUIDE.md)                                                 |
| **Planning**        | ✅ PRD + UX + Epics       | `_bmad-output/planning-artifacts/`                                                             |
| **Domain research** | ✅                        | `_bmad-output/planning-artifacts/research/domain-sia-tk-sekolah-swasta-research-2026-06-28.md` |


**Baseline:** 2026-06-28 — investigasi + planning selesai. **Eksekusi dimulai 2026-06-28:** E9.1 + E1 complete.

---

## Epic Progress


| Epic | Judul                            | Status      | Progress                       |
| ---- | -------------------------------- | ----------- | ------------------------------ |
| E1   | Design System & App Shell        | ✅ Done      | 8/8 stories (E1.8 gate passed) |
| E2   | Modul Siswa & Absensi            | ✅ Done      | 4/5 (2.1–2.2 optional)         |
| E3   | Modul Katering                   | ✅ Done      | 2/2 stories                    |
| E4   | Modul Jemputan                   | ✅ Done      | 3/3 stories                    |
| E5   | Keuangan Lengkap (COA + Laporan) | ✅ Done (v1) | 6/7 (5.7 deferred v1.1)        |
| E6   | Tagihan & Pendaftaran            | ✅ Done      | 4/4 stories                    |
| E7   | Pegawai & Payroll                | ✅ Done      | 3/3 stories                    |
| E8   | Audit & Governance UI            | ✅ Done      | 1/1 stories                    |
| E9   | Quality, Seed & Deployment       | ✅ Done      | 4/4 stories                    |
| E10  | Legacy Alignment & Real Data     | ✅ Done      | 12/12 stories |
| E11  | UAT Dosen — COA, CRUD & UX Humanis | ✅ Done | 12/12 stories  |
| E12  | Dashboard Polish (deferred)      | 🔲 Todo      | —             |


**Legend:** ✅ Done · 🔄 In Progress · 🔲 Todo · ⏸ Blocked · ❌ Cancelled

---

## Story Log (chronological)


| Date       | Story                         | Epic | Status | Catatan                                           |
| ---------- | ----------------------------- | ---- | ------ | ------------------------------------------------- |
| 2026-06-28 | Planning artifacts            | —    | ✅      | PRD, UX, Epics, Domain research                   |
| 2026-06-28 | 9.1 Seed users                | E9   | ✅      | `seed_demo` — 4 role + jenjang/kelompok/siswa/COA |
| 2026-06-28 | 1.1–1.7 Design system & shell | E1   | ✅      | tokens, AppShell, nav SoD, shared components      |
| 2026-06-28 | 1.8 Migrate views             | E1   | ✅      | Semua `*View.vue` → PageLayout + formatRp         |
| 2026-06-28 | 2.4 Rekap absensi             | E2   | ✅      | `/rekap-siswa` + export CSV                       |
| 2026-06-28 | 2.5 Teacher read-only rekap   | E2   | ✅      | banner + API read permission                      |
| 2026-06-28 | 4.1–4.3 Jemputan              | E4   | ✅      | `/jemputan` armada + pendaftaran + rekap          |
| 2026-06-28 | 6.1–6.3 Tagihan enhanced      | E6   | ✅      | preview → editor → cetak faktur                   |
| 2026-06-28 | 5.1–5.6 Keuangan FE           | E5   | ✅      | COA UI, laporan period, tunggakan filter          |
|            | 6.4 Pendaftaran UI            | E6   | ✅      | `/pendaftaran` sit-in → finalisasi                |
| 2026-06-28 | 7.1–7.3 Pegawai & payroll     | E7   | ✅      | periode kerja, absensi grid, slip gaji            |
| 2026-06-28 | 8.1 Audit log viewer          | E8   | ✅      | filter tabel/user/tanggal + detail JSON           |
| 2026-06-28 | 9.2–9.4 Quality & deploy      | E9   | ✅      | vitest, docker-compose, CI, README UAT            |
| 2026-06-28 | UAT walkthrough 31/31         | —    | ✅      | `manage.py uat_walkthrough` + fix tunggakan SoD   |
| 2026-06-30 | E10 planning (legacy)         | E10  | ✅      | Guide 13 + epics + PRD §10; keputusan tarif katering 20/10 |
| 2026-07-01 | 10.1 seed_legacy + 10.3 katering 20/10 | E10  | ✅      | Parser, command, migration, billing, FE rekap |
| 2026-06-28 | 10.1 demo-full (TP roster + absensi) | E10  | ✅      | `--demo-full`: ~160 siswa, absensi Jul 2025–Jun 2026 |
| 2026-07-01 | 10.4 jemput per-trip billing      | E10  | ✅      | billing trip×tarif, parser jemput CSV, seed armada |
| 2026-07-01 | 10.2 template komponen TP         | E10  | ✅      | KomponenBiayaTemplate + seed PDF + tagihan Juli |
| 2026-07-01 | 10.5 batch generate tagihan       | E10  | ✅      | preview-batch + generate-batch API + FE dialog |
| 2026-07-01 | 10.10 dashboard ops KPI           | E10  | ✅      | BE operasional block + FE KPI row + sparkline + jurnal draft |
| 2026-07-01 | 10.6–10.8 KAFALAH + anggaran      | E10  | ✅      | parser KAFALAH, gaji Ali ≈7.16jt, potong pinjaman, anggaran CSV |
| 2026-07-01 | 10.9–10.12 export + validate + UAT | E10  | ✅      | export legacy CSV, validate_legacy, validate-legacy.sh, UAT +2 |
| 2026-07-02 | UAT dosen — investigasi + planning | E11  | ✅      | 23 SS, case file, sprint proposal, guide 14 |
| 2026-07-02 | 11.1–11.12 implementasi          | E11  | ✅      | P0–P2 selesai; E12 polish ditunda |
| 2026-07-02 | 11.1 import_coa_final (merge)    | E11  | ✅      | 190 akun di DB dev; command + test_coa_final |
| 2026-07-02 | 11.2 human error messages        | E11  | ✅      | db_errors.py + exception_handler + errors.ts |
| 2026-07-02 | 11.3 COA RBAC copy               | E11  | ✅      | CoaListView banner per role |
| 2026-07-02 | 11.4 jurnal draft CRUD           | E11  | ✅      | Edit/hapus draft + serializer update |
| 2026-07-02 | 11.5 katering kolom tarif/total  | E11  | ✅      | tarif-stack + CSS min-width |
| 2026-07-02 | 11.6 PeriodPicker 2024+          | E11  | ✅      | minYear default 2024 |
| 2026-07-02 | 11.7 CRUD kelompok + pindah siswa | E11  | ✅      | `/kelompok` + API pindah-siswa |
| 2026-07-02 | 11.8 absensi CRUD (hapus/edit)   | E11  | ✅      | Hapus per siswa/tanggal; simpan=update |
| 2026-07-02 | 11.9 dashboard filter periode    | E11  | ✅      | Filter bulan/tahun/hari; KPI refresh |
| 2026-07-02 | 11.10 katering upload gambar     | E11  | ✅      | Multipart + widget menu di dashboard |
| 2026-07-02 | 11.11 kegiatan + TA              | E11  | ✅      | FK periode; jurnal fiscal_period |
| 2026-07-02 | 11.12 arsip rekap absensi TA     | E11  | ✅      | TA aktif default; panel arsip collapsed |


---

## Milestone Checklist

### M1 — Foundation (target: minggu 1)

- [x] Seed 4 role users + demo data
- [x] Design system tokens applied
- [x] Grouped sidebar + responsive shell
- [ ] Login UAT semua role (UI manual — lihat README)

### M2 — Operational Chain (target: minggu 2–3)

- [x] Absensi siswa (wizard + katering/jemputan flags)
- [x] Rekap katering (v1: flat Rp 22.000/hari — **superseded** → 20rb Sen–Kam + 10rb Jumat, story 10.3)
- [x] Modul jemputan dasar
- [x] Tagihan generate + cetak struk

### M3 — Finance Complete (target: minggu 4)

- [x] UI COA
- [x] Laporan + export CSV / cetak
- [x] Audit log viewer

### M4 — Quality & Demo (target: minggu 5)

- [x] Frontend tests (Vitest — 20 tests)
- [x] Docker + CI
- [x] UAT 3 persona (UJ-1, UJ-2, UJ-3) — `python backend/manage.py uat_walkthrough` 31/31 ✅
- [ ] Demo ke dosen

### M5 — v2 Backlog (post-skripsi)

- [ ] Portal orang tua
- [ ] Integrasi WhatsApp
- [ ] Virtual Account / QRIS
- [ ] ISAK 35 report pack lengkap

### M6 — Legacy Alignment v1.1 (target: post-v1, pre-demo sidang)

> Detail eksekusi: [13-LEGACY-ALIGNMENT-GUIDE.md](./13-LEGACY-ALIGNMENT-GUIDE.md)

- [x] L0 — `seed_legacy --demo-full` (roster + katering + jemput Jul 2025–Jun 2026)
- [x] L1 — Aturan billing: katering ✅, jemput ✅, template TP ✅
- [x] L2 — Batch generate tagihan per kelompok/jenjang
- [x] L3 — Payroll KAFALAH + auto potong pinjaman
- [x] L4 — Import anggaran CSV + realisasi (jurnal POSTED demo)
- [x] L5 — Export rekap legacy + dashboard kepsek KPI operasional
- [x] L6 — `validate_legacy` + extend `uat_walkthrough`

---

## UAT — 3 Persona Walkthrough


| UJ   | Persona          | Langkah                                          | Status      |
| ---- | ---------------- | ------------------------------------------------ | ----------- |
| UJ-1 | Bu Fitri (Admin) | Absensi → tagihan → cetak struk → pendaftaran    | ✅ API 15/15 |
| UJ-2 | Staff Keuangan   | Jurnal → submit → laporan → tunggakan → gaji     | ✅ API 9/9   |
| UJ-3 | Pak Ali (Kepsek) | Dashboard → approve jurnal → audit log → laporan | ✅ API 7/7   |


---

## Blockers & Risks


| ID     | Blocker                  | Impact             | Mitigasi        |
| ------ | ------------------------ | ------------------ | --------------- |
| ~~B1~~ | ~~Belum ada seed user~~  | —                  | ✅ Story 9.1     |
| B2     | FE gap modul operasional | Alur tagihan putus | E2–E4 prioritas |


---

## Quick Links


| Resource                           | Path                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| Epics detail + acceptance criteria | `_bmad-output/planning-artifacts/epics.md`                                                       |
| PRD                                | `_bmad-output/planning-artifacts/prds/prd-beesmartfinance-skripsi-2026-06-28/prd.md`             |
| UX Experience                      | `_bmad-output/planning-artifacts/ux-designs/ux-beesmartfinance-skripsi-2026-06-28/EXPERIENCE.md` |
| UX Design tokens                   | `_bmad-output/planning-artifacts/ux-designs/ux-beesmartfinance-skripsi-2026-06-28/DESIGN.md`     |
| Investigation case file            | `_bmad-output/implementation-artifacts/investigations/school-finance-standards-investigation.md` |
| Legacy data fit investigation      | `_bmad-output/implementation-artifacts/investigations/legacy-data-fit-investigation.md`          |
| Legacy alignment guide (E10)       | [13-LEGACY-ALIGNMENT-GUIDE.md](./13-LEGACY-ALIGNMENT-GUIDE.md)                                   |
| UAT dosen guide (E11)              | [14-DOSEN-FEEDBACK-GUIDE.md](./14-DOSEN-FEEDBACK-GUIDE.md)                                       |
| COA Final (source of truth)        | `legacy-data/Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv`                          |
| UAT investigation case file        | `_bmad-output/implementation-artifacts/investigations/dosen-feedback-uat-investigation.md`     |
| Sprint change proposal 2026-07-02  | `_bmad-output/planning-artifacts/sprint-change-proposal-2026-07-02.md`                           |
| Legacy CSV + PDF referensi         | `legacy-data/` (76 CSV + `biaya masuk PG 2025-2026.pdf`, `Brosur Pricelist RA 2526.pdf`)         |
| API docs (runtime)                 | [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)                               |


---

## Cara Update Log Ini

1. Setelah story selesai → tambah baris di **Story Log**
2. Update counter di **Epic Progress**
3. Centang item di **Milestone Checklist** bila milestone tercapai
4. Detail teknis FE → catat di [11-FRONTEND-GUIDE.md](./11-FRONTEND-GUIDE.md)
5. Perubahan BE (jika ada) → catat di [12-BACKEND-REFERENCE.md](./12-BACKEND-REFERENCE.md)
