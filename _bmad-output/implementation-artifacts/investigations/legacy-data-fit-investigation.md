# Investigation: Kesesuaian legacy-data CSV vs Implementasi BeeSmart Finance

## Hand-off Brief

1. **What happened.** Folder `legacy-data/` berisi 76 CSV dari spreadsheet operasional TK Lebah Madu; implementasi BeeSmart Finance sudah punya modul paralel (siswa, absensi, katering, jemputan, tagihan, payroll, akuntansi) tetapi **belum ada jalur import/ETL** dan beberapa aturan bisnis legacy **belum dimodelkan**.
2. **Where the case stands.** Outcome 2–3 selesai untuk inventaris per kategori; stronghold = 76 file CSV + model `operations_*` / `TrJurnal` di codebase.
3. **What's needed next.** Tentukan prioritas: (A) import pilot satu modul, (B) dokumentasi gap untuk Bab IV skripsi, atau (C) penyesuaian model bisnis (tarif jemput per hari, fee tahunan TP, dll.).

## Case Info

| Field            | Value                                                                 |
| ---------------- | --------------------------------------------------------------------- |
| Ticket           | N/A                                                                   |
| Date opened      | 2026-06-30                                                            |
| Status           | Active                                                                |
| System           | BeeSmart Finance — Django REST + Vue 3, PostgreSQL                    |
| Evidence sources | `legacy-data/*.csv` (76), `legacy-data/*.pdf` (2), backend models, `seed_demo`, `etl_migration.py` |

## Problem Statement

User ingin tahu apakah implementasi BeeSmart Finance saat ini **sudah sesuai** dengan gambaran dan data riil dari spreadsheet legacy di folder `legacy-data/`, atau masih ada gap signifikan.

**Hipotesis awal user (implisit):** CSV hasil konversi seharusnya bisa dipetakan ke sistem yang sudah dibangun.

## Evidence Inventory

| Source                              | Status    | Notes                                              |
| ----------------------------------- | --------- | -------------------------------------------------- |
| `legacy-data/` (76 CSV)             | Available | 7 kelompok workbook; ~50% wireframe/spec, ~50% data |
| `legacy-data/*.pdf` (2)             | Available | Tarif resmi PG & RA TA 2025/2026 — lihat § PDF Extract |
| Backend `operations/models/`        | Available | Siswa, Kehadiran, Tagihan, Pegawai, Gaji, dll.     |
| Backend `accounting/models.py`      | Available | COA, Jurnal, Anggaran                              |
| `database/seeds/etl_migration.py`   | Available | Hanya COA + jurnal legacy desktop                  |
| `seed_demo`                         | Available | 3 siswa demo, bukan data riil                      |
| Bulk import API/command             | Missing   | Tidak ada untuk siswa/absensi/tagihan              |
| `database/raw_data/anggaran.csv`    | Partial   | Ada file, tidak diload seed/ETL                    |

## Investigation Backlog

| # | Path to Explore                              | Priority | Status | Notes                          |
| - | -------------------------------------------- | -------- | ------ | ------------------------------ |
| 1 | Mapping TP 2025-2026 → Tagihan/Pendaftaran   | High     | Open   | Fee tahunan kompleks           |
| 2 | Absen matrix → KehadiranSiswa ETL design     | High     | Open   | Wide sparse CSV                |
| 3 | KAFALAH → GajiPegawai field mapping          | Medium   | Open   | Manual entry today             |
| 4 | LPJ/Budget → TrAnggaran + jurnal pengeluaran  | Medium   | Open   | Hierarchical expense lines     |
| 5 | Pilot import 1 bulan absensi + tagihan       | Low      | Open   | Proof of fit                   |

## Confirmed Findings

### Finding 1: Legacy folder berisi dua jenis file — spec vs data operasional

**Evidence:** Sample `Website_Lebah Madu.xlsx - MENU SISWA.csv`, `JEMPUTAN.csv`, `KATERING.csv`, `KEUANGAN.csv` — berisi definisi menu UI, bukan baris transaksi.

**Detail:** File `Layout Website Lebah Madu.xlsx` duplikat wireframe. Data operasional ada di `Absen siswa`, `Absen Jemputan`, `TP 2025-2026`, `KAFALAH`, `Lap Keuangan`, `LPJ`, `Budget-Report`, `Rencana pemasukan`, `realisasi anggaran`.

### Finding 2: Model siswa sistem ≈ wireframe MENU SISWA, bukan roster TP

**Evidence:** `operations/models/students.py` Siswa fields; `Website_Lebah Madu.xlsx - MENU SISWA.csv` column spec.

