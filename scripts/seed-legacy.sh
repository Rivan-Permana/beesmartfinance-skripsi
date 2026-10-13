#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [[ "${1:-}" == "--dry-run" ]]; then
  python manage.py seed_legacy --demo-full --dry-run
elif [[ -n "${1:-}" ]]; then
  python manage.py migrate --noinput
  python manage.py seed_legacy --month "$1"
else
  python manage.py migrate --noinput
  python manage.py seed_legacy --demo-full
fi
