# BeeSmart Finance — SIA TK Lebah Madu (skripsi)

Django 5.2 REST + PostgreSQL 16 (`backend/`: accounts, accounting, operations).
Vue 3 + PrimeVue 4 + Vite + Pinia (`frontend/src/`: core, features, shared, stores).

## Run
- Backend: `source .venv/bin/activate && cd backend && python manage.py runserver 8000` (API docs /api/docs/)
- Frontend: `cd frontend && npm run dev` (http://localhost:5173)
- Full stack: `docker compose up --build` (FE :8080, BE :8000; auto migrate + seed_demo)
- Demo data: `python manage.py seed_demo`. Four roles: admin.tu, keuangan, kepsek, guru.kegiatan.

## Checks
- Backend tests: `cd backend && python manage.py test`
- Frontend: `npm run test` (Vitest), `npm run build` (vue-tsc typecheck + build)
- API types: `npm run gen:types` after changing `backend/schema.yml`

## Deploy boundary (production, do not trigger)
- Any push to `main` is auto-deployed by `scripts/poll_deploy_vps.sh`: VPS backend
  with production migrations, plus Cloudflare Worker frontend.
- `npm run deploy` in `frontend/` deploys straight to production Cloudflare.
- Never merge to `main`, run deploy scripts, or `npm run deploy` without an explicit
  release decision plus data, migration, and backup checks.
- Mutations for experiments go to a separate UAT/fixture DB, never demo or production data.

## Domain rules
- Segregation of duties: keuangan cannot pay invoices; kepsek approves PENDING journals.

## Current work
Latest status lives in the newest `docs/reviews/*-handoff.md`; read it before tier 2–3 work.
Design system: `docs/design-system.md`. Code style: `docs/07-CODE-STYLE.md`.