**Detail:** Sistem punya NIS, nama, jenjang/kelompok, ortu, spp_nominal, status, periode — selaras wireframe. CSV TP (`Playgroup.csv`, `Siswa Baru.csv`) pakai **nama saja** + komponen biaya tahunan (uang kegiatan, pengembangan, seragam, potongan) — **tidak ada di TagihanDetail auto-generation** (hanya SPP/KATERING/JEMPUTAN/LAIN manual).

### Finding 3: Absensi legacy = matrix harian; sistem = record per siswa per tanggal

**Evidence:** `Absen siswa (3).xlsx - TK A.csv` (kolom hari 1–31, flag `C`); `operations_kehadiransiswa` unique (siswa, tanggal).

**Detail:** Legacy: catering count → nominal 40.000/20.000 (`laporan katering.csv`). Sistem: `ikut_katering` boolean × `TarifKatering` flat per bulan (default Rp 22.000). **Gap:** legacy punya tier partial month (20k vs 40k); sistem flat daily rate. Legacy katering Jul-2024 pakai 40.000/hari — **beda** dari 22.000 website/rekomendasi saat ini.

### Finding 4: Jemputan legacy = per-trip per hari; sistem = flat bulanan

**Evidence:** `Absen Jemputan ... Juni 24.csv` — kolom J/A per hari, TARIF per siswa, total = trip × tarif. `PendaftaranJemputan.harga` summed monthly in `billing.py`.

**Detail:** `jemput_datang`/`jemput_pulang` di KehadiranSiswa **tidak dipakai billing**. Legacy lebih granular (506.000 = 22 trip × 23.000).

### Finding 5: Payroll legacy (KAFALAH) struktural match GajiPegawai, tapi tidak terintegrasi absensi

**Evidence:** `KAFALAH APRIL '2025.xlsx - Salary Table.csv` vs `GajiPegawai` fields; `Absen.csv` vs `AbsenPegawai`.

**Detail:** Slip: gaji pokok, tunjangan, transport, makan (hr×Rp), pinjaman, asuransi — field GajiPegawai cover sebagian besar. **Gap:** gaji manual entry; absen pegawai tidak drive perhitungan; pinjaman tidak auto-potong ke gaji.

### Finding 6: Akuntansi legacy selaras konsep COA + jurnal + anggaran; ETL hanya COA/jurnal desktop

**Evidence:** `database/seeds/etl_migration.py` imports T_GOLKUN, T_AKUN, T_JURNAL; `KEUANGAN.csv` wireframe DEBIT/KREDIT/SALDO; `realisasi anggaran sekolah.xlsx`.

**Detail:** LPJ Playgroup = expense lines + budget vs actual per line — mirip `TrAnggaran` + laporan realisasi, tapi **LPJ line items tidak punya model** (harus jurnal manual). `anggaran.csv` di `database/raw_data/` tidak diload.

### Finding 7: Tidak ada import path dari legacy-data ke database

**Evidence:** `grep` import/legacy-data di backend — no matches; `seed_demo` creates 3 synthetic students only.

**Detail:** Data riil 76 CSV **belum bisa masuk sistem** tanpa ETL/script baru.

## Deduced Conclusions

### Deduction 1: Arsitektur modul sudah on-track dengan workflow sekolah

**Based on:** Finding 1–6, wireframe Website vs frontend routes.

**Conclusion:** **~70% keselarasan konseptual** — modul yang dibangun (siswa → absensi → tagihan → jurnal → laporan → pegawai/gaji) mirror alur spreadsheet dan wireframe MENU SISWA/KEUANGAN.

### Deduction 2: Kesesuaian data riil masih rendah tanpa ETL

**Based on:** Finding 7, format matrix CSV, identifier gaps (no NIS in absensi sheets).

**Conclusion:** **~20–30% siap pakai langsung** — format legacy perlu transform (unpivot matrix, normalize amounts, name→NIS matching, fee component mapping).

## Hypothesized Paths

### Hypothesis 1: Sistem sudah "sesuai gambaran" untuk skripsi/UAT demo, belum untuk migrasi data riil

**Status:** Open → leaning Confirmed

**Would confirm:** User accepts demo + manual entry for UAT; legacy used as validation reference only.

**Would refute:** Requirement to load historical 2023–2025 data into production DB.

### Hypothesis 2: Tarif katering 22.000 vs legacy 20.000/40.000

**Status:** ✅ **Resolved 2026-06-30** — 22.000 adalah shortcut v1; tarif resmi **20.000 Sen–Kam + 10.000 Jumat** (PDF, wireframe, CSV Jul-24 konsisten).

