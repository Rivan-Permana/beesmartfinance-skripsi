# Legacy Alignment v1.1 — Guide & Eksekusi

> **Epic E10** — Satu paket implementasi: selaraskan BeeSmart Finance dengan data & aturan operasional riil TK Lebah Madu (`legacy-data/`), mengganti seed dummy, dan menghidupkan dashboard kepsek untuk demo sidang.

**Status:** 🔲 Planning selesai · implementasi **on hold** sampai user give go  
**Investigasi awal:** `_bmad-output/implementation-artifacts/investigations/legacy-data-fit-investigation.md`  
**Log progress:** [10-EXECUTION-LOG.md](./10-EXECUTION-LOG.md) → section E10

---

## 1. Tujuan Epic

| Aspek | v1 (E1–E9) | E10 (target) |
|-------|------------|--------------|
| Data demo | 3 siswa dummy (`seed_demo`) | Roster + absensi + pegawai **riil** dari legacy |
| Katering | Flat Rp 22.000/hari *(v1 sementara)* | **Sen–Kam Rp 20.000** + **Jumat Rp 10.000** per hari ikut katering |
| Jemput | Flat bulanan | **Per trip** (`jemput_datang`/`jemput_pulang` × tarif) |
| Tagihan TP | SPP + katering + jemput bulanan | + **komponen tahunan** (kegiatan, pengembangan, seragam, potongan) |
| Generate | Per siswa | **Batch** per kelompok / jenjang |
| Payroll | Input manual | Mapping **KAFALAH** + potong pinjaman otomatis |
| Anggaran | UI manual | **Import CSV** legacy + realisasi |
| Rekap export | CSV generic | Mirror format **laporan katering / rekap jemput** |
| Dashboard kepsek | Keuangan saja (sering kosong) | KPI **operasional + keuangan** + jurnal pending |

**Prinsip:** Satu epic, satu rantai dependency — bukan 9 mini-project terpisah.

---

## 1b. Keputusan Tarif Katering (2026-06-30) ✅

> **Canonical** untuk E10 ke depan. Menggantikan keputusan sementara v1 (Rp 22.000 flat).

### Rumus

```
total_katering = (hari_SenKam × 20.000) + (hari_Jumat × 10.000)
```

| Syarat | Aturan |
|--------|--------|
| Hari dihitung | Hanya tanggal **hadir** + `ikut_katering = true` |
| Sen–Kam | Rp **20.000** — makan siang |
| Jumat | Rp **10.000** — snack (sekolah 07.30–11.00) |
| Sabtu/Minggu | Tidak dihitung |

### Sumber kebenaran

| Prioritas | Sumber | Dipakai untuk |
|-----------|--------|---------------|
| 1 | PDF `Brosur Pricelist RA 2526.pdf` | TA 2025/26 ke depan |
| 2 | Wireframe `Website_Lebah Madu.xlsx - KATERING.csv` | Spesifikasi sistem asli |
| 3 | `laporan katering.csv` + absensi TK A/B | Validasi historis Jul–Agu 2024 |

### Per jenjang

| Jenjang | Tagihan katering bulanan |
|---------|--------------------------|
| **TK A / TK B (RA)** | ✅ Optional — rumus 20/10 |
| **Playgroup** | ⚠️ Semester **all-in** — skip auto-tagihan katering (absensi/rekap tetap jalan) |

### Status kode

| Area | v1 (shipped) | Target E10 story 10.3 |
|------|--------------|------------------------|
| `katering_tarif.py` | `DEFAULT = 22000` flat | `tarif_sen_kam=20000`, `tarif_jumat=10000` |
| `billing.py` | `count × flat` | per-tanggal weekday split |
| UI rekap | satu kolom nominal | kolom Sen–Kam / Jumat / total |

---

## 2. Sumber Data & Referensi

### 2.1 Folder `legacy-data/` (76 CSV + 2 PDF)

