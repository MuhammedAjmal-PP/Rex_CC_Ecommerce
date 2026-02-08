<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Cloudinary-Media-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary">
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
- [User Features](#-user-features)
- [Cart Management](#-cart-management)
- [Wishlist System](#-wishlist-system)
- [Checkout & Orders](#-checkout--orders)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [roadmap](#-roadmap)

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
| Checkout | 🔄 In Progress | Address selection, Order summary |
| Orders | 🔄 Planned | Order placement, Tracking, History |

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
    - **Optimized UI**: Horizontal scrolling tables for complex data, unified form templates.
</details>

<details>
<summary><strong>🚚 Order Administration (Backend)</strong></summary>

**Location:** `orders/admin.py`

- **Order Tracking**: Full visibility of Orders and OrderItems.
- **Timeline**: `StatusTimeline` generic relation tracks every status change (Pending -> Shipped -> Delivered).
- **Audit Trail**: Records *who* changed the status (Admin/System) and *when*.
</details>

---

## 👤 User Features

### Profile & Address
- **Profile**: Avatar cropping (Cropper.js), password management.
- **Address**: Limit max addresses (default 5), auto-default selection logic, soft delete to preserve order history.

### Shopping Experience
- **Catalog**: Faceted search (Brand, Category, Color, Movement), sorting, and pagination.
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

**Location:** `orders/views/user/checkout.py`

### Current Status
- ✅ **Checkout Page**: Renders order summary and address selection.
- ✅ **Address Selection**: Users can choose from saved addresses or add new ones inline.
- ✅ **Order Summary**: Calculates Subtotal, Tax, Shipping, and Total dynamically.

### Pending Implementation
- 🔄 **Payment Integration**: Razorpay/Stripe or COD logic.
- 🔄 **Place Order**: Transaction handling to reduce stock and create Order records.
- 🔄 **Order History**: User dashboard to view past orders.

---

## 🏗️ Tech Stack

```
Backend          Frontend           Storage          Tools
─────────────    ─────────────      ─────────────    ─────────────
Django 6.0       Bootstrap 5.3     PostgreSQL       Black (formatter)
django-allauth   Vanilla CSS       Cloudinary       djLint (templates)
                 Cropper.js                         Git
                 Material Icons
```

---

## 📁 Project Structure

```
Rex_CC_Ecommerce/
├── core/                  # Core modules (renamed from pages)
│   ├── validators.py      # Shared validators (moved from utils)
│   └── templates/core/    # Base templates (admin/user)
│
├── accounts/              # Authentication & User Model
├── catalog/               # Products, Brands, Categories, Variants
├── orders/                # Order models & checkout logic
│   ├── admin.py           # Admin configuration for orders
│   └── views/user/        # Checkout & placement views
│
├── users/                 # User domain
│   ├── cart/              # Cart logic & views
│   ├── wishlist/          # Wishlist logic
│   └── user_profile/      # Address & Profile management
│
└── rexcc_project/         # Project settings & URL conf
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Cloudinary Account

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
# Edit .env with your credentials

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
- [x] Address Management (CRUD, Default, Soft-delete)
- [x] Product Catalog (List, Detail, Search, Filter)

### Phase 2 — E-Commerce (🔄 In Progress)
- [x] Wishlist (Offcanvas, AJAX, Profile Sync)
- [x] Cart Management (Stock Validation, Login Redirect, Public API)
- [x] Checkout UI (Address Select, Summary)
- [ ] Order Placement Logic
- [ ] User Order History
- [ ] Admin Order Management UI
- [ ] Inventory Management (Stock decrement)

### Phase 3 — Payments & Growth
- [ ] Razorpay/Stripe Integration
- [ ] Coupon System
- [ ] Wallet & Rewards
- [ ] Referral Program

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">
  <strong>Built with ❤️ for luxury watch enthusiasts</strong>
</p>