## Missing Evidence

| Gap                         | Impact                          | How to Obtain                    |
| --------------------------- | ------------------------------- | -------------------------------- |
| Tarif resmi katering 2025   | Validasi billing vs legacy      | ✅ PDF RA: Rp 20.000/hari Sen–Kam, Rp 10.000 snack Jumat (beda v1 Rp 22.000) |
| Apakah migrasi data wajib   | Scope ETL                       | ✅ **Ya** — Epic E10 (pilot slice, bukan full historis) |
| NIS mapping untuk absensi   | Import absensi by name          | Story 10.1 — NIS sintetis + crosswalk table |

## Conclusion

**Confidence:** Medium

Implementasi BeeSmart Finance **sudah selaras secara modul dan alur bisnis** dengan gambaran spreadsheet/wireframe TK Lebah Madu. **Belum selaras** untuk memuat data riil legacy secara langsung: format CSV berbeda, beberapa aturan billing disederhanakan, dan tidak ada import pipeline.

## PDF Extract — Tarif Resmi TA 2025/2026

> Sumber: `legacy-data/biaya masuk PG 2025-2026.pdf`, `legacy-data/Brosur Pricelist RA 2526.pdf` (diekstrak 2026-06-30).

### Playgroup (`biaya masuk PG 2025-2026.pdf`)

- Semester I total: **Rp 5.375.000** (termasuk uang masuk Rp 700.000, kegiatan Rp 2.5jt, pengembangan Rp 1jt, seragam, portofolio, komite)
- Semester II+: **Rp 4.075.000** per 6 bulan
- SPP: Orens Rp 800.000/bln, Ungu Rp 900.000/bln
- Potongan uang masuk ke RA: Rp 1.000.000 (min 2 semester PG)

### RA/TK (`Brosur Pricelist RA 2526.pdf`)

- Tahun pertama total: **Rp 10.950.000** (uang masuk Rp 3.2jt + kegiatan Rp 4.5jt + pengembangan Rp 1.65jt + seragam Rp 400rb + komite Rp 750rb)
- Tahun kedua: **Rp 6.900.000**
- SPP: **Rp 1.300.000/bulan**
- Katering: **Rp 20.000/hari** (Sen–Kam), snack Jumat **Rp 10.000**
- Potongan uang masuk: PG alumni Rp 1jt, kakak RA Rp 500rb
- Jumat sekolah 07.30–11.00 (shorter day)

### Implikasi ke sistem

| Gap | Detail |
|-----|--------|
| Katering v1 | Sistem pakai Rp 22.000 flat (sementara) | ✅ Resmi 20/10 — **E10 story 10.3** |
| Komponen TP | Sistem belum punya uang kegiatan/pengembangan/seragam/komite/potongan → **E10 story 10.2** |
| SPP default | RA Rp 1.3jt vs PG Rp 800–900rb per kelas → seed per jenjang |

Detail lengkap: [docs/13-LEGACY-ALIGNMENT-GUIDE.md](../../../docs/13-LEGACY-ALIGNMENT-GUIDE.md) §2.2.

## Recommended Next Steps

> **Update 2026-06-30:** Scope hijau + kuning digabung jadi **Epic E10** (satu epic, bukan per-item). Planning selesai; implement on hold.

| Artefak | Path |
|---------|------|
| Guide eksekusi E10 | [docs/13-LEGACY-ALIGNMENT-GUIDE.md](../../../docs/13-LEGACY-ALIGNMENT-GUIDE.md) |
| Execution log | [docs/10-EXECUTION-LOG.md](../../../docs/10-EXECUTION-LOG.md) → M6 |
| Epics & stories 10.1–10.12 | `_bmad-output/planning-artifacts/epics.md` |
| PRD appendix | `prd-beesmartfinance-skripsi-2026-06-28/prd.md` §10 |

### PDF referensi tarif (baru di `legacy-data/`)

| File | Dipakai story |
|------|---------------|
| `biaya masuk PG 2025-2026.pdf` | 10.2 — komponen biaya masuk PG |
| `Brosur Pricelist RA 2526.pdf` | 10.2, 10.3 — pricelist jenjang RA |

### Prioritas implementasi (saat give go)

```
L0 seed_legacy → L1 billing (katering+jemput+TP) → L2 batch tagihan
→ L3 payroll/pinjaman → L4 anggaran/rekap/dashboard → L5 validate_legacy
```

### Diagnostic (unchanged)

Jalankan proof: import 5 siswa dari TP + 1 minggu absensi manual vs hitung tagihan preview — bandingkan dengan `laporan katering.csv`.
