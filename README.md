<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 6.0">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/PostgreSQL-18-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 18">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Razorpay-Payments-0C2451?style=for-the-badge&logo=razorpay&logoColor=white" alt="Razorpay">
  <img src="https://img.shields.io/badge/Cloudinary-Media-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary">
  <img src="https://img.shields.io/badge/License-MIT-F7B731?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">⌚ REX CC</h1>
<p align="center"><strong>Premium Luxury Watch E-Commerce Platform</strong></p>

<p align="center">
  A full-featured Django e-commerce platform built for luxury timepieces.<br>
  Atomic order placement, multi-gateway payments, a universal financial ledger,<br>
  referral rewards, and a Dockerised development stack — in one tightly structured codebase.
</p>

---

## 📖 Table of Contents

- [Feature Overview](#-feature-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start — Local Development](#-quick-start--local-development)
- [Quick Start — Docker](#-quick-start--docker)
- [Documentation](#-documentation)
- [Roadmap](#-roadmap)
- [License](#-license)

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
| Product Reviews | ✅ | 1–5 star rating, purchase-verified, one review per user per product |
| COD Minimum Order | ✅ | Configurable minimum order amount for Cash on Delivery |
| Background Task Worker | ✅ | Auto-expires FAILED Razorpay orders, restores cart from snapshot |
| Docker Dev Stack | ✅ | Single-stage Dockerfile, 3-service Compose stack with hot-reload |
| CI/CD Pipeline | ✅ | GitHub Actions — auto-deploy to AWS EC2 on push to `main` |
| Production Security | ✅ | HSTS, SSL redirect, secure cookies — all gated on `DEBUG=False` |

---

## 🏗️ Architecture

### Docker Compose Stack (Development)

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
              ┌──────────────────────────┐
              │  db (postgres:18-alpine)  │
              │  :5432 · named volume    │
              └──────────────────────────┘

External Services
  ├── Cloudinary CDN   (product images, avatars, return photos)
  └── Razorpay Gateway (payment processing, HMAC-SHA256 callback verification)
```

| Container | Image | Role |
|-----------|-------|------|
| `web` | `python:3.13-slim` | Django dev server (`runserver 0.0.0.0:8000`) |
| `worker` | `python:3.13-slim` | `django-tasks-db` background task processor |
| `db` | `postgres:18-alpine` | Persistent relational store with named volume |

---

## 🛠️ Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Web Framework | Django 6.0 | |
| Language | Python 3.13 | |
| Database | PostgreSQL 18 | `alpine` image |
| ORM | Django ORM | With `select_for_update` row locking |
| Auth | django-allauth 65.x | Email-first + Google OAuth |
| Payments | Razorpay SDK 2.0 | Two-phase flow, HMAC-SHA256 verification |
| Media Storage | Cloudinary | `django-cloudinary-storage` |
| PDF Generation | WeasyPrint 68.x | Invoices & sales reports |
| Excel Export | openpyxl 3.x | Styled `.xlsx` sales reports |
| Background Tasks | django-tasks-db | DB-backed task queue, no Redis required |
| Email | Gmail SMTP | App-password via `django-environ` |
| Phone Numbers | django-phonenumber-field | IN region, NATIONAL format |
| Frontend | Bootstrap 5.3 + Vanilla CSS | Desktop-only layout |
| Charts | Chart.js | Admin revenue/order charts |
| Image Cropping | Cropper.js | In-browser avatar crop & upload |
| Icons | Material Icons | Google Material Design |
| Containerisation | Docker + Docker Compose | 3-service dev stack |
| Timezone | Asia/Kolkata | Configurable via `TIME_ZONE` env |
| GST | 18% | Kerala store, HSN 9102 (wristwatches) |

---

## 📁 Project Structure

```
Rex_CC_Ecommerce/
│
├── 📄 Dockerfile                   # Single-stage Python 3.13-slim dev image
├── 📄 docker-compose.yml           # 3-service stack: web, worker, db
├── 📄 entrypoint.sh                # migrate → exec runserver or db_worker
├── 📄 requirements.txt             # Python dependencies (pinned)
├── 📄 sample.env                   # ← Template: copy to .env and fill in values
├── 📄 .gitignore
│
├── .github/workflows/              # CI/CD
│   └── deploy.yml                  # Auto-deploy to AWS EC2 on push to main
│
├── docs/                           # Extended documentation
│   ├── environment-variables.md    # Full env var reference
│   ├── docker.md                   # Docker setup & container commands
│   ├── architecture.md             # Data models & design decisions
│   └── features.md                 # Feature deep-dives
│
├── rexcc_project/                  # Django project root
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                           # Shared infrastructure
│   ├── validators.py
│   ├── service/dashboard.py        # Admin dashboard stats & chart data
│   └── templates/core/             # base_admin.html, base_user.html, error pages
│
├── accounts/                       # Authentication & user model
│   ├── models.py                   # CustomUser, PasswordReset, BlacklistedEmail
│   ├── middleware.py               # AuthFlowRedirectMiddleware, BlockUnusedAllauthURLsMiddleware
│   ├── signals.py                  # email_confirmed → email-change flow + referral rewards
│   └── views/
│       ├── admin_views/            # Admin login, password reset, user management
│       └── user_views/
│
├── catalog/                        # Products, Brands, Categories, Variants
│   ├── models.py                   # Brand, Category, Product, ProductVariant, InventoryLog
│   ├── service.py                  # update_stock(), manage_product_draft_status()
│   ├── utils.py                    # pack_variants(), get_offer_variants(), _best_discount()
│   └── views/
│       ├── admin/                  # Full CRUD for catalog entities
│       └── user/                   # Catalog list, product detail, variant switching
│
├── offers/                         # Offers & discounts engine
│   ├── models.py                   # Offer (PRODUCT/CATEGORY/BRAND, M2M targets)
│   └── views/admin/
│
├── coupons/                        # Coupon system
│   ├── models.py                   # Coupon (PERCENTAGE/FIXED, soft-delete), CouponUsage
│   ├── service.py                  # validate, apply, revoke, recalculate
│   └── views/
│       ├── admin/
│       └── user/                   # AJAX apply/remove endpoints
│
├── orders/                         # Full order lifecycle
│   ├── models.py                   # Order, OrderItem, Return, ReturnImage
│   ├── tasks.py                    # expire_failed_order() background task
│   ├── service/
│   │   ├── status.py               # Transition engine, cascade, reverse sync
│   │   ├── order_helpers.py        # build_cart_snapshot(), create_items_from_snapshot()
│   │   ├── returns.py              # Return eligibility
│   │   ├── stock.py                # Stock locking & validation
│   │   └── sales_report.py         # Report data aggregation
│   └── views/
│       ├── user/                   # checkout, place_order, razorpay, cancel, return
│       └── admin/                  # order list/detail, returns, sales_report
│
├── payments/                       # Universal financial ledger
│   ├── models.py                   # Transaction (GenericFK, 16-char TXN ID)
│   ├── service.py                  # create, update, initiate_refund, complete_refund
│   ├── razorpay_service.py         # create_razorpay_order(), verify_razorpay_signature()
│   └── views.py                    # Admin transaction & refund management
│
├── reviews/                        # Product review system
│   ├── models.py                   # Review (1–5 stars, UniqueConstraint per user×product)
│   ├── services.py                 # Eligibility checks, ratings summary, per-star distribution
│   ├── forms.py                    # ReviewForm — rating, title, comment
│   └── views.py                    # AJAX submit_review endpoint
│
└── users/                          # User domain
    ├── cart/                       # Cart, CartItem, compute_cart_summary
    ├── wishlist/                   # Wishlist, AJAX toggle
    ├── wallet/                     # Wallet, WalletTransaction, service
    └── user_profile/               # Address, profile edit, avatar, email change
```

---

## 🚀 Quick Start — Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ running locally
- A [Cloudinary](https://cloudinary.com) account
- A [Razorpay](https://razorpay.com) account (test mode is fine)
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833)

### Steps

```bash
# 1. Clone
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
# Edit .env and fill in all required values

# 5. Apply migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Start the dev server
python manage.py runserver
```

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000 | User-facing storefront |
| http://127.0.0.1:8000/adminpanel/ | Admin panel |

> **Background tasks** (auto-expiring failed Razorpay orders) require the worker in a separate terminal:
> ```bash
> python manage.py db_worker
> ```

---

## 🐳 Quick Start — Docker

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Steps

```bash
# 1. Clone
git clone https://github.com/your-username/Rex_CC_Ecommerce.git
cd Rex_CC_Ecommerce

# 2. Configure environment
cp sample.env .env
# Edit .env — fill in all required values including DB_NAME, DB_USER, DB_PASSWORD

# 3. Build and start all containers
docker compose up --build

# 4. Open in browser
# http://localhost:8000
```

Migrations run automatically on every startup via `entrypoint.sh`. To create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

> See [docs/docker.md](docs/docker.md) for the full container reference, common commands, and troubleshooting.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Environment Variables](docs/environment-variables.md) | Full reference for all `.env` variables, Docker override explanation |
| [Docker Guide](docs/docker.md) | Service architecture, container commands, troubleshooting |
| [Architecture & Data Models](docs/architecture.md) | All models, DB indexes, and key design decisions |
| [Feature Deep-Dives](docs/features.md) | Auth flows, offer engine, coupon service, order state machine, payments, wallet, and more |

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
- [x] Wallet top-up via Razorpay

### Phase 4 — Offers, Coupons & Analytics ✅
- [x] Offer engine (Product / Category / Brand offers, best-discount resolution)
- [x] Coupon system (PERCENTAGE & FIXED, per-user limits, race-condition-safe, proportional refunds)
- [x] Referral programme (₹1,000 wallet reward, signal-driven, duplicate-guarded)
- [x] Sales report (date filters, stat cards, PDF & Excel download)
- [x] Admin dashboard (revenue/orders chart with time filters, best-sellers tables)

### Phase 5 — Reviews & CI/CD ✅
- [x] Product reviews (1–5 star, purchase-verified, ratings summary with per-star distribution)
- [x] CI/CD pipeline (GitHub Actions → AWS EC2, auto-deploy on push to `main`)

### Phase 6 — In Progress 🔄
- [ ] Email notifications (order status updates, refund confirmation)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <strong>Built with ❤️ for luxury watch enthusiasts</strong>
</p>
