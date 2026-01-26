# ngrok Setup Guide for EYTGaming

## What is ngrok?

ngrok creates a secure tunnel from a public URL to your local development server, allowing you to:
- Test webhooks (Stripe, Discord, etc.)
- Share your local development with others
- Test on mobile devices
- Test OAuth callbacks

## Setup Complete ✅

The Django settings have been configured to work with ngrok automatically in DEBUG mode.

### Changes Made:

1. **ALLOWED_HOSTS** - Added ngrok domains:
   - `.ngrok-free.app`
   - `.ngrok.io`
   - `.ngrok.app`

2. **CSRF_TRUSTED_ORIGINS** - Added ngrok HTTPS URLs for CSRF protection

## How to Use

### 1. Start Your Django Server

```bash
python manage.py runserver
```

Your server should be running on `http://localhost:8000`

### 2. Start ngrok

In a **separate terminal**, run:

```bash
ngrok http 8000
```

### 3. Get Your Public URL

ngrok will display something like:

```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### 4. Access Your Site

You can now access your Django application at the ngrok URL:
- `https://abc123.ngrok-free.app` - Your site
- `https://abc123.ngrok-free.app/admin` - Django admin
- `https://abc123.ngrok-free.app/tournaments` - Tournament list

## Testing the Tournament System

With ngrok running, you can test:

1. **Tournament List Page**:
   ```
   https://your-ngrok-url.ngrok-free.app/tournaments/
   ```

2. **Search and Filters**:
   - Try searching for tournaments
   - Filter by status, game, format
   - Test pagination

3. **Mobile Testing**:
   - Open the ngrok URL on your phone
   - Test responsive layouts (1/2/3 column grids)

## Important Notes

### Free ngrok Limitations

- URL changes each time you restart ngrok
- Shows an interstitial page before your site (can be removed with paid plan)
- Limited to 40 connections/minute

### Security

- ngrok URLs are temporary and public
- Don't share sensitive data through ngrok URLs
- The configuration only works in DEBUG mode
- Production settings remain secure

### Webhook Testing

If you need to test webhooks (e.g., Stripe payments):

1. Get your ngrok URL
2. Update webhook URLs in the service (Stripe dashboard, Discord app, etc.)
3. Use the format: `https://your-ngrok-url.ngrok-free.app/webhooks/stripe/`

## Troubleshooting

### "Invalid HTTP_HOST header"

If you see this error:
1. Make sure ngrok is running
2. Verify the URL in your browser matches the ngrok forwarding URL
3. Restart Django server if needed

### CSRF Verification Failed

If you get CSRF errors:
1. Clear your browser cookies
2. Make sure you're using HTTPS (not HTTP) with ngrok
3. Restart Django server

### ngrok Not Found

Install ngrok:
```bash
# Windows (with Chocolatey)
choco install ngrok

# Or download from https://ngrok.com/download
```

## Alternative: Using a Static Domain

For a consistent URL, consider:
1. ngrok paid plan (static domains)
2. localtunnel: `npx localtunnel --port 8000`
3. serveo: `ssh -R 80:localhost:8000 serveo.net`

## Next Steps

Now that ngrok is configured, you can:
1. Test the tournament system on mobile devices
2. Share your development progress with team members
3. Test OAuth integrations with real callback URLs
4. Test payment webhooks with Stripe

## Current Task Status

✅ Task 1: Tournament List Template - **COMPLETED**
- Property tests for filtering (100+ iterations) - PASSED
- Property tests for card display - PASSED
- Real data integration - WORKING
- Search and filters - WORKING
- Responsive layout - WORKING
- Pagination - WORKING

You can now test all these features through your ngrok URL!
