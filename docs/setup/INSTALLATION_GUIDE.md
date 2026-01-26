# EYTGaming Platform - Complete Installation Guide

## 📌 Overview

This guide will walk you through setting up the EYTGaming platform from scratch on your local development environment.

## 🛠️ Prerequisites Installation

### 1. Python 3.11+

**Windows:**
```bash
# Download from python.org or use Chocolatey
choco install python --version=3.11.0
```

**Mac:**
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

### 2. PostgreSQL 15+

**Windows:**
- Download installer from https://www.postgresql.org/download/windows/

**Mac:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux:**
```bash
sudo apt install postgresql-15 postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 3. Redis

**Windows:**
- Download from https://github.com/microsoftarchive/redis/releases
- Or use WSL2 and follow Linux instructions

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 4. Node.js 18+ (for Tailwind CSS)

**All Platforms:**
- Download from https://nodejs.org/

Or use package manager:
```bash
# Windows (Chocolatey)
choco install nodejs

# Mac
brew install node

# Linux
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 📥 Project Setup

### Step 1: Clone or Create Project

```bash
# If cloning from repository
git clone <your-repository-url>
cd eytgaming

# Or if starting fresh
mkdir eytgaming
cd eytgaming
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Step 4: Database Setup

```bash
# Create PostgreSQL database
# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL prompt
CREATE DATABASE eytgaming_db;
CREATE USER eytgaming_user WITH PASSWORD 'your_secure_password';
ALTER ROLE eytgaming_user SET client_encoding TO 'utf8';
ALTER ROLE eytgaming_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE eytgaming_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE eytgaming_db TO eytgaming_user;
\q
```

### Step 5: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Windows
notepad .env

# Mac/Linux
nano .env
# or
vim .env
```

**Minimum required .env configuration:**
```bash
DEBUG=True
SECRET_KEY=your-generated-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=eytgaming_db
DB_USER=eytgaming_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
```

**Generate SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 6: Create Project Structure

```bash
# Make setup script executable (Mac/Linux)
chmod +x setup.sh
chmod +x project_structure.sh

# Run structure creation
bash project_structure.sh

# Or manually create directories
mkdir -p media/avatars media/team_logos media/tournament_banners
mkdir -p static/css static/js static/images
mkdir -p templates/base templates/components
mkdir -p logs
```

### Step 7: Django Migrations

```bash
# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Follow prompts to create admin account
```

### Step 8: Load Initial Data

```bash
# Load sample games
python manage.py loaddata fixtures/initial_games.json
```

### Step 9: Setup Tailwind CSS

```bash
# Initialize Tailwind
python manage.py tailwind init

# Install Tailwind dependencies
python manage.py tailwind install

# Build Tailwind (one-time)
python manage.py tailwind build
```

### Step 10: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## 🚀 Running the Application

You'll need **4 terminal windows** for full functionality:

### Terminal 1: Django Development Server
```bash
cd eytgaming
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver
```
Access at: http://localhost:8000

### Terminal 2: Tailwind CSS (Watch Mode)
```bash
cd eytgaming
source venv/bin/activate
python manage.py tailwind start
```

### Terminal 3: Celery Worker
```bash
cd eytgaming
source venv/bin/activate
celery -A config worker -l info
```

### Terminal 4: Celery Beat (Scheduler)
```bash
cd eytgaming
source venv/bin/activate
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## 🐳 Docker Alternative

If you prefer Docker:

```bash
# Build and start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load initial data
docker-compose exec web python manage.py loaddata fixtures/initial_games.json

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔑 Social Authentication Setup

### Discord OAuth
1. Go to https://discord.com/developers/applications
2. Create New Application
3. Go to OAuth2 → General
4. Add redirect URI: `http://localhost:8000/accounts/discord/login/callback/`
5. Copy Client ID and Secret to .env

### Steam OpenID
1. Go to https://steamcommunity.com/dev/apikey
2. Register for API key
3. Copy to .env as STEAM_API_KEY

### Google OAuth
1. Go to https://console.cloud.google.com/
2. Create new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
6. Copy Client ID and Secret to .env

## 💳 Stripe Payment Setup (Optional)

1. Go to https://dashboard.stripe.com/register
2. Get test API keys from Developers → API keys
3. Add to .env:
```bash
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```
4. Setup webhook endpoint for local testing:
```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login
stripe login

# Forward webhooks to local
stripe listen --forward-to localhost:8000/payments/webhook/
```

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Django admin accessible at http://localhost:8000/admin/
- [ ] Can login with superuser account
- [ ] Can view Games in admin
- [ ] PostgreSQL connection working
- [ ] Redis connection working (check Celery worker logs)
- [ ] Tailwind CSS compiling (check for styled elements)
- [ ] Can create a test user account

## 🐛 Common Issues & Solutions

### Issue: "No module named 'psycopg2'"
**Solution:**
```bash
pip install psycopg2-binary
```

### Issue: "Redis connection refused"
**Solution:**
```bash
# Check if Redis is running
redis-cli ping
# Should return PONG

# If not running, start it
# Mac/Linux
redis-server
# Windows: Run redis-server.exe
```

### Issue: "Tailwind not compiling"
**Solution:**
```bash
# Reinstall Node dependencies
cd frontend
npm install
cd ..
python manage.py tailwind build
```

### Issue: "Permission denied" on setup.sh
**Solution:**
```bash
chmod +x setup.sh
bash setup.sh
```

### Issue: Database migrations failing
**Solution:**
```bash
# Reset migrations
python manage.py migrate --fake-initial
# Or drop and recreate database
dropdb eytgaming_db
createdb eytgaming_db
python manage.py migrate
```

## 📱 Next Steps

After successful installation:

1. ✅ Explore the admin panel
2. ✅ Create test user accounts
3. ✅ Review the project documentation
4. ✅ Start building tournament models (next phase)
5. ✅ Setup your development workflow

## 📞 Getting Help

If you encounter issues:

1. Check the logs in `logs/django.log`
2. Review Django error pages (DEBUG mode shows detailed errors)
3. Check PostgreSQL logs
4. Review Celery worker output
5. Consult Django documentation: https://docs.djangoproject.com/

## 🎉 Success!

You're now ready to start developing the EYTGaming platform!

**Important URLs:**
- Application: http://localhost:8000
- Admin Panel: http://localhost:8000/admin/
- API (future): http://localhost:8000/api/

**Default credentials:**
- Use the superuser account you created

---

Happy coding! 🚀