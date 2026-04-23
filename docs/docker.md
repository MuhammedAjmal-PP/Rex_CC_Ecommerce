# Docker Guide

Use this guide to run Rex CC locally with Docker Compose.

---

## 1) What runs in Docker

The Compose stack contains three services:

| Service | Purpose | Port |
|---|---|---|
| `web` | Django application server | `8000` |
| `worker` | Background task worker (`python manage.py db_worker`) | — |
| `db` | PostgreSQL database | `5433 -> 5432` |

The project directory is bind-mounted into `web` and `worker` for live code updates.

---

## 2) Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- A local `.env` file based on `sample.env`

---

## 3) First-time setup

```bash
cp sample.env .env
docker compose up --build
```

Open the app at:

- `http://localhost:8000`

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## 4) Common commands

```bash
# Start services
docker compose up --build

# Start in background
docker compose up --build -d

# Stop services
docker compose down

# Stop and remove volumes (deletes DB data)
docker compose down -v

# View logs
docker compose logs -f

# Run Django commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell

# Open container shell
docker compose exec web sh
```

---

## 5) Environment behavior

- Compose reads `.env` automatically.
- `web` and `worker` override `DATABASE_URL` to use host `db`.
- This avoids the common container networking issue where `localhost` points to the container itself.

---

## 6) Startup behavior

Both `web` and `worker` use `entrypoint.sh`, which retries migrations until the database is ready, then starts the target process.

This ensures schema readiness during fresh setups and restarts.

---

## 7) Troubleshooting quick tips

| Problem | Recommended check |
|---|---|
| Web service exits quickly | `docker compose logs -f web` |
| DB not reachable | `docker compose logs -f db` |
| Port conflict on 8000 | stop local process or change compose port mapping |
| No code hot-reload | verify bind mount exists in `docker-compose.yml` |
| Dependency mismatch | rebuild with `docker compose up --build` |
