# Investigation: Manajemen Akun — UI, Role, & Deployment Real-World

## Hand-off Brief

1. **What happened.** User mengharapkan UI manajemen akun di aplikasi Vue; saat ini hanya ada login 4 role + Django Admin (`/admin/`) yang memerlukan akun staff/superuser terpisah — bukan bagian produk v1.
2. **Where the case stands.** **Confirmed:** v1 tidak punya FR/modul pengguna di frontend; akun dibuat via `seed_demo` / CLI. Django Admin bukan solusi operasional untuk staf TK.
3. **What's needed next.** Untuk skripsi: dokumentasikan model deployment (docker-compose = satu perintah, staf hanya buka browser). Untuk produk: rencanakan **v2 modul `/pengguna`** tanpa role bisnis ke-5 — gunakan permission teknis terpisah.

## Case Info

| Field            | Value                                                                 |
| ---------------- | --------------------------------------------------------------------- |
| Ticket           | N/A (diskusi arsitektur)                                              |
| Date opened      | 2026-06-28                                                            |
| Status           | Concluded                                                             |
| System           | BeeSmart Finance — Django REST + Vue 3, RBAC 4 Groups                 |
| Evidence sources | PRD, seed_demo, accounts API, screenshot Django Admin login           |

## Problem Statement

**Hipotesis user:** "Manajemen akun harusnya ada UI-nya juga kan? Berarti nambah 1 role lagi? Di real world musti jalanin backend dulu gitu?"

**Premise to verify:** (a) gap UI memang ada; (b) solusinya role baru; (c) deployment mengharuskan staf akses backend/admin.

## Evidence Inventory

| Source                         | Status    | Notes                                      |
| ------------------------------ | --------- | ------------------------------------------ |
| PRD v1 (FR-23)                 | Available | Hanya seed users, bukan CRUD UI            |
| `backend/accounts/api.py`      | Available | Hanya `GET /auth/me/` — read profile       |
| `frontend/src/features/auth/`  | Available | Hanya `LoginView.vue`                      |
| `seed_demo` users              | Available | 4 user, `is_staff=True`, **bukan superuser** |
| Django `/admin/`               | Available | User screenshot — login gagal / tidak produk |
| `docker-compose.yml`           | Available | Satu perintah: migrate + seed + run        |
| Frontend nav                   | Available | Tidak ada menu Pengguna/Akun               |

## Confirmed Findings

### Finding 1: v1 tidak punya UI manajemen akun

**Evidence:** `backend/accounts/api.py:11-22` — satu endpoint `MeView` (profil login). Tidak ada `/users/` CRUD di router `backend/config/urls.py`.

**Detail:** Frontend hanya `LoginView` + role di `AppShell`. PRD FR-23: "Seed users & demo data" — bukan manajemen pengguna.

### Finding 2: Empat role bisnis sudah cukup untuk operasional TK

**Evidence:** `backend/accounts/migrations/0002_seed_groups.py`, PRD §2.2 tabel role.

| Group Django          | Persona demo   | Fungsi bisnis                    |
| --------------------- | -------------- | -------------------------------- |
| Administration        | admin.tu       | Operasional siswa/tagihan        |
| Finance               | keuangan       | Jurnal, COA, laporan              |
| SchoolPrincipal       | kepsek         | Approve, oversight, audit        |
| TeacherInCharge       | guru.kegiatan  | Kegiatan sekolah                 |

**Detail:** Keempat ini = **hak akses modul**, bukan "siapa yang buat akun".

### Finding 3: Django Admin ≠ aplikasi produk

**Evidence:** `backend/accounts/admin.py:6` — register User ke Django Admin. `seed_demo.py:132-137` — user demo `is_staff=True` tapi **tidak** `is_superuser=True`.

**Detail:** Screenshot `/admin/login/` menampilkan error "akun **staf**" — ini panel teknis Django, terpisah dari Vue di `:5174`. Staff tanpa superuser/permission model User **tidak bisa** kelola akun dengan nyaman. Ini **by design** untuk developer, bukan Bu Fitri.

### Finding 4: Real-world deployment tidak mengharuskan staf "jalanin backend"

**Evidence:** `docker-compose.yml:38-41` — `migrate && seed_demo && runserver` otomatis.

**Detail:**
- **Development:** 2 proses (API + Vite) atau `docker compose up --build`
- **Production (target):** satu stack Docker / VPS — staf buka **http://sekolah/app** saja
- Django Admin **sebaiknya tidak diekspos** ke internet (firewall / non-prod only)