| Kelompok workbook | File kunci | Dipakai story |
|-------------------|------------|---------------|
| **Absen siswa** | `TK A.csv`, `TK B.csv`, `laporan katering.csv` | 10.1, 10.3, 10.11 |
| **Absen Jemputan** | `Juni 24.csv`, … (12 bulan) | 10.1, 10.4, 10.9 |
| **TP 2025-2026** | `Playgroup.csv`, `Siswa Baru.csv`, `Siswa Daftar Ulang.csv`, `Rekap.csv` | 10.2, 10.5 |
| **KAFALAH APRIL 2025** | `Salary Table.csv`, `Absen.csv`, `Slip.csv`, `Pinjaman.csv` | 10.1, 10.6, 10.7 |
| **Anggaran** | `realisasi anggaran sekolah.xlsx`, `Rencana pemasukan 2025-2026.xlsx`, `Budget-Report … Cashflow.csv` | 10.8 |
| **Lap Keuangan / LPJ** | `saldo.csv`, monthly sheets | Validasi laporan (10.11) |
| **Website wireframe** | `MENU SISWA`, `KEUANGAN`, … | Referensi field — **bukan** data import |

### 2.2 PDF referensi tarif resmi (TA 2025/2026)

Kedua PDF **sudah terekstrak** dan jadi sumber kebenaran tarif untuk story 10.2–10.3.

#### A. `biaya masuk PG 2025-2026.pdf` — Playgroup

**Pendaftaran**

| Komponen | Nominal |
|----------|---------|
| Formulir | Rp 50.000 |
| Observasi | Rp 250.000 |

**Semester I (6 bulan pertama)**

| Komponen | Nominal |
|----------|---------|
| Uang Masuk | Rp 700.000 |
| Uang Kegiatan | Rp 2.500.000 |
| Uang Pengembangan | Rp 1.000.000 |
| Seragam Sekolah (1 stel) | Rp 200.000 |
| Portofolio & Rapor | Rp 300.000 |
| Iuran Komite (1 semester) | Rp 375.000 |
| **Total Semester I** | **Rp 5.375.000** |

**Semester II+ (per 6 bulan)**

| Komponen | Nominal |
|----------|---------|
| Uang Kegiatan | Rp 2.500.000 |
| Uang Pengembangan | Rp 1.000.000 |
| Portofolio & Rapor | Rp 200.000 |
| Iuran Komite (1 semester) | Rp 375.000 |
| **Total per semester** | **Rp 4.075.000** |

**SPP bulanan PG**

| Kelas | Usia | SPP/bulan |
|-------|------|-----------|
| Kelas Orens | 2–3 tahun | Rp 800.000 |
| Kelas Ungu | 3–4 tahun | Rp 900.000 |

**Aturan khusus PG → RA:** Potongan Uang Masuk **Rp 1.000.000** saat naik ke RA Lebah Madu (syarat: minimal 2 semester PG).  
**Jemput (optional):** 80% tarif taksi online, disesuaikan jarak.

---

#### B. `Brosur Pricelist RA 2526.pdf` — RA/TK TA 2025/2026

**Pendaftaran siswa baru**

| Komponen | Nominal |
|----------|---------|
| Formulir | Rp 100.000 |
| Sit in / Observasi | Rp 350.000 |
| Uang Masuk | Rp 3.200.000 |

**Tahun pertama (biaya pendidikan per tahun)**

| Komponen | Nominal |
|----------|---------|
| Uang Kegiatan Ananda | Rp 4.500.000 |
| Uang Pengembangan | Rp 1.650.000 |
| Seragam (2 stel + Batik IGRA) | Rp 400.000 |
| Iuran Komite (1 tahun) | Rp 750.000 |
| **Total tahun pertama** | **Rp 10.950.000** |

**Tahun kedua (naik TK B / mengulang)**

| Komponen | Nominal |
|----------|---------|
| Uang Kegiatan | Rp 4.500.000 |
| Uang Pengembangan | Rp 1.650.000 |
| Iuran Komite (1 tahun) | Rp 750.000 |
| **Total tahun kedua** | **Rp 6.900.000** |

**Biaya bulanan (di luar tahunan)**

