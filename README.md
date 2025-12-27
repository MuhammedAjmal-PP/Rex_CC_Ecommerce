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

## ✨ Features

### 🔐 Authentication System
| Feature | Description |
|---------|-------------|
| **Email-Based Auth** | Custom user model with email as primary identifier |
| **OTP Verification** | Email verification required for new accounts |
| **Google OAuth** | One-click sign-in with Google |
| **Password Reset** | Secure email-based password recovery |
| **Admin Auth** | Separate superuser-only admin login portal |

### 🛠️ Admin Panel

<details>
<summary><strong>👥 User Management</strong></summary>

- Paginated user listing with search
- Filter by status (active/inactive)
- User profile view with activity details
- One-click status toggle
</details>

<details>
<summary><strong>🏷️ Brand Management</strong></summary>

- Full CRUD operations
- Logo upload with Cropper.js integration
- Search and filter functionality
- Soft status toggle (active/inactive)
</details>

<details>
<summary><strong>📁 Category Management</strong></summary>

- AJAX-powered modal forms
- Real-time add/edit without page reload
- Automatic slug generation
- Status management
</details>

<details>
<summary><strong>📦 Product Management</strong></summary>

- Product catalog with thumbnails
- Multi-category assignment
- Soft delete & draft modes
- Rich text descriptions
</details>

<details>
<summary><strong>🎨 Variant Management</strong></summary>

- SKU-based identification
- Watch specifications (dial, case, strap, movement)
- Multi-image upload (min 3 for publishing)
- Primary image selection
- Stock tracking with visual indicators
- Featured & draft toggles
</details>

---

## 🏗️ Tech Stack

```
Backend          Frontend           Storage          Tools
─────────────    ─────────────      ─────────────    ─────────────
Django 6.0       Bootstrap 5.3     PostgreSQL       Black (formatter)
django-allauth   Vanilla CSS       Cloudinary       djLint (templates)
                 Cropper.js                         Git
```

---

## 📁 Project Structure

```
Rex_CC_Ecommerce/
├── accounts/              # User & admin authentication
│   ├── admin_views/       # Admin panel views
│   ├── templates/         # Auth templates
│   └── forms.py           # Custom forms
│
├── catalog/               # Product catalog
│   ├── models.py          # Brand, Category, Product, Variant
│   ├── views/admin/       # CRUD views
│   ├── static/            # CSS & JS
│   └── templates/         # Admin templates
│
├── pages/                 # Static pages & base templates
│   └── templates/admin/   # Admin base layout
│
└── rexcc_project/         # Project settings
    └── settings.py        # Configuration
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
# .venv\Scripts\activate   # Windows

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
```

---

## 🎨 Design System

| Element | Style |
|---------|-------|
| **Primary** | `#000000` (Black) |
| **Background** | `#F5F5F5` (Light Gray) |
| **Accent** | `#FFFFFF` (White) |
| **Font** | Outfit (Google Fonts) |
| **Icons** | Material Icons |
| **Effects** | Glassmorphism, subtle shadows |

---

## 🔒 Security Features

- ✅ CSRF Protection on all forms
- ✅ `@never_cache` on sensitive views  
- ✅ `@user_passes_test` for superuser verification
- ✅ Session-based authentication
- ✅ Secure password hashing (PBKDF2)
- ✅ Email verification required

---

## 📋 Roadmap

### Phase 1 — Core (✅ Complete)
- [x] User Authentication
- [x] Admin Panel
- [x] Product Catalog
- [x] Variant Management

### Phase 2 — E-Commerce (🔄 In Progress)
- [ ] Shopping Cart
- [ ] Wishlist
- [ ] Checkout Flow
- [ ] Order Management

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
