# Ecommerce Orders System

This project is a RESTful API built with Django REST Framework (DRF) for an e-commerce platform. It handles user authentication, product management, order processing, and stock management. It also integrates Celery for background tasks and Pandas for data exports.

## Features
- **User Authentication**: JWT-based login and registration (Admin & Customer roles).
- **Product Management**: CRUD for admins, read-only for customers. Cached using Redis.
- **Order Management**: Transactional order creation with stock validation, and cancellation that restores stock.
- **Exporting Data**: Pandas-based export of orders to CSV and Excel for admins.
- **Background Tasks**: Celery task for simulating order confirmation emails.
- **API Documentation**: Swagger/OpenAPI documentation auto-generated via drf-yasg.
- **Testing**: Pytest setup covering all mandatory business logic.

## Technology Stack
- Python 3.12+
- Django 6.1
- Django REST Framework (DRF)
- PostgreSQL (or SQLite as fallback)
- Celery
- Redis
- Pandas
- Pytest

## Requirements
- Python 3.12+
- PostgreSQL
- Redis Server (Optional for local testing, fallback is SQLite if no DB is configured)

## Installation & Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd "Ecommerce orders system"
   ```

2. **Set up the virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` and configure it:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and fill in your DB/Redis credentials.*

5. **PostgreSQL Setup** (If using Postgres):
   Ensure you have a PostgreSQL database created that matches the credentials in your `.env` file. If `.env` DB variables are omitted, SQLite will be used.

6. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

7. **Create an Admin User**:
   ```bash
   python manage.py createsuperuser
   # Note: For role 'admin', you can also register via the API and set role='admin' if you modify the endpoint, or use the Django admin interface.
   ```

8. **Start Redis Server** (Required for Celery & Caching):
   ```bash
   redis-server
   ```

9. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```

10. **Run Celery Worker**:
    ```bash
    celery -A config worker -l info
    ```

## Running Tests
Run the automated test suite using pytest:
```bash
pytest ecommerce/tests.py -v
```

## Folder Structure
```
Ecommerce orders system/
├── config/              # Main Django configuration (settings, urls, celery, wsgi)
├── ecommerce/           # Core app (models, views, serializers, urls, tasks, tests)
├── venv/                # Virtual Environment
├── db.sqlite3           # Default SQLite Database (if no Postgres config)
├── manage.py
├── pytest.ini
├── requirements.txt
├── README.md
└── .env
```

## API Endpoint Documentation
Swagger documentation is available when the server is running at:
`http://localhost:8000/swagger/`

### Key Endpoints
| Endpoint | Method | Permission | Description |
|---|---|---|---|
| `/api/auth/register/` | POST | AllowAny | Register a new user |
| `/api/auth/login/` | POST | AllowAny | Obtain JWT pair (access & refresh) |
| `/api/auth/refresh/` | POST | AllowAny | Refresh JWT |
| `/api/products/` | GET/POST | IsAuthenticated, Admin/ReadOnly | List (cached) / Create products |
| `/api/products/<id>/` | GET/PUT/DELETE | IsAuthenticated, Admin/ReadOnly | Retrieve, Update, Delete product |
| `/api/orders/` | GET/POST | IsAuthenticated | List own orders / Admin sees all; Create Order |
| `/api/orders/<id>/cancel/` | POST | IsAuthenticated | Cancel own order and restore stock |
| `/api/export/orders/?type=csv|excel` | GET | Admin | Export orders to CSV or Excel |

## Git Workflow
This project utilizes a structured Git workflow:
- `production` branch for stable, production-ready code.
- `dev` branch for active development.
Feature branches should branch off `dev` and merge back into `dev`. `dev` is then merged into `production` upon stable releases.
