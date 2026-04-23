# Feature Guide

This document summarizes what the platform provides from both customer and admin perspectives.

---

## 1) Authentication and accounts

- Email-first signup/login using Django allauth
- Mandatory email verification flow
- Google OAuth sign-in option
- Password reset flow for users and separate admin auth pages
- Email change protection with blacklisting of replaced addresses
- Referral code support with wallet rewards

---

## 2) Catalog and discovery

- Brand and category management
- Product and variant modeling for watch-specific attributes
- Variant-level pricing and discounts
- Rich image handling with primary image support
- Offer-aware pricing utilities for consistent price display

---

## 3) Pricing, offers, and coupons

### Offers
- Scoped offers: product, category, or brand
- Date-bound validity and active/inactive controls
- Validation rules to prevent invalid target combinations

### Coupons
- Fixed and percentage discount types
- Minimum order amounts and optional caps
- Global and per-user usage limits
- Coupon application/removal endpoints during checkout
- Revocation logic for invalidated post-order scenarios

---

## 4) Cart and wishlist

### Cart
- Add/update/remove items with stock checks
- Quantity restrictions by business rule
- Totals computation including tax and shipping
- Offer-aware line pricing

### Wishlist
- AJAX-based toggle experience
- Dedicated wishlist page and quick interactions

---

## 5) Checkout and orders

- Step-based checkout flow (address → payment → review)
- Address selection and inline address creation
- Payment method support:
  - Cash on Delivery
  - Wallet
  - Razorpay
- Atomic order creation workflows
- Order and order-item status tracking
- Order success/failure views and order history pages

---

## 6) Returns and cancellations

- Item-level cancellation paths
- Return request flow with reason capture
- Return image upload support
- Admin moderation for return decisions
- Refund handling integrated with transaction/wallet records

---

## 7) Wallet and transactions

- User wallet with running balance
- Debit/credit operations with transactional safeguards
- Financial ledger in a unified transaction model
- Admin views for transaction and refund management

---

## 8) Reviews

- Product rating and comment submission
- Purchase verification constraints
- One review per user-product pair policy
- Aggregate rating display support

---

## 9) Admin operations and reporting

- User management interface for administrators
- Catalog, offers, coupon, and order administration
- Sales report generation with export options
- Dashboard visualizations for business monitoring

---

## 10) Background processing

- Database-backed worker queue (`django-tasks-db`)
- Automated order/payment housekeeping tasks
- Worker runs independently from web process
