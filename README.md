---

# 🕰️ **Rex CC — Premium Luxury Watch E-Commerce Platform**

Rex CC is a sophisticated, modular Django-based e-commerce platform designed specifically for premium luxury watch sales. Built with scalability and maintainability in mind, this project implements modern web development practices with a focus on user experience and administrative control.

---

## 🎯 **Project Overview**

Rex CC is a full-featured e-commerce solution that combines elegant user-facing interfaces with powerful administrative tools. The platform is designed to handle the unique requirements of luxury watch retail, including detailed product information, secure transactions, and comprehensive user management.

### **Current Status**
The project is in active development with core authentication, user management, and catalog management features fully implemented. Brand and Category management modules are complete with AJAX-based CRUD operations. The foundation is solid and ready for expansion into product, inventory, and order management modules.

---

## 🏗️ **Architecture & Tech Stack**

### **Backend Framework**
- **Django 6.0** - Latest Python web framework
- **PostgreSQL** - Robust relational database
- **django-allauth 65.13.1** - Complete authentication solution
- **django-environ** - Environment variable management

### **Cloud Services**
- **Cloudinary** - Media storage and CDN
- **Email Service** - SMTP integration for notifications

### **Additional Libraries**
- **django-phonenumber-field** - International phone number validation
- **Pillow** - Image processing
- **psycopg2-binary** - PostgreSQL adapter

### **Development Tools**
- **Black** - Code formatting
- **djlint** - Template linting
- **django-humanize** - Template filters for human-readable data

---

## ✨ **Implemented Features**

### 🔐 **User Authentication System**

#### **Custom User Model**
- Email-based authentication (no username required)
- Custom user manager with superuser support
- Profile fields: first name, last name, avatar, phone number
- Cloudinary integration for avatar storage
- Timestamps for account creation and updates

#### **User Registration & Login**
- ✅ Email-based signup with custom form
- ✅ Mandatory email verification via OTP
- ✅ Secure login/logout functionality
- ✅ Password reset with email verification
- ✅ Google OAuth integration for social login
- ✅ Session management (remember me disabled by default)

#### **Branded Templates**
- Custom django-allauth template overrides
- REX CC luxury branding with Playfair Display & Montserrat fonts
- Bronze/gold accent color scheme
- Responsive design with Bootstrap integration
- Premium UI/UX with smooth animations

### 👑 **Admin Panel**

#### **Admin Authentication**
- ✅ Separate admin login system
- ✅ Email-based authentication
- ✅ Forgot password with OTP verification
- ✅ Secure session management
- ✅ Superuser-only access control

#### **User Management Module**
- ✅ **User List View**
  - Paginated user display (5 users per page)
  - Search functionality (name, email)
  - Status filtering (all/active/inactive)
  - User statistics dashboard
  - Quick status toggle actions
  
- ✅ **User Profile View**
  - Comprehensive user information display
  - Multiple delivery addresses (home/office)
  - Recent orders with status tracking
  - Wallet balance and transaction history
  - Payment transaction records
  - Referral rewards tracking
  - Premium UI with Google Material Icons

#### **Security Features**
- `@never_cache` decorators on sensitive views
- `@user_passes_test` for superuser verification
- CSRF protection enabled
- Secure password hashing
- Session-based authentication

### 📦 **Catalog Management**

#### **Brand Management**
- ✅ **Brand CRUD Operations**
  - Create new brands with logo upload
  - Edit existing brand details
  - View brand details page
  - Toggle brand active/inactive status
  
- ✅ **Brand Form Features**
  - Two-column responsive layout
  - Image cropping with Cropper.js
  - Drag-and-drop file upload
  - Preview of cropped image
  - Hover overlay for changing logo
  - Dynamic form for add/edit modes
  
- ✅ **Brand List Page**
  - Paginated brand display
  - Search by brand name
  - Status filtering (all/active/inactive)
  - Quick actions (view/edit/toggle)
  
- ✅ **Brand View Page**
  - Two-column layout with info cards
  - Logo display with Cloudinary
  - Quick action buttons
  - Products placeholder section

#### **Category Management**
- ✅ **Category CRUD Operations**
  - Create new categories via AJAX modal
  - Edit existing categories via AJAX modal
  - Toggle category active/inactive status
  - Inline category listing with real-time updates
  
- ✅ **Category List Page**
  - Paginated category display (10 per page)
  - Search by category name
  - Status filtering (all/active/inactive)
  - Quick actions (edit/toggle status)
  - Bootstrap modal for add/edit operations

