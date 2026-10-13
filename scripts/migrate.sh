#!/usr/bin/env bash
# Jalankan migrate — aman dari root repo ATAU folder backend/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
exec python manage.py migrate "$@"
