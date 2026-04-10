# Environment Variables

Copy `sample.env` to `.env` and fill in your values. The `.env` file is git-ignored and must **never** be committed.

```bash
cp sample.env .env
```

> Variables marked ✅ are **required** — the app will not start without them.
> All others are optional and fall back to the listed default if omitted.

---

## Django Core

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SECRET_KEY` | ✅ | — | Django secret key. Generate: `python -c "from django.utils.crypto import get_random_string; print(get_random_string(50))"` |
| `DEBUG` | ✅ | `False` | `True` for dev (disables HTTPS/HSTS). `False` activates all production security headers. |
| `ALLOWED_HOSTS` | ✅ | — | Comma-separated hostnames. Add tunnel URLs for ngrok / Cloudflare. |
| `SITE_ID` | ✅ | `1` | `django.contrib.sites` framework ID — must match the DB row. |
| `TIME_ZONE` | — | `Asia/Kolkata` | Django timezone string. |

---

## Database

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `DATABASE_URL` | ✅ | — | `postgres://user:pass@host:port/db`. Use `localhost` for local dev — Docker overrides this to `db` automatically. |
| `DB_NAME` | ✅ | — | PostgreSQL database name. Read by `docker-compose.yml` to create the container. |
| `DB_USER` | ✅ | — | PostgreSQL username. Read by `docker-compose.yml`. |
| `DB_PASSWORD` | ✅ | — | PostgreSQL password. Read by `docker-compose.yml`. |

---

## Media Storage (Cloudinary)

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `CLOUDINARY_URL` | ✅ | — | `cloudinary://api_key:api_secret@cloud_name`. Get from [Cloudinary Console](https://cloudinary.com/console). |
| `IMAGE_MAX_SIZE_MB` | — | `5` | Maximum image upload size in MB (applies to all image fields). |

---

## Email (SMTP)

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `EMAIL_BACKEND` | ✅ | — | `django.core.mail.backends.smtp.EmailBackend` for real email, or `console.EmailBackend` to print to terminal during dev. |
| `EMAIL_HOST` | — | `smtp.gmail.com` | SMTP host. |
| `EMAIL_PORT` | — | `587` | SMTP port. |
| `EMAIL_USE_TLS` | — | `True` | Enable TLS for SMTP. |
| `EMAIL_HOST_USER` | ✅ | — | Gmail sender address. |
| `EMAIL_HOST_PASSWORD` | ✅ | — | Gmail **App Password** (not your account password). [How to create one](https://support.google.com/accounts/answer/185833). |

---

## Google OAuth

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GOOGLE_CLIENT_ID` | ✅ | — | Google OAuth 2.0 client ID. Create at [Google Cloud Console](https://console.cloud.google.com/apis/credentials). Authorised redirect: `http://localhost:8000/accounts/google/login/callback/` |
| `GOOGLE_SECRET_KEY` | ✅ | — | Google OAuth 2.0 client secret. |

---

## Payments (Razorpay)

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `RAZORPAY_KEY_ID` | ✅ | — | Razorpay key ID (`rzp_test_...` for test mode). Get from [Razorpay Dashboard](https://dashboard.razorpay.com/app/keys). |
| `RAZORPAY_KEY_SECRET` | ✅ | — | Razorpay key secret. |

---

## Security

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `CSRF_TRUSTED_ORIGINS` | ✅ | — | Comma-separated trusted origins. Include tunnel URLs (ngrok, Cloudflare) during dev. In production, set your exact domain. |

---

## Business Rules

All optional — sensible defaults are applied in `settings.py` if omitted.

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_ADDRESSES_PER_USER` | `5` | Maximum saved addresses per user account. |
| `MAX_QUANTITY_PURCHASE_PER_ITEM` | `5` | Maximum units of a single variant per cart item. |
| `SHIPPING_CHARGE` | `100` | Flat shipping charge per item in the order (₹). |
| `GST_RATE` | `18` | GST percentage applied to all orders. |
| `STORE_STATE` | `KERALA` | Store state name for GST invoicing. |
| `STORE_STATE_CODE` | `32` | GST state code — 32 = Kerala. See [state codes](https://cleartax.in/s/gst-state-codes). |
| `DEFAULT_WATCH_HSN` | `9102` | HSN code for wristwatches (quartz / battery-operated). |
| `WALLET_TOPUP_MIN` | `5000` | Minimum wallet top-up amount (₹). |
| `WALLET_TOPUP_MAX` | `75000` | Maximum wallet top-up amount (₹). |
| `REFERRAL_REWARD_AMOUNT` | `1000` | Wallet credit (₹) paid to both referee and referrer on a successful referral. |
| `RETURN_WINDOW_DAYS` | `7` | Days after delivery within which a return request can be raised. |
| `COD_MIN_ORDER_AMOUNT` | `50000` | Minimum order amount (₹) required for Cash on Delivery. Orders below this must use online payment. |
| `FAILED_ORDER_EXPIRY_SECONDS` | `18000` (5 h) | Seconds before a FAILED Razorpay order is auto-expired by the background worker. Use `120` for fast dev testing. |
| `PHONENUMBER_DEFAULT_REGION` | `IN` | ISO 3166-1 alpha-2 country code for phone number validation. |

---

## How Docker Uses the `.env` File

Docker Compose reads `.env` automatically. Credentials are **never hardcoded** in `docker-compose.yml` — they are injected at runtime via `${VARIABLE}` substitution:

```yaml
# docker-compose.yml (excerpt)
db:
  environment:
    POSTGRES_DB: ${DB_NAME}
    POSTGRES_USER: ${DB_USER}
    POSTGRES_PASSWORD: ${DB_PASSWORD}

web:
  environment:
    # Overrides DATABASE_URL from .env — uses 'db' service name, not 'localhost'
    DATABASE_URL: postgres://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
```

> **Why the override?** Inside Docker, `localhost` refers to the container itself. The `db` service name is how containers discover each other on Docker's internal network. Your `.env` keeps `localhost` for running Django outside Docker — both work without any manual changes.

---

## Production Tips

- When `DEBUG=False`, Django automatically activates:
  - `SECURE_SSL_REDIRECT = True`
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
  - `X_FRAME_OPTIONS = "DENY"`
  - `SECURE_HSTS_SECONDS = 31_536_000` (1 year + subdomains + preload)
  - `SECURE_CONTENT_TYPE_NOSNIFF = True`
- Use a strong, randomly generated `SECRET_KEY` — never reuse dev keys in production.
- Set `ALLOWED_HOSTS` to your exact domain — avoid wildcards in production.
- Switch `rzp_test_...` keys to `rzp_live_...` keys in `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`.
