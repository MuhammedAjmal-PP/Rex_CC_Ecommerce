<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 6.0">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/PostgreSQL-17-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 17">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx">
  <img src="https://img.shields.io/badge/Razorpay-Payments-0C2451?style=for-the-badge&logo=razorpay&logoColor=white" alt="Razorpay">
  <img src="https://img.shields.io/badge/Cloudinary-Media-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary">
  <img src="https://img.shields.io/badge/License-MIT-F7B731?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">⌚ REX CC</h1>
<p align="center"><strong>Premium Luxury Watch E-Commerce Platform</strong></p>

<p align="center">
  A production-ready Django e-commerce platform engineered for luxury timepieces.<br>
  Atomic order placement, multi-gateway payments, a full financial ledger, referral rewards,<br>
  and a four-container Docker stack — all in one tightly structured codebase.
</p>

---

## 📖 Table of Contents

- [Feature Overview](#-feature-overview)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Data Models](#-data-models)
- [Local Development Setup](#-local-development-setup)
- [Docker Deployment](#-docker-deployment)
- [Environment Variables](#-environment-variables)
- [Authentication & Security](#-authentication--security)
- [Catalog & Inventory](#-catalog--inventory)
- [Offers & Discounts](#-offers--discounts)
- [Coupon System](#-coupon-system)
- [Cart & Wishlist](#-cart--wishlist)
- [Checkout & Order Placement](#-checkout--order-placement)
- [Order Lifecycle & Status Engine](#-order-lifecycle--status-engine)
- [Payments & Financial Ledger](#-payments--financial-ledger)
- [Wallet System](#-wallet-system)
- [Referral Programme](#-referral-programme)
- [Background Tasks](#-background-tasks)
- [Admin Panel](#-admin-panel)
- [Business Rules & Configuration](#-business-rules--configuration)
- [Roadmap](#-roadmap)

---

## ✨ Feature Overview

| Feature | Status | Summary |
|---------|:------:|---------|
| Email/OTP Authentication | ✅ | Custom `CustomUser` model, email-first, OTP activation |
| Google OAuth | ✅ | `django-allauth` social login |
| Email Blacklisting | ✅ | Changed emails are blacklisted and cannot be reused |
| Referral Programme | ✅ | Auto-generated `REX-XXXXXX` codes, ₹1,000 wallet credit per referral |
| Admin Dashboard | ✅ | Revenue/order charts, best-seller tables, real-time stat cards |
| Catalog Management | ✅ | Brand, Category, Product, Variant with dynamic image formsets |
| Offer-Aware Pricing | ✅ | Best-discount resolution across variant/product/category/brand offers |
| Coupon System | ✅ | Code-based, PERCENTAGE & FIXED, per-user limits, soft-delete |
| Cart | ✅ | Stock-enforced, guest redirect, wishlist sync, offer pricing |
| Wishlist | ✅ | AJAX toggle, offcanvas UI, profile counter |
| Checkout | ✅ | 3-step stepper (Address → Payment → Review) |
| Order Placement | ✅ | COD / Wallet / Razorpay — all atomic |
| Razorpay Two-Phase | ✅ | Cart snapshot, deferred item creation after callback |
| Razorpay Retry | ✅ | Retry FAILED payments from order list |
| Order Cancellation | ✅ | Item-level, instant wallet refund for prepaid orders |
| Return System | ✅ | 7-day window, photo upload (max 3), admin approve/reject |
| Wallet | ✅ | Credit/debit with `select_for_update` row locking |
| Inventory Logging | ✅ | Every stock change recorded with actor, reason, and reference |
| Sales Report | ✅ | Date filters, stat cards, PDF & Excel export |
| Invoice PDF | ✅ | WeasyPrint luxury-themed templates |
| Background Task Worker | ✅ | Auto-expires FAILED Razorpay orders, restores cart from snapshot |
| Docker Deployment | ✅ | Multi-stage Dockerfile, 4-service Compose stack, Nginx |
| Production Security | ✅ | HSTS, SSL redirect, secure cookies — all gated on `DEBUG=False` |

---

## 🏗️ System Architecture

### Docker Compose Stack

```
Browser
  │
  ▼
┌─────────────────────────────────────────────────────┐
│  nginx:alpine   (:80)                               │
│  Reverse proxy + static file server (30d cache)    │
└───────────┬──────────────────────────────────────── ┘
            │ /static/* → shared volume
            │ /*        → proxy_pass
            ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│  web (Django + Gunicorn) │    │  worker (db_worker)      │
│  3 workers · :8000       │    │  Background task runner  │
│  entrypoint: migrate     │    │  entrypoint: migrate     │
└────────────┬─────────────┘    └────────────┬─────────────┘
             │                               │
             └──────────────┬────────────────┘
                            ▼
              ┌─────────────────────────┐
              │  db (postgres:17-alpine) │
              │  :5432 · named volume   │
              └─────────────────────────┘

External Services
  ├── Cloudinary CDN   (all media: product images, avatars, return photos)
  └── Razorpay Gateway (payment processing, HMAC-SHA256 callback verification)
```

### Container Responsibilities

| Container | Image | Role |
|-----------|-------|------|
| `nginx` | `nginx:alpine` | TLS termination, static file serving, reverse proxy to Gunicorn |
| `web` | Custom Python 3.13 | Django + Gunicorn (3 workers, 120 s timeout) |
| `worker` | Custom Python 3.13 | `django-tasks-db` background task processor (`db_worker`) |
| `db` | `postgres:17-alpine` | Persistent relational store with named volume |

### Dockerfile — Multi-Stage Build

| Stage | Purpose |
|-------|---------|
| **builder** | Installs build tools (`gcc`, `libpq-dev`) + all pip packages + Gunicorn |
| **production** | Copies site-packages from builder + runtime libs only (no build tools) |

`collectstatic` runs at build time using dummy env vars so the image is static-ready on first boot. `entrypoint.sh` always runs `migrate` before handing off to Gunicorn or the worker.

---

## 🛠️ Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Web Framework | Django | 6.0 |
| Language | Python | 3.13 |
| WSGI Server | Gunicorn | Installed in Docker only |
| Database | PostgreSQL | 17 (alpine) |
| ORM | Django ORM | With `select_for_update` row locking |
| Auth | django-allauth | 65.x — email + Google OAuth |
| Social Login | Google OAuth 2.0 | Scopes: profile, email |
| Payments | Razorpay SDK | 2.0 — order create + HMAC-SHA256 verify |
| Media Storage | Cloudinary | `django-cloudinary-storage` |
| PDF Generation | WeasyPrint | 68.x — invoices + sales reports |
| Excel Export | openpyxl | 3.x — styled `.xlsx` sales reports |
| Background Tasks | django-tasks-db | DB-backed task queue |
| Email | Gmail SMTP | App-password via `django-environ` |
| Phone Numbers | django-phonenumber-field | IN region, NATIONAL format |
| Environment | django-environ | `.env` + `.env.docker` |
| Frontend | Bootstrap 5.3 + Vanilla CSS | Desktop-only layout |
| Charts | Chart.js | Admin revenue/order charts |
| Image Cropping | Cropper.js | In-browser avatar crop & upload |
| Icons | Material Icons | Google Material Design |
| Containerisation | Docker + Docker Compose | 4-service stack |
| Web Server | Nginx (Alpine) | Static files + reverse proxy |
| Timezone | Asia/Kolkata | Configurable via `TIME_ZONE` env var |
| GST | 18% | Kerala store, HSN 9102 (wristwatches) |

---

## 📁 Project Structure

```
Rex_CC_Ecommerce/
│
├── 📄 Dockerfile                   # Multi-stage build (builder + production)
├── 📄 docker-compose.yml           # 4-service stack: nginx, web, worker, db
├── 📄 entrypoint.sh                # migrate → exec gunicorn or db_worker
├── 📄 requirements.txt             # Python dependencies (pinned)
├── 📄 sample.env                   # ← Template for local .env
├── 📄 sample.env.docker            # ← Template for Docker .env.docker
├── 📄 .env                         # local dev (git-ignored)
├── 📄 .env.docker                  # docker env (git-ignored)
├── 📄 .gitignore
│
├── nginx/
│   └── default.conf                # Nginx reverse proxy + /static/ caching
│
├── rexcc_project/                  # Django project root
│   ├── settings.py                 # All settings loaded from environment
│   ├── urls.py                     # Root URL conf (custom 404 handler)
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                           # Shared infrastructure
│   ├── validators.py               # image_size_validator, image_file_extension_validator, name_validator
│   ├── service/
│   │   └── dashboard.py            # Admin dashboard: stats, chart data, best-sellers
│   ├── templates/core/             # base_admin.html, base_user.html, error pages
│   └── urls/
│       ├── user_urls.py            # Home, PDP, catalog
│       └── admin_urls.py           # Admin panel home, dashboard
│
├── accounts/                       # Authentication & user model
│   ├── models.py                   # CustomUser, PasswordReset, BlacklistedEmail
│   ├── middleware.py               # AuthFlowRedirectMiddleware, BlockUnusedAllauthURLsMiddleware
│   ├── decorators.py               # @superuser_only_redirect
│   ├── signals.py                  # email_confirmed → email-change flow + referral rewards
│   ├── service.py                  # send_admin_password_reset_email()
│   ├── validators.py               # NoWhitespacePasswordValidator
│   ├── forms.py                    # CustomSignupForm
│   └── views/
│       ├── admin_views/            # Admin login, password reset, user management
│       └── user_views/             # (allauth handles most flows)
│
├── catalog/                        # Products, Brands, Categories, Variants
│   ├── models.py                   # Brand, Category, Product, ProductVariant, ProductImage, InventoryLog
│   ├── service.py                  # update_stock(), manage_product_draft_status()
│   ├── utils.py                    # pack_variants(), get_offer_variants(), _best_discount()
│   ├── forms.py                    # Brand/Category/Product/Variant forms with validation
│   └── views/
│       ├── admin/                  # Full CRUD for brands, categories, products, variants
│       └── user/                   # Catalog list, product detail, variant switching
│
├── offers/                         # Offers & discounts engine
│   ├── models.py                   # Offer (PRODUCT/CATEGORY/BRAND, M2M targets, is_valid property)
│   ├── forms.py                    # OfferForm with type-specific M2M validation
│   └── views/admin/                # Offer list, add, edit, delete
│
├── coupons/                        # Coupon system
│   ├── models.py                   # Coupon (PERCENTAGE/FIXED, soft-delete), CouponUsage
│   ├── service.py                  # validate_coupon(), validate_coupon_locked(), apply_coupon_to_order()
│   │                               # revoke_coupon_usage(), revoke_coupon_if_invalid()
│   │                               # get_exhausted_coupon_ids(), recalculate_with_coupon()
│   ├── forms.py                    # CouponForm
│   ├── views/admin/                # Coupon CRUD
│   └── views/user/                 # AJAX apply/remove endpoints
│
├── orders/                         # Full order lifecycle
│   ├── models.py                   # Order, OrderItem, Return, ReturnImage
│   ├── utils.py                    # get_payment_transaction(), can_generate_invoice()
│   │                               # compute_item_totals(), compute_cancel_refund()
│   │                               # compute_return_refund(), can_return_item()
│   ├── tasks.py                    # expire_failed_order() background task
│   ├── forms.py                    # ReturnForm
│   ├── service/
│   │   ├── __init__.py             # Re-exports change_order_status, change_order_item_status
│   │   ├── status.py               # Transition maps, cascade, reverse sync, COD auto-pay
│   │   ├── order_helpers.py        # build_cart_snapshot(), create_items_from_snapshot()
│   │   ├── returns.py              # Return eligibility check
│   │   ├── stock.py                # Stock locking & validation for order placement
│   │   └── sales_report.py         # get_date_range(), get_sales_report()
│   └── views/
│       ├── user/                   # checkout, place_order, razorpay, cancel_order,
│       │                           # return_order, user_orders, order_results
│       └── admin/                  # order list/detail, returns, sales_report
│
├── payments/                       # Universal financial ledger
│   ├── models.py                   # Transaction (GenericFK, 16-char TXN ID)
│   ├── service.py                  # create_transaction(), update_transaction()
│   │                               # initiate_refund(), complete_refund(), fail_transaction()
│   ├── razorpay_service.py         # create_razorpay_order(), verify_razorpay_signature()
│   └── views.py                    # Admin transaction list/detail, refund list/detail + actions
│
└── users/                          # User domain (split into sub-apps)
    ├── cart/
    │   ├── models.py               # Cart (OneToOne), CartItem
    │   ├── views.py                # view_cart, add_cart, update_cart, get_variant_stock
    │   └── utils.py                # fetch_cart(), compute_cart_summary(), build_cart_summary()
    │                               # summary_to_json()
    ├── wishlist/
    │   ├── models.py               # Wishlist, WishlistItem
    │   └── views.py                # wishlist_view, toggle_wishlist, remove_wishlist_item
    ├── wallet/
    │   ├── models.py               # Wallet (OneToOne), WalletTransaction (balance snapshots)
    │   ├── service.py              # get_or_create_wallet(), can_pay_with_wallet()
    │   │                           # credit_wallet(), debit_wallet()
    │   └── views.py                # User wallet page, transaction detail
    └── user_profile/
        ├── models.py               # Address (UUID PK, soft-delete, auto-default logic)
        ├── validators.py           # full_name_validator, postal_code_validator
        ├── forms.py                # AddressForm, ProfileEditForm
        └── views/                  # Profile page, avatar upload, address CRUD, email change
```

---

## 🗃️ Data Models

### accounts

| Model | Key Fields |
|-------|-----------|
| `CustomUser` | `email` (unique, USERNAME_FIELD), `referral_code` (auto `REX-XXXXXX`), `referred_by` (self-FK), `avatar` (Cloudinary) |
| `PasswordReset` | `reset_id` (UUID), `created_at` — admin password reset flow (10-min expiry) |
| `BlacklistedEmail` | Emails replaced via email-change flow — prevents reuse by anyone |

### catalog

| Model | Key Fields |
|-------|-----------|
| `Brand` | `name`, `slug` (auto), `logo` (Cloudinary), `is_active` |
| `Category` | `name`, `slug` (auto), `is_active` |
| `Product` | `brand` (FK·PROTECT), `category` (M2M), `is_deleted` (soft), `is_drafted` |
| `ProductVariant` | `sku` (uppercase regex), `dial_color`, `strap_color`, `strap_material`, `case_material`, `movement_type`, `case_size_mm` (15–65 mm), `price`, `discount_rate`, `stock`, `is_deleted`, `is_featured`, `is_drafted` |
| `ProductImage` | `variant` (FK), `is_primary` (DB-level unique constraint per variant) |
| `InventoryLog` | `change` (±), `stock_before`, `stock_after`, `reason`, `actor` (FK), `reference_object` (GenericFK), DB-validates `stock_after == stock_before + change` |

### orders

| Model | Key Fields |
|-------|-----------|
| `Order` | `order_number` (auto `ORD-XXXXXXXXXX`), `billing_address` & `shipping_address` (JSONField snapshots), `sub_total`, `tax`, `discount`, `shipping_fee`, `grand_total`, `coupon` (FK), `coupon_discount`, `coupon_revoke`, `cart_snapshot` (JSONField for Razorpay two-phase), `status`, `status_updated_at` |
| `OrderItem` | `order` (FK), `product_variant` (FK·SET_NULL), `quantity`, `price`, `original_price` (MRP at order time), `status`, `status_updated_at` |
| `Return` | `return_number` (auto `RE-XXXXXX`), `order_item` (OneToOne), `status`, `reason_code`, `comment`, `admin_note` |
| `ReturnImage` | `return_request` (FK), `image` (Cloudinary `order_return/`) — up to 3 per return |

### payments

| Model | Key Fields |
|-------|-----------|
| `Transaction` | `transaction_id` (auto `TXN` + 13 hex), `user` (FK), `transaction_type`, `payment_method`, `amount`, `status`, `content_object` (GenericFK), `gateway_order_id`, `gateway_payment_id`, `gateway_signature`, `note` |

### users

| Model | Key Fields |
|-------|-----------|
| `Address` | `id` (UUID PK), `user` (FK), `full_name`, `phone_number`, `address_line_1/2`, `city`, `state`, `postal_code`, `label`, `is_default`, `is_active` (soft-delete) |
| `Cart` | `user` (OneToOne) |
| `CartItem` | `cart` + `product_variant` (unique together), `quantity` |
| `Wallet` | `user` (OneToOne), `balance`, `is_active` |
| `WalletTransaction` | `transaction` (OneToOne → payments.Transaction), `wallet` (FK), `label` (CREDIT/DEBIT), `balance_before`, `balance_after` |

### offers / coupons

| Model | Key Fields |
|-------|-----------|
| `Offer` | `offer_type` (PRODUCT/CATEGORY/BRAND), `discount_type` (PERCENTAGE), `discount_value`, `start_date`, `end_date`, `is_active`, M2M to `products`, `categories`, `brands`. `is_valid` property. |
| `Coupon` | `code` (auto-uppercased, min 3), `discount_type` (PERCENTAGE/FIXED), `discount_value`, `min_order_amount`, `max_discount_amount`, `usage_limit`, `per_user_limit`, `used_count`, `is_deleted` (soft). `calculate_discount()` method. |
| `CouponUsage` | `coupon` (FK), `user` (FK), `order` (OneToOne), `used_at` |

---

## 🚀 Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (running locally)
- A [Cloudinary](https://cloudinary.com) account
- A [Razorpay](https://razorpay.com) account (test mode is fine)
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Rex_CC_Ecommerce.git
cd Rex_CC_Ecommerce

# 2. Create & activate virtualenv
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp sample.env .env
# Open .env and fill in all required values (see Environment Variables below)

# 5. Apply migrations
python manage.py migrate

# 6. Create admin superuser
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

Access the app at **http://127.0.0.1:8000**
Admin panel at **http://127.0.0.1:8000/adminpanel/**

> **Background tasks** (e.g. auto-expiring failed Razorpay orders) need the worker running in a separate terminal:
> ```bash
> python manage.py db_worker
> ```

---

## 🐳 Docker Deployment

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Rex_CC_Ecommerce.git
cd Rex_CC_Ecommerce

# 2. Configure Docker environment
cp sample.env.docker .env.docker
# Open .env.docker and fill in all required values

# 3. Build and start all four containers
docker compose up --build -d

# 4. Open the application
# http://localhost
```

### Container Management

```bash
# Stream logs (all services)
docker compose logs -f

# Stream logs for a specific service
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f nginx

# Stop all containers (data is preserved)
docker compose down

# Stop and delete all volumes (⚠️ deletes database data)
docker compose down -v

# Rebuild after code changes
docker compose up --build -d

# Run a one-off management command inside the web container
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
```

### How It Works

```
docker compose up
  │
  ├── db starts → healthcheck (pg_isready) passes
  │
  ├── web starts
  │   └── entrypoint.sh: python manage.py migrate --noinput (retries every 2s)
  │       └── gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 ...
  │
  ├── worker starts
  │   └── entrypoint.sh: python manage.py migrate --noinput
  │       └── python manage.py db_worker
  │
  └── nginx starts
      ├── /static/*  → /app/staticfiles/ (shared volume, 30-day cache)
      └── /*         → proxy_pass http://web:8000
```

Static files are collected during the Docker build (`RUN python manage.py collectstatic --noinput`) into the `staticfiles/` volume, which Nginx serves directly without touching Django.

---

## 🔧 Environment Variables

Copy `sample.env` → `.env` (local) or `sample.env.docker` → `.env.docker` (Docker).

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SECRET_KEY` | ✅ | — | Django secret key. Generate: `python -c "from django.utils.crypto import get_random_string; print(get_random_string(50))"` |
| `DEBUG` | ✅ | `False` | `True` for dev (disables HTTPS/HSTS). `False` activates all production security headers. |
| `ALLOWED_HOSTS` | ✅ | — | Comma-separated hostnames. Add tunnel URLs for ngrok/Cloudflare. |
| `SITE_ID` | ✅ | `1` | django.contrib.sites ID (must match DB). |
| `DATABASE_URL` | ✅ | — | `postgres://user:pass@host:port/db`. Docker: host = `db` (container name). |
| `CLOUDINARY_URL` | ✅ | — | `cloudinary://api_key:api_secret@cloud_name`. |
| `EMAIL_BACKEND` | ✅ | — | Use `smtp.EmailBackend` for real email or `console.EmailBackend` for dev. |
| `EMAIL_HOST` | — | `smtp.gmail.com` | SMTP host. |
| `EMAIL_PORT` | — | `587` | SMTP port. |
| `EMAIL_USE_TLS` | — | `True` | Use TLS for SMTP. |
| `EMAIL_HOST_USER` | ✅ | — | Gmail sender address. |
| `EMAIL_HOST_PASSWORD` | ✅ | — | Gmail **App Password** (not account password). |
| `GOOGLE_CLIENT_ID` | ✅ | — | Google OAuth 2.0 client ID. |
| `GOOGLE_SECRET_KEY` | ✅ | — | Google OAuth 2.0 client secret. |
| `CSRF_TRUSTED_ORIGINS` | ✅ | — | Comma-separated trusted origins. Include `https://yourdomain.com` in prod. |
| `RAZORPAY_KEY_ID` | ✅ | — | Razorpay key ID (`rzp_test_...` or `rzp_live_...`). |
| `RAZORPAY_KEY_SECRET` | ✅ | — | Razorpay key secret. |
| `TIME_ZONE` | — | `Asia/Kolkata` | Django timezone. |
| `FAILED_ORDER_EXPIRY_SECONDS` | — | `18000` (5 h) | Seconds before a FAILED Razorpay order is auto-expired. Use `120` for dev. |
| `WALLET_TOPUP_MIN` | — | `5000` | Minimum wallet top-up amount in ₹. |
| `WALLET_TOPUP_MAX` | — | `75000` | Maximum wallet top-up amount in ₹. |

> **Production tip:** When `DEBUG=False`, Django automatically enables HSTS (1 year + subdomains + preload), `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `X_FRAME_OPTIONS=DENY`.

---

## 🔐 Authentication & Security

### User Model — `accounts.CustomUser`

- Email is the **username field** (`USERNAME_FIELD = "email"`, no username column)
- **Referral code**: auto-generated `REX-XXXXXX` on first save (10 retries for uniqueness)
- **Avatar**: Cloudinary upload with size (5 MB) and extension validation; old image deleted from Cloudinary on replacement
- **Soft-deletion of avatar**: old Cloudinary object deleted when a new image is uploaded

### OTP / Email Verification

- Powered by `django-allauth` with `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`
- 6-digit OTP delivered via Gmail SMTP; expires after 24 hours (`ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1`)
- `ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True` — user is logged in immediately after confirming

### Email Change Flow (`accounts/signals.py`)

When a user changes their email and confirms the new one via the allauth `email_confirmed` signal:
1. New email is promoted to primary via `email_address.set_as_primary()`
2. Old email is written to `BlacklistedEmail` (reason: `EMAIL_CHANGED`)
3. Old `AllauthEmailAddress` row is deleted
4. No one — including the original owner — can register with the blacklisted email again

### Google OAuth

- `django-allauth` provider: Google (scopes: `profile`, `email`)
- Credentials configured via `GOOGLE_CLIENT_ID` and `GOOGLE_SECRET_KEY` env vars

### Custom Middleware

| Middleware | Purpose |
|-----------|---------|
| `AuthFlowRedirectMiddleware` | Redirects active users away from `/accounts/inactive/`; handles password-reset and confirm-email page guards |
| `BlockUnusedAllauthURLsMiddleware` | Raises `Http404` for allauth paths not used by this app (reauthenticate, email management, login code, etc.) |

### Admin Access

- Separate admin login at `/adminpanel/accounts/login/`
- Protected by `@user_passes_test(lambda u: u.is_superuser)`
- `@superuser_only_redirect` decorator bounces superusers away from user-facing login/register views

### Production Security (`DEBUG=False`)

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Nginx sends this
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31_536_000      # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

---

## 📦 Catalog & Inventory

### Offer-Aware Pricing — `catalog/utils.py`

`pack_variants(variants, offer_data=None)` is the single authoritative function that enriches any variant queryset with computed display fields. It attaches to each variant:

```
variant.primary_image       → ProductImage | None
variant.discount_percentage → int  (0–100, best rate wins)
variant.discount_amount     → Decimal
variant.final_price         → Decimal (price − discount_amount)
```

**Best-discount resolution** (`_best_discount`):
```
1. variant.discount_rate  (own field)
2. Active Product offers whose products include this variant's product
3. Active Category offers whose categories overlap this product's categories (M2M-aware)
4. Active Brand offers whose brands include this product's brand
```
All resolved in **pure Python** after a single DB query for active offers — zero N+1 queries.

`get_offer_variants(qs, limit=8)` filters and sorts variants by highest discount for homepage promotions.

### Centralised Stock Service — `catalog/service.py`

```python
update_stock(
    product_variant,   # Which variant
    change,            # +ve restock · -ve order / return
    reason,            # ORDER_PLACED | ORDER_CANCELLED | PAYMENT_FAILED |
                       # RETURNED | ADMIN_ADJUSTMENT | SYSTEM_CORRECTION
    actor,             # CustomUser who triggered it (or None for system)
    reference_object,  # Order / OrderItem / Return (GenericFK)
    note,              # Free-text context
)  → InventoryLog
```

`InventoryLog` is validated at DB level: `stock_after == stock_before + change` is checked in `clean()` and `save()` calls `full_clean()`.

### Auto-Draft Logic

`manage_product_draft_status()` is called whenever a variant is deleted or drafted. If no active, non-deleted variants remain, the parent `Product` is auto-drafted and the admin is shown a warning message.

---

## 🏷️ Offers & Discounts

**Location:** `offers/`

### Offer Model

| Field | Notes |
|-------|-------|
| `offer_type` | `PRODUCT`, `CATEGORY`, or `BRAND` |
| `discount_type` | `PERCENTAGE` (FIXED is commented out for future expansion) |
| `discount_value` | 0–100 |
| `start_date` / `end_date` | Past start dates rejected on create/update |
| `is_active` | Manual toggle |
| `products` / `categories` / `brands` | M2M — only one type populated per offer |

`is_valid` property: `is_active AND start_date <= now <= end_date`

### Form Validation (`offers/forms.py`)

- A **Product offer** must have ≥1 product; categories and brands must be empty
- A **Category offer** must have ≥1 category; products and brands must be empty  
- A **Brand offer** must have ≥1 brand; products and categories must be empty
- `end_date` must be after `start_date`
- `discount_value` must be > 0 and ≤ 100

---

## 🎟️ Coupon System

**Location:** `coupons/`

### Coupon Model

| Field | Notes |
|-------|-------|
| `code` | Unique, auto-uppercased on save, min 3 chars |
| `discount_type` | `PERCENTAGE` or `FIXED` |
| `discount_value` | > 0; percentage capped at 100 |
| `min_order_amount` | Cart subtotal threshold |
| `max_discount_amount` | Cap for percentage coupons (optional) |
| `usage_limit` | Global uses allowed (null = unlimited) |
| `per_user_limit` | Per-user maximum (default: 1) |
| `used_count` | Non-editable counter |
| `is_deleted` | Soft delete — `ActiveCouponManager` excludes deleted rows |

### Service Layer

```python
validate_coupon(code, user, cart_subtotal)
    → (coupon, discount_amount)   # raises InvalidCouponError on failure

validate_coupon_locked(code, user, cart_subtotal)
    → (coupon, discount_amount)   # SELECT ... FOR UPDATE (used at order placement)

apply_coupon_to_order(coupon, user, order)
    # Creates CouponUsage, increments used_count via F()

revoke_coupon_usage(order)
    # Deletes CouponUsage, decrements used_count

revoke_coupon_if_invalid(order)
    # Called after cancel/return — revokes if remaining subtotal < min_order_amount

get_exhausted_coupon_ids(user)
    # Bulk query: set of coupon PKs this user has fully used

recalculate_with_coupon(sub_total, shipping_fee, gst_rate, coupon_discount)
    # Returns adjusted_sub, shipping_fee, tax, grand_total
```

### Checkout Integration

- Applied coupon stored in `request.session["applied_coupon"]`
- AJAX endpoints: `POST /coupon/apply/` and `POST /coupon/remove/`
- Re-validated at order placement inside `transaction.atomic()` with `select_for_update` to prevent race conditions
- `Order.coupon` FK and `Order.coupon_discount` snapshot the applied coupon and amount
- On full-order cancellation: `revoke_coupon_usage()` restores the usage slot
- `compute_refund` functions recalculate coupon share proportionally per item so partial refunds are accurate

---

## 🛒 Cart & Wishlist

### Cart — `users/cart/`

| Function | Location | Description |
|----------|----------|-------------|
| `view_cart()` | `views.py` | Displays items with real-time stock limits |
| `add_cart()` | `views.py` | Adds items; redirects unauthenticated users to login (preserves `next`) |
| `update_cart()` | `views.py` | AJAX quantity update, respects stock |
| `get_variant_stock()` | `views.py` | **Public API** — returns current stock JSON for frontend checks |
| `fetch_cart()` | `utils.py` | Fetches `CartItem` queryset with all relations prefetched |
| `compute_cart_summary()` | `utils.py` | Calculates MRP, discount, sub_total, tax (18% GST), shipping (₹100/item), grand_total |
| `build_cart_summary()` | `utils.py` | Builds items list for cart page and offcanvas |
| `summary_to_json()` | `utils.py` | Converts summary dict → JSON-safe format for AJAX |

**Key behaviours:**
- Max 5 units per cart item (`MAX_QUANTITY_PURCHASE_PER_ITEM = 5`)
- Adding to cart removes the item from wishlist automatically
- All pricing uses `final_price` from `pack_variants()` (offer-aware)

### Wishlist — `users/wishlist/`

- `toggle_wishlist()` — AJAX add/remove with heartbeat animation response
- `remove_wishlist_item()` — explicit remove from offcanvas or wishlist page
- Real-time counter in profile dashboard
- Offcanvas panel visible on any page without navigation

---

## 🚚 Checkout & Order Placement

### 3-Step Checkout Stepper — `orders/views/user/checkout.py`

| Step | Page | Features |
|------|------|---------|
| **1 — Address** | `/checkout/address/` | Select from saved addresses; inline add-address form |
| **2 — Payment** | `/checkout/payment/` | COD · Razorpay · Wallet; coupon apply/remove |
| **3 — Review** | `/checkout/review/` | Full order summary; confirm & place |

### Order Placement — `orders/views/user/place_order.py`

All payment paths share a common atomic prologue:

```
1. @require_POST
2. Validate: address, payment method, cart not empty
3. Lock variants with SELECT FOR UPDATE
4. Validate stock for each item
5. Validate & lock coupon (validate_coupon_locked)
6. Build pricing (sub_total, tax, shipping, grand_total)
7. create_transaction(... status="PENDING")
8. Create Order (address JSON snapshots, totals, coupon FK)
```

Then diverge by payment method:

```
COD / Wallet
  └── Create OrderItems (price, original_price, quantity)
      update_stock(−qty, ORDER_PLACED) for each
      debit_wallet() if Wallet
      clear CartItems
      Order.status = PLACED → redirect success

Razorpay (Phase 1)
  └── build_cart_snapshot() → Order.cart_snapshot = [...]
      create_razorpay_order(amount_paise) → gateway order dict
      Return JSON for frontend to open Razorpay checkout modal

Razorpay (Phase 2 — after callback)
  └── orders/views/user/razorpay.py → razorpay_callback()
      verify_razorpay_signature() HMAC-SHA256
      create_items_from_snapshot() — lock, validate, create, deduct stock
      mark Transaction PAID → Order PLACED
```

#### Razorpay Retry Flow

```
retry_razorpay_payment()
  ├── Validate stock from cart_snapshot
  ├── Reset Order: FAILED → PLACED
  ├── Create new Transaction (PENDING)
  ├── create_razorpay_order() → new gateway order
  └── Return JSON for frontend modal
```

#### Failed Order Expiry (background task)

`expire_failed_order(order_id)` fires after `FAILED_ORDER_EXPIRY_SECONDS`:
1. No-op if order is no longer FAILED
2. Restore cart from `cart_snapshot` (capped at `MAX_QUANTITY_PURCHASE_PER_ITEM`)
3. `revoke_coupon_usage()` if coupon applied
4. Cancel all PENDING/FAILED transactions
5. `change_order_status(FAILED → EXPIRED)`
6. Clear `cart_snapshot`

---

## 🔄 Order Lifecycle & Status Engine

### Status Flows

```
Order
  PLACED → CONFIRMED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
         ↘ CANCELLED
         ↘ FAILED → PLACED (retry) → EXPIRED

OrderItem
  PENDING → CONFIRMED → PACKING → READY → SHIPPED → IN_TRANSIT
                                                    → OUT_FOR_DELIVERY → DELIVERED
                                                                       ↘ FAILED → OUT_FOR_DELIVERY
                                                                                → RTS
                                                                                → CANCELLED (PENDING also)
  DELIVERED → RETURN_REQUESTED → RETURNED
                               → DELIVERED (rejected)
  any pre-ship → CANCELLED
```

### Transition Engine — `orders/service/status.py`

- **`ORDER_ALLOWED_TRANSITIONS`** and **`ADMIN_ORDER_ALLOWED_TRANSITIONS`** — explicit allowed-next-state maps
- **`change_order_status(order, to_status)`**:
  1. Validates transition
  2. Updates `order.status` + `status_updated_at`
  3. **COD Auto-Pay**: if `to_status == "DELIVERED"` and payment is COD + PENDING → marks Transaction PAID
  4. **Cascade**: calls `_cascade_order_to_items()` to walk items through every intermediate status step
- **`change_order_item_status(order_item, to_status)`**:
  1. Validates transition
  2. Updates item status
  3. **Reverse sync**: `_sync_order_status()` derives the correct order-level status from all sibling items
- **Admin restrictions**: admins cannot set `RETURN_REQUESTED` directly — only the user return flow can

### Cancellation — `orders/views/user/cancel_order.py`

- Cancellable statuses: `PENDING`, `CONFIRMED`, `PACKING`, `READY`
- Item-level selection (user picks which items to cancel)
- `update_stock(+qty, ORDER_CANCELLED)` per cancelled item
- **Prepaid instant refund**: Razorpay or Wallet orders → `compute_cancel_refund(item)` → `credit_wallet()` immediately
- COD orders: no refund (nothing was charged)
- `revoke_coupon_if_invalid()` called if coupon no longer valid after cancellation

### Returns — `orders/views/user/return_order.py`

Eligibility (`can_return_item()`):
- `status == "DELIVERED"`
- Within 7 days of delivery (`status_updated_at`)
- No existing return request (REQUESTED / APPROVED / REJECTED prevents a new one)

Return form: reason dropdown (10 codes), comment, up to 3 photo uploads with inline preview.

On admin approval: `change_order_item_status(RETURN_REQUESTED → RETURNED)` + `update_stock(+qty, RETURNED)` + `initiate_refund()` (→ wallet credit via `complete_refund()`).

---

## 💳 Payments & Financial Ledger

### Universal `Transaction` Model

Every money movement — payment, refund, wallet credit, referral reward — creates exactly one `Transaction`:

| Field | Values |
|-------|--------|
| `transaction_id` | Auto `TXN` + 13 uppercase hex chars (retries on collision) |
| `transaction_type` | `ORDER_PAYMENT` · `CANCELLATION_REFUND` · `RETURN_REFUND` · `WALLET_TOPUP` · `REFERRAL_REWARD` |
| `payment_method` | `COD` · `WALLET` · `RAZORPAY` |
| `status` | `PENDING` → `PAID` / `COMPLETED` / `FAILED` / `CANCELLED` |
| `content_object` | GenericFK → Order / OrderItem / Return / CustomUser |
| `gateway_order_id` | Razorpay order ID |
| `gateway_payment_id` | Razorpay payment ID |
| `gateway_signature` | HMAC-SHA256 signature |

### Service Functions — `payments/service.py`

```python
create_transaction(user, txn_type, method, amount, status, content_object, note)
update_transaction(order, amount, note)      # Adjust COD transaction on partial cancel
initiate_refund(order, user, amount, txn_type, content_object, note)  # PENDING refund
complete_refund(transaction)                 # PENDING → COMPLETED + credit_wallet()
fail_transaction(transaction, note)          # PENDING → FAILED  (alias: fail_refund)
```

### Razorpay Service — `payments/razorpay_service.py`

```python
create_razorpay_order(amount_paise, receipt)
    # Calls Razorpay API · payment_capture=1 (auto-capture)

verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    # HMAC-SHA256 via razorpay.Client.utility.verify_payment_signature()
    # Returns True / False (SignatureVerificationError catches failures)
```

### DB Indexes on Transaction

```python
Index(fields=["user", "-created_at"])
Index(fields=["content_type", "object_id"])
Index(fields=["transaction_type", "status"])
```

---

## 💰 Wallet System

**Location:** `users/wallet/`

### Service API — `users/wallet/service.py`

```python
get_or_create_wallet(user)             # Auto-provisions wallet with zero balance
can_pay_with_wallet(user, amount)      # Returns bool — checks is_active + balance

credit_wallet(user, amount, transaction_obj=None)  # +balance, creates WalletTransaction(CREDIT)
debit_wallet(user, amount, transaction_obj=None)   # -balance, creates WalletTransaction(DEBIT)
```

**Safety guarantees:**
- Both `credit_wallet` and `debit_wallet` use `select_for_update()` on the `Wallet` row
- Wrapped in `db_transaction.atomic()`
- `InsufficientBalanceError` raised if balance < amount
- `WalletInactiveError` raised if wallet is deactivated

**`WalletTransaction`** stores `balance_before` and `balance_after` — immutable snapshot of every operation. Linked OneToOne to the universal `Transaction`.

---

## 🎁 Referral Programme

**Location:** `accounts/signals.py`

- Every `CustomUser` gets a unique `REX-XXXXXX` code on account creation
- A new user can enter a referral code at signup (stored as `referred_by` FK)
- On first-time email confirmation (`email_confirmed` signal):
  - Guard: checks if a `REFERRAL_REWARD` Transaction already exists for this user (prevents duplicate rewards)
  - Both referee (new user) and referrer (existing user) receive **₹1,000 wallet credit**
  - Both `create_transaction(REFERRAL_REWARD)` and `credit_wallet()` calls are inside a single `transaction.atomic()` block

---

## ⏱️ Background Tasks

**Location:** `orders/tasks.py`

Uses `django-tasks-db` (`DatabaseBackend`) — tasks stored in PostgreSQL, processed by the `worker` container running `python manage.py db_worker`.

### `expire_failed_order(order_id)`

Enqueued at Razorpay order creation. Fires after `FAILED_ORDER_EXPIRY_SECONDS`:

| Step | Action |
|------|--------|
| 1 | Guard: exit if order no longer FAILED |
| 2 | Restore cart from `cart_snapshot` (quantities capped at `MAX_QUANTITY_PURCHASE_PER_ITEM`) |
| 3 | `revoke_coupon_usage(order)` if coupon was applied |
| 4 | Bulk-cancel any PENDING/FAILED transactions for this order |
| 5 | `change_order_status(FAILED → EXPIRED)` |
| 6 | Clear `cart_snapshot` (set to `None`, save) |

---

## 🛠️ Admin Panel

All admin views are under `/adminpanel/` and protected by superuser check.

<details>
<summary><strong>📊 Dashboard — core/service/dashboard.py</strong></summary>

- **Stat cards**: Total Revenue, Total Orders, Total Customers, Total Products (excludes CANCELLED + FAILED)
- **Revenue & Orders chart**: Yearly / Monthly / Weekly / Daily — aggregates via `TruncYear`, `TruncMonth`, etc.
- **Best-selling Products**: Top 10 by `SUM(quantity)` for non-cancelled/returned items
- **Best-selling Categories**: Top 10 — M2M-aware (joins through `product__category`)
- **Best-selling Brands**: Top 10 by quantity sold

</details>

<details>
<summary><strong>👥 User Management — accounts/views/admin_views/</strong></summary>

- Paginated user list with search (email/name) and status filter
- User detail with order activity
- One-click active/inactive toggle
- Admin password reset via email (10-minute expiry link)

</details>

<details>
<summary><strong>📦 Catalog Management — catalog/views/admin/</strong></summary>

- **Brands**: AJAX-powered create/edit/delete, logo upload, active toggle
- **Categories**: AJAX CRUD, auto-slug on name change
- **Products**: Multi-category M2M, draft/publish toggle, soft delete
- **Variants**: Dynamic JavaScript formsets — add/remove variant rows without page reload
  - Validation: min 3 images, exactly 1 `is_primary` image per variant (enforced by DB constraint too)
  - Offer-aware pricing preview in form

</details>

<details>
<summary><strong>🏷️ Offer Management — offers/views/admin/</strong></summary>

- Paginated list with search and filter by type (Product/Category/Brand) and status (Active/Inactive/Valid/Expired)
- Add/Edit: date-range picker, M2M target selection (dynamic based on offer type)
- Delete: POST-only hard delete
- Stat cards on list page

</details>

<details>
<summary><strong>🎟️ Coupon Management — coupons/views/admin/</strong></summary>

- Paginated list with search and filter by status
- Stat cards: Total / Active / Inactive / Valid / Expired
- Add/Edit: two-column form — discount config + validity + limits
- Delete: soft-delete (`is_deleted=True`, `is_active=False`)

</details>

<details>
<summary><strong>🚚 Order Administration — orders/views/admin/</strong></summary>

- Paginated order list with search (order number/customer) and status filter
- Order detail: items table, address snapshot display, status update dropdown
- Status cascade: admin changing order status walks all eligible items through every intermediate step
- Return list and detail: approve (→ `RETURNED` + stock restore + refund) or reject
- Invoice PDF download

</details>

<details>
<summary><strong>📊 Sales Report — orders/views/admin/sales_report.py</strong></summary>

- **Filters**: All · Today · This Week (7d) · This Month (30d) · Custom date range
- **Stat cards**: Total Orders, Total Amount, Total Offer Discount, Total Coupon Discount
- **Table**: Order #, Date, Customer, Payment Method, Discount, Coupon, Grand Total — paginated 15/page
- **PDF**: WeasyPrint — header, summary grid, full unpaginated table, generation timestamp
- **Excel**: openpyxl — branded header, summary rows, styled column headers (black fill), currency formatting
- Download links carry active filter querystring — exports always match the on-screen view
- Excludes CANCELLED and FAILED orders from all metrics

</details>

<details>
<summary><strong>💳 Transaction & Refund Administration — payments/views.py</strong></summary>

- Transaction list: search + filter by type / status / payment method
- Transaction detail: full info + gateway IDs + audit timestamps
- Refund list (CANCELLATION_REFUND + RETURN_REFUND): status tracking
- Refund detail: Approve (→ `complete_refund()` → wallet credit) or Reject (→ `fail_transaction()`)

</details>

---

## ⚙️ Business Rules & Configuration

These are hardcoded in `settings.py` but many can be overridden via environment variables:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ADDRESSES_PER_USER` | `5` | Enforced in `Address.clean()` |
| `MAX_QUANTITY_PURCHASE_PER_ITEM` | `5` | Enforced in cart add and snapshot restore |
| `SHIPPING_CHARGE` | `100` (₹) | Per item, per order |
| `GST_RATE` | `18` (%) | 18% GST on watches |
| `STORE_STATE` | `KERALA` | For GST jurisdiction |
| `STORE_STATE_CODE` | `32` | Kerala GST state code |
| `DEFAULT_WATCH_HSN` | `9102` | HSN code for wristwatches |
| `WALLET_TOPUP_MIN` | `₹5,000` | Configurable via `WALLET_TOPUP_MIN` env |
| `WALLET_TOPUP_MAX` | `₹75,000` | Configurable via `WALLET_TOPUP_MAX` env |
| `IMAGE_MAX_SIZE_MB` | `5` MB | Validated for all uploaded images |
| `ALLOWED_IMAGE_EXTENSIONS` | `jpg, jpeg, png, webp, avif` | Validated via `FileExtensionValidator` |
| `FAILED_ORDER_EXPIRY_SECONDS` | `18000` (5 h) | Configurable via env; use `120` for dev |
| `REFERRAL_REWARD_AMOUNT` | `₹1,000` | Hardcoded in `accounts/signals.py` |
| `RETURN_WINDOW_DAYS` | `7` | Hardcoded in `orders/utils.py` `can_return_item()` |
| `PHONENUMBER_DEFAULT_REGION` | `IN` | India phone numbers enforced |

---

## 📋 Roadmap

### Phase 1 — Core ✅
- [x] Custom email-based authentication (OTP, allauth, Google OAuth)
- [x] Admin panel with custom login, password reset, user management
- [x] Email blacklisting on email change
- [x] Brand, Category, Product, Variant management (AJAX formsets, soft delete)
- [x] Custom middleware (auth flow guards, block unused allauth URLs)
- [x] User profile: avatar crop, inline password change
- [x] Address management: max 5, auto-default, soft delete, pincode validation

### Phase 2 — E-Commerce ✅
- [x] Wishlist (offcanvas, AJAX toggle, profile counter sync)
- [x] Cart (stock cap, guest redirect with intent preservation, offer pricing)
- [x] 3-step checkout stepper
- [x] Order placement — COD, Wallet, Razorpay (atomic two-phase flow)
- [x] Centralised inventory service with InventoryLog audit trail
- [x] Order success / failure pages
- [x] User order history, detail, item timeline, invoice PDF
- [x] Admin order management (status cascade, return review)
- [x] Item-level return system (photo upload, admin approve/reject)

### Phase 3 — Payments & Financial ✅
- [x] Universal transaction ledger (GenericFK, indexed)
- [x] Razorpay integration (two-phase flow, HMAC-SHA256 signature verification)
- [x] Razorpay payment retry from order listing
- [x] Failed order auto-expiry (background task, cart restore)
- [x] Wallet system (credit/debit, select_for_update, balance snapshots)
- [x] Item-level cancellation with instant wallet refund
- [x] Admin refund management (approve → wallet credit, reject)
- [x] Admin transaction dashboard (list, detail, filters)
- [x] User wallet page (balance, tabbed history)

### Phase 4 — Offers, Coupons & Analytics ✅
- [x] Offer engine (Product / Category / Brand offers, best-discount resolution)
- [x] Coupon system (PERCENTAGE & FIXED, per-user limits, race-condition-safe, proportional refunds)
- [x] Referral programme (₹1,000 wallet reward, signal-driven, duplicate-guarded)
- [x] Sales report (date filters, stat cards, PDF & Excel download)
- [x] Admin dashboard (revenue/orders chart with time filters, best-sellers tables)

### Phase 5 — In Progress 🔄
- [x] Wallet top-up via Razorpay
- [ ] Email notifications (order status updates, refund confirmation)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <strong>Built with ❤️ for luxury watch enthusiasts</strong>
</p>
