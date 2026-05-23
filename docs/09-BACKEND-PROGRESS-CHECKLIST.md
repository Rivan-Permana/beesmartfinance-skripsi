# ✅ Backend Progress Checklist

> Status implementasi backend `BeeSmart Finance` dicocokkan dengan dokumen
> rencana pengembangan. Diperbarui per fase backend (sebelum frontend).
>
> Legenda: ✅ selesai · 🟡 sebagian · ⬜ belum · ➖ tidak dikerjakan (di luar scope saat ini)

Catatan arsitektur penting (penyimpangan sadar dari draft awal docs):
- **Core accounting** (COA, jurnal, anggaran, periode, audit) dibuat via **raw SQL**
  (`database/schemas/*.sql`) dan diakses Django sebagai model `managed=False` —
  bukan model Django biasa. Integritas akuntansi ditegakkan **trigger PostgreSQL**.
- **Modul operasional** (siswa, pegawai, tagihan, gaji, aset, layanan) dibangun penuh
  dengan **Django ORM** + auto-posting ke core via service layer.
- **Custom user** (`accounts.User`) + RBAC berbasis **Django Groups**.

---

## 1. Migration Roadmap (`08-MIGRATION-ROADMAP.md`)

### Phase 1 — Backend Foundation
- ✅ Setup environment variables (`.env` + `django-environ`, `.env.example`)
- 🟡 Security headers — `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` dari env; header HTTPS (HSTS/SSL redirect) **belum**
- ⬜ Rate limiting
- ✅ Logging audit — `audit_log` + trigger `fn_audit` (tamper-evident)
- ⬜ Error pages (relevan saat ada UI/HTML; API pakai handler DRF)
- ✅ Migrasi ke PostgreSQL (skema + ETL sudah; backend pakai Postgres)
- ✅ Database indexes (`02_governance.sql`: index FK & status)
- ✅ Refactor ke arsitektur berlapis (service layer `services.py`)
- ✅ Service layer untuk modul (tagihan/gaji/kasbon/penyusutan/closing/reversal)

### Phase 2 — API Development
- ✅ Install DRF
- ✅ JWT authentication (SimpleJWT: `/api/auth/token/`, `refresh`)
- ✅ Serializers (coa, jurnal, anggaran, siswa, pegawai, tagihan, gaji, aset, dll)
- ✅ ViewSets (router penuh untuk seluruh resource)
- 🟡 Filtering/search/pagination — pagination ✅; `django-filter`/SearchFilter **belum**
- ✅ Custom endpoints (submit/approve/void/bayar/cairkan/posting/susutkan/tutup)
- ✅ Dokumentasi API (`drf-spectacular`: `/api/schema/`, `/api/docs/`)
- ✅ API tests (21 test lulus)

### Phase 3–7
- ➖ Frontend setup / dashboard / module migration (Vue) — fase berikutnya
- 🟡 Testing — backend tercakup; E2E/coverage report belum
- ⬜ Deployment (Nginx/Docker/CI-CD/monitoring)

---

## 2. API Development (`03-API-DEVELOPMENT.md`)

- ✅ DRF + SimpleJWT + drf-spectacular terpasang
- 🟡 `django-filter` & `corsheaders` — **belum** (CORS diperlukan saat frontend Vue)
- ✅ `REST_FRAMEWORK` config (JWT, IsAuthenticated default, pagination, AutoSchema)
- ✅ `SPECTACULAR_SETTINGS`
- ✅ Serializers + nested (jurnal↔detail, tagihan↔detail) + validasi balance
- ✅ ViewSets + `@action`
- ✅ URLs via DefaultRouter
- ✅ Authentication (JWT) + permission berbasis role
- ✅ Testing API

> Catatan: serializer kita beradaptasi ke skema akuntansi double-entry (bukan contoh
> `Siswa` sederhana di docs). Auth pakai Groups, bukan field role tunggal.

---

## 3. Backend Refactoring (`01-BACKEND-REFACTORING.md`)

