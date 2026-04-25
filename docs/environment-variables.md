# ⚙️ Environment Variables

Copy `sample.env` to `.env` and fill in your credentials. The sample file includes inline comments for every variable.

> [!WARNING]
> The `.env` file contains secrets. **Never commit it to version control.**

---

## 🔐 Core Django

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `SECRET_KEY` | ✅ | — | Django cryptographic key. |
| `DEBUG` | ✅ | `False` | `True` for local dev. `False` activates HSTS, SSL, and secure cookies. |
| `ALLOWED_HOSTS` | ✅ | — | Comma-separated trusted hostnames. |
| `SITE_ID` | — | `1` | Django sites framework ID. |
| `CSRF_TRUSTED_ORIGINS` | ✅ | — | Comma-separated trusted origins for CSRF. |

## 🗄️ Database

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `DATABASE_URL` | ✅ | — | `postgres://user:pass@host:port/db`. Docker overrides the host automatically. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | ✅ | — | Used by Docker Compose to provision PostgreSQL. |

## ☁️ Cloudinary

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `CLOUDINARY_URL` | ✅ | — | `cloudinary://api_key:secret@cloud_name` |

## 📧 Email (SMTP)

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `EMAIL_BACKEND` | ✅ | — | `django.core.mail.backends.smtp.EmailBackend` for real delivery, or `...console.EmailBackend` for dev. |
| `EMAIL_HOST` | — | `smtp.gmail.com` | SMTP server hostname. |
| `EMAIL_PORT` | — | `587` | SMTP port. |
| `EMAIL_USE_TLS` | — | `True` | Enable TLS. |
| `EMAIL_HOST_USER` | ✅ | — | Sender email address. |
| `EMAIL_HOST_PASSWORD` | ✅ | — | Google **App Password** (not your account password). |

## 🔑 Google OAuth

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `GOOGLE_CLIENT_ID` | ✅ | — | OAuth client ID from Google Cloud Console. |
| `GOOGLE_SECRET_KEY` | ✅ | — | OAuth client secret. |

## 💳 Razorpay

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `RAZORPAY_KEY_ID` | ✅ | — | Merchant key ID (`rzp_test_...` or live). |
| `RAZORPAY_KEY_SECRET` | ✅ | — | Merchant key secret. |

---

## 🎛️ Business Rules (Optional)

All variables below have sensible defaults in `settings.py`. Add them to `.env` only to override.

| Variable | Default | Purpose |
|:---|:---|:---|
| `MAX_ADDRESSES_PER_USER` | `5` | Maximum saved addresses per user. |
| `MAX_QUANTITY_PURCHASE_PER_ITEM` | `5` | Anti-hoarding limit per cart item. |
| `SHIPPING_CHARGE` | `100` | Flat shipping fee (₹) per order item. |
| `GST_RATE` | `18` | GST percentage applied at checkout. |
| `COD_MIN_ORDER_AMOUNT` | `50000` | Minimum order amount (₹) for Cash on Delivery. |
| `WALLET_TOPUP_MIN` | `5000` | Minimum wallet deposit (₹). |
| `WALLET_TOPUP_MAX` | `75000` | Maximum wallet deposit (₹). |
| `REFERRAL_REWARD_AMOUNT` | `1000` | Reward (₹) credited to both users on referral. |
| `RETURN_WINDOW_DAYS` | `7` | Days after delivery to initiate a return. |
| `FAILED_ORDER_EXPIRY_SECONDS` | `18000` | Auto-cancel timer for stuck Razorpay orders (5h). |
| `IMAGE_MAX_SIZE_MB` | `5` | Max upload size for all image fields. |
| `STORE_STATE` | `KERALA` | Store location for GST invoicing. |
| `STORE_STATE_CODE` | `32` | GST state code (32 = Kerala). |
| `DEFAULT_WATCH_HSN` | `9102` | HSN code for wristwatches. |
| `PHONENUMBER_DEFAULT_REGION` | `IN` | ISO 3166-1 alpha-2 code for phone validation. |

> [!TIP]
> **Production:** Set `DEBUG=False`, rotate `rzp_test_` keys to live, and use a strong `SECRET_KEY`.
