# 🛒 Ecommerce Orders System

A production-ready RESTful API for an e-commerce platform built with **Django** and **Django REST Framework (DRF)**. It supports JWT-based authentication, role-based access control, transactional order management with stock handling, background tasks via Celery, and data exports via Pandas.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Folder Structure](#folder-structure)
- [Requirements](#requirements)
- [Project Setup Instructions](#project-setup-instructions)
- [Environment Setup](#environment-setup)
- [PostgreSQL Setup](#postgresql-setup)
- [Migration Commands](#migration-commands)
- [How to Create an Admin](#how-to-create-an-admin)
- [How to Run the Project](#how-to-run-the-project)
- [How to Run Tests](#how-to-run-tests)
- [API Endpoints](#api-endpoints)
- [Authentication Instructions](#authentication-instructions)
- [Role and Permission Details](#role-and-permission-details)
- [Optional Features Implemented](#optional-features-implemented)
- [Git Workflow](#git-workflow)

---

## 📌 Project Overview

This is a monolithic Django REST API for managing an ecommerce order system. It provides:

- User registration and JWT-based login for both **Admins** and **Customers**.
- Full **Product CRUD** for Admins with Redis-cached listing for Customers.
- **Order creation** with atomic transactions, stock validation, and multi-product support.
- **Order cancellation** with automatic stock restoration.
- Role-based access so customers can only access their own orders.
- **Swagger/OpenAPI** documentation for all endpoints.
- **Celery** for simulated order confirmation background tasks.
- **Pandas-based** CSV and Excel export of orders for Admins.

---

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12+ | Core language |
| Django 6.1 | Web framework |
| Django REST Framework | API layer |
| djangorestframework-simplejwt | JWT Authentication |
| PostgreSQL | Primary database |
| SQLite | Fallback (dev/testing) |
| Celery | Background task queue |
| Redis | Message broker + API caching |
| Pandas + openpyxl | CSV/Excel data export |
| drf-yasg | Swagger/OpenAPI documentation |
| pytest + pytest-django | Automated testing |
| python-dotenv | Environment variable management |

---

## 📁 Folder Structure

```
Ecommerce orders system/
├── config/                      # Django project configuration
│   ├── __init__.py              # Celery app initialization
│   ├── settings.py              # All project settings
│   ├── urls.py                  # Root URL configuration + Swagger
│   ├── celery.py                # Celery configuration
│   ├── asgi.py
│   └── wsgi.py
├── ecommerce/                   # Core application
│   ├── migrations/              # Database migrations
│   ├── __init__.py
│   ├── admin.py                 # Django admin registration
│   ├── apps.py
│   ├── models.py                # User, Product, Order, OrderItem models
│   ├── serializers.py           # DRF serializers for validation and formatting
│   ├── services.py              # Business logic layer (order creation, cancellation)
│   ├── views.py                 # Thin API views (delegate to services)
│   ├── permissions.py           # Custom role-based permission classes
│   ├── tasks.py                 # Celery background tasks
│   ├── urls.py                  # App-level URL routes
│   └── tests.py                 # Pytest test cases
├── venv/                        # Virtual environment (not committed)
├── manage.py                    # Django management entry point
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # All project dependencies
├── .env                         # Environment variables (not committed)
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

---

## ✅ Requirements

- Python 3.12+
- pip
- PostgreSQL (recommended) or SQLite (fallback)
- Redis Server (for Celery + API caching)
- Git

---

## 🚀 Project Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/tanisha259/Ecommerce-order-system.git
cd "Ecommerce-order-system"
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔧 Environment Setup

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_NAME=ecommerce_db
DATABASE_USER=postgres
DATABASE_PASSWORD=yourpassword
DATABASE_HOST=localhost
DATABASE_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

> **Note:** If `DATABASE_NAME` is not set in `.env`, the project automatically falls back to SQLite for easy local testing.

---

## 🐘 PostgreSQL Setup

1. Install PostgreSQL and start the service.
2. Open psql and create a database:

```sql
CREATE DATABASE ecommerce_db;
CREATE USER postgres WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO postgres;
```

3. Update your `.env` with the correct database credentials.

---

## 🗃️ Migration Commands

Apply database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 👤 How to Create an Admin

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username and password.

> **Important:** After creation, the superuser needs to have `role = 'admin'` set. You can do this via the Django Admin panel at `http://localhost:8000/admin/` by editing the user and setting the role field to `admin`.

---

## ▶️ How to Run the Project

### Step 1 — Start Redis (required for caching and Celery)

```bash
redis-server
```

### Step 2 — Run the Django Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000/`

### Step 3 — Run Celery Worker (in a separate terminal)

```bash
celery -A config worker -l info
```

### Step 4 — Access Swagger API Docs

Open in browser: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)

---

## 🧪 How to Run Tests

```bash
pytest ecommerce/tests.py -v
```

Expected output — **9 tests, all passing:**

```
PASSED  test_customer_creates_order_multiple_products
PASSED  test_insufficient_stock
PASSED  test_invalid_quantity
PASSED  test_customer_sees_own_orders
PASSED  test_admin_sees_all_orders
PASSED  test_customer_can_cancel_own_order
PASSED  test_customer_cannot_cancel_another_customer_order
PASSED  test_customer_cannot_cancel_already_cancelled_order
PASSED  test_transaction_rollback_works_correctly
```

---

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Register a new user (role: `admin` or `customer`) |
| POST | `/api/auth/login/` | Public | Login and obtain JWT access + refresh tokens |
| POST | `/api/auth/refresh/` | Public | Refresh an expired access token |

### Products

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/products/` | Authenticated | List all products (response cached 15 min) |
| POST | `/api/products/` | Admin only | Create a new product |
| GET | `/api/products/<id>/` | Authenticated | Retrieve a single product |
| PUT | `/api/products/<id>/` | Admin only | Update a product |
| DELETE | `/api/products/<id>/` | Admin only | Delete a product |

### Orders

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/orders/` | Authenticated | Customers see their own; Admins see all |
| POST | `/api/orders/` | Authenticated | Create an order (validates stock, atomic transaction) |
| GET | `/api/orders/<id>/` | Owner or Admin | Retrieve a specific order |
| POST | `/api/orders/<id>/cancel/` | Owner or Admin | Cancel order and restore product stock |

### Export (Optional Feature)

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/export/orders/?type=csv` | Admin only | Download all orders as CSV |
| GET | `/api/export/orders/?type=excel` | Admin only | Download all orders as Excel (.xlsx) |

---

## 🔐 Authentication Instructions

This API uses **JWT (JSON Web Token)** authentication exclusively. No session or Basic Auth is used.

**Step 1 — Register a user:**

```bash
POST /api/auth/register/
{
  "username": "john",
  "password": "securepassword",
  "email": "john@example.com",
  "role": "customer"
}
```

**Step 2 — Login to obtain tokens:**

```bash
POST /api/auth/login/
{
  "username": "john",
  "password": "securepassword"
}
```

Response:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Step 3 — Use the token in all subsequent requests:**

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**In Swagger UI:** Click the green **Authorize** button at the top → enter `Bearer <your_access_token>`.

---

## 🛡️ Role and Permission Details

The system has two roles: **Admin** and **Customer**.

### Admin Permissions
- Full CRUD on all Products (create, update, delete).
- View **all** orders in the system.
- Cancel any order.
- Export order data to CSV or Excel.
- Access the Django Admin panel at `/admin/`.

### Customer Permissions
- View products (read-only, cached).
- Create new orders (with stock validation).
- View **only their own** orders — cannot access other customers' orders.
- Cancel **only their own** orders.
- Cannot cancel an already cancelled order.

### Permission Classes (in `permissions.py`)

| Class | Behaviour |
|---|---|
| `IsAdminUserOrReadOnly` | Admins can write; authenticated users can read |
| `IsAdmin` | Only users with `role = 'admin'` can access |
| `IsOwnerOrAdmin` | Object-level: only the order owner or an admin can access |

---

## ⚙️ Optional Features Implemented

### 1. Redis Caching
- The Product Listing API (`GET /api/products/`) is cached using Django's Redis cache backend for **15 minutes**.
- Configured in `settings.py` under `CACHES`.

### 2. Celery (Order Confirmation)
- After a successful order is created, a **Celery background task** (`send_order_confirmation`) is dispatched.
- The task simulates sending an order confirmation email by logging the confirmation to the console.
- No real email service is required.
- Worker command: `celery -A config worker -l info`

### 3. Pandas (Data Export)
- Admin-only endpoint: `GET /api/export/orders/`
- Supports two export formats via query parameter `?type=csv` or `?type=excel`.
- Uses `pandas` DataFrames and `openpyxl` engine for `.xlsx` generation.

---

## 🌿 Git Workflow

| Branch | Purpose |
|---|---|
| `dev` | Active development branch |
| `production` | Stable, production-ready code |

**Workflow:**
1. All development happens on `dev`.
2. Tested and stable code is merged into `production`.

**Commit message convention used:**
- `feat:` — new feature
- `fix:` — bug fix
- `refactor:` — code restructuring without behaviour change
- `test:` — test additions or updates
