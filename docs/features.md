# 🚀 Feature Deep-Dives

Technical breakdowns of Rex CC's core modules.

---

## 🛡️ Authentication & Identity

### Custom User Model
Email is the primary `USERNAME_FIELD` — no usernames.

- **Email Change Flow**: The old email is permanently logged in `BlacklistedEmail`, preventing re-registration on recycled addresses.
- **Middleware Guards**: `AuthFlowRedirectMiddleware` redirects authenticated users away from login pages and locks down sensitive endpoints.

### Google OAuth
Sign-in with Google via `django-allauth`. Configured through `GOOGLE_CLIENT_ID` and `GOOGLE_SECRET_KEY`.

---

## 💎 Dynamic Catalog & Offer Engine

### Offer-Aware Pricing
The `pack_variants` utility computes the best discount dynamically instead of hardcoding sale prices.

> [!NOTE]
> **Resolution Hierarchy:**
> 1. Variant's direct discount
> 2. Active Product-level Offers
> 3. Active Category-level Offers
> 4. Active Brand-level Offers

All active offers are evaluated in pure Python after a single DB fetch — no N+1 queries.

---

## 🎟️ Promotional Systems

### Coupons
`PERCENTAGE` or `FIXED` discount codes with `usage_limit`, `per_user_limit`, and optional `max_discount_amount` cap.

During checkout, coupons are validated using **row-level locking** (`select_for_update()`). This guarantees concurrent requests cannot exceed the usage limit.

Fixed-amount coupons are validated to be less than the `min_order_amount` to prevent zero-cost orders.

### Referral Rewards
New users register with a `REX-XXXXXX` code. On first email verification, ₹1,000 is credited to both referrer and referee wallets inside an atomic transaction.

---

## 🛒 Checkout & Order Placement

### The 3-Step Checkout
1. **Address Selection** — Choose or create a delivery address.
2. **Payment** — COD, Wallet, or Razorpay. Apply coupons.
3. **Review** — Final confirmation before placement.

### Razorpay Two-Phase Commit
1. **Phase 1**: Cart is serialized to `Order.cart_snapshot`. Razorpay modal opens. **No stock deducted yet.**
2. **Phase 2**: On HMAC-SHA256 verified callback, the snapshot is deserialized — inventory deducted and `OrderItems` created.

> [!TIP]
> A background worker runs `expire_failed_order()`. Abandoned Razorpay sessions are auto-cancelled after the configured expiry, and the cart is restored.

---

## 💳 Financial Ledger & Wallet

### Universal Transactions
Every monetary movement — payments, returns, refunds, top-ups, referral bonuses — is recorded in a single `Transaction` model via `GenericForeignKey`. This creates one auditable financial timeline.

### Digital Wallet
- All balance modifications enforce `atomic()` + `select_for_update()` row locking.
- Immutable `WalletTransaction` logs capture `balance_before` and `balance_after` for every movement.

---

## ⭐ Reviews

Purchase-verified product reviews. Only users with a `DELIVERED` order item for a product can leave a review.

- **1–5 star rating** with title and free-text comment.
- **One review per user per product** enforced by a `UniqueConstraint`.
- **Moderation** via `is_active` soft-delete flag.

---

## ❤️ Wishlist

Users can save product variants to a personal wishlist for quick access later. `WishlistItem` links directly to `ProductVariant`.

---

## 📦 Order Lifecycle Management

The `orders/service/status.py` state machine strictly controls order progression.

- **Cascading Updates**: Marking a parent `Order` as `SHIPPED` walks every associated `OrderItem` through its prerequisite statuses (`PACKING` → `READY` → `SHIPPED`).
- **Instant Refunds**: User cancellations on pre-paid items calculate proportional refunds (factoring in split coupons) and credit the wallet automatically.

---

## 🧾 PDF Invoicing

GST-compliant invoices are generated server-side using **WeasyPrint**. Invoices include:

- GSTIN, HSN codes, and CGST/SGST or IGST split based on store vs. delivery state.
- Line-item breakdown with applied discounts and shipping charges.
- Downloadable from the order detail page.
