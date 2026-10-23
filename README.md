
# MEGANO — E-Commerce Platform

MEGANO is a full-stack e-commerce web application developed with Python, Django, and Django REST Framework.

The project was created as the final diploma project for the Python Developer program at Skillbox, in partnership with GeekBrains.

## Features

- Product catalog with categories and product details
- Product search, filtering and sorting
- User registration, authentication and profiles
- Shopping cart for guests and authenticated users
- Order creation and order history
- Order cancellation
- Payment processing workflow
- Product reviews
- Django administration panel
- REST API with Swagger/OpenAPI documentation
- Automated tests

## Technology Stack

**Backend**
- Python
- Django 5.2
- Django REST Framework
- SQLite
- drf-spectacular

**Frontend**
- HTML
- CSS
- JavaScript
- Django templates

**Development tools**
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
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://gitlab.skillbox.ru/filip_tataroi/python_django_diploma.git
cd python_django_diploma
```

### 2. Create a virtual environment

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the local frontend package

```bash
pip install -e ./diploma-frontend
```

### 5. Navigate to the backend

```bash
cd backend
```

### 6. Apply database migrations

```bash
python manage.py migrate
```

### 7. Load demo users

```bash
python manage.py loaddata users

python manage.py loaddata catalog
```

The fixture creates two demonstration accounts:

| Username | Role |
|----------|------|
| demo_admin | Administrator |
| demo_customer | Customer |

For security reasons, passwords are disabled by default.

To set passwords locally:

```bash
python manage.py changepassword demo_admin
python manage.py changepassword demo_customer
```

### 8. Run the development server

```bash
python manage.py runserver
```

Open the application:

http://127.0.0.1:8000/

## API Documentation

Interactive Swagger documentation:

http://127.0.0.1:8000/api/docs/

OpenAPI schema:

http://127.0.0.1:8000/api/schema/

### Main API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/catalog` | Product catalog |
| `/api/categories` | Product categories |
| `/api/product/<id>` | Product details |
| `/api/basket` | Shopping cart |
| `/api/orders` | Orders |
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

The default configuration is intended for local development. Production deployment requires secure environment variables, proper host configuration, static file handling, and production-ready security settings.

## Author

**Filip Tataroi**

Python / Django Developer

Final diploma project — Skillbox Python Developer Program.

## License

This project was developed for educational and portfolio purposes. No open-source license is granted unless explicitly added.
