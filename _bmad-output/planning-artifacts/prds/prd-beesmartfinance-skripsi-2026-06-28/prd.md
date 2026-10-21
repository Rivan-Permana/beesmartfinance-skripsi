---
title: BeeSmart Finance — SIA TK Lebah Madu
created: 2026-06-28
updated: 2026-06-28T2
status: final
---

# PRD: BeeSmart Finance — SIA TK Lebah Madu

## 0. Document Purpose

PRD ini menjadi kontrak produk untuk menyelesaikan BeeSmart Finance dari status **setengah matang** menjadi sistem informasi akuntansi sekolah yang layak dipakai staf TK Lebah Madu. Dokumen ini ditujukan untuk developer, reviewer skripsi, dan stakeholder sekolah.

**Input yang menjadi dasar:**
- Investigasi codebase (`_bmad-output/implementation-artifacts/investigations/school-finance-standards-investigation.md`)
- Mockup HTML sempro (`Layout Website Lebah Madu(FIX).xlsx/*.html`)
- COA & jurnal referensi (`diagrams/Chart Of Accounts*.csv`, `result/T_*.csv`)
- Coretan brief sistem (`coretan kertas brief sustem.png`)
- Website sekolah: [sekolahlebahmadu.com](https://sekolahlebahmadu.com/)
- Benchmark eksternal: [SAKOLA](https://sakola.id/fitur/), [Siswamedia](https://siswamedia.com/kelola-keuangan-sekolah-lebih-mudah-dan-transparan/), literatur SIAS/ISAK 35

**Artefak turunan:** `EXPERIENCE.md`, `DESIGN.md`, `epics.md`

## 1. Vision

BeeSmart Finance adalah **Sistem Informasi Akuntansi (SIA)** web untuk TK/PG Sekolah Lebah Madu — yayasan pendidikan Islami di Jakarta Timur. Sistem menghubungkan **tiga kelompok pengguna operasional** (Administrasi/TU, Keuangan, Kepala Sekolah) dalam satu alur: operasional harian (siswa, absensi, katering, jemputan) → tagihan & pendapatan → jurnal double-entry → laporan keuangan & realisasi anggaran.

Backend sudah kuat (PostgreSQL triggers, maker-checker, auto-posting). Frontend dan UX belum menutup mockup sempro maupun kebutuhan staf non-teknis. Produk v1 menutup gap tersebut dengan desain selaras brand [sekolahlebahmadu.com](https://sekolahlebahmadu.com/) — profesional, ramah, dan mudah dipakai guru/admin di meja kerja maupun tablet.

## 2. Target User

### 2.1 Jobs To Be Done

- **Admin TU:** "Saya perlu input absensi, katering, jemputan, dan tagihan siswa tanpa Excel — dan struk bisa dicetak untuk ortu."
- **Staff Keuangan:** "Saya perlu catat jurnal, kelola COA/anggaran, dan lihat apakah beban sudah melebihi pagu."
- **Kepala Sekolah:** "Saya perlu approve transaksi penting dan lihat kesehatan keuangan sekolah sekilas."
- **Guru Koordinator Kegiatan:** "Saya perlu ajukan realisasi kegiatan dan tahu sisa anggaran."

### 2.2 Prinsip Non-Akuntan vs Akuntansi Proper

Staf operasional (Admin TU, Guru) **tidak wajib** memahami debit/kredit. UI mereka **task-based** (absensi, tagihan, bayar, struk). Standar akuntansi double-entry tetap berjalan di backend (auto-posting tagihan/gaji/aset) dan modul Finance.

| Role | Bahasa UI | Akses akuntansi |
|------|-----------|-----------------|
| Administration | Operasional: "Tagihan", "Bayar", "Cetak Struk" | **Tidak** melihat Jurnal, COA, Laporan |
| Finance | Campuran: nav "Pemasukan"/"Pengeluaran" → layar Jurnal dengan preset filter | Jurnal, COA, laporan penuh |
| SchoolPrincipal | Sama Finance + "Setujui Transaksi" | Approve + read-only oversight |
| TeacherInCharge | "Kegiatan", "Realisasi" | Hanya modul kegiatan; absensi siswa **read-only** |

**Progressive disclosure:** istilah teknis (Neraca Saldo, debit/kredit) hanya di modul Finance/Principal; Admin tidak pernah diarahkan ke layar jurnal.

### 2.3 Non-Users (v1)

- Portal orang tua / pembayaran online (VA, QRIS) — deferred v2
- Multi-yayasan / multi-cabang
- Modul akademik (nilai, rapor)

### 2.4 Key User Journeys

**UJ-1. Bu Fitri menagih SPP bulan ini**
- **Persona:** Bu Fitri, Admin 1, familiar Excel tapi tidak tech-savvy.
- **Entry:** Login Administration → home `/siswa`.
- **Path:** Input absensi harian (jenjang→kelompok→siswa) → cek rekap katering/jemputan → buka Tagihan → generate periode → review line items (SPP, katering, jemputan) → cetak struk untuk ortu.
- **Climax:** Faktur tercetak dengan rincian sesuai biaya di website sekolah.
- **Resolution:** Status tagihan BELUM/SEBAGIAN/LUNAS; Admin dapat **Bayar** langsung (auto-jurnal di backend); Finance memantau tunggakan via dashboard/`/tunggakan-tagihan`.

**UJ-2. Staff Keuangan menutup realisasi kegiatan TK Outing**
- **Persona:** Staff keuangan, paham akuntansi dasar.
- **Entry:** Login Finance → `/kegiatan` atau `/jurnal`.
- **Path:** Buka kegiatan → input realisasi biaya → sistem cek pagu akun 9.x vs beban 5.x → auto-jurnal → submit → Kepsek approve.
- **Climax:** Realisasi anggaran dashboard menunjukkan selisih pagu vs beban.
- **Resolution:** Jurnal POSTED; tidak bisa edit; koreksi via reversal.

**UJ-3. Pak Ali approve jurnal dan review dashboard**
- **Persona:** Pak Ali, Kepala Sekolah, butuh gambaran cepat.
- **Entry:** Login SchoolPrincipal → `/dashboard`.
- **Path:** Lihat KPI kas, surplus/defisit, grafik realisasi anggaran → buka Jurnal Pending → approve → optional: tutup periode akuntansi.
- **Climax:** Approval berhasil; audit log tercatat.
- **Resolution:** Laporan posisi keuangan siap di tab Laporan.

## 3. Glossary

- **COA** — Chart of Accounts; daftar akun dengan kode hierarkis (1–5 operasional, 9 anggaran).
- **Jurnal** — Entri double-entry; status DRAFT → PENDING → POSTED → VOID.
- **Anggaran** — Pagu per akun golongan 9; bukan jurnal operasional.
- **Realisasi** — Beban aktual (golongan 5) dibanding pagu anggaran (golongan 9).
- **Tagihan** — Faktur siswa per periode (SPP, katering, jemputan, biaya tahunan).
- **Maker-Checker** — Pembuat transaksi ≠ penyetuju (Finance vs SchoolPrincipal).
- **Jenjang** — Playgroup / TKA / TKB.
- **Kelompok** — Kelas belajar dalam jenjang.
- **SoD** — Segregation of Duties.

## 4. Features

### 4.1 Design System & Shell

**Description:** Tampilan konsisten brand Lebah Madu (navy/magenta/orange/cream), layout responsif, navigasi modular per role. Realizes semua UJ.

**Functional Requirements:**

#### FR-1: Responsive App Shell

Sidebar collapsible di tablet; konten readable di ≥1024px desktop dan ≥768px tablet.

**Consequences:**
- Sidebar ≤768px menjadi drawer/hamburger.
- Touch target minimum 44px untuk staf tablet.

#### FR-2: Role-aware navigation

Menu hanya menampilkan modul sesuai role; home redirect per role.

**Consequences:**
- Administration: Siswa, Absensi, Tagihan, Katering, Jemputan, Pendaftaran, Absensi Pegawai. **Tidak** ada route Jurnal/COA/Laporan.
- Finance: Dashboard, **Pemasukan** & **Pengeluaran** (alias nav → `/jurnal?jenis=masuk|keluar`), COA, Anggaran, Periode, Pegawai, Gaji, Kasbon, Aset, Laporan, **Tunggakan Tagihan** (read-only).
- SchoolPrincipal: superset Finance + approve actions.
- TeacherInCharge: Kegiatan + absensi siswa read-only + dashboard ringkas.

### 4.2 Modul Siswa & Absensi

**Description:** Menutup mockup MENU SISWA. Realizes UJ-1.

#### FR-3: CRUD Siswa lengkap

Field: NIS, nama, jenjang, kelompok, tanggal lahir, alamat, wali, SPP nominal, status.

#### FR-4: Absensi harian siswa

Alur jenjang → kelompok → daftar siswa; status Hadir/Izin/Sakit/Tidak Hadir; flag katering & jemputan (jemput/pulang).

#### FR-5: Rekapitulasi absensi

Agregat per siswa per periode: hadir, izin, sakit, tidak hadir.

### 4.3 Katering & Jemputan

**Description:** Menutup mockup KATERING & JEMPUTAN. Realizes UJ-1.

#### FR-6: Rekap katering

Tarif per hari dari absensi; filter bulan/jenjang/kelompok.

- **v1 (shipped):** flat **Rp 22.000/hari** — shortcut implementasi.
- **Resmi (2026-06-30, E10):** **Rp 20.000** Sen–Kam + **Rp 10.000** Jumat; lihat §10 & [13-LEGACY-ALIGNMENT-GUIDE.md](../../../docs/13-LEGACY-ALIGNMENT-GUIDE.md) §1b.

#### FR-7: Menu katering mingguan

Input menu Senin–Jumat; upload gambar menu (opsional v1: teks saja).

#### FR-8: Master armada jemputan

CRUD supir, jenis mobil, kapasitas.

#### FR-9: Pendaftaran jemputan siswa

Link ke siswa; alamat; harga dasar.

#### FR-10: Rekap jemputan & pendamping

Rekap siswa per periode; assignment guru pendamping per armada/tanggal.

### 4.4 Keuangan & Akuntansi

**Description:** Menutup mockup MENU KEUANGAN + coretan brief. Realizes UJ-2, UJ-3.

#### FR-11: CRUD COA

Kelola golongan, sub-golongan, akun; import dari CSV referensi.

#### FR-12: Anggaran (kepala 9)

Set pagu per akun/tahun/bulan; carry-over.

#### FR-13: Jurnal dengan maker-checker

Buat multi-baris; submit; approve (Principal); void; immutability POSTED.

**Nav alias (mockup sempro):** Sidebar Finance menampilkan **Pemasukan** dan **Pengeluaran** sebagai entry point ke `/jurnal` dengan preset filter akun pendapatan (4.x) vs beban (5.x). Halaman tetap satu komponen Jurnal — bukan modul terpisah.

#### FR-14: Laporan keuangan

Neraca saldo, posisi keuangan (1–3), laba rugi (4–5), realisasi anggaran, buku besar; filter periode/tahun ajaran.

**v1.1 (deferred):** Laporan arus kas formal (ISAK 35 komponen #5). v1 cukup prediksi kas di dashboard.

#### FR-15: Export & cetak laporan

PDF atau print-friendly CSS untuk laporan dan struk.

### 4.5 Tagihan Siswa

**Description:** Faktur komposit sesuai mockup & biaya website. Realizes UJ-1.

#### FR-16: Generate tagihan otomatis

SPP + katering (absensi bulan lalu) + jemputan (absensi bulan lalu) + komponen tahunan.

#### FR-17: Editor tagihan manual

Edit/hapus line item; BIAYA TAHUNAN/BULANAN/LAIN; grand total.

#### FR-18: Cetak struk/faktur ortu

Layout faktur printable dengan logo sekolah.

### 4.6 Pegawai & Payroll

**Description:** Menutup mockup MENU PEGAWAI.

#### FR-19: CRUD Pegawai + work periode

#### FR-20: Absensi pegawai

Clickable status harian; agregat bulanan.

#### FR-21: Slip gaji lengkap

Gaji pokok, tunjangan, THR, bonus, lunch, asuransi, loan, grand total; posting ke jurnal.

### 4.7 Audit & Governance

#### FR-22: Audit log UI

Read-only list perubahan data untuk Principal/Finance.

#### FR-23: Seed users & demo data

4 role + sample siswa/COA untuk UAT/skripsi.

#### FR-26: Tunggakan tagihan (Finance read-only)

Daftar tagihan BELUM/SEBAGIAN per periode; filter siswa/jenjang; **tanpa** aksi bayar (SoD: Admin yang operasikan pembayaran).

#### FR-27: Absensi siswa read-only (TeacherInCharge)

Guru koordinator dapat melihat rekap absensi kelompok yang menjadi tanggung jawabnya; **tanpa** edit (input tetap Admin TU).

## 10. Legacy Alignment Scope (v1.1 — Epic E10)

> **Keputusan 2026-06-30:** Satu epic unified menggabungkan semua gap hijau + kuning dari investigasi `legacy-data/`. Implementasi **on hold** sampai give go; dokumentasi lengkap di [docs/13-LEGACY-ALIGNMENT-GUIDE.md](../../../docs/13-LEGACY-ALIGNMENT-GUIDE.md).

### 10.1 Konteks

Folder `legacy-data/` berisi 76 CSV spreadsheet operasional riil TK Lebah Madu plus 2 PDF referensi tarif (sudah diekstrak):

| PDF | Isi kunci |
|-----|-----------|
| `biaya masuk PG 2025-2026.pdf` | PG Sem I Rp 5.375.000; SPP Orens Rp 800rb / Ungu Rp 900rb; potongan ke RA Rp 1jt |
| `Brosur Pricelist RA 2526.pdf` | RA tahun 1 Rp 10.950.000; SPP Rp 1.3jt/bln; katering Rp 20rb/hari + snack Jumat Rp 10rb; potongan PG/kakak |

v1 (FR-1–27) memakai `seed_demo` (3 siswa dummy) dan aturan billing disederhanakan (katering flat Rp 22.000/hari sementara, jemput flat bulanan). E10 menutup gap agar demo sidang memakai **data & aturan riil** — tarif katering resmi **Rp 20.000 Sen–Kam + Rp 10.000 Jumat** (keputusan 2026-06-30).

### 10.2 Functional Requirements (E10)

#### FR-28: seed_legacy

Management command import roster, absensi pilot, pegawai, armada dari CSV; idempotent; anchor bulan disarankan Jul-2024.

#### FR-29: Template komponen biaya TP

Komponen tahunan (kegiatan, pengembangan, seragam, potongan tier) per jenjang/status siswa; seed dari TP CSV + PDF pricelist.

#### FR-30: Katering differentiated

**Resmi:** Rp **20.000/hari** Sen–Kam + Rp **10.000** Jumat (snack); hanya hari hadir + `ikut_katering`. PG all-in semester — skip auto-tagihan. Ground truth historis: `laporan katering.csv`.

#### FR-31: Jemput per-trip

Billing `jemput_datang` + `jemput_pulang` × tarif per hari operasional.

#### FR-32: Batch generate tagihan

Generate per kelompok/jenjang/tahun ajaran; preview sebelum commit.

#### FR-33: Payroll KAFALAH mapping

Field Salary Table legacy → slip gaji sistem (tunjangan, transport, uang makan jam×Rp).

#### FR-34: Auto potong pinjaman

Potongan pinjaman pegawai otomatis saat posting gaji.

#### FR-35: Import anggaran CSV

Load rencana & realisasi anggaran dari CSV legacy; tampil di dashboard.

#### FR-36: Export rekap legacy format

CSV katering & jemput mirror layout spreadsheet legacy.

#### FR-37: Dashboard kepsek KPI operasional

Grafik & KPI non-kosong: collection rate, headcount katering, pending approve jurnal.

#### FR-38: validate_legacy

Command bandingkan hitungan sistem vs CSV; laporan diff untuk validasi skripsi.

### 10.3 Non-Goals E10

- Import full historis 2023–2025 semua 76 file
- Portal ortu, WA, VA/QRIS (tetap v2)
- LPJ line-item expense model penuh

### 10.4 Success Criteria E10

- Login kepsek → dashboard menampilkan data dari legacy seed
- Tagihan Jul-2024 TKA ≈ `laporan katering.csv` (toleransi terdokumentasi)
- `uat_walkthrough` extended lulus tanpa regression v1

## 5. Non-Goals (Explicit)

- Portal orang tua & payment gateway (**v2 — setelah 3 role**)
- Integrasi WhatsApp (**v2+**)
- ISAK 35 full compliance report pack (v1 fokus COA sekolah + laporan inti; **laporan arus kas formal → v1.1**)
- Mobile native app
- Integrasi WhatsApp otomatis

## 6. MVP Scope

### 6.1 In Scope

Semua FR-1 s/d FR-27 kecuali FR-7 upload gambar (teks OK) dan komponen arus kas formal FR-14 v1.1. Portal ortu/WA/payment **v2** (setelah 3 role).

### 6.2 Out of Scope for MVP

- Virtual Account per siswa ([benchmark SAKOLA](https://sakola.id/fitur/))
- Multi-unit yayasan
- MFA / SSO

## 7. Success Metrics

**Primary**
- **SM-1:** 100% mockup HTML sub-menu tercover UI Vue — Validates FR-3–FR-21.
- **SM-2:** Alur UJ-1 s/d UJ-3 dapat diselesaikan tanpa workaround API manual — Validates UJ-1–3.

**Secondary**
- **SM-3:** Lighthouse Accessibility ≥85 pada halaman dashboard & tagihan.
- **SM-4:** Frontend test coverage ≥60% critical paths.

**Counter-metrics**
- **SM-C1:** Jangan optimasi jumlah fitur di atas kelengkapan alur end-to-end tiga persona.

## 8. Open Questions

~~Semua resolved 2026-06-28:~~

1. ~~Tarif katering~~ → **Rp 20.000 Sen–Kam + Rp 10.000 Jumat** (2026-06-30; PDF RA + wireframe + CSV Jul-24). v1 sementara 22.000 flat sampai E10.3.
2. ~~Portal ortu~~ → **v2** setelah 3 role terpenuhi; WA/payment v2+
3. ~~Seed credentials~~ → **`<password demo dari seed lokal>`** (dev); lihat `docs/12-BACKEND-REFERENCE.md`
4. ~~Legacy data import~~ → **Epic E10** (FR-28–38); pilot Jul-2024; PDF pricelist diekstrak (PG + RA TA 2025/26)
5. ~~Katering/jemput rules~~ → **E10** katering 20/10 resmi; jemput 80% taksi online per-trip

## 9. Assumptions Index

- `[ASSUMPTION]` Tiga persona utama = Administration, Finance, SchoolPrincipal; TeacherInCharge secondary.
- `[ASSUMPTION]` PrimeVue 4 tetap UI library (no migration Vuetify).
- `[ASSUMPTION]` Backend API `/api/v1/` stabil; pekerjaan dominan di frontend + seed + polish BE minor.
