#!/bin/sh
# Backup harian database produksi: dump -> cek isi -> enkripsi age -> unggah ke Cloudflare R2.
# Dipasang manual di VPS (bukan lewat poller deploy) dan dijalankan cron sebagai root.
# Konfigurasi rahasia ada di /etc/beesmartfinance/backup.env (root, 0600), tidak di repo:
#   BACKUP_AGE_RECIPIENT  kunci publik age (age1...); kunci privat hanya di Mac pengguna
#   RCLONE_REMOTE         mis. r2:beesmartfinance-backup
#   RCLONE_CONFIG_R2_*    kredensial R2 (TYPE=s3, PROVIDER=Cloudflare, ACCESS_KEY_ID,
#                         SECRET_ACCESS_KEY, ENDPOINT); token hanya untuk bucket backup
#   LOCAL_KEEP_DAYS       umur dump harian lokal yang disimpan (default 14)
set -eu

BSF_ROOT=${BSF_ROOT:-/opt/beesmartfinance}
CONFIG=${BACKUP_CONFIG:-/etc/beesmartfinance/backup.env}
MIN_TABLE_DATA=${MIN_TABLE_DATA:-50}

set -a
. "$CONFIG"
set +a
: "${BACKUP_AGE_RECIPIENT:?}" "${RCLONE_REMOTE:?}"
LOCAL_KEEP_DAYS=${LOCAL_KEEP_DAYS:-14}

cd "$BSF_ROOT"
compose() {
    docker compose --env-file .env.vps -f docker-compose.production.yml "$@"
}
fail() {
    rm -f "${dump:-}.age"
    echo "$(date -u +%FT%TZ) GAGAL: $*" >&2
    exit 1
}

umask 077
dir="$BSF_ROOT/backups/daily"
mkdir -p "$dir"
ts=$(date -u +%Y%m%dT%H%M%SZ)
dump="$dir/db-$ts-daily.dump"

compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U beesmartfinance -d db_lebah_madu' > "$dump" \
    || { rm -f "$dump"; fail "pg_dump"; }
tables=$(compose exec -T db pg_restore --list < "$dump" | grep -c "TABLE DATA" || true)
[ "$tables" -ge "$MIN_TABLE_DATA" ] || fail "dump hanya memuat $tables TABLE DATA (minimal $MIN_TABLE_DATA)"

age -r "$BACKUP_AGE_RECIPIENT" -o "$dump.age" "$dump" || fail "enkripsi age"
size=$(wc -c < "$dump.age" | tr -d ' ')
rclone copyto "$dump.age" "$RCLONE_REMOTE/db/db-$ts.dump.age" --s3-no-check-bucket || fail "unggah R2"
remote_size=$(rclone size --json "$RCLONE_REMOTE/db/db-$ts.dump.age" | sed -n 's/.*"bytes":\([0-9]*\).*/\1/p')
[ "$remote_size" = "$size" ] || fail "ukuran di R2 ($remote_size) beda dengan lokal ($size)"
rm -f "$dump.age"

# Hanya dump harian di folder daily yang dihapus; dump deploy dan backup bernama tidak disentuh.
find "$dir" -name 'db-*-daily.dump' -mtime +"$LOCAL_KEEP_DAYS" -delete
echo "$ts" > "$dir/last_success"
echo "$(date -u +%FT%TZ) OK db-$ts.dump.age $size byte, $tables TABLE DATA"
