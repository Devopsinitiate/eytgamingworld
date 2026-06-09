# PythonAnywhere Free Tier - 500 Error Fix

## Problem
Getting "HTTP ERROR 500" after signup on PythonAnywhere free tier.

## Root Causes

The free tier doesn't support:
1. ❌ **Redis** - No background caching
2. ❌ **Celery** - No background tasks
3. ⚠️ **Email Verification** - May fail if SMTP not configured
4. ❌ **Rate Limiting with Redis**

## Quick Fix Steps

### Step 1: Update Your `.env` File on PythonAnywhere

SSH into PythonAnywhere or use the bash console, then edit your `.env`:

```bash
cd ~/eytgamingworld
nano .env
```

**Make these critical changes:**

```env
# 1. DISABLE EMAIL VERIFICATION (Critical!)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# 2. DISABLE RATE LIMITING (Requires Redis)
RATE_LIMIT_ENABLED=False
RATELIMIT_ENABLE=False
STORE_RATE_LIMIT_ENABLED=False

# 3. Make sure these are NOT set (remove or comment out)
# CELERY_BROKER_URL=
# REDIS_URL=
```

### Step 2: Update `settings.py` for Email Verification

You need to **DISABLE mandatory email verification** for signups. 

**Option A: Quick Fix - Make Email Verification Optional**

In your PythonAnywhere bash console:

```bash
cd ~/eytgamingworld
nano config/settings.py
```

Find line 227 and change:
```python
# OLD (causes 500 error):
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# NEW (allows signup without email):
ACCOUNT_EMAIL_VERIFICATION = 'optional'
# or completely disable:
ACCOUNT_EMAIL_VERIFICATION = 'none'
```

**Option B: Configure Email Properly**

If you want email verification, add to `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=noreply@eytgaming.com
```

> **Note**: For Gmail, you need an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

### Step 3: Reload Web App

After making changes:

1. Go to **Web** tab on PythonAnywhere
2. Click the green **Reload** button

### Step 4: Test Signup Again

Try signing up again. It should work now.

## Check Error Logs

If still getting 500 errors, check the error log:

1. Go to **Web** tab
2. Scroll to **Log files** section
3. Click on **Error log** link
4. Look at the most recent error

Common errors and fixes:

### Error: "No module named 'celery'"
**Fix**: Celery is trying to run. In `.env`:
```env
RATE_LIMIT_ENABLED=False
```

### Error: "ConnectionError: Error 111 connecting to localhost:6379"
**Fix**: Redis is trying to connect. In `.env`:
```env
RATE_LIMIT_ENABLED=False
RATELIMIT_ENABLE=False
```

### Error: "SMTPAuthenticationError" or email errors
**Fix**: Email sending is failing. In `settings.py`:
```python
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # or 'none'
```

Or configure email properly in `.env`.

### Error: "OperationalError" or database errors
**Fix**: Database credentials wrong. Check `.env`:
```env
DB_USER=eytgaming  # Your PythonAnywhere username
DB_PASSWORD=your_mysql_password
DB_HOST=eytgaming.mysql.pythonanywhere-services.com
DB_NAME=eytgaming$default  # username$databasename
```

## Recommended Configuration for Free Tier

**`.env` file:**

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=eytgaming.pythonanywhere.com

# Database
DB_USER=eytgaming
DB_PASSWORD=your_password
DB_HOST=eytgaming.mysql.pythonanywhere-services.com
DB_NAME=eytgaming$default
DB_PORT=3306

# Site
SITE_URL=https://eytgaming.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://eytgaming.pythonanywhere.com

# Email - CONSOLE BACKEND (no actual emails sent)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Disable features requiring Redis
RATE_LIMIT_ENABLED=False
RATELIMIT_ENABLE=False
STORE_RATE_LIMIT_ENABLED=False
```

**`config/settings.py` (line 227):**

```python
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # or 'none'
```

## After Fixing

1. Save all changes
2. Reload web app from Web tab
3. Clear browser cache/cookies
4. Try signup again

## Still Having Issues?

1. **Check the error log** - Web tab → Error log
2. **Check if migrations ran** - In bash console:
   ```bash
   cd ~/eytgamingworld
   workon eytgaming
   python manage.py migrate
   ```
3. **Verify static files** - In bash console:
   ```bash
   python manage.py collectstatic --noinput
   ```
4. **Check WSGI file** - Make sure it matches the template in `config/wsgi_pythonanywhere.py`

## Key Takeaway

For PythonAnywhere **FREE tier**, you MUST:
- ✅ Use console email backend OR configure SMTP
- ✅ Disable email verification OR set to 'optional'/'none'
- ✅ Disable all rate limiting
- ✅ Don't use Celery/Redis
- ✅ Use database cache instead of Redis cache