### Phase 1 — Security Hardening
- ✅ `.env` + tanpa secret hardcode (kredensial ETL & Django via env)
- ✅ Validasi password (Django default validators aktif)
- 🟡 Security settings produksi (CSRF/session aktif; HSTS/secure cookie/SSL redirect belum diset)
- ✅ Anti SQL injection — ORM + query parameter (`%s`) di raw query laporan
- ⬜ Rate limiting / brute-force protection

### Phase 2 — Code Architecture
- ✅ Class-Based Views (DRF ViewSets/APIView)
- ✅ Service layer (auto-posting, closing, reversal)
- ✅ Mixins/permission terstruktur (`accounts/permissions.py`)
- ✅ Pemisahan domain (apps: accounts/accounting/operations)

### Phase 3 — Database Optimization
- ✅ Index pada FK & kolom status (`02_governance.sql`)
- ✅ `select_related`/`prefetch_related` di queryset API
- ✅ Constraint DB (CHECK balance/SoD, unique anggaran, FK)

---

## 4. OWASP Top 10 2025 (`01-BACKEND-REFACTORING-OWASP.md`)

- ✅ **A01 Broken Access Control** — RBAC Groups + DRF permission per-action; SoD
  (approver ≠ maker) di kode **dan** CHECK DB; audit trail perubahan
- 🟡 **A02 Security Misconfiguration** — `DEBUG`/secret via env ✅; security headers
  produksi (HSTS, secure cookies, `SECURE_SSL_REDIRECT`) **belum**
- ✅ **A03 Supply Chain** — dependency terkunci di `uv.lock`
- ✅ **A04 Cryptographic Failures** — tidak ada secret di repo; password ke `.env`;
  password Django di-hash (PBKDF2 default)
- ✅ **A05 Injection** — ORM + parameterized query; tidak ada string SQL ter-interpolasi
- ✅ **A06 Insecure Design** — maker-checker (DRAFT→PENDING→POSTED), hard-block anggaran
  (service + trigger row-lock), immutability jurnal POSTED, koreksi via reversing entry
- 🟡 **A07 Authentication Failures** — JWT + validator password ✅; lockout/rate-limit
  & rotasi token lanjutan **belum**
- ✅ **A08 Data Integrity Failures** — jurnal POSTED immutable (trigger), audit log
  JSONB old/new, soft-delete (haram hard-delete)
- ✅ **A09 Logging & Alerting** — `audit_log` trigger menangkap user (`app.current_user_id`);
  alerting eksternal (Sentry) **belum** (opsional)
- ✅ **A10 Exceptional Conditions** — error trigger DB (pagu/periode/immutability)
  dipetakan ke respons 400 yang rapi, bukan 500 mentah

---

## 5. Yang masih terbuka (rencana berikutnya)

- ⬜ **Frontend Vue 3** (SPA + Pinia + JWT) — `02-FRONTEND-MIGRATION.md`
- 🟡 **CORS + django-filter** (diperlukan/berguna saat integrasi frontend)
- 🟡 **Security headers produksi** + rate limiting (A02/A07)
- ⬜ **Bersihkan project Django lama di root** (`penelitian_tk` + apps lama) setelah
  logika selesai diport
- ⬜ **Deployment**: Docker, Nginx, CI/CD, monitoring (Phase 7)

---

## Ringkasan endpoint terimplementasi

Auth: `auth/token`, `auth/token/refresh` · Docs: `schema`, `docs`

Core: `golongan`, `sub-golongan`, `coa`, `periode` (+`tutup`), `anggaran`,
`jurnal` (+`submit`/`approve`/`void`), `audit-log`

Operasional: `jenjang`, `kelompok`, `siswa`, `kehadiran-siswa`, `absen-pegawai`,
`menu-katering`, `armada-jemputan`, `pendaftaran-jemputan`, `tagihan` (+`bayar`)

Kepegawaian/aset: `pegawai`, `pinjaman` (+`cairkan`), `gaji` (+`posting`),
`aset` (+`susutkan`)

Laporan/dashboard: `laporan/neraca-saldo`, `laporan/laba-rugi`,
`laporan/posisi-keuangan`, `laporan/realisasi-anggaran`,
`laporan/buku-besar/{kode}`, `dashboard/ringkasan`, `dashboard/prediksi-kas`

**Status uji:** 21/21 test lulus · OpenAPI schema valid tanpa warning.
