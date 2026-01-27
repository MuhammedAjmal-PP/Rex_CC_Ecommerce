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
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Next Steps - Implementation Plan](#-next-steps---implementation-plan)

---

## ✨ Features Overview

| Feature | Status | Description |
|---------|--------|-------------|
| Authentication System | ✅ Complete | Email, OTP, Google OAuth, Password Reset |
| Admin Panel | ✅ Complete | User, Brand, Category, Product, Variant Management |
| User Profile | ✅ Complete | Profile settings, Avatar with crop |
| Address Management | ✅ Complete | Full CRUD, Default selection, Soft delete |
| Product Catalog | ✅ Complete | Listing, Detail, Search, Filter, Pagination |
| Cart Management | 🔄 Next | Add/Remove, Quantity, Stock validation |
| Checkout System | 🔄 Next | Address, Summary, COD payment |
| Order Management | 🔄 Next | User & Admin order handling |

---

## 🔐 Authentication System

### Implementation Details

| Feature | Description | How It Works |
|---------|-------------|--------------|
| **Email-Based Auth** | Custom `CustomUser` model with email as primary identifier | Uses Django's `AbstractBaseUser`, email replaces username |
| **OTP Verification** | Email verification for new accounts | 6-digit OTP sent via SMTP, stored in session with expiry |
| **Google OAuth** | One-click sign-in via `django-allauth` | OAuth2 flow with GOOGLE_CLIENT_ID/SECRET |
| **Password Reset** | Secure email-based recovery | Token-based reset links with 24hr expiry |
| **Admin Auth** | Separate superuser-only portal | `@user_passes_test(lambda u: u.is_superuser)` decorator |

### Key Files
- `accounts/models.py` - CustomUser model with email authentication
- `accounts/views/admin_views/admin_auth.py` - Admin login, logout, password reset
- `accounts/decorators.py` - Custom authentication decorators
- `accounts/validators.py` - Input validation (password strength, email format)

---

## 🛠️ Admin Panel

<details>
<summary><strong>👥 User Management</strong></summary>

**Location:** `accounts/views/admin_views/user_management.py`

| Function | Description |
|----------|-------------|
| `user_list()` | Paginated listing with search & status filter |
| `user_profile_view()` | Detailed user profile with activity |
| `toggle_user_status()` | One-click active/inactive toggle |

**Features:**
- Paginated user listing using Django Paginator
- Search by email or name
- Filter by status (active/inactive)
- User profile view with activity details
</details>

<details>
<summary><strong>🏷️ Brand Management</strong></summary>

**Location:** `catalog/views/admin/brand.py`

| Function | Description |
|----------|-------------|
| `brands()` | List all brands with pagination |
| `brand_add()` | Create new brand with logo upload |
| `brand_edit()` | Edit brand with Cropper.js integration |
| `brand_delete()` | Soft delete with status toggle |

**Model Fields:** `name`, `slug` (auto-generated), `tagline`, `logo` (Cloudinary), `description`, `is_active`
</details>

<details>
<summary><strong>📁 Category Management</strong></summary>

**Location:** `catalog/views/admin/category.py`

| Function | Description |
|----------|-------------|
| `categories()` | List with AJAX-powered modals |
| `category_add()` | Create with auto-slug generation |
| `category_edit()` | Edit without page reload |
| `category_toggle()` | Toggle active status |

**Model Fields:** `name`, `slug` (auto-generated on save), `is_active`
</details>

<details>
<summary><strong>📦 Product Management</strong></summary>

**Location:** `catalog/views/admin/product.py`

| Function | Description |
|----------|-------------|
| `products()` | List with search, filter, pagination |
| `product_add()` | Create with thumbnail & multi-category |
| `product_edit()` | Edit with brand/category changes |
| `product_view()` | Detailed view with all variants |
| `product_delete_toggle()` | Soft delete with cascade to variants |
| `product_draft_toggle()` | Draft/publish toggle |

**Model Fields:** `name`, `slug`, `brand` (FK), `category` (M2M), `description`, `thumbnail`, `is_deleted`, `is_drafted`

**Logic:**
- Soft delete with `is_deleted` flag and `deleted_at` timestamp
- Draft mode prevents product from appearing on storefront
- Slug auto-generated from name on create, updated on name change
</details>

<details>
<summary><strong>🎨 Variant Management</strong></summary>

**Location:** `catalog/views/admin/product.py`

| Function | Description |
|----------|-------------|
| `variant_add()` | Create with watch specs & multi-image upload |
| `variant_edit()` | Edit specs, price, stock, images |
| `variant_view()` | Detailed view with image gallery |
| `variant_delete_toggle()` | Soft delete toggle |
| `variant_draft_toggle()` | Draft/publish toggle (requires min 3 images) |

**Model Fields:**
- **Identity:** `sku` (unique), `product` (FK)
- **Watch Specs:** `dial_color`, `strap_color`, `strap_material`, `case_material`, `movement_type`, `case_size_mm`
- **Pricing:** `price`, `discount_percentage` (0-100)
- **Inventory:** `stock`
- **Status:** `is_featured`, `is_drafted`, `is_deleted`

**`final_price` Property:**
```python
@property
def final_price(self):
    if self.discount_percentage > 0:
        discount = (self.price * self.discount_percentage) / 100
        return self.price - discount
    return self.price
```

**ProductImage Model:**
- Multi-image upload with primary image selection
- Unique constraint: only one primary image per variant
- Cloudinary storage with auto-deletion on remove
</details>

---

## 👤 User Features

### Profile Management

**Location:** `users/user_profile/views/profile_settings.py`

| Function | Description |
|----------|-------------|
| `profile()` | Dashboard displaying user info and avatar |
| `edit_profile()` | Edit name, phone, avatar with Cropper.js crop |
| `change_password()` | Password change with current password validation |

### Address Management

**Location:** `users/user_profile/views/address_management.py`

| Function | Description |
|----------|-------------|
| `user_address()` | List all active addresses |
| `add_address()` | Add new address with validation, max limit check |
| `edit_address()` | Edit existing address |
| `delete_address()` | Soft delete via AJAX (sets `is_active=False`) |
| `toggle_default_address()` | Set address as default |

**Model Fields:**
- **Identity:** `id` (UUID), `user` (FK)
- **Contact:** `full_name`, `phone_number` (PhoneNumberField)
- **Location:** `address_line_1`, `address_line_2`, `city`, `state`, `postal_code`, `country`
- **Meta:** `label` (Home/Work/Custom), `is_default`, `is_active`

**Key Logic:**
- `MAX_ADDRESSES_PER_USER` setting limits total addresses
- First address automatically set as default
- When default is deleted, most recent active becomes default
- `AddressActiveManager` custom manager filters soft-deleted (`is_active=False`)

### Product Catalog (User)

**Location:** `catalog/views/user/product.py`

| Function | Description |
|----------|-------------|
| `product_list()` | Variant-based listing with search, filter, sort, pagination |
| `product_detail()` | Product page with variant selection, images, specs, stock status |

**product_list() Features:**
- Search by: product name, brand, category, SKU, dial color, strap color, movement
- Filter by: category (multi-select), brand (multi-select), price range
- Sort by: price (low/high), name (A-Z/Z-A), new arrivals, featured
- Pagination: 15 variants per page
- Only shows: non-deleted, non-drafted, active brand & category

**product_detail() Features:**
- Variant selection via query param (`?variant=SKU`)
- Image gallery with primary image
- Stock status: "In Stock" / "Only X left!" / "Out of Stock"
- Price display with original price & discount percentage
- Dynamic breadcrumbs
- Related products from same categories
- Specifications table (movement, case, dial, strap)

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
├── accounts/              # User & admin authentication
│   ├── views/admin_views/ # Admin auth & user management
│   ├── templates/         # Auth templates (login, signup, reset)
│   ├── models.py          # CustomUser, PasswordReset
│   └── forms.py           # Auth forms with validation
│
├── catalog/               # Product catalog
│   ├── models.py          # Brand, Category, Product, ProductVariant, ProductImage
│   ├── views/admin/       # Admin CRUD (brand, category, product)
│   ├── views/user/        # product_list, product_detail
│   └── templates/         # Admin & user product templates
│
├── pages/                 # Static pages & base templates
│   ├── views/user_pages.py  # Homepage with featured products
│   └── templates/         # Base layouts (admin, user)
│
├── users/                 # User-specific features
│   └── user_profile/
│       ├── models.py      # Address model
│       ├── views/         # Profile & address management
│       └── templates/     # Profile templates
│
├── utils/                 # Shared utilities
│   └── validators.py      # Custom validation functions
│
└── rexcc_project/         # Project settings
    ├── settings.py        # Django configuration
    └── urls.py            # Root URL configuration
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

### Environment Variables

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/rexcc

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=your-key
CLOUDINARY_API_SECRET=your-secret

# Email (Gmail SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# App Settings
MAX_ADDRESSES_PER_USER=5
```

---

## 🔒 Security Features

- ✅ CSRF Protection on all forms
- ✅ `@never_cache` on sensitive views
- ✅ `@user_passes_test` for superuser verification
- ✅ Session-based authentication
- ✅ Secure password hashing (PBKDF2)
- ✅ Email verification required
- ✅ UUID primary keys for addresses

---

## 📋 Next Steps - Implementation Plan

### c. Cart Management
- [ ] **Add to Cart** - Add variant to cart, if product/category is blocked or unlisted, prevent addition even from product detail page
- [ ] **Quantity Update** - If product already in cart, increase quantity instead of adding duplicate
- [ ] **Wishlist Integration** - When adding to cart, auto-remove from wishlist if exists
- [ ] **Increment/Decrement** - Validate against stock left in inventory
- [ ] **Max Quantity Limit** - Handle maximum quantity per product per user
- [ ] **Out of Stock Display** - Show disabled state, prevent checkout for unavailable items
- [ ] **Cart Listing** - Display all cart items with product image, price, quantity

### d. Checkout Page
- [ ] **Address Selection** - Display user addresses, allow add/edit, ensure one is selected as default
- [ ] **Product Summary** - Show product image, quantity, item total
- [ ] **Price Breakdown** - Display taxes (optional), applicable discount, final price summary
- [ ] **Place Order (COD)** - Cash on Delivery payment method
- [ ] **Order Success Page** - Thank you message with illustration, buttons to order detail and continue shopping

### e. Order Management (User)
- [ ] **Order Listing** - List orders with unique orderID (not MongoDB `_id`), status, order date
- [ ] **Order Detail** - Detailed view of each order
- [ ] **Cancel Order/Item** - Cancel entire order or specific products, restore stock on cancellation, ask for optional reason
- [ ] **Return Order** - Available only when delivered, mandatory reason required
- [ ] **Invoice Download** - Generate PDF invoice for each order
- [ ] **Search Orders** - Find specific orders by orderID or product name

### f. Order Management (Admin)
- [ ] **Order Listing** - Descending by order date
- [ ] **Order Details** - Show orderID, date, user details, view button for detailed view
- [ ] **Status Management** - Change status (pending, shipped, out for delivery, delivered, cancelled)
- [ ] **Search/Sort/Filter** - With clear search functionality
- [ ] **Pagination** - Paginated order list

### g. Inventory/Stock Management
- [ ] **Stock Tracking** - Track stock at variant level
- [ ] **Stock Updates** - Decrement on order, increment on cancellation/return
- [ ] **Low Stock Indicators** - Visual indicators in admin panel

---

## 📋 Full Roadmap

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

### Phase 2 — E-Commerce (🔄 Next)
- [ ] Cart Management
- [ ] Wishlist
- [ ] Checkout Flow
- [ ] Order Management (User & Admin)
- [ ] Invoice Generation
- [ ] Inventory Management

### Phase 3 — Payments & Growth
- [ ] Razorpay/Stripe Integration
- [ ] Coupon System
- [ ] Wallet & Rewards
- [ ] Referral Program

### Phase 4 — Enhancement
- [ ] Product Reviews
- [ ] Analytics Dashboard
- [ ] Notification System
- [ ] Support Tickets

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">
  <strong>Built with ❤️ for luxury watch enthusiasts</strong>
</p>
