# UAT Dosen Akuntansi — Guide & Eksekusi (Epic E11)

> **Epic E11** — Perbaikan pasca-UAT dosen akuntansi: COA Final, pesan humanis, CRUD fleksibel, filter & informatif per halaman.  
> **Status:** ✅ E11 selesai (2026-07-02) · E12 dashboard polish ditunda  
> **Investigasi:** `_bmad-output/implementation-artifacts/investigations/dosen-feedback-uat-investigation.md`  
> **Sprint change:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-07-02.md`  
> **Log progress:** [10-EXECUTION-LOG.md](./10-EXECUTION-LOG.md) → section E11

---

## 1. Konteks & Prinsip

| Prinsip | Artinya di kode |
|---------|-----------------|
| **Fleksibel, bukan immutable** | Edit/nonaktif > hapus paksa; guard FK dengan pesan jelas |
| **Humanis** | Guru/staf tidak perlu baca `violates foreign key constraint` |
| **Informatif per halaman** | Banner biru: apa halaman ini, siapa yang boleh ubah, rumus jika ada |
| **COA Final = source of truth** | `legacy-data/Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv` |

**Ditunda (E12):** Polish visual dashboard (chart, spacing, "kunok").

### 1b. Pola informatif per halaman — status saat ini

**Sudah ada (partial):**

| Lapisan | Implementasi | Contoh |
|---------|--------------|--------|
| **Subtitle** di bawah judul | `PageLayout` — semua halaman utama | "Kelola golongan, sub-golongan, dan akun" |
| **Banner biru** (`Message severity="info"`) | ~11 dari ~21 halaman | COA, katering, jemputan, laporan, rekap absensi |
| **Toast humanis** (framework) | `core/errors.ts` — summary ID | "Data belum sesuai", "Koneksi terputus" |

**Belum / perlu E11:**

| Gap | Target E11 |
|-----|------------|
| ~10 halaman **tanpa banner** (jurnal, siswa, pegawai, periode, kegiatan, dashboard, …) | Tambah banner singkat + siapa yang boleh edit |
| Banner COA **sama untuk semua role** | Kepsek: "lihat saja"; Keuangan: "bisa tambah/ubah" |
| **Detail error** masih mentah | Map FK/validasi → kalimat untuk guru (story 11.2) |
| **Hint inline** di form (contoh: pilih sub-golongan dulu) | Helper text di dialog COA/jurnal |

**Pendekatan copy:** informatif tapi humanis — jelaskan *apa*, *siapa*, *rumus/batasan*; hindari istilah DB/API.

### 1c. Operabilitas COA — bug dikonfirmasi (belum diperbaiki)

| Gejala | Penyebab (Confirmed) |
|--------|----------------------|
| **Buat akun gagal** | FE kirim `sub_golongan` = `kode_sub` (string); API expect **id numerik** FK (`CoaListView.vue:307`, OpenAPI `MsCoa.sub_golongan: number`) |
| **Hapus kadang bisa kadang tidak** | Expected: baris tanpa referensi bisa dihapus; yang dipakai jurnal/sub-golongan → FK block. UX buruk karena pesan PostgreSQL mentah |
| **Edit kode akun/sub** | Sengaja disabled di UI saat edit (`:disabled="!!editingKey"`) |

Story **11.1 + 11.2 + fix FE sub_golongan** = COA harus bisa ditambah, diedit (nama/nonaktif), dihapus hanya jika aman, dengan pesan jelas.

---

## 2. Mapping Screenshot → Issue

| SS | Halaman | Role | Issue terkonfirmasi |
|----|---------|------|---------------------|
| COA kepsek | `/coa` | Kepsek | Copy "tambah/edit" tapi **tanpa tombol** — read-only by design, copy salah |
| COA keuangan | `/coa` | Keuangan | Hanya ~5 akun; delete → **error FK mentah** |
| Sub-golongan | `/coa` tab | Keuangan | Delete golongan/sub → FK error mentah |
| Buku besar | `/laporan` | Keuangan | Dropdown akun **tidak lengkap** |
| Pemasukan | `/jurnal?jenis=masuk` | Keuangan | Akun 4.x sedikit; **draft tidak bisa edit** |
| Pengeluaran | `/jurnal?jenis=keluar` | Keuangan | Akun 5.x sedikit; sama draft issue |
| Katering rekap | `/katering` | Staf TU | **Kolom Tarif & Total nabrak** |
| Katering menu | `/katering` | Staf TU | Modal teks saja — **belum upload gambar** |
| Jemputan rekap | `/jemputan` | Staf TU | Datang/Pulang/Total **semua 0** |
| Rekap absensi | `/rekap-siswa` | Staf TU | **Tahun 2024 tidak ada** di dropdown |
| Absensi | `/absensi` | Staf TU | Input ada; **edit/hapus** belum |
| Periode | `/periode` | Keuangan | Hanya 1 periode; perlu **TA/kegiatan** |
| Dashboard | `/` | Kepsek/Keuangan | **Tanpa filter tanggal**; arus kas kosong |
| Audit log | `/audit-log` | Keuangan | Toast **"Invalid page"** |

---

## 3. Backlog → Story E11

### P0 — Blocker sidang / demo keuangan

| ID | Story | Acceptance criteria | File kunci |
|----|-------|---------------------|------------|
| **11.1** | Import COA Final | ≥180 akun; golongan/sub hierarkis; seed + legacy resolver | `seed_demo.py`, command baru `import_coa_final` |
| **11.2** | Pesan error humanis | FK/check → bahasa ID; tidak tampil nama constraint | `exception_handler.py`, `errors.ts` |
| **11.3** | COA copy & RBAC | Kepsek: banner read-only; Keuangan: CRUD penuh | `CoaListView.vue` |
| **11.4** | Jurnal draft CRUD | Edit + hapus draft; dropdown akun lengkap | `JurnalListView.vue`, `jurnal/api.ts` |

### P1 — Operasional TU

| ID | Story | Acceptance criteria | File kunci |
|----|-------|---------------------|------------|
| **11.5** | Fix katering UI | Kolom Tarif wrap/min-width; Total terbaca | `KateringView.vue` |
| **11.6** | Rekap absensi filter | Tahun dari min/max data absensi (2024–2026+); filter bulan benar | `PeriodPicker.vue`, `RekapSiswaView.vue` |
| **11.7** | CRUD kelompok | Halaman kelola jenjang/kelompok; pindah siswa antar kelompok | router, BE `KelompokViewSet` |
| **11.8** | Absensi CRUD | Edit/hapus absensi per tanggal+siswa (Staf TU) | absensi API + FE |

### P2 — Fitur lanjutan

| ID | Story | Acceptance criteria |
|----|-------|---------------------|
| **11.9** | Dashboard filter | Pilih hari/bulan/tahun; KPI refresh sesuai periode | ✅ |
| **11.10** | Katering gambar | Upload foto menu per hari; widget di dashboard | ✅ |
| **11.11** | Kegiatan + TA | Periode/tahun pelajaran; posting kegiatan → akun penanggung jawab | ✅ |
| **11.12** | Arsip absensi | TA lama collapsed/archived; rekap default TA aktif | ✅ |

### Cross-cutting (semua story)

- Banner informatif per halaman (siapa edit, rumus, batasan)
- Toast sukses konsisten via `notifySuccess`
- Edit kode sub-golongan: allowed jika tidak direferensi (backend validation)

---

## 4. COA Final — Rencana Migrasi

### Sumber

```
legacy-data/Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv
```

| Metrik | Nilai |
|--------|-------|
| Akun leaf | ~187 |
| Golongan/sub | ~21 |
| Format kode | Hierarkis: `111`, `411`, `5101` (bukan `1101`, `4101`) |

### Langkah implementasi

1. Parser CSV: baris dengan `NAMA AKUN` = leaf; baris dengan `TIPE AKUN` = sub/golongan
2. Command `python manage.py import_coa_final [--replace]`
3. Mapping kode lama → baru untuk jurnal posted (lookup table atau one-time script)
4. Update `anggaran_import.resolve_kode_akun` untuk prefix baru
5. Update filter jurnal: `startsWith("4")` tetap valid untuk pendapatan `41x`, `411`, dll.

### Verifikasi

```bash
cd backend
python manage.py import_coa_final
python manage.py shell -c "from accounting.models import MsCoa; print(MsCoa.objects.count())"
# expect >= 180
```

---

## 5. Pesan Error — Katalog Humanis

| Situasi teknis | Pesan untuk user |
|----------------|------------------|
| FK `ms_coa` / `tr_jurnal_detail` | "Akun ini masih tercatat di jurnal. Nonaktifkan akun, atau hubungi Keuangan untuk cek jurnal terkait." |
| FK `ms_sub_golongan` → `ms_coa` | "Sub-golongan masih punya akun di dalamnya. Pindahkan atau hapus akun-akun tersebut dulu." |
| FK golongan → sub | "Golongan masih punya sub-golongan. Hapus sub-golongan terlebih dahulu." |
| Periode tutup | "Periode akuntansi sudah ditutup. Tidak bisa mengubah data di periode ini." |
| Pagination invalid | "Halaman tidak ditemukan. Coba kembali ke halaman pertama." |
| Network | (sudah ada) "Koneksi terputus…" |

---

## 6. RBAC COA (keputusan produk)

| Role | `/coa` |
|------|--------|
| **Staff Keuangan** | Full CRUD golongan, sub, akun |
| **Kepala Sekolah** | **Read-only** + laporan; approve jurnal, tutup periode |
| **Staf TU** | Tidak akses menu COA |

Copy banner Kepsek:

> *Daftar akun akuntansi sekolah — **mode lihat saja**. Untuk menambah atau mengubah akun, minta Staff Keuangan.*

---

## 7. UAT Checklist per Role (post-E11 + BE↔FE sync)

### Persiapan (sekali, sebelum UAT)

```bash
cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py import_coa_final   # jika COA < 180 akun
../.venv/bin/python manage.py runserver 8000
# frontend: npm run dev → hard refresh browser
```

| Akun | Role | Password | Home default |
|------|------|----------|--------------|
| `admin.tu` | Staf TU | `<password demo dari seed lokal>` | `/siswa` |
| `keuangan` | Staf Keuangan | `<password demo dari seed lokal>` | `/dashboard` |
| `kepsek` | Kepala Sekolah | `<password demo dari seed lokal>` | `/dashboard` |
| `guru.kegiatan` | Guru PIC Kegiatan | `<password demo dari seed lokal>` | `/kegiatan` |

**Pass criteria umum:** tidak ada error PostgreSQL mentah di toast; pesan error bahasa Indonesia; aksi sesuai RBAC (role yang tidak boleh edit tidak melihat tombol).

---

### UJ-1 — Bu Fitri (`admin.tu`) · Operasional Siswa & TU

| # | Halaman | Langkah | Expected | ✓ |
|---|---------|---------|----------|---|
| 1 | Login | Masuk `admin.tu` | Redirect ke Data Siswa | [ ] |
| 2 | `/siswa` | Tambah siswa → edit → hapus (siswa tanpa tagihan) | CRUD OK | [ ] |
| 3 | `/kelompok` | Tab Jenjang/Kelompok: tambah, edit, hapus (kosong) | Guard FK pesan jelas | [ ] |
| 4 | `/kelompok` | Tab Pindah Siswa: pindah antar kelompok | Siswa kelompok berubah | [ ] |
| 5 | `/absensi-siswa` | Input absensi hari ini + simpan | Record tersimpan | [ ] |
| 6 | `/absensi-siswa` | Edit flag katering/jemput + **Hapus** record | Update/hapus OK | [ ] |
| 7 | `/rekap-siswa` | Default TA aktif; pilih TA lama (arsip) | Angka bulan sesuai | [ ] |
| 8 | `/rekap-siswa` | Export CSV | File terunduh | [ ] |
| 9 | `/katering` | Rekap: kolom tarif/total rapi | Tidak overlap | [ ] |
| 10 | `/katering` | Menu: upload foto + keterangan | Thumbnail muncul | [ ] |
| 11 | `/jemputan` | Armada + pendaftaran siswa | CRUD OK | [ ] |
| 12 | `/jemputan` | Rekap bulan — angka datang/pulang | Bukan semua 0 (jika ada absensi) | [ ] |
| 13 | `/tagihan` | Preview & Edit → simpan tagihan | Tagihan tercatat | [ ] |
| 14 | `/tagihan` | **Generate Langsung** (1 siswa) | Tagihan auto dari absensi | [ ] |
| 15 | `/tagihan` | Batch generate per kelompok | N tagihan dibuat | [ ] |
| 16 | `/tagihan` | Bayar + cetak struk | Jurnal draft + preview struk | [ ] |
| 17 | `/pendaftaran` | Sit-in bayar → finalisasi | Siswa baru muncul di `/siswa` | [ ] |
| 18 | `/pegawai` | CRUD pegawai | OK | [ ] |
| 19 | `/absensi-pegawai` | Grid bulk-save | Rekap bulanan pegawai OK | [ ] |
| 20 | RBAC | Coba buka `/coa` atau `/dashboard` | Redirect / tidak ada menu | [ ] |

---

### UJ-2 — Staff Keuangan (`keuangan`) · Keuangan & Payroll

| # | Halaman | Langkah | Expected | ✓ |
|---|---------|---------|----------|---|
| 1 | Login | Masuk `keuangan` | Dashboard terbuka | [ ] |
| 2 | `/dashboard` | Filter bulan/tahun/hari | KPI & grafik refresh | [ ] |
| 3 | `/dashboard` | Widget menu katering hari ini | Teks/foto (jika ada menu) | [ ] |
| 4 | `/coa` | List ≥180 akun | COA Final loaded | [ ] |
| 5 | `/coa` | Tambah akun (pilih sub-golongan) | Berhasil, bukan error FK | [ ] |
| 6 | `/coa` | Hapus akun **terpakai** jurnal | Pesan humanis (bukan PostgreSQL) | [ ] |
| 7 | `/jurnal?jenis=masuk` | Dropdown akun pendapatan lengkap | Semua akun 4.x | [ ] |
| 8 | `/jurnal?jenis=masuk` | Buat draft → **Edit** → Submit | Maker-checker flow | [ ] |
| 9 | `/jurnal?jenis=keluar` | Dropdown akun beban lengkap | Semua akun 5.x | [ ] |
| 10 | `/jurnal?jenis=keluar` | Hapus draft | OK | [ ] |
| 11 | `/laporan` | Buku besar — dropdown akun lengkap | Semua akun aktif | [ ] |
| 12 | `/laporan` | Neraca, LR, posisi keuangan | Data tampil per tahun | [ ] |
| 13 | `/anggaran` | Tambah/edit/hapus baris anggaran | CRUD OK | [ ] |
| 14 | `/periode` | Tambah periode TA (2025/2026) | Periode OPEN | [ ] |
| 15 | `/tunggakan-tagihan` | List tagihan BELUM | Filter benar | [ ] |
| 16 | `/gaji` | Buat slip → edit → hapus (belum posting) | CRUD OK | [ ] |
| 17 | `/gaji` | Posting gaji | Jurnal DRAFT terbuat | [ ] |
| 18 | `/pinjaman` | Ajukan → edit → hapus (belum cair) | CRUD OK | [ ] |
| 19 | `/pinjaman` | Cairkan kasbon | Jurnal DRAFT terbuat | [ ] |
| 20 | `/aset` | Tambah aset → edit → susutkan | Penyusutan + jurnal | [ ] |
| 21 | `/aset` | Hapus aset tanpa penyusutan | OK | [ ] |
| 22 | `/audit-log` | Page 2+ pagination | Tidak ada "Invalid page" | [ ] |
| 23 | RBAC | Approve jurnal sendiri | Ditolak (SoD) | [ ] |

---

### UJ-3 — Pak Ali (`kepsek`) · Governance & Read-only

| # | Halaman | Langkah | Expected | ✓ |
|---|---------|---------|----------|---|
| 1 | Login | Masuk `kepsek` | Dashboard terbuka | [ ] |
| 2 | `/dashboard` | Filter periode + KPI operasional | Angka siswa/hadir/tagihan | [ ] |
| 3 | `/coa` | Buka halaman COA | Banner **mode lihat saja**; **tanpa** tombol tambah/edit/hapus | [ ] |
| 4 | `/jurnal` | Lihat jurnal PENDING | Bisa approve | [ ] |
| 5 | `/jurnal` | Approve jurnal dari keuangan | Status → POSTED | [ ] |
| 6 | `/jurnal` | Void jurnal posted | Reversal entry | [ ] |
| 7 | `/periode` | Tutup buku periode OPEN | Jurnal penutup + status CLOSED | [ ] |
| 8 | `/laporan` | Laporan keuangan | Read-only, data tampil | [ ] |
| 9 | `/tunggakan-tagihan` | Lihat tunggakan | Read-only list | [ ] |
| 10 | `/audit-log` | Filter + detail JSON | Log tampil | [ ] |
| 11 | `/kegiatan` | Buat kegiatan + pilih TA | Periode terikat | [ ] |
| 12 | `/kegiatan` | Edit/hapus kegiatan (belum realisasi) | CRUD OK | [ ] |
| 13 | RBAC | Buat jurnal manual | Tidak ada tombol / ditolak | [ ] |
| 14 | RBAC | Buka `/siswa`, `/tagihan` | Tidak ada menu TU | [ ] |

---

### UJ-4 — Guru PIC (`guru.kegiatan`) · Kegiatan (opsional)

| # | Halaman | Langkah | Expected | ✓ |
|---|---------|---------|----------|---|
| 1 | Login | Masuk `guru.kegiatan` | Redirect `/kegiatan` | [ ] |
| 2 | `/kegiatan` | Catat realisasi kegiatan | Jurnal DRAFT + pagu berkurang | [ ] |
| 3 | `/kegiatan` | Laporan utilisasi | Rincian nominal | [ ] |
| 4 | `/rekap-siswa` | Buka rekap (read-only) | Banner guru; tidak bisa edit absensi | [ ] |
| 5 | RBAC | Buat/hapus kegiatan | Tidak ada tombol (Kepsek only) | [ ] |

---

### Cross-cutting (semua role relevan)

- [ ] Toast sukses konsisten (hijau), error humanis (merah/orange)
- [ ] Logout → login role lain → menu sidebar berubah sesuai role
- [ ] API walkthrough: `cd backend && ../.venv/bin/python manage.py uat_walkthrough` → 31/31

**Catatan sidang:** centang minimal UJ-1 (20) + UJ-2 (23) + UJ-3 (14) = **57 item**. UJ-4 opsional untuk demo kegiatan sekolah.

---

## 8. Urutan Eksekusi (recommended)

```
11.1 COA Final → 11.2 errors → 11.3 RBAC copy → 11.4 jurnal CRUD
     ↓
11.5 katering UI → 11.6 rekap filter → 11.7 kelompok → 11.8 absensi CRUD
     ↓
11.9 dashboard filter → 11.10 gambar → 11.11 kegiatan → 11.12 arsip
     ↓
E12 dashboard polish (terpisah)
```

---

## Quick Links

| Resource | Path |
|----------|------|
| COA Final CSV | `legacy-data/Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv` |
| Investigation | `_bmad-output/implementation-artifacts/investigations/dosen-feedback-uat-investigation.md` |
| Sprint proposal | `_bmad-output/planning-artifacts/sprint-change-proposal-2026-07-02.md` |
| Execution log | [10-EXECUTION-LOG.md](./10-EXECUTION-LOG.md) |
