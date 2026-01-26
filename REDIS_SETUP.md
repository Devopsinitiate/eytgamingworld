# Redis Setup Guide

## Current Configuration

The application is now configured to work **without Redis in development mode**:

- **Development (DEBUG=True)**: Uses database-backed cache and sessions
- **Production (DEBUG=False)**: Uses Redis for cache and sessions

## Why This Change?

Redis was causing connection errors because it wasn't running on your system. The application now uses Django's database cache in development, which requires no additional services.

## If You Want to Use Redis (Optional)

### Windows Installation

1. **Download Redis for Windows**:
   - Visit: https://github.com/microsoftarchive/redis/releases
   - Download the latest `.msi` installer
   - Install Redis

2. **Start Redis**:
   ```bash
   redis-server
   ```

3. **Verify Redis is Running**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### Using Docker (Recommended)

If you have Docker installed:

```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### Update Configuration for Redis

If you want to use Redis in development, update `.env`:

```env
# Add this to use Redis in development
USE_REDIS=true
```

Then update `config/settings.py` to check this flag.

## Current Setup Benefits

✅ No external dependencies required for development  
✅ Simpler setup for new developers  
✅ Sessions persist in database (survive server restarts)  
✅ Cache works immediately without configuration  
✅ Production can still use Redis for better performance  

## Testing

You can now:
1. Start the server: `python manage.py runserver`
2. Access admin: http://127.0.0.1:8000/admin/
3. Login with: `admin@eytgaming.com` / `admin123`

No Redis required!
