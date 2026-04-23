# Rex CC Ecommerce

<p align="center">
  <strong>A modern Django e-commerce platform for premium watches.</strong><br/>
  Built with clean app boundaries, transactional order workflows, and production-aware defaults.
</p>

---

## Why this project

Rex CC is a full-stack commerce application that covers the complete shopping lifecycle:

- Account creation and login (email verification + Google OAuth)
- Catalog, offers, and coupon-driven pricing
- Cart, wishlist, and 3-step checkout
- Order placement (COD, Wallet, Razorpay)
- Returns, cancellations, refunds, and wallet ledgering
- Admin reporting (dashboard, PDF/Excel sales exports)

It is designed for **clarity**, **maintainability**, and **real-world business rules**.

---

## Core capabilities

### Customer features
- Email-first authentication with OTP verification
- Google sign-in via `django-allauth`
- Product browsing, filtering, and variant switching
- Wishlist and cart with stock-aware quantity controls
- Checkout with saved addresses and coupon support
- Order history, item tracking, cancellations, and return requests
- Wallet balance and transaction history
- Purchase-verified product reviews

### Admin features
- Dedicated admin authentication flow (`/adminpanel/...`)
- Brand, category, product, and variant management
- Offer and coupon management
- Order operations and return decisioning
- Transaction/refund review interfaces
- Revenue and sales analytics with downloadable reports

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0 |
| Language | Python 3.13 |
| Database | PostgreSQL 18 |
| Auth | django-allauth |
| Payments | Razorpay |
| Media | Cloudinary |
| Background jobs | django-tasks + django-tasks-db |
| Reports | WeasyPrint (PDF), openpyxl (Excel) |
| Runtime | Local Python or Docker Compose |

---

## Project structure

```text
Rex_CC_Ecommerce/
├── rexcc_project/          # Django project settings and root URLs
├── accounts/               # Authentication, custom user, admin auth
├── core/                   # Shared templates, dashboard, static assets
├── catalog/                # Brands, categories, products, variants, inventory log
├── offers/                 # Offer engine (product/category/brand)
├── coupons/                # Coupon validation and lifecycle
├── users/                  # cart, wishlist, wallet, profile/address
├── orders/                 # checkout, order placement, status, returns
├── payments/               # transaction ledger and refund operations
├── reviews/                # purchase-verified product reviews
├── docs/                   # project documentation
├── docker-compose.yml      # local development stack
└── sample.env              # environment variable template
```

---

## Quick start (local)

### 1) Prerequisites
- Python 3.13+
- PostgreSQL running locally
- Cloudinary account
- Razorpay test keys
- SMTP credentials (or console email backend)

### 2) Setup

```bash
git clone <your-repo-url>
cd Rex_CC_Ecommerce

python -m venv .venv
source .venv/bin/activate         # Linux/macOS
# .venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt
cp sample.env .env
```

Edit `.env` and provide required values.

### 3) Run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In a second terminal (for background tasks):

```bash
python manage.py db_worker
```

App URLs:
- Storefront: `http://127.0.0.1:8000`
- Admin area: `http://127.0.0.1:8000/adminpanel/`

---

## Quick start (Docker)

```bash
git clone <your-repo-url>
cd Rex_CC_Ecommerce
cp sample.env .env
docker compose up --build
```

Then open `http://localhost:8000`.

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Documentation map

- [Architecture](docs/architecture.md)
- [Feature Guide](docs/features.md)
- [Environment Variables](docs/environment-variables.md)
- [Docker Guide](docs/docker.md)

---

## Contributing

1. Fork and create a feature branch.
2. Keep changes focused and well-tested.
3. Update docs when behavior changes.
4. Open a pull request with a clear summary.

---

## License

This repository is available under the MIT License.
