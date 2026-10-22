# Investigation: UAT Dosen Akuntansi — Post-E10 Feedback

## Hand-off Brief

1. **What happened.** Setelah E10 (legacy alignment), dosen akuntansi menguji aplikasi dengan 3 role demo dan menemukan ~19 isu fungsional/UX: COA tidak lengkap (5 akun vs 187 di COA Final), pesan error PostgreSQL mentah, Kepsek melihat copy "tambah/edit" tanpa tombol aksi, jurnal draft tidak bisa diedit di UI, dan beberapa modul operasional belum CRUD fleksibel.
2. **Where the case stands.** Root cause terkonfirmasi untuk cluster COA, RBAC copy, error handler, jurnal FE gap, PeriodPicker tahun; jemputan nol & arus kas kosong masih **Medium** (perlu verifikasi seed/absensi flag).
3. **What's needed next.** Jalankan Epic **E11** per [14-DOSEN-FEEDBACK-GUIDE.md](../../../docs/14-DOSEN-FEEDBACK-GUIDE.md): P0 = COA Final import + human errors + RBAC copy; P1 = jurnal CRUD + dropdown akun penuh.

## Case Info

| Field            | Value                                                                 |
| ---------------- | --------------------------------------------------------------------- |
| Ticket           | N/A (UAT dosen akuntansi, skripsi submit)                             |
| Date opened      | 2026-07-02                                                            |
| Status           | Concluded (diagnosis) — implementasi menunggu E11                     |
| System           | BeeSmart Finance — Django REST + Vue 3 + PostgreSQL, localhost:5173   |
| Evidence sources | 23 screenshot UAT, backlog user, codebase grep, COA Final CSV         |

## Problem Statement

User melaporkan backlog skripsi dari feedback dosen: modul keuangan & operasional terasa "immutable" pasca-import, pesan error/sukses terlalu teknis, halaman kurang informatif, COA tidak selaras dengan spreadsheet final di `legacy-data/`, dan banyak fitur CRUD/filter belum ada atau tidak konsisten. Dashboard & polish UX ditunda setelah backlog ini.

## Evidence Inventory

| Source                              | Status    | Notes                                                          |
| ----------------------------------- | --------- | -------------------------------------------------------------- |
| 23 screenshot UAT (2026-07-02)      | Available | COA kepsek tanpa aksi, FK error toast, katering kolom nabrak   |
| `legacy-data/...COA Final.csv`      | Available | 187 akun leaf + 21 baris golongan/sub                          |
| `database/raw_data/T_AKUN.csv`      | Available | ~17 baris — seed lama                                          |
| `backend/config/exception_handler.py` | Available | Pass-through pesan PostgreSQL mentah                           |
| `frontend/src/core/errors.ts`       | Available | `detail` dari backend ditampilkan apa adanya pada 400          |
| `frontend/src/features/coa/CoaListView.vue` | Available | `canWrite` hanya Finance; banner tidak beda role               |
| `frontend/src/features/jurnal/JurnalListView.vue` | Available | Hanya Submit/Approve/Void — tidak ada Edit draft               |
| `frontend/src/shared/components/PeriodPicker.vue` | Available | Tahun = `[y-1, y, y+1]` saja — 2024 hilang di 2026             |
| Git / CI logs                       | Missing   | Tidak relevan untuk diagnosis UX                               |

## Investigation Backlog

| # | Path to Explore | Priority | Status | Notes |
| - | --------------- | -------- | ------ | ----- |
| 1 | COA seed vs COA Final | High | Done | 187 vs ~5 akun di DB demo |
| 2 | Jurnal draft edit FE | High | Done | BE support update; FE tidak expose |
| 3 | Jemput datang/pulang 0 | Medium | Open | Perlu cek flag absensi + bulan filter |
| 4 | Audit log "Invalid page" | Medium | Open | Pagination API vs FE page param |
| 5 | Kegiatan + TA periode | Low | Open | Model kegiatan belum terhubung TA |

## Timeline of Events

| Time        | Event                                      | Source              | Confidence  |
| ----------- | ------------------------------------------ | ------------------- | ----------- |
| 2026-06-30  | E10 legacy alignment selesai 12/12         | execution log       | Confirmed   |
| 2026-07-02  | UAT dosen — 23 screenshot + backlog        | user input          | Confirmed   |
| 2026-07-02  | COA Final CSV ditambahkan user di legacy-data | file inventory    | Confirmed   |

