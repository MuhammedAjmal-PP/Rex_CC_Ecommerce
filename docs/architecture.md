# Architecture

This document explains how Rex CC is organized, how data flows through the system, and why key design choices were made.

---

## 1) System overview

Rex CC follows a modular Django app architecture. Each domain owns its models, service logic, views, and templates.

### Runtime components

- **Web app**: Django server handling user/admin requests.
- **Worker**: `django-tasks-db` worker for background jobs.
- **Database**: PostgreSQL as the source of truth.
- **External services**:
  - Cloudinary for media storage
  - Razorpay for payment processing

---

## 2) Application modules

| App | Responsibility |
|---|---|
| `accounts` | Custom user model, auth flow, admin authentication, email blacklisting |
| `core` | Shared layout, static assets, dashboard and common pages |
| `catalog` | Brands, categories, products, variants, inventory logging |
| `offers` | Time-bound offer definitions and targeting |
| `coupons` | Coupon validation, usage tracking, and revocation |
| `users.cart` | Cart storage and cart summary logic |
| `users.wishlist` | Wishlist and AJAX toggling |
| `users.wallet` | Wallet balance and wallet transaction records |
| `users.user_profile` | Profile and address management |
| `orders` | Checkout, order placement, item lifecycle, returns |
| `payments` | Generic transaction ledger and refund flows |
| `reviews` | Purchase-verified product reviews |

---

## 3) Data model highlights

### Identity and access
- `accounts.CustomUser` is email-first (`AUTH_USER_MODEL`).
- Email changes are protected via `BlacklistedEmail` history.

### Catalog and stock
- `Product` and `ProductVariant` support draft/soft-delete workflows.
- `InventoryLog` records every stock mutation for auditability.

### Order lifecycle
- `Order` stores pricing snapshots, addresses, and payment references.
- `OrderItem` tracks item-level status for granular operations.
- `Return` and `ReturnImage` support return workflow evidence.

### Money movement
- `payments.Transaction` acts as a universal financial ledger.
- Wallet operations map to transaction records through `WalletTransaction`.

### Pricing controls
- `Offer` supports PRODUCT/CATEGORY/BRAND scoping.
- `Coupon` + `CouponUsage` controls discount governance and limits.

---

## 4) Service-layer strategy

Business-critical operations are centralized in service modules to keep views thin and reusable.

- `catalog/service.py`: stock updates, draft status management
- `coupons/service.py`: validation, application, revocation, recalculation
- `orders/service/*`: order status logic, stock checks, returns, sales reports
- `payments/service.py`: transaction creation and refund completion
- `users/wallet/service.py`: safe wallet credit/debit operations

This improves consistency and reduces repeated logic across views.

---

## 5) Transaction safety and consistency

Rex CC emphasizes data integrity:

- **`transaction.atomic()`** for order placement and payment paths
- **`select_for_update()`** where row-level locking is required
- Snapshot fields on orders to avoid historical drift
- Controlled status transitions for orders and items

These patterns reduce race conditions and keep financial and stock data coherent.

---

## 6) Payment architecture (Razorpay)

Razorpay follows a two-phase model:

1. Create pending order context and gateway order ID
2. Verify callback signature and finalize payment effects

Only after verification does the system finalize items, stock impact, and status updates.

---

## 7) Deployment shape (development)

Docker Compose defines a three-service setup:

- `db` → PostgreSQL
- `web` → Django app
- `worker` → background task processor

The web and worker services both run migrations at startup via `entrypoint.sh` before executing their main command.

---

## 8) Design goals

- **Modularity**: clear domain ownership by app
- **Auditability**: explicit inventory and transaction records
- **Reliability**: transaction-safe writes and lock-based critical paths
- **Maintainability**: service-layer separation and predictable naming
- **Extensibility**: easy to add new payment methods, reports, or catalog rules
