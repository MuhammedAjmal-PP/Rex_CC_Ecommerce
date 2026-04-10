# ─────────────────────────────────────────────
# Development Dockerfile
# Uses Django's built-in dev server — NOT for production use
# ─────────────────────────────────────────────
FROM python:3.13-slim

# Prevent Python from writing .pyc cache files and buffer logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies:
#   - gcc, libpq-dev  → build psycopg2 (PostgreSQL driver)
#   - libpango, libcairo, etc. → WeasyPrint (PDF generation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    libharfbuzz0b \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first so Docker can cache this layer.
# If requirements.txt hasn't changed, pip install is skipped on rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project code
COPY . .

# Copy and make the entrypoint script executable.
# entrypoint.sh runs `migrate` before the server starts.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Django dev server listens on port 8000
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

# Start Django's built-in development server
# 0.0.0.0 makes it accessible from outside the container
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]