## Confirmed Findings

### Finding 1: COA di database jauh lebih sedikit dari COA Final

**Evidence:** `legacy-data/Chart Of Accounts (COA) Lebah Madu(FIX) - COA Final.csv` → 187 akun leaf; screenshot Buku Besar/jurnal menampilkan ~5 akun (1101, 1103, 4101, 5201, …). Seed memakai `database/raw_data/T_AKUN.csv` (~17 baris) via `seed_demo._seed_coa_from_csv`.

**Detail:** Skema kode berbeda — COA Final memakai `111`, `411`, `5101`; seed lama memakai `1101`, `4101`. Filter jurnal pemasukan/pengeluaran (`startsWith("4")` / `"5"`) akan gagal sebagian besar akun jika kode tidak dinormalisasi konsisten.

### Finding 2: Pesan error menampilkan constraint PostgreSQL mentah

**Evidence:** `backend/config/exception_handler.py:20-22` — `IntegrityError` → `Response({"detail": msg})` dengan `msg = str(exc)`. Screenshot: toast "Data belum sesuai" + `violates foreign key constraint "ms_coa_sub_golongan_id_fkey"`.

**Detail:** `frontend/src/core/errors.ts:44-48` menampilkan `detail` backend langsung pada HTTP 400.

### Finding 3: Kepsek melihat copy "tambah/edit" tanpa tombol aksi — by design, copy salah

**Evidence:** `frontend/src/features/coa/CoaListView.vue:29` — `canWrite = auth.hasRole(["Finance"])`. Tombol Tambah/Edit/Delete hanya render jika `canWrite`. Backend: `IsFinanceOrReadOnly` pada COA viewsets (`backend/accounting/api.py:36-48`).

**Detail:** Premise user benar (UX membingungkan); bukan bug permission backend melainkan **copy + visibility** yang tidak selaras RBAC.

### Finding 4: Kode akun/golongan/sub tidak bisa diedit saat edit mode

**Evidence:** `frontend/src/features/coa/CoaListView.vue:291,300,304` — `:disabled="!!editingKey"` pada field kode.

**Detail:** User ingin fleksibilitas edit kode sub-golongan; saat ini sengaja immutable di UI (PK/FK risk).

### Finding 5: Jurnal draft — backend CRUD ada, frontend tidak ada Edit

**Evidence:** `backend/accounting/api.py:90-93` — Finance boleh `update`, `partial_update`, `destroy` pada draft. `frontend/src/features/jurnal/JurnalListView.vue:255-280` — kolom Aksi hanya Submit / Approve / Void; dialog header tetap "Buat Jurnal", tidak ada `openEdit`.

### Finding 6: PeriodPicker tidak menampilkan tahun arsip (2024)

**Evidence:** `frontend/src/shared/components/PeriodPicker.vue:15-17` — opsi tahun = `[currentYear - 1, currentYear, currentYear + 1]`. Pada 2026, 2024 tidak muncul padahal seed absensi legacy mencakup 2024–2026.

### Finding 7: Katering — kolom Tarif dan Total overlap

**Evidence:** Screenshot rekap tagihan katering — string `Rp 20.000 / Rp 10.000` overflow ke kolom Total. Perlu fix CSS/lebar kolom di `KateringView.vue`.

## Deduced Conclusions

### Deduction 1: "List akun belum lengkap" di jurnal & laporan = efek COA seed, bukan bug dropdown terpisah

**Based on:** Finding 1

**Reasoning:** `coaApi.list()` mengembalikan semua `MsCoa` di DB; jumlah kecil karena seed, bukan filter API yang salah (kecuali filter prefix 4.x/5.x yang perlu diselaraskan dengan skema kode baru).

### Deduction 2: Hapus COA "kadang bisa kadang tidak" = expected FK protection, UX buruk

**Based on:** Finding 2

**Reasoning:** Delete gagal bila akun dipakai di `tr_jurnal_detail` atau sub-golongan masih punya akun. Perilaku DB benar; yang salah adalah tidak ada pre-check + pesan humanis.

## Hypothesized Paths

### Hypothesis 1: Jemputan Datang/Pulang semua 0 karena absensi demo tidak set flag jemput

**Status:** Open

