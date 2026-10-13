#!/bin/sh
set -eu
umask 077

app=/opt/beesmartfinance
source_dir="$HOME/.cache/beesmartfinance-source"
state_dir="$HOME/.local/state/beesmartfinance"
cloudflare_env="$HOME/.config/beesmartfinance/cloudflare.env"

mkdir -p "$source_dir" "$state_dir"
exec 9>"$state_dir/lock"
flock -n 9 || exit 0

test -f "$app/.env.vps" || { echo 'Missing VPS configuration' >&2; exit 1; }
test -r "$cloudflare_env" || { echo 'Missing Cloudflare deployment token' >&2; exit 1; }

if ! git -C "$source_dir" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$source_dir" init -q
    git -C "$source_dir" remote add origin https://github.com/Rivan-Permana/beesmartfinance-skripsi.git
fi
git -C "$source_dir" fetch -q --depth=1 origin main
sha=$(git -C "$source_dir" rev-parse FETCH_HEAD)

if [ "$(cat "$state_dir/backend_sha" 2>/dev/null || true)" != "$sha" ]; then
    echo "$(date -u +%FT%TZ) Deploy backend $sha"
    git -C "$source_dir" archive "$sha" \
        .dockerignore backend docker database/schemas \
        database/raw_data/coa.csv database/raw_data/T_AKUN.csv \
        database/raw_data/T_GOLKUN.csv database/raw_data/T_SUBGOL.csv \
        pyproject.toml uv.lock README.md docker-compose.production.yml \
        scripts/deploy_vps.sh | tar -xf - -C "$app"
    sh "$app/scripts/deploy_vps.sh"
    curl --fail --silent --show-error --retry 10 --retry-delay 3 \
        --retry-all-errors -o /dev/null https://srv2054916.hstgr.cloud/api/schema/
    printf '%s\n' "$sha" > "$state_dir/backend_sha"
fi

if [ "$(cat "$state_dir/frontend_sha" 2>/dev/null || true)" != "$sha" ]; then
    echo "$(date -u +%FT%TZ) Deploy frontend $sha"
    git -C "$source_dir" archive "$sha" frontend | tar -xf - -C "$app"
    docker run --rm --user "$(id -u):$(id -g)" \
        --env-file "$cloudflare_env" \
        -e HOME=/tmp -e CI=1 -e VITE_API_BASE_URL=/api/v1 \
        -v "$app/frontend:/app" -w /app node:22-bookworm-slim \
        sh -c 'npm ci --no-audit --no-fund && npm run build && npx wrangler deploy --keep-vars'
    curl --fail --silent --show-error --retry 10 --retry-delay 3 \
        --retry-all-errors -o /dev/null \
        https://beesmartfinance-skripsi.ansinar2003.workers.dev/login
    printf '%s\n' "$sha" > "$state_dir/frontend_sha"
fi