---

## 📁 **Project Structure**

```
Rex_CC_Ecommerce/
├── accounts/                      # Authentication & User Management
│   ├── admin_views/
│   │   ├── admin_auth.py         # Admin authentication views
│   │   └── user_management.py    # User management views
│   ├── migrations/
│   ├── static/account/
│   │   ├── css/
│   │   │   ├── admin_auth.css
│   │   │   ├── user_auth.css
│   │   │   └── user_management/
│   │   │       ├── user_list.css
│   │   │       └── user_profile.css
│   │   └── js/
│   ├── templates/
│   │   ├── account/              # django-allauth overrides
│   │   │   ├── login.html
│   │   │   ├── signup.html
│   │   │   ├── password_reset.html
│   │   │   └── ...
│   │   └── accounts/
│   │       ├── admin_auth/       # Admin authentication templates
│   │       └── user_management/  # User management templates
│   ├── admin_urls.py
│   ├── forms.py                  # Custom signup form
│   ├── models.py                 # CustomUser, PasswordReset
│   ├── service.py                # Email services
│   └── decorators.py             # Custom decorators
│
├── pages/                         # Static pages
│   ├── views/
│   │   ├── admin_pages.py
│   │   └── user_pages.py
│   ├── urls/
│   │   ├── admin_urls.py
│   │   └── user_urls.py
│   └── templates/
├── catalog/                       # Catalog & Product Management
│   ├── forms.py                  # BrandForm, CategoryForm
│   ├── models.py                 # Brand, Category models
│   ├── static/catalog/
│   │   ├── css/admin/
│   │   │   ├── brand/            # Brand-specific styles
│   │   │   └── category/         # Category-specific styles
│   │   └── js/admin/
│   │       ├── brand/            # Brand form JS (Cropper.js)
│   │       └── category/         # Category modal JS
│   ├── templates/catalog/admin/
│   │   ├── brand/                # Brand templates
│   │   └── category/             # Category templates
│   ├── urls/admin_urls.py
│   └── views/admin/
│       ├── brand.py          # Brand management views
│       └── category.py       # Category management views
│
├── manage.py
├── requirements.txt
├── .env                          # Environment variables
└── .gitignore
```

---

## 📝 **Development Roadmap**

### ✅ **Phase 1: Foundation (Completed)**
- [x] Custom User model with email authentication
- [x] User signup with email verification
- [x] Login/Logout functionality
- [x] Password reset flow
- [x] Google OAuth integration
- [x] Admin authentication system
- [x] User management (list, profile, status toggle)

### ✅ **Phase 2: Catalog Management (Completed)**
- [x] Brand model with Cloudinary logo storage
- [x] Brand CRUD operations (create, read, update)
- [x] Brand list with search, filter, pagination
- [x] Brand form with image cropping (Cropper.js)
- [x] Brand view page with details display
- [x] Category model with AJAX CRUD operations
- [x] Category modal-based add/edit via AJAX
- [x] Category list with search, filter, pagination
- [x] Category status toggle functionality

### 🚧 **Phase 3: Product Management (In Progress)**
- [ ] Product model with variants
- [ ] Product image gallery
- [ ] Product listing and detail pages
- [ ] Search and filtering

### 🚧 **Phase 4: Shopping Experience (Planned)**
- [ ] Shopping cart functionality
- [ ] Wishlist management
- [ ] User profile completion
- [ ] Multiple delivery addresses
- [ ] Checkout process

### 🚧 **Phase 5: Orders & Payments (Planned)**
- [ ] Order creation and tracking
- [ ] Razorpay/Stripe integration
- [ ] Payment verification
- [ ] Order management dashboard
- [ ] Return request handling

### 🚧 **Phase 6: Promotions & Loyalty (Planned)**
- [ ] Coupon system
- [ ] Reward points
- [ ] Referral program
- [ ] Wallet functionality

### 🚧 **Phase 7: Advanced Features (Planned)**
- [ ] Product reviews and ratings
- [ ] Inventory management
- [ ] Notification system
- [ ] Support ticket system
- [ ] Analytics dashboard

---

## 🚀 **Setup Instructions**

### **Prerequisites**
- Python 3.10 or higher
- PostgreSQL 12 or higher
- Cloudinary account
- Google OAuth credentials (optional)
- SMTP email service

