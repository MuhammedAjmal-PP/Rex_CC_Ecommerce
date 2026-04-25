# 🐳 Docker Environment Guide

A 3-container development stack running Django, a background worker, and PostgreSQL — zero manual configuration required.

> [!WARNING]
> This stack is for **local development only**. It uses `runserver` and lacks production hardening (Nginx, Gunicorn).

---

## 🏗️ Service Architecture

| Service | Image | Responsibility |
|:---|:---|:---|
| **`web`** | `python:3.12-slim` (custom) | Django dev server at `0.0.0.0:8000`. |
| **`worker`** | `python:3.12-slim` (custom) | Background task processor (`db_worker`). |
| **`db`** | `postgres:18-alpine` | Persistent PostgreSQL data store. |

### The `entrypoint.sh` Magic
Both `web` and `worker` share the same entrypoint. It waits for PostgreSQL, runs `migrate`, then starts the service. You never need to run migrations manually.

---

## ⚡ Daily Commands

```bash
# 🚀 Start all services (detached)
docker compose up --build -d

# 🛑 Stop all services
docker compose down

# 🗑️ Destroy everything including database volume
docker compose down -v

# 📜 Real-time logs for a specific service
docker compose logs -f web
docker compose logs -f worker

# 🛠️ Run Django management commands
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
```

---

## 📂 Volumes & Data Persistence

- **`postgres_data`** — Named volume housing all PostgreSQL data. Survives container restarts.
- **Bind Mount (`.:/app`)** — Local source code mounted into the container. Save a file and Django hot-reloads instantly.

> [!TIP]
> Added a new package to `requirements.txt`? Rebuild the image: `docker compose up --build`

---

## 🔌 Database URL

Your `.env` uses `localhost` in `DATABASE_URL` for native development. Docker Compose automatically overrides this to use the internal `db` hostname:

```yaml
# docker-compose.yml (excerpt)
environment:
  DATABASE_URL: postgres://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
```

No manual toggling needed — the same `.env` works for both Docker and native setups.

---

## 🚑 Troubleshooting

| Issue | Solution |
|:---|:---|
| `web` container exits immediately | Run `docker compose logs web` — likely a missing `.env` variable. |
| Migrations retry endlessly | Check `docker compose logs db` — the DB may be failing health checks. |
| Port `8000` already in use | Stop any native Django server, or change the port mapping in `docker-compose.yml`. |

---

## 🖥️ Local Setup Alternative

If you prefer running without Docker:

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (includes WeasyPrint system deps — see Dockerfile for list)
pip install -r requirements.txt

# 3. Configure environment
cp sample.env .env
# Edit .env — ensure DATABASE_URL points to your local PostgreSQL

# 4. Run migrations and start
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> [!NOTE]
> WeasyPrint requires system libraries (`libpango`, `libcairo`, etc.). On Ubuntu/Debian:
> ```bash
> sudo apt install libpango1.0-dev libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-xlib-2.0-0 libffi-dev
> ```

To run the background task worker in a separate terminal:
```bash
python manage.py db_worker
```
