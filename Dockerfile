# ─────────────────────────────────────────────
# Development Dockerfile
# ─────────────────────────────────────────────

#base image
FROM python:3.14-slim

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



COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]