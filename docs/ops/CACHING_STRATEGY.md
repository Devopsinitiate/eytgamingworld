# Caching Strategy

## Cache Architecture

### Layer 1: Application Cache (Redis)

- **Purpose**: Reduce database load for frequently accessed data
- **Backend**: `django_redis.cache.RedisCache` (production)
- **Fallback**: `DatabaseCache` (development)
- **Default TTL**: 300 seconds (5 minutes)

### Layer 2: Browser Cache (HTTP Headers)

- **Purpose**: Reduce server load for static/lists
- **Static files**: Cache-Control: public, max-age=31536000 (1 year)
- **API responses**: Conditional ETag/Last-Modified headers

### Layer 3: CDN (Production Only)

- **Purpose**: Serve static/media assets from edge locations
- **Service**: CloudFront / CloudFlare

## Cache Key Convention

```
eytgaming:{app}:{model}:{id}:{field}
eytgaming:{app}:{view}:{params_hash}
```

Examples:
```
eytgaming:coaching:coach_list:page=1
eytgaming:tournaments:detail:slug=my-tournament
eytgaming:notifications:unread:user_id=42
```

## What to Cache

### High Priority (Cache Heavily)

| Data | Key Pattern | TTL | Invalidation |
|---|---|---|---|
| Coach list (public) | `coaching:list:page:{n}` | 300s | On coach create/update |
| Tournament list (public) | `tournaments:list:{params_hash}` | 300s | On tournament create/update |
| Game list | `games:list` | 600s | Admin action (rare) |
| Site settings | `core:site_settings` | 3600s | Admin action |
| Public venue list | `venues:list:{params_hash}` | 300s | On venue create/update |

### Medium Priority

| Data | Key Pattern | TTL | Invalidation |
|---|---|---|---|
| User profile (public) | `users:profile:{id}` | 120s | On profile update |
| Coach detail | `coaching:detail:{id}` | 300s | On coach update |
| Tournament detail | `tournaments:detail:{slug}` | 120s | On match/participant update |
| Available slots | `coaching:slots:{coach_id}:{date}` | 60s | On booking |

### Low Priority (Don't Cache or Short TTL)

- User-specific data (dashboard, notifications, payment history)
- Authentication/CSRF tokens
- Admin views

## Implementation

### View-Level Caching Decorator

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutes
def coach_list_view(request):
    # ... expensive query
```

### Template Fragment Caching

```django
{% load cache %}
{% cache 300 coach_card coach.id %}
  {% include "coaching/_coach_card.html" %}
{% endcache %}
```

### Low-Level Cache API

```python
from django.core.cache import cache

def get_coach_stats(coach_id):
    key = f'coaching:stats:{coach_id}'
    stats = cache.get(key)
    if stats is None:
        stats = CoachProfile.objects.get(id=coach_id)
        stats.total_reviews  # force evaluate
        cache.set(key, stats, 300)
    return stats
```

### Cache Invalidation

Use Django signals to invalidate caches on model changes:

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=CoachProfile)
def invalidate_coach_cache(sender, instance, **kwargs):
    cache.delete_pattern('coaching:*')
```

## Monitoring

Track these cache metrics:
- **Hit rate**: `cache.get(key)` vs `None` ratio (target: >80%)
- **Miss latency**: Time spent regenerating after a cache miss
- **Invalidation rate**: How often caches are cleared (avoid excessive invalidation)
- **Memory usage**: Redis `INFO memory` (monitor for evictions)