### **1️⃣ Clone the Repository**

```bash
git clone <repository-url>
cd Rex_CC_Ecommerce
```

### **2️⃣ Create Virtual Environment**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### **3️⃣ Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4️⃣ Configure Environment Variables**

Create a `.env` file in the project root:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
TIME_ZONE=Asia/Kolkata
SITE_ID=1
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration
DATABASE_URL=postgres://username:password@localhost:5432/rexcc_db

# Cloudinary Configuration
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_SECRET_KEY=your-google-secret-key

# Security
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

### **5️⃣ Database Setup**

```bash
# Create PostgreSQL database
createdb rexcc_db

# Run migrations
python manage.py migrate
```

### **6️⃣ Create Superuser**

```bash
python manage.py createsuperuser
```

### **7️⃣ Start Development Server**

```bash
python manage.py runserver
```

### **8️⃣ Access the Application**

- **User Site**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/adminpanel/accounts/login/
- **Django Admin**: http://127.0.0.1:8000/default-admin/

---

## 🔑 **Key Features Highlights**

### **User Experience**
- Elegant, luxury-focused design
- Responsive layouts for all devices
- Smooth animations and transitions
- Intuitive navigation
- Real-time form validation

### **Admin Capabilities**
- Comprehensive user management
- Advanced search and filtering
- Detailed user analytics
- Quick action buttons
- Secure access control

### **Security**
- Email verification required
- CSRF protection
- Secure password hashing
- Session management
- Superuser-only admin access

### **Scalability**
- Modular app structure
- Separation of concerns
- Reusable components
- Environment-based configuration
- Cloud-ready architecture

---

## 🛡️ **Security Best Practices**

- All sensitive data stored in environment variables
- CSRF tokens on all forms
- Password reset tokens with expiration
- Email verification for new accounts
- Superuser verification for admin access
- Never cache decorators on sensitive views
- Secure session configuration

---

## 📚 **API Endpoints**

### **User Authentication**
- `POST /accounts/signup/` - User registration
- `POST /accounts/login/` - User login
- `GET /accounts/logout/` - User logout
- `POST /accounts/password/reset/` - Password reset request
- `GET /accounts/confirm-email/<key>/` - Email verification

### **Admin Panel**
- `POST /adminpanel/accounts/login/` - Admin login
- `GET /adminpanel/accounts/logout/` - Admin logout
- `GET /adminpanel/accounts/users/` - User list
- `GET /adminpanel/accounts/user/<id>/profile/` - User profile
- `POST /adminpanel/accounts/user/<id>/toggle-status/` - Toggle user status

### **Brand Management**
- `GET /adminpanel/catalog/brands/` - Brand list
- `GET /adminpanel/catalog/brand/add/` - Add brand form
- `POST /adminpanel/catalog/brand/add/` - Create brand
- `GET /adminpanel/catalog/brand/<id>/` - View brand details
- `GET /adminpanel/catalog/brand/<id>/edit/` - Edit brand form
- `POST /adminpanel/catalog/brand/<id>/edit/` - Update brand
- `POST /adminpanel/catalog/brand/<id>/toggle-status/` - Toggle brand status

### **Category Management**
- `GET /adminpanel/catalog/categories/` - Category list
- `POST /adminpanel/catalog/category/add/` - Create category (AJAX)
- `POST /adminpanel/catalog/category/<id>/edit/` - Update category (AJAX)
- `POST /adminpanel/catalog/category/<id>/stats-toggle/` - Toggle category status

---

## 🎨 **Design System**

### **Typography**
- **Headings**: Playfair Display (serif, elegant)
- **Body**: Montserrat (sans-serif, modern)

### **Color Palette**
- **Primary**: Bronze/Gold accents (#d4af37)
- **Background**: Dark theme with gradients
- **Text**: High contrast for readability

### **UI Components**
- Bootstrap 5 framework
- Google Material Icons
- Cropper.js for image cropping
- Custom CSS for luxury aesthetics
- Glassmorphism effects

---

## 🧪 **Testing**

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test pages
```

---

## 📄 **License**

MIT License - Feel free to use this project for learning and development.

---

## 🤝 **Contributing**

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 **Support**

For questions or issues, please open an issue on the repository.

---

## 🙏 **Acknowledgments**

- Django framework and community
- django-allauth for authentication
- Bootstrap for UI components
- Cloudinary for media management

---

**Built with ❤️ for luxury watch enthusiasts**
