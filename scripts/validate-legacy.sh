#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

MONTH="${1:-}"
ARGS=(--report)
if [[ -n "$MONTH" ]]; then
  ARGS+=(--month "$MONTH")
fi
if [[ -n "${TOLERANSI:-}" ]]; then
  ARGS+=(--toleransi "$TOLERANSI")
fi

python manage.py validate_legacy "${ARGS[@]}"
