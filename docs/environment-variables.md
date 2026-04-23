# Environment Variables

This project uses environment variables for secrets, service credentials, and business-rule configuration.

---

## 1) Setup

Create your local file:

```bash
cp sample.env .env
```

Never commit `.env` to source control.

---

## 2) Required variables

These values are required for normal runtime:

### Django and core
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `SITE_ID`

### Database
- `DATABASE_URL`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### Media and email
- `CLOUDINARY_URL`
- `EMAIL_BACKEND`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`

### Auth and payments
- `GOOGLE_CLIENT_ID`
- `GOOGLE_SECRET_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

### Security
- `CSRF_TRUSTED_ORIGINS`

---

## 3) Optional variables with defaults

If omitted, these defaults are used in settings:

| Variable | Default |
|---|---|
| `TIME_ZONE` | `Asia/Kolkata` |
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `True` |
| `IMAGE_MAX_SIZE_MB` | `5` |
| `MAX_ADDRESSES_PER_USER` | `5` |
| `MAX_QUANTITY_PURCHASE_PER_ITEM` | `5` |
| `SHIPPING_CHARGE` | `100` |
| `WALLET_TOPUP_MIN` | `5000` |
| `WALLET_TOPUP_MAX` | `75000` |
| `REFERRAL_REWARD_AMOUNT` | `1000` |
| `RETURN_WINDOW_DAYS` | `7` |
| `FAILED_ORDER_EXPIRY_SECONDS` | `18000` |
| `GST_RATE` | `18` |
| `COD_MIN_ORDER_AMOUNT` | `50000` |
| `STORE_STATE` | `KERALA` |
| `STORE_STATE_CODE` | `32` |
| `DEFAULT_WATCH_HSN` | `9102` |
| `PHONENUMBER_DEFAULT_REGION` | `IN` |

---

## 4) Docker-specific note

When running via Docker Compose:

- `.env` is still the source of credentials.
- `DATABASE_URL` is overridden for containers to use host `db`.
- This is expected and prevents connection failures inside containers.

---

## 5) Security guidance

- Use strong random `SECRET_KEY` values.
- Keep `DEBUG=False` outside local development.
- Use production domains in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Store live payment keys only in secure deployment environments.
