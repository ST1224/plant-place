# 🌿 Plant Palace — Nursery Management System
> A production-ready Django e-commerce application for plant nurseries.

---

## 📋 Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
- [Project Structure](#project-structure)
- [Issues Fixed](#issues-fixed)
- [Production Checklist](#production-checklist)

---

## ✅ Features

| Feature | Status |
|---|---|
| Modern responsive UI (Bootstrap 5) | ✅ |
| Product catalogue with categories | ✅ |
| DB-backed cart (no localStorage hack) | ✅ |
| Proper order flow (Cart → Checkout → Payment) | ✅ |
| Order status tracking (Pending/Paid/Shipped/Delivered) | ✅ |
| User registration + profile | ✅ |
| Password reset via email | ✅ |
| Admin panel with full CRUD | ✅ |
| Payment simulation (replace with Razorpay/PayU) | ✅ |
| Server-side price calculation (secure) | ✅ |
| Search with Django Q objects | ✅ |
| Pagination on product listing | ✅ |
| CSRF protection on all views | ✅ |
| Mobile-first responsive design | ✅ |

---

## 🛠 Tech Stack

- **Backend:** Python 3.10+, Django 4.2+
- **Frontend:** Bootstrap 5, Bootstrap Icons, Google Fonts (Poppins)
- **Database:** SQLite (dev) — swap to PostgreSQL for production
- **Media:** Pillow (image uploads)

---

## 🚀 Setup Instructions

### 1. Clone / Extract the project
```bash
cd plant_palace/
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment (optional but recommended)
```bash
cp .env.example .env
# Edit .env with your secret key and email settings
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create a superuser (admin)
```bash
python manage.py createsuperuser
```

### 7. Seed the database with products & categories
```bash
python manage.py seed_data
```
This populates **5 categories** and **62 products** with real plant images.  
Images are served from `media/shop/images/` which is already populated in this package.

To reset and re-seed from scratch:
```bash
python manage.py seed_data --clear
```

### 8. Run the development server
```bash
python manage.py runserver
```
Open: http://127.0.0.1:8000/

### 9. Access Admin
Open: http://127.0.0.1:8000/admin/
Login with the superuser credentials you created.

---

## 📁 Project Structure

```
plant_palace/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── db.sqlite3              # Created after migrate
│
├── nursery_project/        # Django project config
│   ├── settings.py         # ⚙️ Main settings (reads from env)
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py
│
└── shop/                   # Main application
    ├── models.py           # All DB models (Product, Cart, Order, etc.)
    ├── views.py            # All view logic (modular, secure)
    ├── urls.py             # Shop URL patterns
    ├── admin.py            # Admin panel configuration
    ├── apps.py             # App config + signals
    ├── signals.py          # Auto-create UserProfile on signup
    ├── context_processors.py  # Global cart count
    ├── migrations/         # DB migrations
    ├── static/shop/
    │   ├── css/style.css   # Main stylesheet (nature theme)
    │   └── js/main.js      # Cart AJAX, UI interactions
    └── templates/shop/
        ├── base.html       # Base layout (navbar, footer, modals)
        ├── index.html      # Home page
        ├── product_list.html
        ├── product_detail.html
        ├── cart.html
        ├── checkout.html
        ├── order_success.html
        ├── order_list.html
        ├── order_detail.html
        ├── payment.html
        ├── tracker.html
        ├── profile.html
        ├── about.html
        ├── contact.html
        └── password_reset*.html
```

---

## 🔧 Issues Fixed (vs Original)

### Critical Bugs
| Original Problem | Fix Applied |
|---|---|
| `product_id = models.AutoField` — missing `()` (never a real PK) | Removed; Django auto-creates pk |
| `items_json` — entire cart stored as JSON string | Replaced with `Cart` + `CartItem` models |
| Frontend-submitted `amount` used directly in order | Server-side calculation only |
| `@csrf_exempt` on checkout view | Removed; proper CSRF on all views |
| Hardcoded PayTm credentials in source code | Moved to settings/env variables |
| Hardcoded email password in settings.py | Moved to environment variable |
| `myuser.phone = phone` — User model has no phone field | `UserProfile.phone` via OneToOne |
| `searchMatch()` — Python loops over all products | Django Q objects (DB-level filtering) |
| `Orders.userId` — bare IntegerField, no relation | `Order.user` ForeignKey to User |
| `OrderUpdate.order_id` — IntegerField, no relation | `OrderUpdate.order` ForeignKey |
| No order status field | `Order.status` with choices |
| Orders created BEFORE payment verification | Pending → Paid flow |
| Cart stored in `localStorage` — lost on logout | DB-backed Cart per user |
| Bootstrap 4 with conflicting versions imported | Single Bootstrap 5 |
| No pagination on product list | `Paginator` with 12 per page |
| `HTTP_REFERER` redirect after login (can break) | Proper `next` parameter |
| No input validation server-side | Validation in all POST views |
| `rangefilter` in INSTALLED_APPS (not installed) | Removed |

---

## 🏭 Production Checklist

- [ ] Set `DJANGO_DEBUG=False` in production
- [ ] Generate a strong `DJANGO_SECRET_KEY`
- [ ] Configure real SMTP email credentials
- [ ] Integrate real payment gateway (Razorpay recommended for India)
- [ ] Run `python manage.py collectstatic`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up Nginx + Gunicorn
- [ ] Configure `ALLOWED_HOSTS` to your domain
- [ ] Enable HTTPS / SSL certificate

---

## 💳 Payment Integration

The project includes a **simulation mode**. To integrate a real gateway:

### Razorpay (Recommended for India)
1. Install: `pip install razorpay`
2. Replace `payment_initiate` view with Razorpay order creation
3. Add Razorpay checkout JS to `payment.html`
4. Replace `payment_simulate_success` with Razorpay webhook handler

---

*Built with ❤️ and 🌿 — Plant Palace Nursery Management System*