| Komponen | Nominal | Catatan |
|----------|---------|---------|
| SPP | Rp 1.300.000/bulan | Bayar tgl 1–15 tiap bulan |
| Catering makan siang | **Rp 20.000/hari** | Sen–Kamis |
| Catering snack Jumat | **Rp 10.000** | Per hari Jumat |
| Antar jemput | 80% taksi online | Optional, by jarak |

**Potongan Uang Masuk RA**

| Kondisi | Potongan |
|---------|----------|
| Alumni PG Lebah Madu (min. 10 bulan) | Rp 1.000.000 |
| Kakak pernah sekolah di RA Lebah Madu | Rp 500.000 |

**Jadwal relevan billing:** Sen–Kam full day (07.30–13.00); **Jumat 07.30–11.00** (sekolah lebih pendek → snack Jumat terpisah, bukan makan siang penuh).

---

#### C. Gap v1 vs keputusan resmi (catatan implementasi)

| Aturan | v1 (E1–E9, shipped) | Keputusan resmi 2026-06-30 | Aksi E10 |
|--------|---------------------|------------------------------|----------|
| Katering | Flat **Rp 22.000/hari** *(sementara)* | **Rp 20.000** Sen–Kam + **Rp 10.000** Jumat | Story 10.3 |
| SPP RA | Field `spp` per siswa | **Rp 1.300.000/bulan** default | Seed template per jenjang |
| Komponen TP | SPP + katering + jemput saja | Uang masuk, kegiatan, pengembangan, seragam, komite, potongan | Story 10.2 |
| Jemput | Flat bulanan | 80% taksi online by jarak | Story 10.4 — tarif per siswa/zona |
| PG katering | — | All-in semester, tidak ditagih terpisah | Skip auto-tagihan PG |

> **Prioritas ground truth:** Untuk validasi historis Jul-2024, bandingkan dengan `laporan katering.csv`. Untuk TA 2025/2026 ke depan, PDF pricelist = canonical.

### 2.3 Bulan anchor pilot (disarankan)

**Juli 2024** — alasan:
- Ada `Absen siswa - TK A/B.csv` + `laporan katering.csv` (ground truth nominal)
- Ada sheet `Absen Jemputan - Juli 23` / continuity ke Jun 24 untuk pola tarif

Alternatif: **April 2025** (KAFALAH + TP penuh) jika fokus payroll.

---

## 3. Arsitektur Epic (dependency)

```
L0  seed_legacy + PDF tariff seed
      ↓
L1  Aturan billing (katering diff, jemput per-trip, template TP)
      ↓
L2  batch generate tagihan
      ↓
L3  Payroll KAFALAH + auto potong pinjaman
      ↓
L4  Import anggaran CSV + realisasi
      ↓
L5  Export rekap legacy + dashboard ops KPI
      ↓
L6  validate_legacy + extend uat_walkthrough
```

**Jangan** batch generate (L2) sebelum L1 stabil — tagihan historis akan salah.

---

## 4. Stories E10 (satu epic, semua scope hijau + kuning)

| ID | Story | Scope | FR |
|----|-------|-------|-----|
| **10.1** | `seed_legacy` — import roster, absensi pilot, pegawai, armada | CSV matrix → ORM; NIS sintetis jika perlu; idempotent | FR-28 |
| **10.2** | Template komponen biaya TP (PG/TK, baru/lama, tier potongan) | Model + admin/API; seed dari TP CSV + 2 PDF | FR-29 |
| **10.3** | Katering differentiated (Sen–Kam vs Jumat; optional per jenjang) | Extend `TarifKatering` / `billing.py` | FR-30 |
| **10.4** | Jemput per-hari (trip × tarif siswa) | `build_tagihan_komponen` + UI rekap | FR-31 |
| **10.5** | Batch generate tagihan (kelompok / jenjang / TA) | `POST /tagihan/generate-batch/` + UI | FR-32 |
| **10.6** | Payroll: mapping field KAFALAH (tunjangan, transport, uang makan hr×Rp) | Extend `GajiPegawai` / slip preview | FR-33 |
| **10.7** | Potong pinjaman otomatis ke gaji | Service link `PinjamanPegawai` → `GajiPegawai` | FR-34 |
| **10.8** | Load anggaran dari CSV legacy + sinkron realisasi | `anggaran.csv` + `realisasi anggaran sekolah` | FR-35 |
| **10.9** | Export rekap mirror legacy (katering, jemput) | CSV layout seperti `laporan katering.csv` | FR-36 |
| **10.10** | Dashboard kepsek: KPI operasional + pending approve + sparkline | Extend `DashboardRingkasan` + FE widgets | FR-37 |
| **10.11** | `validate_legacy` — bandingkan hitung sistem vs CSV | Management command ± toleransi | FR-38 |
| **10.12** | Tooling: scripts, extend `uat_walkthrough`, README runbook | `scripts/seed-legacy.sh`, CI smoke | NFR-12 |