## Deduced Conclusions

### Deduction 1: Gap UI manajemen akun memang ada — tapi bukan scope v1

**Based on:** Finding 1, PRD FR-23

**Conclusion:** Wajar user merasa "kurang" saat pegawai baru masuk. v1 mengandalkan seed/CLI; belum ada alur "Kepsek tambah user Bu Fitri baru".

### Deduction 2: Jangan tambah role bisnis ke-5 "Admin Sistem"

**Based on:** Finding 2, PRD persona

**Reasoning:** Role ke-5 akan bentrok dengan Administration (nama "admin") dan membingungkan SoD. Pola yang lebih bersih: **capability teknis** terpisah dari 4 role operasional.

**Conclusion:** Manajemen akun = **permission/capability**, bukan persona bisnis TK.

## Hypothesized Paths

### Hypothesis 1: Perlu modul `/pengguna` di Vue (v2)

**Status:** Open (rekomendasi produk)

**Theory:** CRUD user, assign group, reset password — UI selaras brand.

**Would confirm:** FR baru + epic implementasi.

**Would refute:** Sekolah setuju semua perubahan akun via IT vendor (CLI saja).

### Hypothesis 2: Kepsek yang mengelola akun staf

**Status:** Open

**Theory:** `SchoolPrincipal` + permission `manage_users` — masuk akal governance TK.

**Would confirm:** Wawancara stakeholder.

**Alternative:** TU kepala (`Administration`) — risiko SoD lebih besar.

### Hypothesis 3: Screenshot admin gagal karena bukan superuser / password salah

**Status:** Confirmed (partial)

**Theory:** `admin.tu` + `<password demo dari seed lokal>` punya `is_staff` tapi tanpa superuser tidak punya menu User di admin.

**Would confirm:** `createsuperuser` bisa login admin penuh.

## Missing Evidence

| Gap                    | Impact                          | How to Obtain              |
| ---------------------- | ------------------------------- | -------------------------- |
| Kebijakan sekolah      | Siapa boleh buat/hapus akun     | Wawancara kepala sekolah   |
| Hosting target prod    | Apakah admin Django diekspos    | Keputusan deploy skripsi   |

## Conclusion

**Confidence:** **High** untuk arsitektur saat ini; **Medium** untuk desain v2 manajemen akun.

**Ringkas:**
- **Ya**, idealnya ada UI manajemen akun — **belum ada di v1** (sengaja di-defer).
- **Tidak perlu** role bisnis ke-5 — pisahkan **Manajemen Pengguna** sebagai permission/modul v2.
- **Tidak**, staf real-world **tidak** harus akses `/admin/` atau terminal — mereka pakai Vue app; backend jalan sebagai service (Docker).

## Recommended Next Steps

### Untuk skripsi (sekarang)

1. Di bab implementasi/deployment: jelaskan **3 lapisan akses**
   - Staf → Vue app (`:5174` / `:8080`)
   - Setup awal → `seed_demo` / `createsuperuser` (sekali)
   - Django Admin → **dev/IT only**, bukan user story
2. Demo sidang: `docker compose up` → buka frontend → login 4 persona
3. Backlog v2: **Epic Pengguna** — `/pengguna`, assign role, reset password

### Untuk v2 (implementasi)

| Item | Detail |
| ---- | ------ |
| API | `GET/POST/PATCH /users/`, `POST /users/{id}/reset-password/` |
| Permission | `IsSuperuserOrManageUsers` — superuser ATAU group + flag |
| UI | `PenggunaListView.vue` — DataTable, dialog form, multi-select group |
| Siapa akses | **Rekomendasi:** Kepsek saja (bukan role baru) |
| Seed dev | Opsional: `createsuperuser` untuk IT; jangan andalkan `/admin/` untuk demo |

### Fix cepat dev (opsional)

Jika perlu Django Admin untuk debugging:

```bash
python backend/manage.py createsuperuser
# atau seed satu superuser dev-only (jangan commit password prod)
```

---

## Side Findings

- User demo `is_staff=True` (`seed_demo.py:137`) — cukup untuk login admin tapi **tanpa hak kelola** kecuali superuser.
- `auth/me` mengembalikan `is_superuser` (`accounts/api.py:20`) — frontend sudah siap gate fitur admin di masa depan via `auth.user.is_superuser`.
