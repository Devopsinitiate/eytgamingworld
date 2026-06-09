# CDN & Asset Pipeline Configuration

## Architecture

```
User → CloudFront CDN → Load Balancer → Django (static/media)
                        ↕
                   S3 Bucket (origin for static/media)
```

## S3 Static Files Setup

### 1. Create S3 Buckets

```bash
# Static files bucket
aws s3 mb s3://eytgaming-static

# Media files bucket
aws s3 mb s3://eytgaming-media
```

### 2. Configure IAM User

Create an IAM user with this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": ["arn:aws:s3:::eytgaming-static", "arn:aws:s3:::eytgaming-media"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::eytgaming-static/*",
                "arn:aws:s3:::eytgaming-media/*"
            ]
        }
    ]
}
```

### 3. Configure Django Settings

Add to `config/settings.py`:

```python
# S3 Storage for Static Files
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STATIC_BUCKET', default='eytgaming-static')
AWS_S3_REGION_NAME = config('AWS_S3_REGION', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = config('CLOUDFRONT_DOMAIN', default='')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = None

# Static files
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files (separate bucket for user uploads)
AWS_MEDIA_BUCKET_NAME = config('AWS_MEDIA_BUCKET', default='eytgaming-media')
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

### 4. Add to `.env`

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STATIC_BUCKET=eytgaming-static
AWS_MEDIA_BUCKET=eytgaming-media
AWS_S3_REGION=us-east-1
CLOUDFRONT_DOMAIN=d1234.cloudfront.net
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## CloudFront Distribution

### Origin Configuration

| Origin | Domain | Origin Path |
|--------|--------|-------------|
| Static | `eytgaming-static.s3.amazonaws.com` | `/` |
| Media  | `eytgaming-media.s3.amazonaws.com`  | `/` |
| App    | `app.eytgaming.com` (ALB)          | `/` |

### Cache Behaviors

| Path Pattern | Origin | TTL | Allowed Methods |
|---|---|---|---|
| `/static/*` | S3 Static | 1 year | GET, HEAD |
| `/media/*` | S3 Media | 1 year | GET, HEAD |
| `/health/*` | App | 0s | GET |
| `/api/*` | App | 0s | GET, POST, PUT, DELETE |
| Default `/*` | App | 0s | GET, HEAD, OPTIONS |

### WAF Rules

- Rate-based rule: 2000 req/5min per IP
- SQL injection detection
- XSS detection
- AWS managed rule group for common attacks

## Asset Optimization

### Image Optimization

```python
# settings.py
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=31536000',  # 1 year for immutable assets
}
```

### Implementation Checklist

- [ ] Create S3 buckets with blocking public access
- [ ] Create CloudFront distribution
- [ ] Update `django-storages` configuration
- [ ] Run `collectstatic`
- [ ] Update DNS (CNAME for CDN domain)
- [ ] Configure WAF rules
- [ ] Test cache invalidation: `aws cloudfront create-invalidation --distribution-id XYZ --paths "/*"`
- [ ] Verify SSL certificate (ACM)

## Migration from WhiteNoise

During the transition, run both systems in parallel:

```python
# Temporary: try S3, fall back to WhiteNoise
STATICFILES_STORAGE = 'config.storage.FallbackStorage'
```
