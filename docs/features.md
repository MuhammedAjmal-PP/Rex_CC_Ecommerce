# Feature Deep-Dives

---

## 🔐 Authentication & Security

### User Model — `accounts.CustomUser`

- Email is the **username field** (`USERNAME_FIELD = "email"` — no `username` column)
- **Referral code**: auto-generated `REX-XXXXXX` on first save (10 retries for uniqueness)
- **Avatar**: Cloudinary upload with 5 MB size and extension validation; old image is deleted from Cloudinary on replacement

### OTP / Email Verification

- Powered by `django-allauth` with `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`
- 6-digit OTP delivered via Gmail SMTP; expires after 24 hours
- `ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True` — user is logged in immediately after confirming

### Email Change Flow (`accounts/signals.py`)

When a user changes their email and confirms the new address via the allauth `email_confirmed` signal:
1. New email is promoted to primary via `email_address.set_as_primary()`
2. Old email is written to `BlacklistedEmail` (reason: `EMAIL_CHANGED`)
3. Old `AllauthEmailAddress` row is deleted
4. No one — including the original owner — can ever register with the blacklisted email again

### Google OAuth

- `django-allauth` provider: Google (scopes: `profile`, `email`)
- Credentials configured via `GOOGLE_CLIENT_ID` and `GOOGLE_SECRET_KEY` env vars
- Authorised redirect URI (development): `http://localhost:8000/accounts/google/login/callback/`

### Custom Middleware

| Middleware | Purpose |
|-----------|---------|
| `AuthFlowRedirectMiddleware` | Redirects active users away from `/accounts/inactive/`; guards password-reset and confirm-email pages |
| `BlockUnusedAllauthURLsMiddleware` | Raises `Http404` for allauth paths not used by this app (reauthenticate, email management, login code, etc.) |

### Admin Access

- Separate admin login at `/adminpanel/accounts/login/`
- All admin views protected by `@user_passes_test(lambda u: u.is_superuser)`
- `@superuser_only_redirect` decorator bounces superusers away from user-facing login/register views

### Production Security (`DEBUG=False`)

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
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

`pack_variants(variants, offer_data=None)` is the single authoritative function that enriches any variant queryset with computed display fields:

```
variant.primary_image       → ProductImage | None
variant.discount_percentage → int  (0–100, best rate wins)
variant.discount_amount     → Decimal
variant.final_price         → Decimal (price − discount_amount)
```

