#!/bin/sh
set -eu

BSF_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$BSF_ROOT"
if [ ! -f .env.vps ]; then
    echo 'Create the private configuration first: python3 scripts/init_vps_env.py <api-hostname>' >&2
    exit 1
fi

compose() {
    docker compose --env-file .env.vps -f docker-compose.production.yml "$@"
}

compose up -d --wait --wait-timeout 120 db
umask 077
backup_dir="$BSF_ROOT/backups"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
backup_file="$backup_dir/db-$(date -u +%Y%m%dT%H%M%SZ).dump"
if ! compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$backup_file"; then
    rm -f "$backup_file"
    echo 'Database backup failed; deployment stopped.' >&2
    exit 1
fi
compose build backend
compose run --rm backend python manage.py migrate --noinput
compose run --rm backend python manage.py collectstatic --noinput
compose up -d backend caddy
compose ps
