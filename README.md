<div align="center">

# ⌚ REX CC E-Commerce
**Premium Luxury Watch E-Commerce Platform**

[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

A full-featured Django e-commerce platform built for luxury timepieces — atomic order placement, multi-gateway payments, a universal financial ledger, and a Dockerised development stack.

</div>

---

## ✨ Highlights

- **Robust Order Lifecycle** — Atomic transactions, Razorpay two-phase flow, and automated refund management.
- **Dynamic Offer Engine** — Resolves the best discount across brands, categories, and products at runtime.
- **Centralised Inventory** — Strict stock enforcement with immutable `InventoryLog` audit trails.
- **Race-Safe Financials** — Row-level locking on wallet and coupon operations via `select_for_update()`.
- **Verified Reviews** — Purchase-gated product reviews with moderation support.
- **PDF Invoicing** — GST-compliant invoices generated server-side with WeasyPrint.
- **Docker-Ready** — One-command dev environment with hot-reload and auto-migrations.

---

## 🚀 Quick Start

```bash
# 1. Clone & configure
git clone <your-repo-url>
cd Rex_CC_Ecommerce
cp sample.env .env          # fill in your credentials

# 2. Launch with Docker
docker compose up --build
```

> [!TIP]
> The app is available at `http://localhost:8000`. Migrations run automatically on every start.

For non-Docker setup, see the [Local Development Guide](./docs/docker.md#local-setup-alternative).

---

## 🗂️ Project Structure

```
Rex_CC_Ecommerce/
├── accounts/          # Custom user model, auth, Google OAuth, middleware
├── catalog/           # Products, variants, brands, categories, inventory
├── core/              # Shared utilities, decorators, template tags
├── coupons/           # Coupon engine with usage tracking
├── offers/            # Dynamic product/category/brand offers
├── orders/            # Order lifecycle, returns, status state machine
├── payments/          # Universal transaction ledger (GenericFK)
├── reviews/           # Purchase-verified product reviews
├── users/             # Address, cart, wishlist, wallet sub-apps
├── rexcc_project/     # Django settings, root URL config
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
└── sample.env         # Full env reference with comments
```

---

## 📚 Documentation

| Topic | What's Inside |
|:---|:---|
| 🏗️ [Architecture & Data Models](./docs/architecture.md) | Domain models, relationships, and state machines. |
| 🐳 [Docker Guide](./docs/docker.md) | Container setup, daily commands, and troubleshooting. |
| ⚙️ [Environment Variables](./docs/environment-variables.md) | Complete `.env` reference for all services. |
| 🚀 [Features Deep-Dive](./docs/features.md) | Auth, offers, coupons, payments, wallet, reviews. |

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

<div align="center">
  <p>Built with ❤️ for luxury watch enthusiasts.</p>
</div>