**Theory:** Rekap jemput menghitung dari field `jemput_datang`/`jemput_pulang` di absensi; seed legacy atau input manual default "Tidak".

**Would confirm:** Query absensi Juli 2026 — count flag true > 0; atau trace `jemputan` rekap service.

**Would refute:** Parser jemput CSV sudah mengisi flag tapi rekap filter bulan/siswa salah.

### Hypothesis 2: Audit log "Invalid page" = page query melebihi total halaman API

**Status:** Open

**Would confirm:** Network tab saat buka audit log — request `?page=N` dengan N invalid.

## Missing Evidence

| Gap                         | Impact                          | How to Obtain                    |
| --------------------------- | ------------------------------- | -------------------------------- |
| Count jemput flags in DB    | Konfirmasi H1                   | `manage.py shell` atau test query |
| Audit log pagination params | Konfirmasi H2                   | Repro + network trace            |

## Source Code Trace

| Element       | Detail                                                                 |
| ------------- | ---------------------------------------------------------------------- |
| Error origin  | `backend/config/exception_handler.py:20-22`                            |
| Trigger       | DELETE/UPDATE COA/sub-golongan yang masih direferensi                |
| Condition     | `IntegrityError` / `DatabaseError` tidak ditangkap DRF default         |
| Related files | `frontend/src/core/errors.ts`, `CoaListView.vue`, `accounting/api.py`  |

| Element       | Detail                                                                 |
| ------------- | ---------------------------------------------------------------------- |
| Error origin  | `frontend/src/features/jurnal/JurnalListView.vue` — no edit handler      |
| Trigger       | User buka Pemasukan/Pengeluaran, lihat draft                           |
| Condition     | Status DRAFT + role Finance — hanya tombol Submit                      |
| Related files | `backend/accounting/api.py` TrJurnalViewSet, `jurnal/api.ts`           |

## Conclusion

**Confidence:** **High** untuk cluster COA incompleteness, error messaging, Kepsek COA copy/RBAC, jurnal draft FE gap, kode akun disabled on edit, PeriodPicker tahun sempit. **Medium** untuk jemput nol & audit pagination.

Gejala dominan bukan "sistem immutable total" melainkan kombinasi: (1) seed COA partial + skema kode lama, (2) UI sengaja lock kode/PK, (3) pesan error pass-through DB, (4) beberapa CRUD belum di-wire di FE meski BE sudah ada.

## Recommended Next Steps

### Fix direction

| Mekanisme | Aksi |
| --------- | ---- |
| Data      | Importer COA Final → `seed_demo` / command baru; migrasi mapping kode lama→baru |
| UX/RBAC   | Banner COA beda teks Kepsek vs Finance; hide "tambah/edit" untuk read-only |
| Errors    | Map FK/IntegrityError ke pesan ID di exception_handler + patterns di errors.ts |
| CRUD      | Jurnal edit draft; kelompok/jenjang CRUD; absensi edit/hapus per tanggal |
| Filter    | PeriodPicker dari data absensi/jurnal min–max tahun; opsi arsip TA |
| CSS       | Katering column min-width / wrap tarif |

### Diagnostic

- Setelah COA import: assert `MsCoa.objects.count() >= 180`
- UAT: hapus akun terpakai → toast humanis, bukan constraint name
- UAT: kepsek `/coa` → banner "hanya lihat, hubungi Keuangan untuk ubah"

## Reproduction Plan

1. `seed_demo` + login `keuangan` / `<password demo dari seed lokal>`
2. `/coa` → tab Akun → hitung baris (~5)
3. Hapus sub-golongan `51` → toast FK mentah
4. Login `kepsek` → `/coa` → baca banner, konfirmasi tidak ada tombol
5. `/jurnal?jenis=masuk` → buat draft → tidak ada Edit
6. `/rekap-siswa` → dropdown tahun → 2024 tidak ada

## Side Findings

- Dashboard Arus Kas kosong (Confirmed screenshot) — kemungkinan tidak ada jurnal POSTED di rentang chart; terpisah dari COA issue.
- User menunda polish dashboard visual — scope E11+ atau E12.

## Follow-up: 2026-07-02

### New Evidence

COA Final CSV parsed: 187 leaf accounts, format kode hierarkis (111, 5101, …).

### Updated Conclusion

Epic E11 direncanakan; lihat sprint change proposal & guide 14.
