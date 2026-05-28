# Types

- `openapi.d.ts` — **canonical**, di-generate dari OpenAPI backend
  (`/api/schema` → `backend/schema.yml`). Jangan diedit tangan.
- `api.ts` — alias tipe domain yang dipakai oleh kode FE (mis. `Siswa`,
  `Tagihan`, `Jurnal`). Saat ini ditulis tangan dan dibiarkan agar
  pekerjaan refactor bisa bertahap; idealnya ke depan tiap entitas
  re-export dari `openapi.d.ts` agar 100% sinkron dgn backend.

## Cara regenerate

1. Pastikan backend menyediakan schema terbaru:
   ```bash
   cd backend
   uv run python manage.py spectacular --file schema.yml --validate
   ```
2. Generate ulang tipe FE:
   ```bash
   cd frontend
   npm run gen:types
   ```
   Output: `frontend/src/types/openapi.d.ts`.

## Contoh pemakaian (incremental migration)

```ts
import type { components } from "@/types/openapi"
type Siswa = components["schemas"]["Siswa"]
```

`components["schemas"]` berisi seluruh DTO backend (Siswa, Tagihan, Jurnal,
TrJurnalDetail, dst). Path/parameters tersedia juga via `components["paths"]`.
