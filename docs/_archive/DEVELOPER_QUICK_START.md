# Developer Quick Start

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (optional for development, required for production)
- Node.js 18+ (for Tailwind CSS)

## Local Setup

### 1. Clone and Enter the Project

```bash
git clone <repo-url> eytgaming
cd eytgaming
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration:
#   - DB_NAME, DB_USER, DB_PASSWORD: PostgreSQL credentials
#   - SECRET_KEY: Django secret key
#   - SENTRY_DSN: (optional) Sentry error tracking
#   - STRIPE keys: (optional) Payment processing
```

### 5. Create Database

```bash
createdb eytgaming_db
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Cache Table (Development)

```bash
python manage.py createcachetable
```

### 8. Create Superuser

```bash
python manage.py createsuperuser
```

### 9. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest accounts/tests.py

# Run E2E tests (requires live server + Playwright)
pytest e2e/ --base-url http://localhost:8000
```

## Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy .

# Security audit
pip-audit --requirement requirements.txt --strict

# Pre-commit (install once)
pre-commit install
pre-commit run --all-files
```

## Common Tasks

### Making Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

### Running Background Tasks (Celery)

```bash
celery -A config worker -l info
celery -A config beat -l info  # For scheduled tasks
```

## Project Structure

```
eytgaming/
├── config/          # Django project settings, URLs, WSGI
├── accounts/        # Authentication, profiles, 2FA
├── api/             # REST API v1 (DRF viewsets + serializers)
├── coaching/        # Coaching marketplace
├── core/            # Core models (User, Game, etc.)
├── dashboard/       # User dashboard
├── e2e/             # Playwright E2E tests
├── health/          # Health check endpoints
├── notifications/   # In-app + push notifications
├── payments/        # Stripe/Paystack payment processing
├── security/        # Audit logs, security events, middleware
├── store/           # Merchandise store
├── teams/           # Team management
├── tournaments/     # Tournament management
├── venues/          # Venue booking

├── templates/       # Django templates
├── static/          # Static assets (CSS, JS, images)
├── docs/            # Documentation
├── .github/         # CI/CD, PR templates, CODEOWNERS
└── requirements.txt # Python dependencies
```
