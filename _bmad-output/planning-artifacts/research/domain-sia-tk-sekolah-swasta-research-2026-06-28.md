---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-beesmartfinance-skripsi-2026-06-28/prd.md
  - _bmad-output/implementation-artifacts/investigations/school-finance-standards-investigation.md
  - ../Bismillah Skripsi/diagrams/Chart Of Accounts (COA) Lebah Madu(FIX) - COA .csv
  - ../Bismillah Skripsi/coretan kertas brief sustem.png
workflowType: research
lastStep: 6
research_type: domain
research_topic: Sistem Informasi Akuntansi Sekolah Swasta TK/PG (SIA) — Indonesia
research_goals: Menentukan standar fungsional, akuntansi, dan UX yang seharusnya dipenuhi BeeSmart Finance untuk TK Lebah Madu
user_name: Sinarivan-permananjung
date: 2026-06-28
web_research_enabled: true
source_verification: true
---

# Research Report: Domain — SIA Sekolah Swasta TK/PG Indonesia

**Date:** 2026-06-28  
**Author:** Sinarivan-permananjung  
**Research Type:** Domain / Industry Research

---

## Research Overview

Penelitian domain ini mensintesis standar industri, regulasi akuntansi nirlaba, praktik sekolah swasta Indonesia, dan kebutuhan spesifik TK Lebah Madu untuk memandu penyelesaian BeeSmart Finance v1 (3 role operasional, tanpa portal ortu).

**Metodologi:** Web research (Exa), analisis produk kompetitor, literatur ISAK 35, dokumen referensi sempro, website sekolah.

---

## 1. Konteks Domain

### 1.1 Entitas & karakteristik

