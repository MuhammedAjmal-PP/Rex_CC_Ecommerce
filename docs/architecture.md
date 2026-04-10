# Architecture & Data Models

---

## Data Models

### `accounts`

| Model | Key Fields |
|-------|-----------|
| `CustomUser` | `email` (unique, `USERNAME_FIELD`), `referral_code` (auto `REX-XXXXXX`), `referred_by` (self-FK), `avatar` (Cloudinary) |
| `PasswordReset` | `reset_id` (UUID), `created_at` — admin password reset flow (10-min expiry link) |
| `BlacklistedEmail` | Emails replaced via the email-change flow — can never be reregistered by anyone |

### `catalog`

| Model | Key Fields |
|-------|-----------|
| `Brand` | `name`, `slug` (auto), `logo` (Cloudinary), `is_active` |
| `Category` | `name`, `slug` (auto), `is_active` |
| `Product` | `brand` (FK·PROTECT), `category` (M2M), `is_deleted` (soft), `is_drafted` |
| `ProductVariant` | `sku` (uppercase regex), `dial_color`, `strap_color`, `strap_material`, `case_material`, `movement_type`, `case_size_mm` (15–65 mm), `price`, `discount_rate`, `stock`, `is_deleted`, `is_featured`, `is_drafted` |
| `ProductImage` | `variant` (FK), `is_primary` (DB-level unique constraint per variant) |
| `InventoryLog` | `change` (±), `stock_before`, `stock_after`, `reason`, `actor` (FK), `reference_object` (GenericFK). DB-validates `stock_after == stock_before + change` in `clean()` + `save()`. |

### `orders`

| Model | Key Fields |
|-------|-----------|
| `Order` | `order_number` (auto `ORD-XXXXXXXXXX`), `billing_address` & `shipping_address` (JSONField snapshots), `sub_total`, `tax`, `discount`, `shipping_fee`, `grand_total`, `coupon` (FK), `coupon_discount`, `coupon_revoke`, `cart_snapshot` (JSONField — used in Razorpay two-phase flow), `status`, `status_updated_at` |
| `OrderItem` | `order` (FK), `product_variant` (FK·SET_NULL), `quantity`, `price`, `original_price` (MRP at order time), `status`, `status_updated_at` |
| `Return` | `return_number` (auto `RE-XXXXXX`), `order_item` (OneToOne), `status`, `reason_code`, `comment`, `admin_note` |
| `ReturnImage` | `return_request` (FK), `image` (Cloudinary `order_return/`) — up to 3 per return |

### `payments`

| Model | Key Fields |
|-------|-----------|
| `Transaction` | `transaction_id` (auto `TXN` + 13 hex chars), `user` (FK), `transaction_type`, `payment_method`, `amount`, `status`, `content_object` (GenericFK), `gateway_order_id`, `gateway_payment_id`, `gateway_signature`, `note` |

**DB Indexes on `Transaction`:**
```python
Index(fields=["user", "-created_at"])
Index(fields=["content_type", "object_id"])
Index(fields=["transaction_type", "status"])
```

### `users`

| Model | Key Fields |
|-------|-----------|
| `Address` | `id` (UUID PK), `user` (FK), `full_name`, `phone_number`, `address_line_1/2`, `city`, `state`, `postal_code`, `label`, `is_default`, `is_active` (soft-delete) |
| `Cart` | `user` (OneToOne) |
| `CartItem` | `cart` + `product_variant` (unique together), `quantity` |
| `Wishlist` | `user` (OneToOne) |
| `WishlistItem` | `wishlist` + `product_variant` (unique together), `added_at` |
| `Wallet` | `user` (OneToOne), `balance`, `is_active` |
| `WalletTransaction` | `transaction` (OneToOne → `payments.Transaction`), `wallet` (FK), `label` (`CREDIT`/`DEBIT`), `balance_before`, `balance_after` |

### `offers` / `coupons`

| Model | Key Fields |
|-------|-----------|
| `Offer` | `offer_type` (`PRODUCT`/`CATEGORY`/`BRAND`), `discount_type` (`PERCENTAGE`), `discount_value`, `start_date`, `end_date`, `is_active`, M2M to `products`, `categories`, `brands`. `is_valid` property. |
| `Coupon` | `code` (auto-uppercased, min 3 chars), `discount_type` (`PERCENTAGE`/`FIXED`), `discount_value`, `min_order_amount`, `max_discount_amount`, `usage_limit`, `per_user_limit`, `used_count`, `is_deleted` (soft). `calculate_discount()` method. |
| `CouponUsage` | `coupon` (FK), `user` (FK), `order` (OneToOne), `used_at` |

### `reviews`

| Model | Key Fields |
|-------|-----------|
| `Review` | `user` (FK), `product` (FK), `rating` (1–5, validated), `title` (120 chars), `comment` (1000 chars), `is_active` (soft-delete / moderation). `UniqueConstraint(user, product)` — one review per user per product. Only users with a `DELIVERED` OrderItem for the product can submit a review. |

---

## Order & Item Status Flows

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
                                                                                → CANCELLED
  PENDING → CANCELLED (pre-shipment)
  DELIVERED → RETURN_REQUESTED → RETURNED
                               → DELIVERED (rejected)
```

---

## Design Decisions

### Why GenericFK on `Transaction`?
One `Transaction` model serves every money movement — order payments, cancellation refunds, return refunds, wallet top-ups, and referral rewards. Using a `GenericForeignKey` lets each transaction point to its source object (Order, OrderItem, Return, CustomUser) without separate tables.

### Why `select_for_update()` on Wallet?
Wallet credits and debits use row-level locking to prevent race conditions when two requests (e.g. a payment + a refund) try to update the same wallet balance simultaneously. All wallet operations are wrapped in `transaction.atomic()`.

### Why `cart_snapshot` on Order?
Razorpay payments are a two-phase flow. Phase 1 opens the Razorpay modal (no items created yet). Phase 2 fires after the callback. The `cart_snapshot` JSONField stores the cart state between phases, so items are only created and stock is only deducted after payment is confirmed.

### Why `InventoryLog` validated at the DB level?
Every stock change writes an `InventoryLog` entry. The constraint `stock_after == stock_before + change` is checked in `clean()` which is called from `save()`. This catches bugs where stock math is wrong before they silently corrupt data.

### Why soft-delete on `Product`, `ProductVariant`, `Coupon`, `Address`?
Hard deletes would break order history (a deleted variant's name would disappear from old orders). Soft-delete preserves referential integrity while hiding the record from active queries. `OrderItem.product_variant` uses `SET_NULL` as an additional safety net for variants that are hard-deleted during cleanup.

### Why `BlacklistedEmail`?
When a user changes their email, the old email is blacklisted. Without this, someone could register a new account with the previous email of an existing user — potentially re-triggering OAuth flows or impersonating someone's old identity.
