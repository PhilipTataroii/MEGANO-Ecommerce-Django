# MEGANO — E-Commerce Platform

🌐 **Documentation Languages**

🇬🇧 **English** | 🇷🇺 [Русский](README.ru.md) | 🇷🇴 [Română](README.ro.md)

## Overview

MEGANO is a full-stack e-commerce web application developed using Python, Django, and Django REST Framework.

The project was created as the final diploma project for the Python Developer professional training program at Skillbox, in partnership with GeekBrains.

The application demonstrates practical experience in backend development, REST API design, database management, user authentication, order processing, and automated testing.

## Features

- Product catalog with categories and detailed product pages
- Product search, filtering, and sorting
- User registration, authentication, and profile management
- Shopping cart for guests and authenticated users
- Order creation and order history
- Order cancellation
- Payment processing workflow
- Product reviews
- Django administration panel
- REST API with Swagger/OpenAPI documentation
- Automated tests

## Technology Stack

### Backend

- Python
- Django 5.2
- Django REST Framework
- SQLite
- drf-spectacular

### Frontend

- HTML
- CSS
- JavaScript
- Django Templates

### Development Tools

- Git
- GitLab
- PyCharm

## Project Structure

```text
django_diploma/
├── backend/
│   ├── accounts/
│   │   └── fixtures/
│   │       └── users.json
│   ├── basket/
│   ├── catalog/
│   ├── orders/
│   ├── config/
│   └── manage.py
├── diploma-frontend/
├── requirements.txt
├── README.md
├── README.ru.md
└── README.ro.md
```

## Installation

### 1. Clone the Repository

```bash
git clone https://gitlab.skillbox.ru/filip_tataroi/python_django_diploma.git
cd python_django_diploma
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Local Frontend Package

```bash
pip install -e ./diploma-frontend
```

### 5. Navigate to the Backend Directory

```bash
cd backend
```

### 6. Apply Database Migrations

```bash
python manage.py migrate
```

### 7. Load Demo Data

```bash
python manage.py loaddata users
python manage.py loaddata catalog
```

The fixtures provide two demonstration accounts:

| Username | Role |
|---|---|
| `demo_admin` | Administrator |
| `demo_customer` | Customer |

For security reasons, passwords are disabled by default.

To configure passwords locally:

```bash
python manage.py changepassword demo_admin
python manage.py changepassword demo_customer
```

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open the application:

http://127.0.0.1:8000/

## API Documentation

**Interactive Swagger Documentation**

http://127.0.0.1:8000/api/docs/

**OpenAPI Schema**

http://127.0.0.1:8000/api/schema/

### Main API Endpoints

| Endpoint | Description |
|---|---|
| `/api/catalog` | Product catalog |
| `/api/categories` | Product categories |
| `/api/product/<id>` | Product details |
| `/api/basket` | Shopping cart |
| `/api/orders` | Order management |
| `/api/payment/<order_id>` | Payment processing |
| `/api/products/popular` | Popular products |
| `/api/products/limited` | Limited products |
| `/api/banners` | Promotional banners |

## Testing

Run automated tests from the backend directory:

```bash
python manage.py test
```

## Development Notes

This application is an educational portfolio project.

The default configuration is intended for local development.

Production deployment requires secure environment variables, appropriate host configuration, static file management, and production-ready security settings.

## Author

**Filip Tataroi**

Python / Django Developer

**Project Type:** Final Diploma Project — Skillbox Python Developer Program

GitHub: https://github.com/PhilipTataroii

LinkedIn: https://www.linkedin.com/in/filip-tataroi/

## License

This project was developed for educational and portfolio purposes. No open-source license is granted unless explicitly added.