---

## 5. Tools & Commands (rencana)

```bash
# Seed data riil (dry-run dulu)
./scripts/seed-legacy.sh --dry-run --month 2024-07
./scripts/seed-legacy.sh --apply --month 2024-07

# Validasi vs spreadsheet
cd backend && python manage.py validate_legacy --month 2024-07 --report

# UAT extended (setelah 10.12)
python manage.py uat_walkthrough --legacy-month 2024-07

# Demo reset (dev)
python manage.py seed_demo --users-only   # users tetap
python manage.py seed_legacy --apply --month 2024-07
```

| Script | Fungsi |
|--------|--------|
| `scripts/seed-legacy.sh` | Wrapper env check + migrate + seed_legacy |
| `scripts/validate-legacy.sh` | Wrapper validate_legacy + diff report |
| `backend/.../seed_legacy.py` | Management command utama |
| `backend/.../validate_legacy.py` | Compare tagihan vs laporan katering CSV |

---

## 6. Monitoring Progress

Centang di [10-EXECUTION-LOG.md](./10-EXECUTION-LOG.md) setiap story selesai.

**Definition of Done (E10 epic):**
- [ ] Login kepsek → dashboard menampilkan grafik **non-kosong** (data legacy)
- [ ] Generate batch tagihan Jul-2024 untuk TKA → total katering ± match `laporan katering.csv` (toleransi dokumentasi)
- [ ] Slip gaji 1 pegawai dari KAFALAH ≈ field legacy
- [ ] Anggaran ter-load minimal 1 TA; realisasi dashboard terisi
- [ ] Export rekap katering/jemput downloadable
- [ ] `uat_walkthrough` extended lulus
- [ ] Bab IV dapat tabel mapping legacy ↔ sistem

---

## 7. Risiko & Mitigasi

| Risiko | Mitigasi |
|--------|----------|
| CSV matrix susah parse | Parser per workbook; log unmatched rows; `--dry-run` |
| Nama tanpa NIS | NIS sintetis + mapping table; fuzzy match manual review |
| PDF tidak machine-readable | Tarif diinput sekali ke template; PDF = referensi manusia |
| Scope creep (76 file) | **Slice pilot** Jul-2024 + April-2025 KAFALAH; bukan full historis |
| UAT 31/31 regression | Extend walkthrough; jangan break `seed_demo` default |

---

## 8. Out of Scope E10 (tetap v2)

- Portal orang tua, WhatsApp, VA/QRIS
- Import full historis 2023–2025 semua workbook
- LPJ line-item expense model (tetap jurnal manual)
- Piutang aging / cicilan SEBAGIAN penuh

---

## 9. Quick Links

| Resource | Path |
|----------|------|
| Legacy CSV + PDF | `legacy-data/` |
| Investigation | `_bmad-output/implementation-artifacts/investigations/legacy-data-fit-investigation.md` |
| Epics E10 detail | `_bmad-output/planning-artifacts/epics.md` → Epic 10 |
| PRD appendix | `_bmad-output/planning-artifacts/prds/.../prd.md` → §10 |
| Backend billing | `backend/operations/services/billing.py` |
| Dashboard FE | `frontend/src/features/dashboard/DashboardView.vue` |
