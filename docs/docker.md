# Docker Guide

This project ships a **development-only** Docker setup — three containers orchestrated by Docker Compose. No Nginx, no Gunicorn; the Django built-in dev server is used for simplicity and hot-reload support.

> For production deployment, you would add Gunicorn, Nginx/Caddy, and harden the environment variables. This guide covers local Docker development only.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Rex_CC_Ecommerce.git
cd Rex_CC_Ecommerce

# 2. Configure environment
cp sample.env .env
# Edit .env and fill in all required values

# 3. Build and start all containers
docker compose up --build

# 4. Open the app
# http://localhost:8000
```

On first run, `entrypoint.sh` automatically runs `python manage.py migrate` before the server starts — no manual migration step needed.

---

## Service Architecture

```
┌──────────────────────────┐    ┌──────────────────────────┐
│  web                     │    │  worker                  │
│  Django dev server       │    │  db_worker               │
│  0.0.0.0:8000            │    │  Background task runner  │
│  entrypoint: migrate     │    │  entrypoint: migrate     │
└────────────┬─────────────┘    └────────────┬─────────────┘
             │                               │
             └──────────────┬────────────────┘
                            ▼
              ┌─────────────────────────┐
              │  db (postgres:18-alpine) │
              │  :5432 · named volume   │
              └─────────────────────────┘

External Services
  ├── Cloudinary CDN   (product images, avatars, return photos)
  └── Razorpay Gateway (payment processing, HMAC-SHA256 verification)
```

### Container Responsibilities

| Container | Image | Role |
|-----------|-------|------|
| `web` | Custom `python:3.13-slim` | Django dev server (`runserver 0.0.0.0:8000`) |
| `worker` | Custom `python:3.13-slim` | `django-tasks-db` background task processor (`db_worker`) |
| `db` | `postgres:18-alpine` | Persistent relational store with named volume |

---

## How `entrypoint.sh` Works

Both `web` and `worker` share the same `entrypoint.sh`:

```sh
# Retries migrate every 2s until the database is ready
until python manage.py migrate --noinput; do
    sleep 2
done
# Then hands off to the container's CMD
exec "$@"
```

This ensures migrations always run before the app starts — safe for fresh clones and after schema changes.

---

## Common Commands

```bash
# Start containers (attach — see logs in terminal)
docker compose up --build

# Start containers in background
docker compose up --build -d

# Stream logs (all services)
docker compose logs -f

# Stream logs for a specific service
docker compose logs -f web
docker compose logs -f worker

# Stop all containers (data is preserved in named volume)
docker compose down

# Stop and delete all volumes (⚠️ destroys database data)
docker compose down -v

# Rebuild after dependency changes (requirements.txt)
docker compose up --build

# Run a one-off management command inside the web container
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
docker compose exec web python manage.py migrate

# Open a shell inside a container
docker compose exec web sh
docker compose exec db psql -U rexcc_user -d rexcc_db
```

---

## Named Volumes

| Volume | Purpose |
|--------|---------|
| `postgres_data` | PostgreSQL data — persists across container restarts and rebuilds |

The project source is **bind-mounted** (`- .:/app`) so code changes reflect immediately without rebuilding the image. Only `requirements.txt` changes require a rebuild (`docker compose up --build`).

---

## DATABASE_URL — localhost vs Docker

Your `.env` uses `localhost` in `DATABASE_URL` for running Django directly on your machine. Docker Compose **automatically overrides** this to use the `db` service name:

```yaml
# docker-compose.yml
environment:
  DATABASE_URL: postgres://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
```

You never need to edit `.env` to switch between running locally and running in Docker.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `web` container exits immediately | Check `docker compose logs web` — likely a missing env var or bad `DATABASE_URL` |
| `migrate` keeps retrying | The `db` healthcheck hasn't passed yet — wait a few seconds or check `docker compose logs db` |
| Port 8000 already in use | Stop your local Django dev server or change the port mapping in `docker-compose.yml` |
| Code changes not reflected | Ensure the bind-mount `- .:/app` is present in `docker-compose.yml` |
| `psycopg2` errors | Run `docker compose up --build` to reinstall dependencies inside the container |
