#!/bin/sh
set -e

FLAG=/app/.migrated

if [ ! -f "$FLAG" ]; then
    echo "⏳ Running migrations..."
    python manage.py migrate --noinput
    touch "$FLAG"
    echo "✅ Migrations complete."
else
    echo "⏩ Migrations already applied, skipping."
fi

exec "$@"