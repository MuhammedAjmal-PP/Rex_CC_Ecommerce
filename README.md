---

# 🕰️ **Rex CC — Premium Luxury Watch E-Commerce System**

Rex CC is a modular and scalable Django-based e-commerce platform designed for premium luxury watch sales.
This project is currently at the **initial development stage**, with modules to be added gradually.

---


## 📝 **To-Do List (Development Roadmap)**

Features will be added step-by-step.

---

### 🔐 User Authentication

* [x] Custom User model
* [x] Signup with email
* [x] OTP email verification
* [x] Login / Logout
* [x] Forgot password
* [x] Oauth - Socail account login (google)

---

### 🔐 Custom Admin Authentication

* [ ] Signup with email
* [ ] OTP email verification for Forgot password
* [ ] Login / Logout
* [ ] Forgot password

---

### 🏷️ Catalog

* [ ] Brand model
* [ ] Category model
* [ ] Product model
* [ ] Product Variant model
* [ ] Product images
* [ ] Product listing page
* [ ] Product detail page

---

### 📦 Inventory

* [ ] Stock model
* [ ] Inventory logs
* [ ] Low-stock alerts
* [ ] Admin stock updates

---

### 🛒 User Panel

* [ ] User profile
* [ ] Multiple delivery addresses
* [ ] Cart
* [ ] Wishlist
* [ ] Checkout
* [ ] Apply coupon
* [ ] Apply wallet balance
* [ ] Apply rewards

---

### 🎟 Promotions

#### **Coupons**

* [ ] Create coupon
* [ ] Apply coupon

#### **Rewards**

* [ ] Reward point system
* [ ] Reward earning
* [ ] Reward redeeming

#### **Referral**

* [ ] Referral code generation
* [ ] Referral rewards

---

### 💳 Payments

* [ ] Razorpay/Stripe integration
* [ ] Payment verification
* [ ] Refund processing

---

### 📋 Orders

* [ ] Order creation
* [ ] Order tracking
* [ ] Order detail view
* [ ] Return request (within 7 days)
* [ ] Admin order management

---

### ⭐ Reviews

* [ ] User reviews
* [ ] Review images
* [ ] Admin moderation

---

### 🔔 Notifications

* [ ] User notifications
* [ ] Admin notification system

---

### 🆘 Support

* [ ] User support ticket
* [ ] Admin replies
* [ ] Ticket history

---

### 👑 Admin Panel

* [ ] Dashboard
* [ ] User management
* [ ] Catalog management
* [ ] Inventory control
* [ ] Promotions management
* [ ] Order management
* [ ] Support module

---

## 🛠 **Tech Stack**

* Python
* Django
* PostgreSQL
* django-environ
* Razorpay/Stripe (future)
* Tailwind / Bootstrap (optional for UI)

---

## 📦 **Setup Instructions**

### 1️⃣ Create virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
```

### 2️⃣ Install dependencies

```
pip install -r requirements.txt
```

### 3️⃣ Configure `.env`

```
DEBUG=True
SECRET_KEY=your_secret_key
TIME_ZONE=Asia/Kolkata
SITE_ID=1
ALLOWED_HOSTS=127.0.0.1,localhost

DATABASE_URL=postgres://<db-username>:<password>@localhost:5432/<db-name>
CLOUDINARY_URL=cloudinary://<your_api_key>:<your_api_secret>@<your-id>
EMAIL_URL=smtp+tls://<your-email>:<app-password>@smtp.gmail.com:587

GOOGLE_CLIENT_ID=<Client_id>
GOOGLE_SECRET_KEY=<Secret_key>
```

### 4️⃣ Apply migrations

```
python manage.py migrate
```

### 5️⃣ Start development server

```
python manage.py runserver
```

---

## 📜 License

MIT License

---

## 🤝 Contributing

Pull requests are welcome as the project evolves.

---