Yayasan Pendidikan Sobat Kecil mengelola **Sekolah Lebah Madu** (Playgroup & Kindergarten) di Jakarta Timur — sekolah swasta Islami, terakreditasi A ([sekolahlebahmadu.com](https://sekolahlebahmadu.com/)).

**Karakteristik keuangan sekolah swasta TK/PG:**

| Aspek | Implikasi sistem |
|-------|------------------|
| Sumber dana | SPP, uang masuk, uang kegiatan, uang pengembangan, komite, katering opsional, jemputan opsional |
| Bukan entitas laba | Pelaporan mengacu standar organisasi nirlaba (ISAK 35), bukan laba maksimalisasi |
| Staf non-akuntan | UI harus sederhana; istilah Indonesia; alur harian jelas |
| Transparansi ortu | v1: struk cetak; v2+: portal & notifikasi |
| Skala single-unit | Tidak perlu multi-yayasan di v1 |

**Komponen biaya canonical (dari website sekolah, disetujui user 2026-06-28):**

- SPP TK: **Rp 1.350.000/bulan**
- Katering opsional: **Rp 22.000/hari** (Senin–Kamis)
- Jemputan: tarif per jarak, minimal Rp 20.000
- Biaya tahunan: uang masuk, kegiatan ananda, pengembangan, seragam, komite, formulir, observasi/sit-in

### 1.2 Stakeholder & tiga role operasional (v1)

| Role | Persona | Tanggung jawab keuangan |
|------|---------|-------------------------|
| Administration | Bu Fitri (Admin TU) | Siswa, absensi, katering/jemputan input, generate tagihan, cetak struk |
| Finance | Staff Keuangan | COA, jurnal, anggaran, payroll, laporan |
| SchoolPrincipal | Pak Ali (Kepsek) | Approve jurnal, review dashboard, tutup periode |

**Guru Koordinator (TeacherInCharge):** kegiatan & realisasi anggaran — secondary role.

---

## 2. Standar Akuntansi & Pelaporan

### 2.1 ISAK 35 (entitas nirlaba)

ISAK 35 mengatur penyajian laporan keuangan entitas berorientasi nonlaba ([IAI — DE ISAK 35](https://www.iaiglobal.or.id/v03/files/file_berita/DE%20ISAK%2035.pdf)). Efektif sejak 1 Januari 2020, menggantikan PSAK 45.

**Lima komponen laporan ISAK 35:**

1. Laporan posisi keuangan
2. Laporan penghasilan komprehensif
3. Laporan perubahan aset neto
4. Laporan arus kas
5. Catatan atas laporan keuangan

**Klasifikasi aset neto:** dengan pembatasan (with restrictions) vs tanpa pembatasan (without restrictions).

**Relevansi BeeSmart Finance v1:**

| ISAK 35 | BeeSmart sekarang | Rekomendasi v1 |
|---------|-------------------|----------------|
| Posisi keuangan | ✅ Laporan posisi keuangan | Pertahankan |
| Laba/rugi style | ✅ Laba rugi (golongan 4–5) | OK untuk operasional internal |
| Arus kas | 🟡 Prediksi kas dashboard | Tambah laporan arus kas formal v1.1 |
| Aset neto | ❌ | Deferred — skripsi fokus COA sekolah |
| Catatan atas LK | ❌ | Deferred |

Studi empiris menunjukkan banyak sekolah swasta **belum** sepenuhnya compliant ISAK 35 karena keterbatasan SDM ([JOPBA 2025](https://doi.org/10.31328/jopba.v6i1.401), [JHSS 2024](https://journal.unpak.ac.id/index.php/jhss/article/view/10878)). BeeSmart v1 target: **operasional akuntansi double-entry + laporan inti**; ISAK 35 full compliance sebagai roadmap v2.

### 2.2 COA sekolah swasta (Lebah Madu)

Struktur COA referensi sempro:

| Golongan | Fungsi |
|----------|--------|
| 1 | Aset (kas, bank, perlengkapan) |
| 2 | Liabilitas |
| 3 | Ekuitas / modal |
| 4 | Pendapatan (SPP, uang masuk, formulir, sit-in, dll.) |
| 5 | Beban (TK/PG per kegiatan, pegawai, operasional sekolah) |
| 9 | **Anggaran** — mirror golongan 5 (bukan jurnal operasional) |

**Aturan bisnis:** Setiap akun beban 5.x.x.xx punya pasangan anggaran 9.x.x.xx. Realisasi dibanding pagu; surplus/defisit per periode.

---

## 3. Landscape Kompetitif (Indonesia)

### 3.1 Pola fitur standar industri

Berdasarkan [SAKOLA](https://sakola.id/fitur/), [Siswamedia](https://siswamedia.com/kelola-keuangan-sekolah-lebih-mudah-dan-transparan/), [SISCHOOL](https://sischool.nht01.cloud/), [EDUCASH](https://educash.id/sekolah/), [SAKA ERP](https://www.saka-erp.id/industri/pendidikan):

| Fitur | Prevalensi | BeeSmart v1 |
|-------|------------|-------------|
| Double-entry + COA | Standar | ✅ BE / 🟡 FE COA UI |
| Tagihan SPP otomatis | Sangat umum | 🟡 perlu polish |
| Absensi → billing | Umum (terintegrasi) | ❌ FE gap |
| Maker-checker / approval | Enterprise | ✅ |
| Dashboard KPI keuangan | Standar | ✅ |
| Realisasi anggaran | Yayasan | ✅ |
| Export PDF laporan | Standar | ❌ planned |
| Virtual Account / QRIS | Premium | ❌ v2 |
| Portal orang tua | Premium | ❌ v2 (setelah 3 role) |
| WhatsApp notifikasi | Emerging | ❌ v2 |
| Audit trail UI | Enterprise | ❌ planned |
| ISAK 35 report pack | Yayasan besar | ❌ v2 |

### 3.2 Best practice alur operasional

**Rantai emas sektor pendidikan swasta:**

```
Master siswa → Absensi harian (+ katering/jemputan)
    → Rekap bulanan → Generate tagihan → Bayar → Auto-jurnal
        → Laporan keuangan + realisasi anggaran → Approve kepsek
```

Ini selaras mockup sempro HTML dan literatur SIAS ([JPML 2024 — SIAS Muhammadiyah](https://doi.org/10.30587/jpml.v2i2.7320)).

---

## 4. Rekomendasi Arsitektur Sistem Ideal (BeeSmart Finance v1)

### 4.1 Prinsip desain

1. **Operasional dulu, integrasi ortu belakangan** — 3 role harus end-to-end tanpa API manual.
2. **Backend otoritatif** — UI gating ≠ security; RBAC + SoD di server.
3. **Brand-professional** — dashboard admin selaras [sekolahlebahmadu.com](https://sekolahlebahmadu.com/), bukan clone landing page.
4. **Bahasa & angka Indonesia** — Rp, locale id-ID, istilah akuntansi familiar staf.
5. **Mobile-tablet untuk absensi** — desktop untuk keuangan/laporan.

### 4.2 Modul wajib v1 (prioritas)

| Prioritas | Modul | Justifikasi domain |
|-----------|-------|-------------------|
| P0 | Absensi siswa + flags katering/jemputan | Input billing chain |
| P0 | Tagihan generate + cetak struk | Core revenue TK |
| P0 | COA UI | Master data akuntansi |
| P0 | App shell role-aware | 3 persona |
| P1 | Katering rekap + menu | Website biaya katering |
| P1 | Jemputan armada + pendaftaran | Layanan opsional sekolah |
| P1 | Export laporan PDF | Standar industri |
| P1 | Audit log viewer | Akuntabilitas yayasan |
| P2 | Portal ortu, VA, WA | Post-v1 |

### 4.3 Keputusan produk (confirmed user 2026-06-28)

| Keputusan | Nilai |
|-----------|-------|
| Tarif katering canonical | **Rp 22.000/hari** (website TK) |
| Portal ortu | **v2** — setelah 3 role complete |
| Integrasi WA/pembayaran | **v2+** |
| Seed credentials | Dev standard (lihat Backend Reference) |

---

## 5. Gap BeeSmart vs Domain Ideal

| Domain requirement | Status | Epic |
|--------------------|--------|------|
| Rantai absensi→tagihan | Broken FE | E2–E4, E6 |
| COA management | BE only | E5 |
| 3 role journeys UJ-1/2/3 | Partial | E1, E6, E9 |
| Katering Rp22rb | Not configured | E3 |
| ISAK 35 full | Not required v1 | Backlog |
| Export laporan | Missing | E5.5 |

---

## 6. Kesimpulan Domain

BeeSmart Finance berada di domain **SIA sekolah swasta single-unit TK/PG**. Standar industri menuntut integrasi operasional→akuntansi→pelaporan dalam satu sistem. Backend BeeSmart sudah memenuhi **fondasi akuntansi profesional** (double-entry, anggaran 9.x, maker-checker, audit DB). Gap dominan ada di **frontend operasional** dan **UX staf non-teknis**.

**Target v1:** Sistem yang memungkinkan Bu Fitri, Staff Keuangan, dan Pak Ali menjalankan alur harian/bulanan tanpa Excel — selaras mockup sempro dan biaya resmi website sekolah.

**Target v2:** Portal ortu, notifikasi WA, pembayaran digital, laporan ISAK 35 lengkap.

---

## Sources

- [Sekolah Lebah Madu — website resmi](https://sekolahlebahmadu.com/)
- [SAKOLA — fitur modul keuangan sekolah](https://sakola.id/fitur/)
- [Siswamedia — kelola keuangan sekolah](https://siswamedia.com/kelola-keuangan-sekolah-lebih-mudah-dan-transparan/)
- [SISCHOOL Indonesia](https://sischool.nht01.cloud/)
- [EDUCASH — modul keuangan sekolah](https://educash.id/sekolah/)
- [SAKA ERP — pendidikan](https://www.saka-erp.id/industri/pendidikan)
- [IAI — DE ISAK 35 PDF](https://www.iaiglobal.or.id/v03/files/file_berita/DE%20ISAK%2035.pdf)
- [JOPBA — Penerapan ISAK 35 lembaga pendidikan](https://doi.org/10.31328/jopba.v6i1.401)
- [JPML — Implementasi SIAS sekolah](https://doi.org/10.30587/jpml.v2i2.7320)
- [Accounting+ — aplikasi keuangan sekolah swasta](https://accountingplus.id/blog/aplikasi-pencatat-keuangan-sekolah-swasta-yayasan-pendidikan/)
- [SI-PEKA — pengendalian internal anggaran pendidikan](https://doi.org/10.25170/balance.v21i1.5005)
