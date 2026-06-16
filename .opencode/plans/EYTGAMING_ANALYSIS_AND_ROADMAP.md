# EYTGaming Platform — Comprehensive Analysis & World-Standard Remediation Roadmap

> **Audit Date:** 2026-05-31  
> **Scope:** Full-stack esports tournament & gaming community platform  
> **Stack:** Django 5.2 / PostgreSQL 15 / Redis / Celery / TailwindCSS / HTMX  
> **Objective:** Identify weaknesses and define a plan to elevate this platform to enterprise world-standard

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What This Project Does](#2-what-this-project-does)
3. [Architecture Overview](#3-architecture-overview)
4. [Current Strengths](#4-current-strengths)
5. [Weakness Analysis & Risk Rating](#5-weakness-analysis--risk-rating)
6. [World-Standard Remediation Plan](#6-world-standard-remediation-plan)
   - [Phase 0: Quick Wins (Week 1)](#phase-0-quick-wins-week-1)
   - [Phase 1: Security Hardening (Weeks 2–3)](#phase-1-security-hardening-weeks-2-3)
   - [Phase 2: Engineering Excellence (Weeks 4–6)](#phase-2-engineering-excellence-weeks-4-6)
   - [Phase 3: Testing & Reliability (Weeks 7–8)](#phase-3-testing--reliability-weeks-7-8)
   - [Phase 4: Monitoring & Observability (Weeks 9–10)](#phase-4-monitoring--observability-weeks-9-10)
   - [Phase 5: Architecture & Scale (Weeks 11–16)](#phase-5-architecture--scale-weeks-11-16)
   - [Phase 6: Culture & Process (Ongoing)](#phase-6-culture--process-ongoing)
7. [Key Performance Indicators](#7-key-performance-indicators)
8. [Risk Register](#8-risk-register)
9. [Appendix: Tooling Reference](#9-appendix-tooling-reference)

---

## 1. Executive Summary

EYTGaming is a **feature-rich, production-capable esports platform** with strong security fundamentals, comprehensive data models, and a well-organized Django architecture. The platform supports tournament management, coaching, team management, venue booking, payments (Stripe + Paystack), a full e-commerce store, notifications, and gamification.

**The good news:** The codebase is mature (7,355 Python files, 89 test files), well-structured with clean app separation, and already implements many security best practices — audit logging, XSS sanitization via `bleach`, rate limiting, account lockout after 5 failed attempts, CSRF protection, security headers (CSP, HSTS, X-Frame-Options), and webhook signature verification for payments.

**The gaps:** Secrets are exposed in plaintext (`.env` contains live Stripe/Paystack keys and DB password), there's no CI/CD pipeline, no static analysis/linting, no 2FA/MFA, push notifications are stubbed, code coverage has gaps, and the project has a single-developer bus factor with no code review process.

**The goal of this roadmap** is to systematically close every gap and graduate EYTGaming from "well-built monolith" to **world-standard enterprise platform** — resilient, observable, auditable, secure, and built for a team of any size.

---

## 2. What This Project Does

EYTGaming is a comprehensive esports community platform that provides:

- **Tournament Management** — Single/double elimination, Swiss, round-robin brackets with registration, check-in, match reporting, and live bracket updates via SSE
- **Coaching Platform** — Coach profiles, session booking, package purchases, reviews/ratings, Stripe-integrated payments
- **Team Management** — Team creation, member roles (captain/co-captain/member/substitute), join requests, recruiting
- **Venue Management** — Physical venue listings for local tournaments with location mapping, amenities, QR check-in
- **Payments** — Dual payment processor integration (Stripe + Paystack) with webhook verification, refunds, invoices
- **E-Commerce Store** — Full product catalog, cart, checkout, order management, inventory tracking, product reviews
- **Notifications** — Multi-channel notification system (in-app, email, push) with per-user preferences, quiet hours, templates
- **User Dashboard** — Activity feed, achievements/gamification (levels, points), profile completeness tracking, personalized recommendations
- **Authentication** — Email-based auth with Discord, Steam, and Google OAuth via django-allauth; role-based access (Player/Coach/Organizer/Admin/Parent)

---

## 3. Architecture Overview

```
eytgaming/
├── config/               # Django settings, ASGI/WSGI, Celery, URL routing
├── core/                 # Custom User model (UUID PK, email-based auth, RBAC), Game, SiteSettings
├── accounts/             # django-allauth adapter, social auth, signup forms
├── tournaments/          # Tournament engine — brackets, matches, participants, analytics, live updates
├── teams/                # Team CRUD, membership, signals for notifications
├── coaching/             # Coach profiles, session booking, packages, reviews
├── payments/             # Stripe + Paystack integration, Payment model, refunds
├── venues/               # Physical venue management, bookings, QR check-in
├── notifications/        # Notification model, preferences, templates, email/push delivery
├── dashboard/            # Activity feed, achievements, recommendations, profile completeness
├── store/                # Products, categories, cart, checkout, orders, reviews, rate limiting
├── security/             # Audit logging, security events, security headers middleware
├── templates/            # Server-rendered HTML templates (TailwindCSS)
├── static/               # CSS, JS (vanilla + modules), images, fonts, service worker
├── media/                # User-uploaded files
├── tests/                # Integration and unit test suites
└── fixtures/             # Initial seed data (games)
```

**Data Flow:**
- **Sync**: Django Views → Models → PostgreSQL (with Redis cache layer)
- **Async**: Celery workers handle notifications, tournament status updates, reminders, analytics
- **Real-time**: SSE (Server-Sent Events) via `live_updates.py` for tournament bracket updates
- **Payments**: Client → Stripe/Paystack Elements → Stripe API → Webhook → Django

---

## 4. Current Strengths

### Architecture & Design
- Clean Django app separation (10+ apps, each with single responsibility)
- UUID primary keys everywhere (no sequential ID enumeration attack surface)
- Custom email-based User model with role-based access control (5 distinct roles)
- Service layer pattern (`StripeService`, `TournamentSecurityValidator`, `TournamentAccessControl`)
- Generic Foreign Keys for extensible relations (notifications, activities, recommendations)
- Signals for decoupled cross-app communication (team → notifications)
- Docker Compose for reproducible development environments (5 services)
- Celery Beat scheduled tasks (tournament starts, session reminders, review requests, data cleanup)

### Security (Already Implemented)
| Measure | Implementation |
|---------|---------------|
| Security headers | `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| XSS prevention | `bleach` HTML sanitization, `escape()` on user strings, Django template auto-escaping |
| CSRF | Django CSRF middleware, SameSite=Lax cookies, custom failure view |
| Rate limiting | Custom middleware (10 req/min checkout, 100/min general), `django-ratelimit` |
| Account lockout | 5 failed attempts → `lock_account()` with reason tracking |
| Audit logging | `AuditLogMiddleware` tracks all POST/PUT/DELETE/PATCH; `AuditLog` + `SecurityEvent` models |
| Payment security | Stripe/Paystack webhook signature verification; no card data stored server-side |
| Authentication | django-allauth with Discord/Steam/Google OAuth; password validators |
| Transport security | HSTS (1 year, preload), HTTPS enforced in production, secure cookies |

### Code Quality
- 89 `test_*.py` files spanning unit, integration, and property-based tests (Hypothesis + factory_boy)
- Well-indexed database models (composite indexes on common query patterns)
- Comprehensive documentation across the repo (setup guides, testing guides, completion trackers)
- Formal `.kiro/specs/` specification system (requirements → design → tasks per feature)
- Service worker for offline caching and performance optimization
- Cross-browser compatibility testing suite

---

## 5. Weakness Analysis & Risk Rating

| ID | Weakness | Risk | Impact | Effort | Root Cause |
|----|----------|------|--------|--------|------------|
| **W1** | **Live secrets in `.env` file** — Stripe `sk_test_...`, Paystack keys, DB password `OriSha@OloKun01@` | **Critical** | Credential leak → fraudulent charges, data breach, financial liability | Small | Development convenience not cleaned up |
| **W2** | **Hardcoded fallback SECRET_KEY** in `settings.py:26` | **High** | Session forgery, CSRF token prediction if `.env` is missing | Small | Default from `django-admin startproject` left in place |
| **W3** | **No CI/CD pipeline** | **High** | No automated testing gate, manual deployment, no rollback strategy | Medium | Single-developer project |
| **W4** | **No static analysis / linting / formatting** — no `ruff`, `black`, `pre-commit` | **High** | Inconsistent code style, preventable bugs reach production, secrets can be committed | Small | Tooling not initialized |
| **W5** | **No 2FA / MFA** | **High** | Account takeover via credential compromise (especially admin/organizer accounts) | Medium | Not yet implemented |
| **W6** | **Push notifications are stubbed** — `send_push()` is a `TODO` placeholder | **Medium** | Broken UX promise, feature gap in multi-channel notification system | Medium | Incomplete implementation |
| **W7** | **`CSRF_COOKIE_HTTPONLY = False`** | **Medium** | XSS → CSRF token exfiltration (partially mitigated by other XSS defenses) | Small | Needed for JS AJAX access — solvable via dedicated endpoint |
| **W8** | **Single-developer bus factor** (15 commits, 1 author) | **Medium** | No code review, no knowledge distribution, project risk if developer unavailable | Large | Solo project |
| **W9** | **No pre-commit hooks** | **Medium** | Secrets, large files, debug statements can be committed | Small | Not configured |
| **W10** | **No dependency vulnerability scanning** | **Medium** | `pip` packages may have known CVEs; `pip-audit` not run | Small | Not implemented |
| **W11** | **No type checking** (mypy/pyright) | **Medium** | Type-related runtime bugs, poor DX, harder onboarding | Medium | Not configured |
| **W12** | **No API documentation** — DRF endpoints listed as "coming soon" | **Medium** | No integration surface for frontend/mobile clients; poor developer experience | Medium | Not implemented |
| **W13** | **Documentation sprawl** — 100+ `.md` completion-tracker files in project root | **Low** | Poor discoverability, maintenance overhead | Small | Feature-by-feature tracking without consolidation |
| **W14** | **No health check endpoints** | **Low** | Ops can't probe service health; containers restart blindly | Small | Not implemented |
| **W15** | **No structured logging** — standard `logging` module, not JSON | **Medium** | Hard to parse/search logs at scale; no log aggregation | Medium | Not implemented |
| **W16** | **No backup/restore procedures documented** | **Medium** | Data loss risk, no disaster recovery plan | Small | Not documented |
| **W17** | **`SESSION_ENGINE = 'db'`** (not Redis) | **Low** | Slower session lookups, no session invalidation at scale | Small | Fallback for environments without Redis |
| **W18** | **No automated SAST/DAST scanning** | **High** | Security vulnerabilities can ship undetected | Medium | Not implemented |

---

## 6. World-Standard Remediation Plan

### Phase 0: Quick Wins (Week 1)

Immediate, low-effort, high-impact fixes that should be done before anything else.

#### 0.1 — Rotate All Exposed Secrets
**Why:** W1 is critical. The `.env` file contains live (test-mode) credentials for Stripe, Paystack, and the database.

**Actions:**
1. Regenerate Stripe test keys (`sk_test_...` and `pk_test_...`) in Stripe dashboard
2. Regenerate the Stripe webhook secret
3. Regenerate Paystack keys in Paystack dashboard
4. Change the PostgreSQL database password
5. Generate a new Django `SECRET_KEY`:  
   `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
6. Update `.env` with all new values
7. Deactivate/delete old keys in all dashboards

**Verification:** `pip-audit` on env vars pattern; confirm old keys return 401/403.

#### 0.2 — Remove Fallback SECRET_KEY from Code
**Why:** W2 — the code has a hardcoded fallback that would be used if `.env` is misconfigured.

**File:** `config/settings.py:26`

**Actions:**
1. Change line 26 from:
   ```python
   SECRET_KEY = config('SECRET_KEY', default='django-insecure-)6&8w(h5*v(...)')
   ```
   To:
   ```python
   SECRET_KEY = config('SECRET_KEY')
   ```
2. Optionally add a startup-time guard:
   ```python
   from django.core.exceptions import ImproperlyConfigured
   if not SECRET_KEY:
       raise ImproperlyConfigured("SECRET_KEY must be set in environment")
   ```

**Verification:** App crashes with `ImproperlyConfigured` if `SECRET_KEY` is missing from environment.

#### 0.3 — Verify .env is Properly Git-Ignored
**Why:** Ensure secrets can never be committed.

**Actions:**
1. Confirm `.env` is in `.gitignore`
2. Run `git rm --cached .env` if `.env` was ever tracked historically
3. Run `git diff --cached` to verify no staged `.env` content

**Verification:** `git status` shows no `.env` changes; a fresh clone + `cp .env.example .env` is required.

#### 0.4 — Add SECRET_KEY Startup Check
**Why:** Fail fast on misconfiguration.

**File:** `config/settings.py`

**Action:** Add after `SECRET_KEY` assignment:
```python
assert SECRET_KEY, "SECRET_KEY must be set in environment"
```

#### 0.5 — Implement Push Notifications
**Why:** W6 — `send_push()` is a no-op placeholder that silently fails.

**Files affected:** `notifications/models.py`, `notifications/services.py` (new), `core/models.py`

**Actions:**
1. Choose provider: Firebase Cloud Messaging (FCM) or Web Push API (`pywebpush`)
2. Create `Device` model to store user push tokens:
   ```python
   class Device(models.Model):
       user = ForeignKey(User, on_delete=CASCADE, related_name='devices')
       push_token = CharField(max_length=500)
       platform = CharField(max_length=20)  # 'web', 'android', 'ios'
       created_at = DateTimeField(auto_now_add=True)
   ```
3. Create `send_push_notification()` service function
4. Add Web Push API subscription endpoint (`/notifications/subscribe/`)
5. Add `sw.js` push event handler for browser notifications
6. Replace the `send_push()` placeholder in `Notification` model

**Verification:** A notification with `delivery_methods=['push']` actually appears on the user's device.

---

### Phase 1: Security Hardening (Weeks 2–3)

#### 1.1 — Add Two-Factor Authentication (2FA)
**Why:** W5 — no MFA makes accounts vulnerable to credential compromise.

**Tools:** `django-otp` + `django-two-factor-auth`

**Actions:**
1. Install and configure `django-otp` and `django-two-factor-auth`
2. Add TOTP device support (Google Authenticator / Authy)
3. Generate backup codes for account recovery
4. Make 2FA **mandatory** for Admin and Organizer roles; optional for others
5. Create 2FA setup/enable/disable views at `/accounts/2fa/`
6. Update login flow to detect 2FA-enabled users and prompt for TOTP code
7. Add 2FA status indicator on dashboard security settings page

**Verification:** Admin user with 2FA enabled cannot complete login without valid TOTP code.

#### 1.2 — Session Management Hardening
**Why:** Sessions are stored in DB (slower, no easy invalidation). No "force logout all" capability.

**Actions:**
1. In production, switch `SESSION_ENGINE` to Redis-backed: `'redis_sessions.session'`
2. Add session invalidation on password change (override `User.save()` or use signal)
3. Add "force logout all sessions" admin action on User model
4. Create session list view in `/dashboard/security/` showing active sessions with device info
5. Add "logout this session" / "logout all other sessions" buttons

**Verification:** Changing password invalidates existing sessions; user must re-login.

#### 1.3 — Brute-Force Protection on All Auth Endpoints
**Why:** Only the default login has rate limiting; signup, password reset, and social auth endpoints are unprotected.

**Tools:** `django-ratelimit` (already installed)

**Actions:**
1. Apply `@ratelimit(key='ip', rate='10/m', method='POST')` to:
   - Login view
   - Signup view
   - Password reset request view
   - Password reset confirm view
2. Apply stricter `@ratelimit(key='ip', rate='3/m')` on payment-related auth views
3. Apply `@ratelimit(key='post:email', rate='5/h')` on password reset (prevent email enumeration)
4. Add reCAPTCHA v3 (invisible) to signup and login forms for headless browser protection

**Verification:** Sending 20 rapid POST requests to login returns 429; password reset rate-limited per email.

#### 1.4 — Add Security.txt & Vulnerability Disclosure Policy
**Why:** Industry standard for responsible disclosure; required for security maturity.

**Actions:**
1. Create `content/` in `config/urls.py` to serve `/.well-known/security.txt`:
   ```
   Contact: mailto:security@eytgaming.com
   Policy: https://eytgaming.com/security-policy
   Encryption: https://eytgaming.com/pgp-key.txt
   Preferred-Languages: en
   ```
2. Create `docs/security/VULNERABILITY_DISCLOSURE.md` with policy details

**Verification:** `curl https://eytgaming.com/.well-known/security.txt` returns valid RFC 9116 content.

#### 1.5 — CSRF Cookie Hardening
**Why:** W7 — `CSRF_COOKIE_HTTPONLY = False` allows JS to read the CSRF cookie.

**Actions:**
1. Evaluate each place JS reads CSRF token
2. Replace `document.cookie` CSRF reads with a dedicated API endpoint: `GET /api/csrf-token/`
3. Once JS no longer reads the cookie directly, set `CSRF_COOKIE_HTTPONLY = True`
4. Add `CSRF_USE_SESSIONS = True` for additional security (store token server-side)

**Trade-off:** Slight performance cost for storing CSRF tokens in session vs. cookie, but eliminates the exfiltration surface.

**Verification:** `document.cookie` in browser console no longer exposes `csrftoken`.

#### 1.6 — Dependency Vulnerability Scanning
**Why:** W10 — no automated scanning means known CVEs can persist indefinitely.

**Actions:**
1. Add `pip-audit` to development dependencies
2. Add `pip-audit` to CI pipeline (fail CI on any known vulnerability)
3. Add `npm audit` to CI for JS dependencies
4. Create `scripts/audit_deps.sh` for local scanning
5. Configure Dependabot or Renovate for automated dependency update PRs
6. Schedule weekly dependency review in team calendar

**Verification:** `pip-audit` returns zero known vulnerabilities on current `requirements.txt`.

---

### Phase 2: Engineering Excellence (Weeks 4–6)

#### 2.1 — CI/CD Pipeline (GitHub Actions)
**Why:** W3 — no automated testing or deployment pipeline.

**File:** `.github/workflows/ci.yml`

**Pipeline stages:**
1. **Quality Gate** — Runs on every push and PR:
   - `ruff check .` — lint errors
   - `ruff format --check .` — formatting consistency
   - `mypy .` — type safety
   - `pip-audit` — dependency vulnerabilities
   - `bandit -r . -f json` — SAST security scanning
2. **Test Suite** — Runs on every push and PR:
   - Service containers: PostgreSQL 15, Redis 7
   - `pytest --cov=. --cov-fail-under=80 -x --tb=short`
   - `npx jest` — JS unit tests
3. **Build & Deploy** — Runs on push to `main`:
   - Build Docker images
   - Push to container registry
   - Deploy to staging environment
   - Run smoke tests on staging
   - On tag (`v*`): deploy to production

**Branch protection rules:**
- Require CI to pass before merge
- Require at least 1 reviewer
- Require up-to-date branches
- Require signed commits

**Verification:** A PR with a lint error or failing test cannot be merged.

#### 2.2 — Code Quality Tooling
**Why:** W4 (no linting), W9 (no pre-commit hooks), W11 (no type checking)

**File:** `pyproject.toml`, `.pre-commit-config.yaml`

**Actions:**
1. Create `pyproject.toml` with:
   ```toml
   [tool.ruff]
   target-version = "py311"
   line-length = 100
   select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "ARG", "PL"]
   ignore = ["PLR0913"]  # Allow reasonable number of function args

   [tool.ruff.format]
   quote-style = "single"

   [tool.mypy]
   python_version = "3.11"
   strict = true
   plugins = ["mypy_django_plugin.plugin"]
   disallow_untyped_defs = true
   ```

2. Create `.pre-commit-config.yaml`:
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.x
       hooks:
         - id: ruff
         - id: ruff-format
     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.x
       hooks:
         - id: mypy
     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.x
       hooks:
         - id: detect-private-key
         - id: trailing-whitespace
         - id: end-of-file-fixer
         - id: check-yaml
         - id: debug-statements
     - repo: https://github.com/PyCQA/bandit
       rev: 1.x
       hooks:
         - id: bandit
           args: ["-r", "."]
   ```

3. Apply `ruff --fix` across the entire codebase once
4. Run `pre-commit install` — required for all developers
5. Document in `CONTRIBUTING.md`

**Verification:** `pre-commit run --all-files` passes cleanly with zero warnings.

#### 2.3 — Type Hint Coverage
**Why:** W11 — mypy can't enforce types that aren't written.

**Actions:**
1. Install `django-stubs` for better Django type inference
2. Add return type annotations to all views:
   ```python
   def tournament_detail(request: HttpRequest, slug: str) -> HttpResponse:
   ```
3. Add type annotations to all service-layer methods
4. Add type annotations to model methods and properties
5. Target `mypy --strict` coverage on `core/`, `payments/`, `security/` first, then expand app by app

**Verification:** `mypy . --strict` reports zero errors.

#### 2.4 — API Documentation (OpenAPI / Swagger)
**Why:** W12 — no API surface documentation; DRF endpoints are "coming soon."

**Actions:**
1. Install `drf-spectacular`
2. Add DRF router and viewsets for key resources (Tournaments, Teams, Coaching, etc.)
3. Generate OpenAPI schema via `drf-spectacular`
4. Serve Swagger UI at `/api/docs/` and ReDoc at `/api/redoc/`
5. Document all authentication methods (session, token, OAuth)
6. Add request/response examples for critical endpoints

**Verification:** Navigating to `/api/docs/` shows complete, interactive API documentation with authorizable endpoints.

#### 2.5 — Documentation Consolidation & Cleanup
**Why:** W13 — 100+ `.md` completion-tracker files in project root make it hard to find actual documentation.

**Actions:**
1. Archive all feature-completion `.md` files into `docs/_archive/`
2. Organize remaining documentation into a hierarchy:
   ```
   docs/
   ├── architecture/       # System design, data flow, decisions (ADRs)
   ├── development/        # Setup, contributing, coding standards
   ├── deployment/         # Docker, CI/CD, environments
   ├── security/           # Security model, incident response, vulnerability disclosure
   ├── api/                # API documentation, integration guides
   ├── ops/                # Monitoring, backups, disaster recovery
   └── _archive/           # Historical completion trackers
   ```
3. Update root `README.md` to reference `docs/` instead of listing all features inline
4. Consider `mkdocs` with Material theme for a searchable documentation site

**Verification:** Root directory is clean; `docs/` contains a browsable, well-organized hierarchy.

---

### Phase 3: Testing & Reliability (Weeks 7–8)

#### 3.1 — Expand Test Coverage to ≥ 80%
**Why:** Security, reliability, and refactoring confidence require comprehensive test coverage.

**Target apps (priority order):**
1. **Payments** — Edge cases: failed charges, retries, refunds, webhook replay, race conditions
2. **Tournaments** — Full lifecycle: registration → bracket generation → match reporting → completion
3. **Coaching** — Booking → payment → session → review flow
4. **Store** — Cart → checkout → payment → fulfillment flow
5. **Security** — XSS attempts, CSRF tokens, rate limit enforcement, permission checks

**Types of tests to add:**
- **View tests**: Every endpoint tested for correct status code, redirect, auth enforcement, and template used
- **Form tests**: Every form validated with valid/invalid/boundary data
- **Model tests**: Every model method/property/constraint tested
- **Security tests**: Unauthenticated access denied, XSS payloads sanitized, SQL injection blocked
- **Integration tests**: Cross-app workflows (e.g., tournament registration triggers notification)

**Tool:**
```bash
pytest --cov=. --cov-report=term-missing --cov-fail-under=80
```

**Verification:** `pytest --cov=.` reports ≥ 80% line coverage.

#### 3.2 — Add End-to-End Tests
**Why:** Unit tests can't catch frontend-backend integration failures.

**Tool:** Playwright (Puppeteer is already in `package.json`)

**Actions:**
1. Create `tests/e2e/` directory
2. Add E2E tests for critical user journeys:
   - User registration → email verification → login → dashboard
   - Browse tournaments → register → view bracket
   - Browse coaches → book session → complete payment
   - Browse store → add to cart → checkout
3. Add E2E tests for critical security flows:
   - Failed login → account lockout after 5 attempts
   - CSRF protection on forms
   - Rate limit exceeded

**Verification:** `npx playwright test` runs all E2E scenarios and passes.

#### 3.3 — Add Load & Performance Tests
**Why:** Ensure the platform handles expected concurrent load.

**Tool:** `locust`

**Actions:**
1. Create `tests/load/locustfile.py` with user behaviors:
   - Browse tournament listing (heavy read)
   - Register for tournament (write)
   - Checkout flow (payment write)
   - Dashboard loading (personalized query)
2. Set baseline performance budgets:
   - Page load < 500ms (p95)
   - API response < 200ms (p95)
   - Concurrent users: 100 baseline, 500 peak

**Verification:** Locust reports all metrics within budget for simulated user counts.

#### 3.4 — Expand Property-Based Tests
**Why:** Hypothesis tests find edge cases that example-based tests miss.

**Actions:**
1. Add stateful Hypothesis tests for tournament lifecycle (state machine testing)
2. Add Hypothesis tests for:
   - Payment amount calculations (rounding, currency conversion, fee splits)
   - Bracket generation (correct number of matches, no duplicate pairings)
   - Leaderboard calculations (correct sorting, tie-breaking)
3. Add data integrity property tests (no orphaned records, cascading correct)

**Verification:** `pytest --hypothesis-show-statistics` shows broad exploration coverage.

---

### Phase 4: Monitoring & Observability (Weeks 9–10)

#### 4.1 — Health Check Endpoints
**Why:** W14 — no way for orchestration to know if the app is healthy.

**Tool:** `django-health-check`

**Actions:**
1. Install `django-health-check`
2. Add backends:
   - `health_check.db` — database connectivity
   - `health_check.cache` — Redis/Database cache connectivity
   - `health_check.contrib.celery` — Celery worker availability
   - `health_check.contrib.celery.backends` — Celery result backend
   - `health_check.storage` — Media storage accessibility
3. Expose at `/health/` (with detailed view for ops, basic for public)
4. Configure Docker healthchecks to use these endpoints

**Verification:** `curl /health/` returns JSON with all backend statuses.

#### 4.2 — Structured Logging
**Why:** W15 — plain `logging` module output is not machine-parseable.

**Tool:** `structlog`

**Actions:**
1. Install `structlog` and configure it as the logging processor
2. Replace `logging.getLogger(...)` with `structlog.get_logger(...)` across all apps
3. Standardize log fields:
   ```json
   {
     "timestamp": "2026-05-31T12:00:00Z",
     "level": "INFO",
     "logger": "tournaments.views",
     "request_id": "abc-123",
     "user_id": "uuid-here",
     "path": "/tournaments/create/",
     "method": "POST",
     "duration_ms": 45,
     "event": "Tournament created",
     "tournament_id": "uuid-here"
   }
   ```
4. Configure JSON output for production, colored console for development
5. Add `RequestIDMiddleware` to inject unique request IDs for tracing

**Verification:** Production log output is valid JSON consumable by Logstash/Splunk/Datadog.

#### 4.3 — Error Tracking & APM (Sentry)
**Why:** Sentry DSN is configured but still set to placeholder `your_sentry_dsn`.

**Actions:**
1. Update `SENTRY_DSN` in `.env` with real DSN
2. Enable performance tracing (`traces_sample_rate=0.1` already configured)
3. Add custom instrumentation for critical paths:
   - Checkout flow
   - Bracket generation
   - Tournament registration
4. Set up Sentry alert rules:
   - Error spike > 10 in 5 minutes → notify
   - New error type → notify
   - Performance degradation (p95 > 1s) → notify
5. Add release tracking: `sentry_sdk.set_tag("release", __version__)`

**Verification:** Forced exception in development appears in Sentry dashboard within 30 seconds.

#### 4.4 — Metrics & Dashboards
**Why:** No visibility into system health, request rates, or database performance.

**Tools:** `django-prometheus` + Prometheus + Grafana

**Actions:**
1. Install `django-prometheus`
2. Instrument:
   - Request count, latency, and error rate by endpoint
   - Database query count and timing
   - Cache hit/miss ratio
   - Template rendering time
   - Celery task duration and queue depth
3. Expose `/metrics` endpoint
4. Create Grafana dashboard (provisioned as JSON) showing:
   - RED metrics (Rate, Errors, Duration) for all endpoints
   - Database connection pool usage
   - Cache hit ratio over time
   - Celery worker status and queue depth
   - 4xx/5xx rate

**Verification:** `curl /metrics` returns Prometheus-format metrics.

#### 4.5 — Automated Backups & Disaster Recovery
**Why:** W16 — no backup procedure means data loss is permanent.

**Actions:**
1. Create `scripts/backup_db.sh`:
   ```bash
   pg_dump -d eytgaming_db | gzip | aws s3 cp - s3://eytgaming-backups/db/$(date +%Y%m%d_%H%M%S).sql.gz
   ```
2. Create `scripts/restore_db.sh`:
   ```bash
   aws s3 cp s3://eytgaming-backups/db/$LATEST_BACKUP - | gunzip | psql -d eytgaming_db
   ```
3. Create `scripts/backup_media.sh` for user-uploaded media
4. Schedule daily backups via Celery Beat or system cron
5. Create `docs/ops/DISASTER_RECOVERY.md` with:
   - RPO (Recovery Point Objective): < 24 hours
   - RTO (Recovery Time Objective): < 1 hour
   - Step-by-step restore procedure
   - Contact tree for incident escalation

**Verification:** Run restore script on a staging database; `SELECT COUNT(*)` matches production.

---

### Phase 5: Architecture & Scale (Weeks 11–16)

#### 5.1 — API-First Architecture
**Why:** W12 — the current server-rendered approach limits growth. A proper API enables mobile apps, third-party integration, and frontend framework migration.

**Actions:**
1. Add DRF viewsets for all resources, building on existing models
2. Add API versioning: `/api/v1/tournaments/`, `/api/v1/teams/`, etc.
3. Add token authentication (JWT via `djangorestframework-simplejwt`) alongside session auth
4. Add proper permission classes (object-level via `django-guardian` already available)
5. Add throttling classes per endpoint (different limits for public vs. authenticated)
6. Add pagination with metadata (count, next, previous links)
7. Add filtering and search via `django-filter`
8. Document in `/api/docs/` via `drf-spectacular`

**Verification:** `curl /api/v1/tournaments/ -H "Authorization: Bearer <token>"` returns paginated JSON.

#### 5.2 — Identify Service Extraction Candidates
**Why:** As the platform grows, the monolith may need to split. Prepare the architecture.

**Actions:**
1. Wrap the following bounded contexts with clean internal interfaces:
   - **Payments Service** — Already has `StripeService`; ensure all payment access goes through it
   - **Notifications Service** — Create `send_notification()` facade that could become an HTTP/RPC call
   - **Tournament Engine** — Bracket generation is CPU-intensive; could be a separate service
2. Add feature flags (`waffle` or `gargoyle`) to toggle dependent service behavior
3. Document service boundaries in `docs/architecture/`

**Guideline:** Do NOT split services until traffic demands it, but design the interfaces as if each could become a service tomorrow.

#### 5.3 — Database Performance Optimization
**Why:** As user base grows, query performance becomes critical.

**Actions:**
1. Audit slow queries using Django Debug Toolbar (already installed) or `pg_stat_statements`
2. Add `select_related` / `prefetch_related` to all view querysets (many already done)
3. Add missing composite indexes based on actual query patterns
4. Add `CONN_MAX_AGE` for persistent database connections (already configured to 600s)
5. Add PgBouncer for connection pooling in Docker Compose
6. Consider materialized views for leaderboards and analytics

**Verification:** `EXPLAIN ANALYZE` on top 10 most-executed queries shows index scans, not sequential scans.

#### 5.4 — Caching Strategy
**Why:** Reduce database load for read-heavy pages (tournament listings, landing page).

**Actions:**
1. Add view-level caching for public pages:
   ```python
   from django.views.decorators.cache import cache_page
   
   @cache_page(60 * 15)  # 15 minutes
   def tournament_listing(request):
       ...
   ```
2. Add template fragment caching for dashboard partials
3. Add Redis caching for:
   - Tournament statistics (cache until next match completes)
   - Leaderboard data (refresh every 5 minutes)
   - User notification counts (short TTL)
4. Add cache invalidation hooks in model `save()` methods via signals

**Verification:** First request is slow; subsequent requests serve from cache with 10x speed improvement.

#### 5.5 — CDN & Asset Pipeline
**Why:** Static assets should be served from edge locations for global performance.

**Actions:**
1. Configure WhiteNoise with compression and caching headers (already done)
2. Add CDN (CloudFront or Cloudflare) as reverse proxy
3. Enable Django `MANIFEST_STORAGE` for cache-busting filenames (already configured)
4. Add automated image optimization (WebP conversion, responsive srcsets) on upload
5. Add lazy loading for images and iframes in templates
6. Add `preconnect` / `dns-prefetch` hints for external resources

**Verification:** Lighthouse audit scores > 90 for Performance, Best Practices, and Accessibility.

---

### Phase 6: Culture & Process (Ongoing)

#### 6.1 — Code Review Process
**Why:** W8 — single-developer bus factor. Code reviews catch bugs and distribute knowledge.

**Actions:**
1. Enable GitHub branch protection on `main`:
   - Require PR with at least 1 approval
   - Require CI to pass
   - Require up-to-date branch
   - Require signed commits
2. Create `.github/PULL_REQUEST_TEMPLATE.md` with checklist:
   ```markdown
   ## Description
   - What does this PR do?
   - Why is it needed?
   
   ## Checklist
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] Lint/type checks pass
   - [ ] No secrets committed
   - [ ] Migrations backwards-compatible
   ```
3. Establish definition of done:
   - Code reviewed
   - Tests passing
   - Docs updated
   - No `TODO` comments introduced
   - Performance impact assessed

#### 6.2 — Developer Onboarding
**Why:** New developers should be productive within hours, not days.

**Actions:**
1. Update `DEVELOPER_QUICK_START.md` with verified, step-by-step setup (including `.env.example`)
2. Create `CONTRIBUTING.md` with:
   - Branch naming convention (`feature/description`, `fix/description`, `chore/description`)
   - Commit message format (`type(scope): description`)
   - Coding standards (references `pyproject.toml` config)
   - Testing requirements (all tests must pass before PR)
3. Create `docs/development/` guides for each major subsystem:
   - How tournaments work (data flow, key models, entry points)
   - How payments work (Stripe integration, webhooks, idempotency)
   - How notifications work (templates, channels, delivery)
4. Create `docs/development/DEBUGGING.md` with common troubleshooting steps

**Verification:** A new developer with Django experience can set up, run tests, and make a change in under 30 minutes.

#### 6.3 — Dependency Update Cadence
**Why:** Regular updates prevent technical debt and close vulnerability windows.

**Actions:**
1. Enable Dependabot (GitHub native) for automated dependency PRs
2. Configure Dependabot to group minor/patch updates
3. Create `.github/dependabot.yml`:
   ```yaml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
     - package-ecosystem: "npm"
       directory: "/"
       schedule:
         interval: "monthly"
   ```
4. Maintain `requirements.in` (human-readable, loose pins) + `requirements.txt` (exact pins via `pip-compile`)
5. Schedule weekly 30-minute dependency review session

#### 6.4 — Security Incident Response Plan
**Why:** Speed of response determines the impact of a security incident.

**Actions:**
1. Create `docs/security/INCIDENT_RESPONSE.md`:
   ```
   # Incident Severity Levels
   - SEV1 (Critical): Data breach, payment fraud, service outage
   - SEV2 (High): Account takeover, XSS/CSRF vulnerability confirmed
   - SEV3 (Medium): Non-exploitable vulnerability found, rate limiting bypass
   - SEV4 (Low): Dependency CVE announced but not exploitable
   
   # Response Steps (SEV1)
   1. Acknowledge incident (5 min) — page on-call engineer
   2. Triage (15 min) — assess scope and impact
   3. Contain (30 min) — disable affected feature, revoke keys, block IPs
   4. Eradicate — deploy fix, rotate credentials
   5. Recover — restore from backup if needed
   6. Post-mortem — within 72 hours, blameless analysis
   ```
2. Document contact tree (who to call for each severity level)
3. Create post-mortem template (what happened, why, how to prevent, action items)
4. Conduct quarterly tabletop exercises (simulate a breach scenario)

**Verification:** A SEV1 tabletop exercise reveals mean time to acknowledge < 5 minutes.

---

## 7. Key Performance Indicators

| Area | Metric | Target | Phase |
|------|--------|--------|-------|
| Security | SAST scan (bandit) | 0 high-severity findings | Phase 1 |
| Security | Dependency vulnerabilities | 0 known CVEs | Phase 1 |
| Security | 2FA adoption | 100% Admin/Organizer accounts | Phase 1 |
| Testing | Code coverage | >= 80% line coverage | Phase 3 |
| Testing | E2E critical path coverage | 100% | Phase 3 |
| Performance | Lighthouse score | >= 90 on all 4 categories | Phase 5 |
| Performance | API p95 response time | < 300ms | Phase 5 |
| Performance | Page load (p95) | < 2 seconds | Phase 5 |
| Reliability | Uptime | 99.9% (8.76h downtime/year) | Phase 4 |
| Reliability | Backup RTO/RPO | RTO < 1hr, RPO < 24hrs | Phase 4 |
| Observability | Metrics coverage | All endpoints instrumented | Phase 4 |
| Observability | Log format | 100% structured JSON | Phase 4 |
| Engineering | CI pass rate on first attempt | > 95% | Phase 2 |
| Engineering | PR merge time (p50) | < 24 hours | Phase 6 |
| Engineering | Pre-commit hook violations | 0 on `main` branch | Phase 2 |

---

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation | Trigger |
|------|-----------|--------|------------|---------|
| Secrets leaked via public repo | Medium | Critical | Pre-commit `detect-private-key` hook, `.gitignore` confirmation, rotate on day zero | Accidental push |
| Database corruption/failure | Low | Critical | Daily encrypted backups to S3, quarterly restore drills | Disk failure, software bug |
| Single-developer knowledge loss | Medium | High | Documentation, PR reviews, pair programming, `docs/` guides | Developer unavailability |
| Dependency zero-day exploit | Medium | High | `pip-audit` in CI, Dependabot auto-PRs, prompt patching SLA (< 48h) | CVE publication |
| Production outage | Low | High | Health checks, automated rollback, documented runbooks, Docker healthchecks | Bad deploy, resource exhaustion |
| Account takeover (no 2FA) | Medium | High | 2FA enforcement for Admin/Organizer, rate limiting, suspicious login alerts | Credential stuffing |
| Payment processing failure | Low | Critical | Stripe webhook idempotency, automated retries, Sentry alert on failure | Stripe API outage |
| Data privacy breach (GDPR/CCPA) | Low | Critical | AuditLog for all data access, data anonymization, export/deletion endpoints | Insider threat, misconfiguration |

---

## 9. Appendix: Tooling Reference

| Tool | Purpose | Phase | Command / Config |
|------|---------|-------|-----------------|
| `ruff` | Python linter + formatter (replaces flake8 + isort + black) | Phase 2 | `ruff check .` / `pyproject.toml` |
| `mypy` | Static type checking for Python | Phase 2 | `mypy .` / `pyproject.toml` |
| `pre-commit` | Git hook automation | Phase 2 | `pre-commit run --all-files` |
| `bandit` | Python SAST security scanner | Phase 1 | `bandit -r .` |
| `pip-audit` | Python dependency vulnerability scanner | Phase 1 | `pip-audit` |
| `playwright` | E2E browser testing (JS) | Phase 3 | `npx playwright test` |
| `locust` | Load / performance testing (Python) | Phase 3 | `locust -f tests/load/locustfile.py` |
| `structlog` | Structured JSON logging | Phase 4 | `structlog.get_logger(...)` |
| `sentry-sdk` | Error tracking + APM | Phase 4 | Already in `requirements.txt` |
| `django-prometheus` | Prometheus metrics export | Phase 4 | `/metrics` endpoint |
| `grafana` | Metrics dashboards | Phase 4 | Provisioned JSON dashboard |
| `drf-spectacular` | OpenAPI schema + Swagger UI | Phase 2 | `/api/docs/` endpoint |
| `django-otp` | TOTP two-factor authentication | Phase 1 | `pip install django-otp` |
| `django-health-check` | Health check endpoints | Phase 4 | `/health/` endpoint |
| `pgbouncer` | PostgreSQL connection pooling | Phase 5 | Docker Compose service |
| `dependabot` | Automated dependency update PRs | Phase 6 | `.github/dependabot.yml` |
| `django-stubs` | Django type stubs for mypy | Phase 2 | `pip install django-stubs` |

---

## Summary Roadmap Timeline

```
Phase 0: Quick Wins                    Week 1
  ├── Rotate all exposed secrets          ██
  ├── Remove fallback SECRET_KEY          ██
  ├── Push notifications implementation   ██
  
Phase 1: Security Hardening             Weeks 2-3
  ├── Two-factor authentication (2FA)     ██████
  ├── Session management hardening        ██████
  ├── Brute-force protection              ██████
  ├── SAST scanning + pip-audit           ██████
  
Phase 2: Engineering Excellence         Weeks 4-6
  ├── CI/CD pipeline (GitHub Actions)     ███████
  ├── Ruff + mypy + pre-commit            ███████
  ├── Type hint coverage                  ███████
  ├── OpenAPI / Swagger docs              ███████
  └── Documentation consolidation         ███████
  
Phase 3: Testing & Reliability          Weeks 7-8
  ├── 80% code coverage target            ██████
  ├── End-to-end tests (Playwright)       ██████
  ├── Load tests (Locust)                 ██████
  └── Property-based test expansion       ██████
  
Phase 4: Monitoring & Observability     Weeks 9-10
  ├── Health check endpoints              ██████
  ├── Structured logging (structlog)      ██████
  ├── Sentry APM full configuration       ██████
  ├── Prometheus + Grafana dashboards     ██████
  └── Automated backups + DR plan         ██████
  
Phase 5: Architecture & Scale           Weeks 11-16
  ├── API-first (DRF + JWT)               ████████████
  ├── Service extraction prep             ████████████
  ├── Database performance optimization   ████████████
  ├── Caching strategy (Redis)            ████████████
  └── CDN + asset pipeline                ████████████

Phase 6: Culture & Process              Ongoing
  ├── Code review process                 ████████████████
  ├── Developer onboarding docs           ████████████████
  ├── Dependency update cadence           ████████████████
  └── Security incident response plan     ████████████████
```

**Total estimated effort:** 16 weeks to complete all phases, with Culture & Process continuing indefinitely.

---

*This document is a living roadmap. Reassess quarterly, update risks, and celebrate each phase completion.*

**Start with Phase 0 — rotate those secrets today. Everything else builds on a secure foundation.**
