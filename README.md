<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/PostgreSQL-18-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Cloudinary-Media-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary">
  <img src="https://img.shields.io/badge/Razorpay-Payments-0C2451?style=for-the-badge&logo=razorpay&logoColor=white" alt="Razorpay">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap">
</p>

<h1 align="center">⌚ REX CC</h1>
<p align="center"><strong>Premium Luxury Watch E-Commerce Platform</strong></p>

<p align="center">
  A sophisticated Django-based e-commerce platform crafted for luxury timepieces.<br>
  Built with modern architecture, clean aesthetics, and enterprise-grade security.
</p>

---

## 📖 Table of Contents

- [Features Overview](#-features-overview)
- [Authentication System](#-authentication-system)
- [Admin Panel](#-admin-panel)
- [Offers & Discounts](#-offers--discounts)
- [Coupon System](#%EF%B8%8F-coupon-system)
- [User Features](#-user-features)
- [Cart Management](#-cart-management)
- [Wishlist System](#-wishlist-system)
- [Checkout & Orders](#-checkout--orders)
- [Payments & Transactions](#-payments--transactions)
- [Wallet System](#-wallet-system)
- [Inventory Management](#-inventory-management)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Roadmap](#-roadmap)

---

## ✨ Features Overview

| Feature | Status | Description |
|---------|--------|-------------|
| Authentication | ✅ Complete | Email/OTP, Google OAuth, Password Reset |
| Admin Panel | ✅ Complete | Dynamic variant forms, validation, advanced CRUD |
| User Profile | ✅ Complete | Settings, Avatar cropping, Address book |
| Catalog | ✅ Complete | Search, Filter, Sort, Stock status |
| Cart | ✅ Complete | Real-time stock, Guest handling, Wishlist sync |
| Wishlist | ✅ Complete | Offcanvas UI, AJAX toggle, Persistent storage |
| Checkout | ✅ Complete | 3-step stepper, Address selection, Order summary |
| Order Placement | ✅ Complete | COD, Razorpay, Wallet — Atomic transactions |
| Payments | ✅ Complete | Razorpay gateway, Transaction ledger, Refund management |
| Wallet | ✅ Complete | Credit/Debit, Balance snapshots, Transaction history |
| Inventory | ✅ Complete | Centralized stock service, Audit logs |
| Offers & Discounts | ✅ Complete | Product/Category/Brand offers, Best-offer pricing, Admin CRUD |
| Coupon System | ✅ Complete | Code-based coupons, checkout apply/remove, per-user limits, order integration |
| Order Management (User) | ✅ Complete | Order history, Item tracking, Cancellation, Returns, Invoice PDF |
| Order Management (Admin) | ✅ Complete | Status cascade, Return review, Refund approve/reject |
| Sales Report | ✅ Complete | Date filters (Daily/Weekly/Monthly/Custom), stats, PDF & Excel download |

---

## 🔐 Authentication System

### Implementation Details

| Feature | Description | How It Works |
|---------|-------------|--------------|
| **Email-Based Auth** | Custom `CustomUser` model | Email replaces username as primary identifier |
| **OTP Verification** | Account Activation | 6-digit OTP sent via SMTP, stored in session |
| **Google OAuth** | Social Login | `django-allauth` integration with Google Provider |
| **Password Reset** | Recovery | Secure token-based link with 24hr expiry |
| **Admin Access** | Role-based | Superuser-only access via `@user_passes_test` |

---

## 🛠️ Admin Panel

<details>
<summary><strong>👥 User Management</strong></summary>

**Location:** `accounts/views/admin_views/user_management.py`

- Paginated user listing with search & status filter
- Detailed user profile with activity view
- One-click active/inactive toggle
</details>

<details>
<summary><strong>📦 Catalog Management</strong></summary>

**Location:** `catalog/views/admin/`

- **Brands & Categories**: AJAX-powered CRUD, logo uploads, soft deletes.
- **Products**: Multi-category support, draft/publish toggle, soft delete.
- **Variants**:
    - **Dynamic Formsets**: Add/edit variants without page reloads using JavaScript.
    - **Strict Validation**: Enforces minimum 3 images and exactly 1 primary image per variant.
    - **Offer-Aware Pricing**: Variant `discount_percentage` automatically resolves the best rate across own discount, product offers, category offers, and brand offers.
    - **Optimized UI**: Horizontal scrolling tables for complex data, unified form templates.
</details>

<details>
<summary><strong>🏷️ Offer Management</strong></summary>

**Location:** `offers/views/admin/views.py`

- **Offer List**: Paginated listing with search, filter by type (Product/Category/Brand) and status (Active/Inactive/Valid/Expired), stat cards
- **Add / Edit Offer**: Form with date-range picker, percentage discount value, dynamic M2M target selection (products, categories, or brands based on offer type)
- **Delete Offer**: POST-only hard delete
- **Form Validation**: Enforces single-target-type rule (e.g., a Product offer cannot link to categories or brands), date ordering, and max percentage cap
</details>

<details>
<summary><strong>🎟️ Coupon Management</strong></summary>

**Location:** `coupons/views/admin/views.py`

- **Coupon List**: Paginated listing with search, stat cards (Total/Active/Inactive/Valid/Expired), filter by status
- **Add / Edit Coupon**: Two-column form with discount type/value, validity period, usage limits, per-user limit, min order amount, active toggle
- **Delete Coupon**: POST-only hard delete with confirmation
- **Form Validation**: Start/end date ordering, percentage cap, minimum order amount enforcement
</details>

<details>
<summary><strong>🚚 Order Administration</strong></summary>

**Location:** `orders/views/admin/`

- **Order List**: Paginated listing with search, filter by status, stat cards
- **Order Detail**: View items, addresses, timeline; update order status
- **Status Cascade**: Changing order status automatically walks all items through every intermediate status (e.g., order → SHIPPED cascades items through CONFIRMED → PACKING → READY → SHIPPED)
- **Return Management**: Separate return list/detail views, approve/reject returns, admin cannot set RETURN_REQUESTED directly
- **Invoice**: PDF generation via WeasyPrint with luxury-themed template
</details>

<details>
<summary><strong>📊 Sales Report</strong></summary>

**Location:** `orders/views/admin/sales_report.py` + `orders/service/sales_report.py`

- **Filter Options**: Quick filters (Today / This Week / This Month) + Custom date range picker
- **Summary Stats**: Total Orders, Total Order Amount, Total Discount (offers), Total Coupon Discount — displayed as stat cards
- **Orders Table**: Paginated table of orders in the selected period showing discount & coupon breakdowns
- **PDF Download**: WeasyPrint-generated report with summary stats + full orders table
- **Excel Download**: Styled `.xlsx` export via openpyxl with formatted headers and currency columns
- **Filter Persistence**: All downloads respect the currently active date filter
- **Excluded Statuses**: Cancelled and Failed orders are excluded from report metrics
</details>

<details>
<summary><strong>↩️ Return Management</strong></summary>

**Location:** `orders/views/admin/returns.py` + `orders/service/returns.py`

- **Eligibility Rules**: Must be DELIVERED, within 7-day window, no existing return (including rejected)
- **User Flow**: Custom return form with reason selection, comments, photo upload (up to 3, inline preview + remove)
- **Admin Review**: Approve/reject with status cascade back to item
</details>

<details>
<summary><strong>💳 Transaction & Refund Administration</strong></summary>

**Location:** `payments/views.py`

- **Transaction List**: Paginated view of all transactions with search and type/status/method filters
- **Transaction Detail**: Full detail view with linked order/item, gateway IDs, audit timestamps
- **Refund List**: Filtered view of refund-type transactions (cancellation + return refunds) with status tracking
- **Refund Detail**: Admin detail page with approve/reject action buttons
- **Refund Actions**: Approve (credits user wallet) or reject pending refunds
</details>

---

## 🏷️ Offers & Discounts

**Location:** `offers/`

### Offer Model

| Field | Description |
|-------|-------------|
| `name` | Human-readable label (min 3 chars) |
| `offer_type` | PRODUCT, CATEGORY, or BRAND |
| `discount_type` | PERCENTAGE (extensible to FIXED in future) |
| `discount_value` | Percentage value (0–100) |
| `start_date` / `end_date` | Validity window (datetime) |
| `is_active` | Manual on/off toggle |
| `products` / `categories` / `brands` | M2M relations — attach offer to targets |

### Pricing Integration

The `ProductVariant.discount_percentage` property automatically resolves the **best available discount** across all sources:

```
1. Variant's own `discount_rate`
2. Active Product offers linked to the variant's product
3. Active Category offers linked to any of the product's categories
4. Active Brand offers linked to the product's brand
```

The highest rate wins, and `final_price` = `price − discount_amount`.

### Validation Rules

- A **Product offer** must link to at least one product and cannot link to categories or brands
- A **Category offer** must link to at least one category and cannot link to products or brands
- A **Brand offer** must link to at least one brand and cannot link to products or categories
- `end_date` must be after `start_date`
- Percentage discount capped at 100%

---

## 🎟️ Coupon System

**Location:** `coupons/`

### Coupon Model

| Field | Description |
|-------|-------------|
| `code` | Unique uppercase coupon code |
| `description` | Optional human-readable description |
| `discount_type` | PERCENTAGE or FIXED_AMOUNT |
| `discount_value` | Discount amount (percentage or absolute) |
| `min_order_amount` | Minimum cart subtotal required |
| `max_discount_amount` | Cap on percentage discounts (optional) |
| `usage_limit` | Global usage cap (null = unlimited) |
| `per_user_limit` | Max uses per user (default: 1) |
| `start_date` / `end_date` | Validity window |
| `is_active` | Manual on/off toggle |
| `used_count` | Tracks total redemptions |

### CouponUsage Model

Tracks individual coupon usage per user, linked to orders:
- `coupon` → FK to Coupon
- `user` → FK to User
- `order` → FK to Order
- `used_at` → Timestamp

### Service Layer (`coupons/service.py`)

```python
validate_coupon(code, user, cart_subtotal)    # Full validation → (coupon, discount)
apply_coupon_to_order(coupon, user, order)    # Record usage + increment count
revoke_coupon_usage(order)                   # Undo usage on full cancellation
```

### Checkout Integration

- **Session State**: Applied coupon stored in `request.session["applied_coupon"]`
- **AJAX Endpoints**: `/coupon/apply/` and `/coupon/remove/` for real-time apply/remove
- **Available Coupons**: Only shows coupons where user hasn't reached `per_user_limit`
- **Server Re-validation**: Coupon re-validated at order placement to prevent stale usage
- **Order Model**: `coupon` FK and `coupon_discount` field store applied coupon on the order
- **Proportional Refunds**: `OrderItem.coupon_share` distributes coupon discount proportionally for per-item refunds

### Validation Rules

- Coupon must exist, be active, and within date range
- Global `usage_limit` and per-user `per_user_limit` enforced
- Cart subtotal must meet `min_order_amount`
- Percentage discounts capped by `max_discount_amount`
- Full cancellation revokes coupon usage (restores count)

---

## 👤 User Features

### Profile & Address
- **Profile**: Avatar cropping (Cropper.js), inline password management.
- **Address**: Limit max addresses (default 5), auto-default selection logic, soft delete to preserve order history.
- **Address Validation**: Server-side India Post pincode-to-state mapping ensures address accuracy.

### Shopping Experience
- **Catalog**: Multi-select faceted filtering (Brand, Category, Color, Movement), sorting, and pagination.
- **Product Detail**: Variant selection changes URL/Images/Price dynamically. Stock status indicators.

---

## 🛒 Cart Management

**Location:** `users/cart/`

| Function | Description |
|----------|-------------|
| `view_cart()` | Displays items with real-time stock limits |
| `add_cart()` | Adds items, merges quantities, redirects guests to login (preserving intent) |
| `update_cart()` | Updates quantity via AJAX, respects stock limit |
| `get_variant_stock()` | **Public API** for frontend stock checking |

**Key Logics:**
1.  **Stock Validation**: Prevents adding more than available stock.
2.  **Guest Handling**: Guests clicking "Add to Cart" are redirected to Login, then back to PDP.
3.  **Wishlist Sync**: Adding to cart automatically removes from wishlist.
4.  **Cart Properties**: `sub_total`, `tax` (GST), `shipping_fee`, `grand_total` as computed model properties.

---

## ❤️ Wishlist System

**Location:** `users/wishlist/`

| Function | Description |
|----------|-------------|
| `wishlist_view()` | Main page listing all saved items |
| `toggle_wishlist()` | AJAX toggle (Add/Remove) from Cards/PDP |
| `remove_wishlist_item()` | Removes specific item via Offcanvas/Page |

**Key Features:**
- **Offcanvas UI**: Quick view of wishlist items without leaving current page.
- **AJAX Interactions**: Instant feedback (Heartbeat animation) without page reload.
- **Profile Integration**: Real-time counter sync in Profile Dashboard.

---

## 🚚 Checkout & Orders

### Checkout Flow

**Location:** `orders/views/user/checkout.py`

A **3-step stepper** UI guides the user through:

| Step | Feature | Details |
|------|---------|---------|
| 1. **Address** | Select/Add delivery address | Saved addresses with default selection, inline address form |
| 2. **Payment** | Choose payment method | COD, Razorpay, Wallet |
| 3. **Review** | Final order review | Item summary, pricing breakdown, dynamic payment method display, confirm & place |

### Order Placement

**Location:** `orders/views/user/place_order.py`

| Function | Description |
|----------|-------------|
| `place_order_view()` | `@require_POST` — Handles COD, Wallet, and Razorpay order creation. For Razorpay: returns JSON with gateway order data |
| `razorpay_callback()` | Verifies Razorpay signature via HMAC-SHA256 and completes the transaction |
| `razorpay_payment_failed()` | Marks transaction as FAILED when user dismisses modal or Razorpay reports failure |
| `order_success_view()` | Animated success page with order number, guards against invalid access |
| `order_failure_view()` | Payment failure page shown when Razorpay payment fails |

**Transaction Flow (Atomic):**
1. Validate address, payment method, cart items, and stock (with `select_for_update` row locking)
2. Create `Transaction` record via payments service
3. Create `Order` with address snapshots (JSONField) and totals, linked to Transaction
4. Create `OrderItem` for each cart item with initial `PENDING` status
5. Decrement stock via `update_stock()` service (creates `InventoryLog`)
6. Set initial `PLACED` status on the Order via `StatusTimeline`
7. **COD/Wallet**: Complete transaction immediately; **Razorpay**: Return gateway order data for frontend checkout modal
8. Clear purchased items from cart
9. Redirect to order success/failure page

### Order Cancellation

**Location:** `orders/views/user/cancel_order.py`

| Function | Description |
|----------|-------------|
| `cancel_order()` | `@require_GET` — Displays cancellable items with checkboxes |
| `cancel_order_submit()` | `@require_POST` — Processes selected item cancellations atomically |

**Cancellation Logic:**
- **Item-level cancellation**: Users select individual items to cancel (items in PENDING, CONFIRMED, PACKING, or READY status)
- **Stock restoration**: Cancelled items' stock is restored via inventory service
- **Instant Refunds**: For prepaid orders (Razorpay/Wallet), cancellations trigger an **instant** refund directly to the user's wallet. COD orders skip refund since no payment was collected
- **Reason tracking**: User provides a cancellation reason, recorded in status timeline

### Order Models

| Model | Description |
|-------|-------------|
| `Order` | User, address snapshots (JSON), totals, linked Transaction (`GenericRelation`), auto-generated order number |
| `OrderItem` | Links Order ↔ ProductVariant with quantity and price |
| `StatusTimeline` | **Generic relation** — tracks status history for both Order and OrderItem with actor audit |
| `Return` | Return request linked to OrderItem with reason code, comment, status (REQUESTED/APPROVED/REJECTED/COMPLETED) |
| `ReturnImage` | Photos uploaded as return evidence (up to 3 per return) |

**Status Flows:**
- **Order**: PLACED → CONFIRMED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED (+ CANCELLED, FAILED)
- **OrderItem**: PENDING → CONFIRMED → PACKING → READY → SHIPPED → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED (+ CANCELLED, RETURN_REQUESTED, RETURNED, FAILED, RTS)

**Status Service** (`orders/service/status.py`):
- **Progressive Cascade**: Order status changes walk items through every intermediate status in the chain
- **Reverse Sync**: Item status changes auto-derive the correct order-level status
- **Admin Restrictions**: Admins cannot set RETURN_REQUESTED directly; only the user return flow triggers it

### User Order Pages

| Page | Description |
|------|-------------|
| Order List | Tabular history with status badges, date, payment method |
| Order Detail | Items table (qty, price, total, status), address, summary, timeline, invoice download |
| Order Item Detail | Product info, vertical status timeline, return button (if eligible) |
| Cancel Order | Item-selection form with checkboxes, reason input, cancel confirmation |
| Return Form | Reason dropdown, comments, styled photo upload with inline preview |
| Invoice PDF | WeasyPrint-generated luxury-themed PDF with meta info, items, GST breakdown |

---

## 💳 Payments & Transactions

### Transaction Ledger

**Location:** `payments/models.py` + `payments/service.py`

A universal `Transaction` model records every financial event in the system:

| Field | Description |
|-------|-------------|
| `transaction_id` | UUID — unique identifier |
| `transaction_type` | ORDER_PAYMENT, CANCELLATION_REFUND, RETURN_REFUND, WALLET_CREDIT, WALLET_DEBIT |
| `payment_method` | COD, WALLET, RAZORPAY |
| `status` | PENDING → PAID / COMPLETED / FAILED / CANCELLED |
| `content_object` | GenericFK linking to the source (Order, OrderItem, Return, etc.) |
| `gateway_*` | Razorpay-specific fields (order_id, payment_id, signature) |

**Service Functions:**

```python
create_transaction(user, txn_type, method, amount, status, content_object, note)
initiate_refund(order, user, amount, txn_type, content_object, note)
complete_refund(transaction)      # → marks COMPLETED + credits wallet
fail_refund(transaction, note)    # → marks FAILED (admin rejects)
complete_transaction(transaction) # → PENDING → COMPLETED
fail_transaction(transaction)     # → PENDING → FAILED
```

### Razorpay Integration

**Location:** `payments/razorpay_service.py`

| Function | Description |
|----------|-------------|
| `create_razorpay_order()` | Creates a Razorpay order (amount in paise, auto-capture enabled) |
| `verify_razorpay_signature()` | HMAC-SHA256 signature verification of Razorpay callback |

**Flow**: Place order → Create Razorpay order → Frontend opens checkout modal → Razorpay callback verifies → Transaction marked PAID → Order confirmed

---

## 💰 Wallet System

**Location:** `users/wallet/`

### Models

| Model | Description |
|-------|-------------|
| `Wallet` | One-per-user, stores `balance` with `is_active` flag |
| `WalletTransaction` | Balance snapshots (`balance_before` / `balance_after`), linked to universal `Transaction` via OneToOne |

### Service Layer

```python
get_or_create_wallet(user)           # Auto-provision wallet
can_pay_with_wallet(user, amount)    # Balance check
credit_wallet(user, amount, txn)     # Add funds (refunds, rewards)
debit_wallet(user, amount, txn)      # Deduct funds (order payment)
```

**Safety Features:**
- `select_for_update()` row locking prevents race conditions
- `InsufficientBalanceError` / `WalletInactiveError` custom exceptions
- Every operation creates a `WalletTransaction` with balance snapshots

### User Pages

| Page | Description |
|------|-------------|
| Wallet Page | Balance display + tabbed transaction history (Wallet / All Transactions) with pagination |
| Transaction Detail | Full detail of a transaction with linked order/item info |

---

## 📊 Inventory Management

**Location:** `catalog/service.py` + `catalog/models.py`

### Centralized Stock Service

```python
update_stock(
    product_variant,   # Which variant
    change,            # +ve (restock) or -ve (order/return)
    reason,            # ORDER_PLACED, ORDER_CANCELLED, RETURNED, ADMIN_ADJUSTMENT
    actor,             # Who triggered the change
    reference_object,  # Order/OrderItem/Return (generic FK)
    note               # Extra context
)
```

### InventoryLog Model

Every stock change is recorded with:
- `stock_before` / `stock_after` — Full audit trail
- `reason` — Categorized (ORDER_PLACED, RETURNED, ADMIN_ADJUSTMENT, etc.)
- `actor` — Who made the change (user/admin/system)
- `reference_object` — Generic FK linking to the Order/OrderItem that caused it
- Validation ensures `stock_after == stock_before + change`

---

## 🏗️ Tech Stack

```
Backend          Frontend           Storage          Payments         Tools
─────────────    ─────────────      ─────────────    ─────────────    ─────────────
Django 6.0       Bootstrap 5.3     PostgreSQL       Razorpay         Black (formatter)
django-allauth   Vanilla CSS       Cloudinary                        djLint (templates)
WeasyPrint       Cropper.js                                          Git
                 Material Icons
```

---

## 📁 Project Structure

```
Rex_CC_Ecommerce/
├── core/                  # Core modules
│   ├── validators.py      # Shared validators
│   └── templates/core/    # Base templates (admin/user)
│
├── accounts/              # Authentication & User Model
│   └── views/admin_views/ # User management (admin)
│
├── catalog/               # Products, Brands, Categories, Variants
│   ├── models.py          # Product, Variant, InventoryLog
│   ├── service.py         # update_stock(), draft management
│   └── views/admin/       # Full catalog CRUD
│
├── offers/                # Offers & Discounts
│   ├── models.py          # Offer (Product/Category/Brand, M2M targets)
│   ├── forms.py           # OfferForm with type-specific validation
│   └── views/admin/       # Offer list, add, edit, delete
│
├── coupons/               # Coupon System
│   ├── models.py          # Coupon, CouponUsage
│   ├── forms.py           # CouponForm with validation
│   ├── service.py         # validate, apply, revoke coupon logic
│   ├── views/admin/       # Admin CRUD (list, add, edit, delete)
│   └── views/user/        # AJAX apply/remove endpoints
│
├── orders/                # Order lifecycle
│   ├── models.py          # Order, OrderItem, StatusTimeline, Return, ReturnImage
│   ├── service/           # Status transitions, returns, stock validation
│   │   ├── status.py      # Progressive cascade, sync, transition validation
│   │   ├── returns.py     # Return eligibility checks
│   │   ├── stock.py       # Stock locking & validation for order placement
│   │   └── sales_report.py # Date-range aggregation for sales reports
│   ├── forms.py           # ReturnForm
│   ├── views/user/        # Checkout, Place Order, Cancel, Returns, Order Detail
│   └── views/admin/       # Order list/detail, Return list/detail, Sales report
│
├── payments/              # Financial transactions
│   ├── models.py          # Transaction (universal ledger)
│   ├── service.py         # create_transaction, refund ops, status helpers
│   ├── razorpay_service.py # Razorpay order creation & signature verification
│   └── views.py           # Admin transaction/refund management
│
├── users/                 # User domain
│   ├── cart/              # Cart logic, utils, computed properties
│   ├── wishlist/          # Wishlist toggle, offcanvas
│   ├── wallet/            # Wallet balance, credit/debit, transaction history
│   │   ├── models.py      # Wallet, WalletTransaction
│   │   ├── service.py     # credit_wallet, debit_wallet, balance checks
│   │   └── views.py       # User wallet page, transaction detail
│   └── user_profile/      # Address (with pincode validation), Profile
│
└── rexcc_project/         # Project settings & URL conf
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Cloudinary Account
- Razorpay Account (for online payments)

### Installation

```bash
# Clone repository
git clone https://github.com/your-repo/Rex_CC_Ecommerce.git
cd Rex_CC_Ecommerce

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   DATABASE_URL, CLOUDINARY_*, EMAIL_*,
#   RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

---

## 📋 Roadmap

### Phase 1 — Core (✅ Complete)
- [x] User Authentication (Email, OTP, Google)
- [x] Admin Panel (Dashboard, User Management)
- [x] Brand Management (CRUD, Logo, Status)
- [x] Category Management (AJAX, Auto-slug)
- [x] Product Management (Multi-category, Draft, Soft-delete)
- [x] Variant Management (Specs, Images, Stock, Discount)
- [x] User Profile (Avatar, Password Change)
- [x] Address Management (CRUD, Default, Soft-delete, Pincode Validation)
- [x] Product Catalog (List, Detail, Search, Multi-select Filters)

### Phase 2 — E-Commerce (✅ Complete)
- [x] Wishlist (Offcanvas, AJAX, Profile Sync)
- [x] Cart Management (Stock Validation, Login Redirect, Public API)
- [x] Checkout UI (3-Step Stepper, Address Select, Summary)
- [x] Order Placement (COD, Atomic Transactions, Stock Deduction)
- [x] Inventory Management (Centralized Service, InventoryLog Audit)
- [x] Order Success Page (Animated SVG Confirmation)
- [x] User Order History & Tracking (List, Detail, Item Timeline, Invoice PDF)
- [x] Admin Order Management (Status Cascade, Return Review, Detail View)
- [x] Return System (Eligibility Rules, Photo Upload, Admin Approve/Reject)

### Phase 3 — Payments & Financial (✅ Complete)
- [x] Transaction Ledger (Universal model, GenericFK, audit trail)
- [x] Razorpay Integration (Order creation, Signature verification, Callback handling)
- [x] Wallet System (Credit/Debit, Balance snapshots, Row locking)
- [x] Order Cancellation (Item-level, Stock restore, Auto-refund initiation)
- [x] Refund Management (Admin approve/reject, **Instant cancel refunds** to wallet)
- [x] Payment Failure Handling (FAILED status, Failure page)
- [x] Admin Transaction Dashboard (List, Detail, Search, Filters)
- [x] User Wallet Page (Balance, Transaction history, Tabs)
- [x] Consistent Monetary Formatting (`floatformat:2` everywhere)

### Phase 4 — Offers & Growth (🔄 In Progress)
- [x] Offers & Discounts (Product/Category/Brand offers, best-offer pricing)
- [x] Admin Offer Management (List, Add, Edit, Delete with filters & stat cards)
- [x] Coupon System (Code-based coupons, checkout integration, per-user limits, order integration, proportional refunds)
- [ ] Referral Program
- [x] Sales Report (Date filters, Summary stats, PDF & Excel download)
- [ ] Email Notifications (Order updates, Refund status)

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">
  <strong>Built with ❤️ for luxury watch enthusiasts</strong>
</p>
