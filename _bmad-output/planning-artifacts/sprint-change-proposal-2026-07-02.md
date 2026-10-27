# Sprint Change Proposal — UAT Dosen Akuntansi (E11)

**Tanggal:** 2026-07-02  
**Trigger:** Feedback UAT dosen akuntansi + 23 screenshot + COA Final CSV  
**Status:** Draft — menunggu approval implementasi  
**Investigasi:** `_bmad-output/implementation-artifacts/investigations/dosen-feedback-uat-investigation.md`

---

## 1. Issue Summary

Setelah Epic E10 (legacy alignment) dinyatakan selesai, dosen akuntansi menguji aplikasi dengan role Keuangan, Kepsek, dan Staf TU. Hasilnya: modul keuangan terasa kaku pasca-import, daftar akun tidak lengkap (~5 akun vs 187 di COA Final), pesan error menampilkan constraint PostgreSQL mentah, dan banyak halaman operasional belum punya CRUD/filter yang fleksibel.

**Prinsip user:** Jangan buat data "immutable" hanya karena di-import; tetap fleksibel. Semua pesan sukses/error harus humanis untuk guru/staf. Setiap halaman perlu aspek informatif (banner/petunjuk).

**Deferred:** Polish visual dashboard (grafik "kunok") — setelah E11 selesai.

---

## 2. Impact Analysis

### Epic Impact

| Epic | Dampak |
|------|--------|
| **E5 Keuangan** | COA seed, edit kode, delete guard, jurnal CRUD, dropdown akun |
| **E2 Siswa/Absensi** | CRUD absensi, rekap filter + arsip tahun, kelompok CRUD |
| **E3 Katering** | Fix UI kolom, upload gambar menu |
| **E4 Jemputan** | Perbaikan data datang/pulang/total |
| **E6/E10 Kegiatan** | Periode/tahun pelajaran, posting kegiatan → akun penanggung jawab |
| **E10 Dashboard** | Filter tanggal/bulan/tahun, widget katering |
| **NEW E11** | Satu epic penutup UAT dosen |

### Story Impact

19 item backlog user → 12 story E11 (lihat guide 14). FR-11, FR-13, FR-25 perlu revisi acceptance criteria.

### Artifact Conflicts

| Artifact | Konflik |
|----------|---------|
| PRD | COA source of truth → COA Final CSV, bukan T_AKUN.csv |
| Epics | Perlu section E11 + update FR-11 |
| Architecture | Importer COA hierarkis; optional image storage katering |
| UX | Copy COA role-aware; error message catalog |

### Technical Impact

- **Breaking:** Migrasi kode akun `1101` → `112` (mapping table atau re-seed fresh DB)
- **Backend:** `exception_handler.py`, COA import command, pre-delete checks
- **Frontend:** Jurnal edit, PeriodPicker dinamis, kelompok CRUD page, errors.ts patterns
- **Seed:** `seed_demo` + `seed_legacy` harus pakai COA Final

---

## 3. Recommended Approach

**Direct Adjustment** — tambah Epic E11 tanpa rollback E10. Data legacy tetap; COA dan UX gaps diperbaiki incrementally.

| Aspek | Nilai |
|-------|-------|
| Effort | ~12 story, estimasi 3–5 hari dev fokus |
| Risk | Medium — migrasi kode COA bisa break jurnal existing |
| Timeline | P0 tonight/tomorrow submit docs; implementasi P0–P1 sebelum sidang |

**Mitigasi migrasi COA:** Command `import_coa_final` dengan `--fresh` untuk dev; production mapping kode lama→baru untuk jurnal posted.

---

## 4. Detailed Change Proposals

### Story: E11.1 — COA Final Import

**Section:** Acceptance Criteria

**OLD:**
- Seed dari `T_AKUN.csv` (~17 akun)

**NEW:**
- Import `legacy-data/Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv`
- ≥180 akun aktif; golongan/sub-golongan hierarkis
- Resolver kode untuk anggaran/jurnal legacy

**Rationale:** Root cause list akun tidak lengkap

---

### Story: E11.2 — Human Error Messages

**OLD:**
- `IntegrityError` → pass-through PostgreSQL string

**NEW:**
- Map FK violations ke: "Akun ini masih dipakai di jurnal. Nonaktifkan saja, atau hapus jurnal terkait dulu."
- `errors.ts` deteksi pattern constraint → ganti pesan generik

---

### Story: E11.3 — COA RBAC & Copy Kepsek

**OLD:**
- Banner sama semua role: "tambah atau edit di sini"

**NEW:**
- Finance: banner + tombol CRUD
- Kepsek: banner "Daftar akun hanya untuk melihat. Perubahan akun dilakukan oleh Staff Keuangan."

---

### Story: E11.4 — Jurnal Draft CRUD

**OLD:**
- FE: Submit saja untuk draft

**NEW:**
- Tombol Edit + Hapus untuk status DRAFT
- Dialog edit pre-fill detail lines
- Dropdown akun dari COA penuh (filter 4.x/5.x sesuai skema baru)

---

### PRD § COA

**OLD:** Import CSV COA dari seed demo

**NEW:** Source of truth = COA Final Lebah Madu; fleksibel edit nama/nonaktif; kode editable dengan guard FK

---

## 5. Implementation Handoff

**Scope classification:** **Moderate** — backlog reorganization + multi-module dev

| Penerima | Tanggung jawab |
|----------|----------------|
| Developer | Implementasi story E11.1–E11.12 per prioritas |
| User/PO | Approve COA kode mapping sebelum re-seed production |
| Dosen | Re-UAT checklist guide 14 |

### Success Criteria

- [ ] COA ≥180 akun; dropdown jurnal/laporan lengkap
- [ ] Hapus akun terpakai → pesan humanis (bukan constraint name)
- [ ] Kepsek `/coa` tanpa tombol, copy jelas
- [ ] Draft jurnal bisa edit/hapus
- [ ] Rekap absensi: tahun 2024+ selectable; filter bulan benar
- [ ] Katering: kolom tarif/total tidak overlap
- [ ] UAT walkthrough pass untuk 3 role

### Routing

→ **Developer agent** (`bmad-quick-dev` / `bmad-dev-story`) untuk implementasi per story  
→ Guide: [14-DOSEN-FEEDBACK-GUIDE.md](../../docs/14-DOSEN-FEEDBACK-GUIDE.md)
