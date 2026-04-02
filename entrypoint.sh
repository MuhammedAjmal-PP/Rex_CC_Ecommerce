#!/bin/sh
# entrypoint.sh — runs before gunicorn OR the worker starts
# WHY? On a fresh deploy, the database is empty. Django needs its tables
# (auth, sessions, tasks, etc.) before it can serve any request.
# Running migrate here ensures the schema is always up to date on every start.

set -e  # Exit immediately if any command fails

echo "⏳ Waiting for database to be ready..."
# Simple retry loop — 'python manage.py migrate' will fail cleanly if DB isn't up yet
until python manage.py migrate --noinput 2>&1; do
    echo "⚠️  Database not ready yet, retrying in 2 seconds..."
    sleep 2
done

echo "✅ Migrations complete. Starting process..."

# Run whatever command was passed (gunicorn for web, db_worker for worker)
exec "$@"
