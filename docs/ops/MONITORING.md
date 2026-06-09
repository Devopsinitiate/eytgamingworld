# Monitoring & Observability

## Health Checks

The application exposes health check endpoints at `/health/`:

| Endpoint | Purpose | Expected Status |
|---|---|---|
| `/health/` | Overall health | 200 |
| `/health/db/` | Database connectivity | 200 / 503 |
| `/health/cache/` | Cache connectivity | 200 / 503 |
| `/health/redis/` | Detailed Redis check | 200 / 503 |
| `/health/ready/` | Readiness probe (k8s) | 200 / 503 |
| `/health/live/` | Liveness probe (k8s) | 200 |
| `/health/metrics/` | Prometheus metrics | 200 |

## Prometheus

Metrics are exposed at `/health/metrics/` in Prometheus text format.

### Scrape Configuration (prometheus.yml)

```yaml
scrape_configs:
  - job_name: 'eytgaming'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/health/metrics/'
```

### Available Metrics

- `eyt_gaming_info` — Static app info (version, environment)
- `eyt_db_up` — Database connection status (1/0)
- `eyt_cache_up` — Cache connection status (1/0)
- `eyt_users_total` — Active user count
- `eyt_tournaments_total` — Tournament count
- `eyt_coaches_total` — Active coach count
- `eyt_sessions_total` — Coaching session count
- `eyt_payments_total` — Payment count
- `eyt_notifications_total` — Notification count

## Sentry APM

Sentry is configured with:
- Traces sample rate: 0.2 (captures 20% of transactions)
- Profiles sample rate: 0.1 (captures 10% of traces with profiling)
- Send default PII: disabled
- Environment: auto-detected from DEBUG setting

### Setup

Set `SENTRY_DSN` in `.env`:
```
SENTRY_DSN=https://your-dsn@sentry.io/your-project
```

## Alerting Recommendations

### Critical Alerts (PagerDuty / Opsgenie)

- **App down**: `/health/` returns non-200 for >1 minute
- **Database down**: `/health/db/` returns 503
- **High error rate**: >5% HTTP 5xx in 5-minute window
- **Payment failures**: >3 failed payment intents in 5 minutes

### Warning Alerts (Email / Slack)

- **Cache down**: `/health/cache/` returns 503 (fallback degrades performance)
- **High latency**: P95 response time >2s
- **Low disk space**: <10% remaining on logs partition
- **Certificate expiry**: SSL certificate expires within 14 days
