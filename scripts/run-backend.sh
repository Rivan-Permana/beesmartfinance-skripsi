#!/usr/bin/env bash
# Jalankan Django dev server — aman dari root repo ATAU folder backend/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
exec python manage.py runserver "${1:-8000}"
