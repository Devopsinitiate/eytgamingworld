# Database Performance Optimization

## Current Index Analysis

### Required Additional Indexes

Run these migrations to add performance-critical indexes:

```sql
-- Coaching: frequently filtered by status + coach/student
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_coaching_sessions_coach_status
ON coaching_sessions (coach_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_coaching_sessions_student_status
ON coaching_sessions (student_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_coaching_sessions_scheduled_start
ON coaching_sessions (scheduled_start);

-- Notifications: filtered by user + read status (most common query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_read
ON notifications (user_id, read)
WHERE read = false;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_created
ON notifications (user_id, created_at DESC);

-- Payments: filtered by user + status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_user_status
ON payments (user_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_stripe_payment_intent
ON payments (stripe_payment_intent_id)
WHERE stripe_payment_intent_id != '';

-- Tournaments: filtered by status + game
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tournaments_status_game
ON tournaments (status, game_id);

-- Security events: filtered by IP + not resolved
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_ip_unresolved
ON security_events (ip_address)
WHERE resolved = false;

-- Audit logs: time-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp
ON audit_logs (timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action
ON audit_logs (user_id, action, timestamp DESC);
```

## Query Optimization Patterns

### 1. N+1 Query Prevention

Always use `select_related()` for ForeignKey/OneToOne relationships
and `prefetch_related()` for ManyToMany/reverse relations:

```python
# Bad: N+1 queries
sessions = CoachingSession.objects.all()
for s in sessions:
    print(s.coach.user.email)  # Extra query per session

# Good: Single query with JOIN
sessions = CoachingSession.objects.select_related('coach__user', 'student', 'game')
```

### 2. Pagination

Use cursor-based pagination for large datasets instead of offset/limit:

```python
from django.core.paginator import Paginator

# Bad for large datasets
page = request.GET.get('page', 1)
paginator = Paginator(Payment.objects.all(), 25)

# Better: keyset pagination (requires unique sort field)
payments = Payment.objects.filter(created_at__lt=last_seen).order_by('-created_at')[:25]
```

### 3. Query Counting Optimization

Avoid `len(queryset)` — use `queryset.count()` instead:

```python
# Bad: loads all objects into memory
user_count = len(User.objects.all())

# Good: single COUNT query
user_count = User.objects.count()
```

### 4. Bulk Operations

Use bulk operations for batch updates instead of per-row updates:

```python
# Bad: N queries
notifications = Notification.objects.filter(user=user, read=False)
for n in notifications:
    n.read = True
    n.save()

# Good: 1 query
Notification.objects.filter(user=user, read=False).update(
    read=True, read_at=timezone.now()
)
```

### 5. Partial Updates

Use `update_fields` to avoid saving all fields:

```python
# Bad: saves all model fields
user.save()

# Good: saves only changed fields
user.save(update_fields=['total_points', 'level'])
```

## Migration Strategy

1. Add indexes via Django migrations (`./manage.py makemigrations`)
2. For tables with >100k rows, use `CREATE INDEX CONCURRENTLY` in raw SQL
3. Run `ANALYZE` after adding indexes to update query planner statistics
4. Monitor slow query log and add missing indexes

## Connection Pooling

Production settings should include connection pooling:

```python
# In settings.py
DATABASES['default']['OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
}
```