**Best-discount resolution** (`_best_discount`) — evaluated in priority order:
1. `variant.discount_rate` (the variant's own field)
2. Active **Product** offers whose products include this variant's product
3. Active **Category** offers whose categories overlap this product's M2M categories
4. Active **Brand** offers whose brands include this product's brand

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

`InventoryLog` is validated at the DB level: `stock_after == stock_before + change` is enforced in `clean()` called from `save()`.

### Auto-Draft Logic

`manage_product_draft_status()` is called whenever a variant is deleted or drafted. If no active, non-deleted variants remain, the parent `Product` is auto-drafted and the admin is shown a warning.

---

## 🏷️ Offers & Discounts

### Offer Model

| Field | Notes |
|-------|-------|
| `offer_type` | `PRODUCT`, `CATEGORY`, or `BRAND` |
| `discount_type` | `PERCENTAGE` |
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
- `discount_value` must be between 1 and 100

---

## 🎟️ Coupon System

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
- `compute_refund` functions recalculate coupon share proportionally per item for accurate partial refunds

---

## 🛒 Cart & Wishlist

### Cart — `users/cart/`

| Function | Description |
|----------|-------------|
| `view_cart()` | Displays items with real-time stock limits |
| `add_cart()` | Adds items; redirects unauthenticated users to login (preserves `next`) |
| `update_cart()` | AJAX quantity update, respects stock cap |
| `get_variant_stock()` | **Public API** — returns current stock JSON for frontend checks |
| `fetch_cart()` | Fetches `CartItem` queryset with all relations prefetched |
| `compute_cart_summary()` | Calculates MRP, discount, sub_total, 18% GST, shipping (₹100/item), grand_total |
| `build_cart_summary()` | Builds items list for cart page and offcanvas |
| `summary_to_json()` | Converts summary dict → JSON-safe format for AJAX |

Key behaviours:
- Max 5 units per cart item (`MAX_QUANTITY_PURCHASE_PER_ITEM = 5`)
- Adding to cart removes the item from wishlist automatically
- All pricing uses `final_price` from `pack_variants()` (offer-aware)

### Wishlist — `users/wishlist/`

- `toggle_wishlist()` — AJAX add/remove with heartbeat animation response
- `remove_wishlist_item()` — explicit remove from offcanvas or wishlist page
- Real-time counter in profile dashboard
- Offcanvas panel accessible from any page without navigation

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
  └── razorpay_callback()
      verify_razorpay_signature() HMAC-SHA256
      create_items_from_snapshot() — lock, validate, create, deduct stock
      mark Transaction PAID → Order PLACED
```

### Razorpay Retry Flow

```
retry_razorpay_payment()
  ├── Validate stock from cart_snapshot
  ├── Reset Order: FAILED → PLACED
  ├── Create new Transaction (PENDING)
  ├── create_razorpay_order() → new gateway order
  └── Return JSON for frontend modal
```

### Failed Order Expiry (Background Task)

`expire_failed_order(order_id)` fires after `FAILED_ORDER_EXPIRY_SECONDS`:

| Step | Action |
|------|--------|
| 1 | Guard: exit if order is no longer FAILED |
| 2 | Restore cart from `cart_snapshot` (quantities capped at `MAX_QUANTITY_PURCHASE_PER_ITEM`) |
| 3 | `revoke_coupon_usage(order)` if coupon was applied |
| 4 | Bulk-cancel any PENDING/FAILED transactions for this order |
| 5 | `change_order_status(FAILED → EXPIRED)` |
| 6 | Clear `cart_snapshot` (set to `None`, save) |

---

## 🔄 Order Status Engine

### Transition Engine — `orders/service/status.py`

- `ORDER_ALLOWED_TRANSITIONS` and `ADMIN_ORDER_ALLOWED_TRANSITIONS` — explicit allowed-next-state maps
- **`change_order_status(order, to_status)`**:
  1. Validates transition is allowed
  2. Updates `order.status` + `status_updated_at`
  3. **COD Auto-Pay**: if `to_status == "DELIVERED"` and payment is COD + PENDING → marks Transaction PAID
  4. **Cascade**: calls `_cascade_order_to_items()` to walk all items through every intermediate status step
- **`change_order_item_status(order_item, to_status)`**:
  1. Validates transition is allowed
  2. Updates item status
  3. **Reverse sync**: `_sync_order_status()` derives the correct order-level status from all sibling items

### Cancellation — `orders/views/user/cancel_order.py`

- Cancellable statuses: `PENDING`, `CONFIRMED`, `PACKING`, `READY`
- Item-level selection (user picks which items to cancel)
- `update_stock(+qty, ORDER_CANCELLED)` per cancelled item
- **Prepaid instant refund**: Razorpay or Wallet orders → `compute_cancel_refund(item)` → `credit_wallet()` immediately
- COD orders: no refund (nothing was charged)
- `revoke_coupon_if_invalid()` called if coupon no longer meets minimum after cancellation

### Returns — `orders/views/user/return_order.py`

Eligibility (`can_return_item()`):
- `status == "DELIVERED"`
- Within 7 days of delivery (`status_updated_at`)
- No existing return request for this item

Return form: reason dropdown (10 reason codes), comment, up to 3 photo uploads with inline preview.

On admin approval: `change_order_item_status(RETURN_REQUESTED → RETURNED)` + `update_stock(+qty, RETURNED)` + `initiate_refund()` → `complete_refund()` → wallet credit.

---

## 💳 Payments & Financial Ledger

### Universal `Transaction` Model

Every money movement creates exactly one `Transaction`:

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
fail_transaction(transaction, note)          # PENDING → FAILED
```

### Razorpay Service — `payments/razorpay_service.py`

```python
create_razorpay_order(amount_paise, receipt)
    # Calls Razorpay API · payment_capture=1 (auto-capture)

verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    # HMAC-SHA256 via razorpay.Client.utility.verify_payment_signature()
    # Returns True / False
```

---

## 💰 Wallet System

### Service API — `users/wallet/service.py`

```python
get_or_create_wallet(user)             # Auto-provisions wallet with zero balance
can_pay_with_wallet(user, amount)      # Returns bool — checks is_active + balance

credit_wallet(user, amount, transaction_obj=None)  # +balance, creates WalletTransaction(CREDIT)
debit_wallet(user, amount, transaction_obj=None)   # -balance, creates WalletTransaction(DEBIT)
```

Safety guarantees:
- Both `credit_wallet` and `debit_wallet` use `select_for_update()` on the `Wallet` row
- Wrapped in `db_transaction.atomic()`
- `InsufficientBalanceError` raised if balance < amount
- `WalletInactiveError` raised if the wallet is deactivated

`WalletTransaction` stores `balance_before` and `balance_after` — an immutable snapshot of every operation, linked OneToOne to the universal `Transaction`.

---

## 🎁 Referral Programme

**Location:** `accounts/signals.py`

- Every `CustomUser` gets a unique `REX-XXXXXX` code on account creation
- A new user can enter a referral code at signup (stored as `referred_by` FK)
- On first-time email confirmation (`email_confirmed` signal):
  - Guard: checks if a `REFERRAL_REWARD` Transaction already exists for this user (prevents duplicate rewards)
  - Both referee (new user) and referrer (existing user) receive **₹1,000 wallet credit**
  - Both `create_transaction(REFERRAL_REWARD)` and `credit_wallet()` are inside a single `transaction.atomic()` block

---

## ⏱️ Background Tasks

**Location:** `orders/tasks.py`

Uses `django-tasks-db` (`DatabaseBackend`) — tasks stored in PostgreSQL, processed by the `worker` container running `python manage.py db_worker`.

### `expire_failed_order(order_id)`

Enqueued at Razorpay order creation. Fires after `FAILED_ORDER_EXPIRY_SECONDS` (default: 5 hours, use `120` for dev):

| Step | Action |
|------|--------|
| 1 | Guard: exit if order is no longer `FAILED` |
| 2 | Restore cart from `cart_snapshot` (quantities capped at `MAX_QUANTITY_PURCHASE_PER_ITEM`) |
| 3 | `revoke_coupon_usage(order)` if coupon was applied |
| 4 | Bulk-cancel any `PENDING`/`FAILED` transactions for this order |
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
- Return list and detail: approve (→ `RETURNED` + stock restore + wallet refund) or reject
- Invoice PDF download

</details>

<details>
<summary><strong>📊 Sales Report — orders/views/admin/sales_report.py</strong></summary>

- **Filters**: All · Today · This Week (7d) · This Month (30d) · Custom date range
- **Stat cards**: Total Orders, Total Amount, Total Offer Discount, Total Coupon Discount
- **Table**: Order #, Date, Customer, Payment Method, Discount, Coupon, Grand Total — paginated 15/page
- **PDF**: WeasyPrint — header, summary grid, full unpaginated table, generation timestamp
- **Excel**: openpyxl — branded header, summary rows, styled column headers, currency formatting
- Download links carry active filter querystring — exports always match the on-screen view
- Excludes CANCELLED and FAILED orders from all metrics

</details>

<details>
<summary><strong>💳 Transaction & Refund Administration — payments/views.py</strong></summary>

- Transaction list: search + filter by type / status / payment method
- Transaction detail: full info + gateway IDs + audit timestamps
- Refund list (`CANCELLATION_REFUND` + `RETURN_REFUND`): status tracking
- Refund detail: Approve (→ `complete_refund()` → wallet credit) or Reject (→ `fail_transaction()`)

</details>

---

## ⭐ Product Reviews

### Review Model

| Field | Notes |
|-------|-------|
| `user` | FK to `CustomUser` |
| `product` | FK to `Product` (one review per user per product) |
| `rating` | 1–5 (validated with `MinValueValidator` / `MaxValueValidator`) |
| `title` | Short summary (max 120 chars) |
| `comment` | Detailed review text (max 1000 chars) |
| `is_active` | Soft-delete / moderation flag |

**DB constraint:** `UniqueConstraint(fields=["user", "product"])` — prevents duplicate reviews.

### Eligibility — `reviews/services.py`

```python
can_review(user, product)
    # True only if:
    #   1. User has at least one DELIVERED OrderItem for any variant of the product
    #   2. User has NOT already submitted an active review for this product

get_product_reviews(product, limit=None)
    # Active reviews, newest first, with user select_related

get_ratings_summary(product)
    # Returns: {average, total_reviews, distribution: {5: %, 4: %, ...}}

get_user_review(user, product)
    # Returns existing review or None
```

### AJAX Endpoint

| URL | Method | Description |
|-----|--------|-------------|
| `/reviews/<product_id>/submit/` | POST | Submit a new review (login required) |

Returns JSON with the rendered review data (author, date, rating, title, comment) for live DOM insertion without page reload.

---

## ⚙️ Business Rules & Configuration

All configurable via environment variables — set them in `.env` (see `sample.env` for the full reference). Every setting has a default so you only need to override what you want to change.

| Setting | Env Variable | Default | Description |
|---------|-------------|---------|-------------|
| `MAX_ADDRESSES_PER_USER` | `MAX_ADDRESSES_PER_USER` | `5` | Enforced in `Address.clean()` |
| `MAX_QUANTITY_PURCHASE_PER_ITEM` | `MAX_QUANTITY_PURCHASE_PER_ITEM` | `5` | Enforced in cart add and snapshot restore |
| `SHIPPING_CHARGE` | `SHIPPING_CHARGE` | `₹100` | Flat charge per item, per order |
| `GST_RATE` | `GST_RATE` | `18` (%) | GST rate applied to all orders |
| `STORE_STATE` | `STORE_STATE` | `KERALA` | Store state for GST invoicing |
| `STORE_STATE_CODE` | `STORE_STATE_CODE` | `32` | GST state code (32 = Kerala) |
| `DEFAULT_WATCH_HSN` | `DEFAULT_WATCH_HSN` | `9102` | HSN code for wristwatches |
| `WALLET_TOPUP_MIN` | `WALLET_TOPUP_MIN` | `₹5,000` | Minimum wallet top-up amount |
| `WALLET_TOPUP_MAX` | `WALLET_TOPUP_MAX` | `₹75,000` | Maximum wallet top-up amount |
| `IMAGE_MAX_SIZE_MB` | `IMAGE_MAX_SIZE_MB` | `5 MB` | Max upload size for all image fields |
| `FAILED_ORDER_EXPIRY_SECONDS` | `FAILED_ORDER_EXPIRY_SECONDS` | `18000` (5 h) | Use `120` for fast dev testing |
| `PHONENUMBER_DEFAULT_REGION` | `PHONENUMBER_DEFAULT_REGION` | `IN` | ISO 3166-1 alpha-2 country code |
| `REFERRAL_REWARD_AMOUNT` | `REFERRAL_REWARD_AMOUNT` | `₹1,000` | Wallet credit paid to both referee and referrer on a successful referral |
| `RETURN_WINDOW_DAYS` | `RETURN_WINDOW_DAYS` | `7` | Days after delivery within which a return request can be raised |
| `COD_MIN_ORDER_AMOUNT` | `COD_MIN_ORDER_AMOUNT` | `₹50,000` | Minimum order amount required for Cash on Delivery; orders below must use online payment |

