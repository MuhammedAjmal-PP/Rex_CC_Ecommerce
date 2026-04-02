# ─────────────────────────────────────────────
# Stage 1: Build stage
# ─────────────────────────────────────────────
# WHY python:3.13-slim? It's a small version of Python that has just enough
# to run Django. The "slim" part means fewer unnecessary tools = smaller image.
FROM python:3.13-slim AS builder

# WHY set these? They prevent Python from:
#   - PYTHONDONTWRITEBYTECODE=1 → creating .pyc cache files (not needed in Docker)
#   - PYTHONUNBUFFERED=1 → buffering output (so you see logs immediately)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# WHY a work directory? It's like doing `cd /app` — all future commands
# run inside this folder. Keeps things organized.
WORKDIR /app

# Install system dependencies needed for:
#   - gcc, libpq-dev → building psycopg2 (PostgreSQL driver for Python)
#   - libpango1.0-dev, libcairo2, etc. → WeasyPrint (PDF generation)
#   - libgdk-pixbuf2.0-0, libffi-dev → WeasyPrint image handling
# WHY in one RUN command? Each RUN creates a "layer" in Docker. Fewer layers = smaller image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    # WeasyPrint system dependencies
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    libharfbuzz0b \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (before the rest of the code).
# WHY? Docker caches each step. If requirements.txt hasn't changed,
# Docker won't re-install packages — saves LOTS of time on rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now install Gunicorn (the production server).
# WHY not in requirements.txt? Because you don't use Gunicorn on Windows during
# development — it only runs on Linux/Mac. Docker runs Linux inside.
RUN pip install --no-cache-dir gunicorn

# ─────────────────────────────────────────────
# Stage 2: Production stage
# ─────────────────────────────────────────────
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install only the RUNTIME dependencies (not the build tools like gcc).
# This makes the final image much smaller.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi8 \
    libharfbuzz0b \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy your project code into the container
COPY . .

# Copy and make the entrypoint script executable
# WHY? entrypoint.sh runs `migrate` before gunicorn/worker starts,
# ensuring the database schema is always in sync on every fresh deploy.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Dummy env vars for build time only ──────────────────────────────
# Django imports settings.py at startup, which requires ALL env vars to be set.
# collectstatic doesn't actually USE these values — it just scans for static files.
# The real values from .env.docker override these completely at runtime.
ENV SECRET_KEY=dummy-build-only-not-used-in-production \
    DEBUG=False \
    ALLOWED_HOSTS=localhost \
    DATABASE_URL=postgres://user:pass@localhost:5432/db \
    CLOUDINARY_URL=cloudinary://000000000000000:dummy@dummy \
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend \
    EMAIL_HOST_USER=dummy@example.com \
    EMAIL_HOST_PASSWORD=dummy \
    GOOGLE_CLIENT_ID=dummy.apps.googleusercontent.com \
    GOOGLE_SECRET_KEY=dummy \
    CSRF_TRUSTED_ORIGINS=http://localhost \
    RAZORPAY_KEY_ID=dummy \
    RAZORPAY_KEY_SECRET=dummy \
    SITE_ID=1

# Collect static files into STATIC_ROOT (staticfiles/ folder)
# WHY --noinput? So it doesn't ask "Are you sure?" during build
RUN python manage.py collectstatic --noinput

# Expose port 8000 — this is where Gunicorn will listen
# WHY 8000? It's the Django convention. Nginx will forward requests here.
EXPOSE 8000

# ENTRYPOINT runs first, always. It executes migrate then hands off to CMD.
# The worker container overrides CMD via docker-compose (python manage.py db_worker),
# but both still run migrate through this entrypoint first.
ENTRYPOINT ["/entrypoint.sh"]

# The command to start Gunicorn
# --bind 0.0.0.0:8000 → listen on all network interfaces, port 8000
# --workers 3 → handle 3 requests simultaneously (good for a t2.micro server)
# --timeout 120 → wait up to 120s for slow requests (PDF generation can be slow)
# rexcc_project.wsgi:application → tells Gunicorn where your Django app is
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "rexcc_project.wsgi:application"]