# EYTGaming Store - Security Documentation

## Overview

This document provides comprehensive security documentation for the EYTGaming Store e-commerce platform. It covers all implemented security features, best practices for maintenance, and incident response procedures.

**Last Updated:** February 9, 2026  
**Version:** 1.0  
**Security Audit Status:** ✅ PASSED

---

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Implemented Security Features](#implemented-security-features)
3. [Security Best Practices for Maintenance](#security-best-practices-for-maintenance)
4. [Incident Response Procedures](#incident-response-procedures)
5. [Security Testing](#security-testing)
6. [Compliance and Standards](#compliance-and-standards)
7. [Security Contacts](#security-contacts)

---

## Security Architecture

### Defense-in-Depth Strategy

The EYTGaming Store implements a multi-layered security approach:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                   │
│ - HTTPS enforcement                                          │
│ - Secure cookie flags (HTTPOnly, Secure, SameSite)         │
│ - HSTS headers                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Application Security                               │
│ - CSRF protection                                           │
│ - Rate limiting                                             │
│ - Input validation and sanitization                         │
│ - SQL injection prevention (Django ORM)                     │
│ - XSS prevention (template auto-escaping)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Authentication & Authorization                      │
│ - Session-based authentication                              │
│ - Permission checks                                         │
│ - Account lockout after failed attempts                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Payment Security                                    │
│ - PCI DSS compliance via Stripe/Paystack                    │
│ - No card data stored on server                             │
│ - Webhook signature verification                            │
│ - Secure payment token handling                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Data Security                                       │
│ - Encrypted database connections                            │
│ - Secure password hashing (PBKDF2)                          │
│ - Audit logging for security events                         │
│ - Regular security log review                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Implemented Security Features

### 1. SQL Injection Prevention

**Implementation:**
- Django ORM is used exclusively for database queries
- All user inputs are parameterized through ORM
- Search queries are sanitized using `InputValidator.sanitize_search_query()`

**Code Location:** `store/utils.py` - `InputValidator` class

**Testing:** `store/tests/security/test_security_audit.py` - `SQLInjectionTests`

**Verification:**
```python
# Example of safe query
products = Product.objects.filter(name__icontains=sanitized_query)
```

### 2. Cross-Site Scripting (XSS) Prevention

**Implementation:**
- Django template auto-escaping is enabled (default)
- User-generated content (reviews, comments) is sanitized before storage
- HTML tags are stripped from user input using `bleach` library

**Code Location:** `store/utils.py` - `InputValidator.sanitize_html()`

**Testing:** `store/tests/security/test_security_audit.py` - `XSSPreventionTests`

**Verification:**
```python
# All templates use {{ variable }} which auto-escapes
# Manual escaping: {{ variable|escape }}
```

### 3. Cross-Site Request Forgery (CSRF) Protection

**Implementation:**
- Django CSRF middleware is enabled
- All forms include `{% csrf_token %}`
- AJAX requests include CSRF token in headers
- CSRF cookies use Secure and SameSite flags

**Code Location:** 
- Middleware: `config/settings.py` - `MIDDLEWARE`
- Templates: All forms include CSRF token

**Testing:** `store/tests/security/test_security_audit.py` - `CSRFProtectionTests`

**Configuration:**
```python
# settings.py
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

### 4. Rate Limiting

**Implementation:**
- Custom `RateLimitMiddleware` tracks requests per IP
- Default limit: 100 requests per minute
- Checkout endpoints: 10 requests per minute
- Rate limit violations are logged

**Code Location:** `store/middleware.py` - `RateLimitMiddleware`

**Testing:** `store/tests/security/test_security_audit.py` - `RateLimitingTests`

**Configuration:**
```python
# Adjust limits in middleware.py
def get_limit(self, path):
    if '/checkout/' in path:
        return 10  # Stricter for checkout
    return 100  # Default
```

### 5. Authentication Enforcement

**Implementation:**
- `@login_required` decorator on protected views
- Checkout, wishlist, and order history require authentication
- Session timeout after inactivity

**Code Location:** `store/views.py` - View decorators

**Testing:** `store/tests/security/test_security_audit.py` - `AuthenticationEnforcementTests`

**Protected Endpoints:**
- `/store/checkout/` - Checkout flow
- `/store/wishlist/` - Wishlist management
- `/store/reviews/submit/` - Review submission

### 6. Authorization Checks

**Implementation:**
- Admin panel requires `is_staff` and `is_superuser` permissions
- Users can only access their own orders and data
- Review submission requires verified purchase

**Code Location:** `store/admin.py`, `store/views.py`

**Testing:** `store/tests/security/test_security_audit.py` - `AuthorizationTests`

**Example:**
```python
# Only allow users to view their own orders
orders = Order.objects.filter(user=request.user)
```

### 7. Secure Session Management

**Implementation:**
- Session cookies use HTTPOnly, Secure, and SameSite flags
- Session timeout: 2 weeks (configurable)
- Session data stored in database (not cookies)

**Code Location:** `config/settings.py`

**Configuration:**
```python
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
```

### 8. Payment Security

**Implementation:**
- Stripe and Paystack SDKs handle all card data
- No card numbers stored on server
- Payment tokens are single-use
- Webhook signatures are verified before processing

**Code Location:** `store/managers.py` - Payment processor classes

**Testing:** `store/tests/security/test_security_audit.py` - `PaymentSecurityTests`

**Critical Rules:**
- ❌ NEVER log card numbers, CVV, or full card data
- ✅ ALWAYS verify webhook signatures
- ✅ ALWAYS use HTTPS for payment communications

### 9. Webhook Signature Verification

**Implementation:**
- Stripe webhooks verify signature using `stripe.Webhook.construct_event()`
- Paystack webhooks verify HMAC signature
- Invalid signatures are rejected with 400 error

**Code Location:** `store/views.py` - Webhook handlers

**Testing:** `store/tests/security/test_security_audit.py` - `WebhookSignatureVerificationTests`

**Example:**
```python
# Stripe verification
event = stripe.Webhook.construct_event(
    payload, signature, settings.STRIPE_WEBHOOK_SECRET
)

# Paystack verification
computed_hash = hmac.new(
    settings.PAYSTACK_SECRET_KEY.encode(),
    payload,
    hashlib.sha512
).hexdigest()
```

### 10. Input Validation

**Implementation:**
- `InputValidator` utility class validates all user inputs
- Quantity: 1-100 range
- Email: Format validation and normalization
- Search queries: Sanitized to remove special characters

**Code Location:** `store/utils.py` - `InputValidator`

**Testing:** `store/tests/security/test_security_audit.py` - `InputValidationTests`

**Validation Methods:**
- `validate_quantity(quantity)` - Validates product quantities
- `validate_email(email)` - Validates and normalizes emails
- `sanitize_search_query(query)` - Sanitizes search inputs
- `sanitize_html(content)` - Removes dangerous HTML

### 11. File Upload Validation

**Implementation:**
- Admin forms validate file types (JPEG, PNG, WebP only)
- File size limit: 5MB per image
- File content validation (not just extension)

**Code Location:** `store/admin.py` - Admin form configuration

**Testing:** `store/tests/security/test_security_audit.py` - `FileUploadValidationTests`

**Allowed Types:**
- `image/jpeg`
- `image/png`
- `image/webp`

### 12. Security Event Logging

**Implementation:**
- `SecurityLogger` utility logs all security events
- Failed logins, payment failures, rate limit violations
- No sensitive data in logs
- Log rotation: Daily, 90-day retention

**Code Location:** `store/utils.py` - `SecurityLogger`

**Testing:** `store/tests/security/test_security_audit.py` - `SecurityLoggingTests`

**Logged Events:**
- Failed login attempts (with IP address)
- Payment failures (without card data)
- Rate limit violations
- CSRF validation failures
- File upload rejections

---

## Security Best Practices for Maintenance

### Code Review Checklist

When reviewing or modifying code, always check:

- [ ] **No raw SQL queries** - Use Django ORM exclusively
- [ ] **User input is validated** - Use `InputValidator` for all user inputs
- [ ] **Templates auto-escape** - Use `{{ variable }}` not `{{ variable|safe }}`
- [ ] **Forms include CSRF token** - `{% csrf_token %}` in all forms
- [ ] **Protected views use decorators** - `@login_required` where needed
- [ ] **No sensitive data in logs** - Never log passwords, card numbers, tokens
- [ ] **Webhook signatures verified** - Always verify before processing
- [ ] **Database transactions used** - Use `transaction.atomic()` for critical operations

### Dependency Management

**Keep dependencies updated:**

```bash
# Check for security updates
pip list --outdated

# Update specific package
pip install --upgrade django

# Update all packages (test thoroughly)
pip install --upgrade -r requirements.txt
```

**Critical packages to monitor:**
- Django (security patches)
- Stripe SDK (API changes)
- Paystack SDK (API changes)
- Pillow (image processing vulnerabilities)

### Environment Variables

**Never commit sensitive data to version control:**

```bash
# .env file (never commit)
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
PAYSTACK_SECRET_KEY=sk_test_...
DATABASE_URL=postgresql://...
```

**Use environment variables in settings:**

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
```

### Database Security

**Best practices:**

1. **Use encrypted connections:**
   ```python
   DATABASES = {
       'default': {
           'OPTIONS': {
               'sslmode': 'require',
           }
       }
   }
   ```

2. **Regular backups:**
   ```bash
   # Daily automated backups
   pg_dump eytgaming_db > backup_$(date +%Y%m%d).sql
   ```

3. **Principle of least privilege:**
   - Application database user should not have DROP/CREATE permissions
   - Use separate user for migrations

### Password Security

**Django's password hashing is secure by default:**

```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]
```

**Password requirements:**
- Minimum 8 characters
- Must include uppercase, lowercase, numbers
- Cannot be common passwords

### HTTPS Enforcement

**Production settings:**

```python
# settings.py (production)
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Regular Security Audits

**Schedule:**
- **Weekly:** Review security logs for anomalies
- **Monthly:** Run automated security tests
- **Quarterly:** Manual penetration testing
- **Annually:** Third-party security audit

**Automated testing:**

```bash
# Run security audit tests
python manage.py test store.tests.security.test_security_audit

# Check for known vulnerabilities
pip install safety
safety check

# Django security check
python manage.py check --deploy
```

---

## Incident Response Procedures

### Incident Classification

**Severity Levels:**

- **Critical (P0):** Active breach, data exposure, payment system compromise
- **High (P1):** Vulnerability discovered, potential data exposure
- **Medium (P2):** Security misconfiguration, non-critical vulnerability
- **Low (P3):** Security improvement opportunity

### Response Workflow

#### 1. Detection and Identification

**Indicators of compromise:**
- Unusual spike in failed login attempts
- Unexpected payment failures
- Rate limit violations from multiple IPs
- Suspicious database queries in logs
- Webhook signature verification failures

**Monitoring tools:**
- Security event logs: `/var/log/eytgaming/security.log`
- Django admin: Security event dashboard
- Payment gateway dashboards (Stripe, Paystack)

#### 2. Containment

**Immediate actions for critical incidents:**

1. **Isolate affected systems:**
   ```bash
   # Disable affected endpoints
   # Add to urls.py temporarily
   path('store/', lambda r: HttpResponse('Maintenance', status=503))
   ```

2. **Revoke compromised credentials:**
   ```bash
   # Rotate API keys immediately
   # Update .env file
   STRIPE_SECRET_KEY=new_key
   PAYSTACK_SECRET_KEY=new_key
   
   # Restart application
   sudo systemctl restart gunicorn
   ```

3. **Block malicious IPs:**
   ```python
   # Add to middleware or firewall
   BLOCKED_IPS = ['1.2.3.4', '5.6.7.8']
   ```

#### 3. Investigation

**Collect evidence:**

1. **Review security logs:**
   ```bash
   # Check for suspicious activity
   grep "SECURITY" /var/log/eytgaming/security.log
   grep "Failed login" /var/log/eytgaming/security.log
   ```

2. **Database audit:**
   ```sql
   -- Check for unauthorized changes
   SELECT * FROM django_admin_log 
   WHERE action_time > 'incident_start_time'
   ORDER BY action_time DESC;
   ```

3. **Payment transaction review:**
   - Check Stripe dashboard for unusual transactions
   - Review Paystack dashboard for anomalies

#### 4. Eradication

**Remove threat:**

1. **Patch vulnerabilities:**
   ```bash
   # Update dependencies
   pip install --upgrade django
   pip install --upgrade stripe
   
   # Apply security patches
   python manage.py migrate
   ```

2. **Clean compromised data:**
   ```python
   # Remove malicious content
   ProductReview.objects.filter(
       comment__contains='<script>'
   ).delete()
   ```

3. **Reset affected accounts:**
   ```python
   # Force password reset for affected users
   User.objects.filter(
       last_login__gte=incident_start
   ).update(password='!')
   ```

#### 5. Recovery

**Restore normal operations:**

1. **Verify system integrity:**
   ```bash
   # Run security tests
   python manage.py test store.tests.security
   
   # Check deployment configuration
   python manage.py check --deploy
   ```

2. **Re-enable services:**
   ```bash
   # Remove maintenance mode
   # Restore normal URL routing
   sudo systemctl restart gunicorn
   ```

3. **Monitor closely:**
   - Watch logs for 24-48 hours
   - Verify no recurring issues

#### 6. Post-Incident Review

**Document and learn:**

1. **Incident report template:**
   ```markdown
   # Security Incident Report
   
   **Date:** YYYY-MM-DD
   **Severity:** P0/P1/P2/P3
   **Incident ID:** INC-YYYYMMDD-001
   
   ## Summary
   Brief description of incident
   
   ## Timeline
   - HH:MM - Detection
   - HH:MM - Containment
   - HH:MM - Resolution
   
   ## Root Cause
   What caused the incident
   
   ## Impact
   - Users affected: X
   - Data exposed: Yes/No
   - Financial impact: $X
   
   ## Actions Taken
   1. Action 1
   2. Action 2
   
   ## Lessons Learned
   - What went well
   - What could be improved
   
   ## Follow-up Actions
   - [ ] Action 1 (Owner: Name, Due: Date)
   - [ ] Action 2 (Owner: Name, Due: Date)
   ```

2. **Update security measures:**
   - Implement additional monitoring
   - Add new security tests
   - Update documentation

### Communication Plan

**Internal communication:**
- Notify development team immediately
- Update management within 1 hour
- Daily status updates during incident

**External communication:**
- Notify affected users within 24 hours (if data breach)
- Provide clear, honest information
- Offer remediation steps (password reset, etc.)

**Template for user notification:**
```
Subject: Important Security Notice - EYTGaming Store

Dear [User],

We are writing to inform you of a security incident that may have 
affected your account. On [DATE], we discovered [BRIEF DESCRIPTION].

What happened:
[CLEAR EXPLANATION]

What information was involved:
[SPECIFIC DATA TYPES]

What we're doing:
[ACTIONS TAKEN]

What you should do:
1. Reset your password immediately
2. Review your recent orders
3. Monitor your payment methods

We take security seriously and apologize for any inconvenience.

For questions, contact: security@eytgaming.com

Sincerely,
EYTGaming Security Team
```

---

## Security Testing

### Automated Testing

**Run security test suite:**

```bash
# Full security audit
python manage.py test store.tests.security.test_security_audit

# Specific test categories
python manage.py test store.tests.security.test_security_audit.SQLInjectionTests
python manage.py test store.tests.security.test_security_audit.XSSPreventionTests
python manage.py test store.tests.security.test_security_audit.CSRFProtectionTests
```

**Test coverage:**

```bash
# Run with coverage
coverage run --source='store' manage.py test store.tests.security
coverage report
coverage html  # Generate HTML report
```

### Manual Testing

**SQL Injection testing:**

```bash
# Test search with SQL injection attempts
curl "http://localhost:8000/store/?search='; DROP TABLE store_product; --"
curl "http://localhost:8000/store/?search=1' OR '1'='1"
```

**XSS testing:**

```bash
# Test review submission with XSS
curl -X POST http://localhost:8000/store/reviews/submit/ \
  -d "comment=<script>alert('XSS')</script>" \
  -d "rating=5"
```

**CSRF testing:**

```bash
# Test form submission without CSRF token
curl -X POST http://localhost:8000/store/cart/add/ \
  -d "product_id=123" \
  -d "quantity=1"
# Should return 403 Forbidden
```

### Penetration Testing

**Recommended tools:**
- **OWASP ZAP:** Web application security scanner
- **Burp Suite:** Security testing platform
- **SQLMap:** SQL injection testing
- **Nikto:** Web server scanner

**Third-party services:**
- HackerOne bug bounty program
- Synack penetration testing
- Cobalt security assessments

---

## Compliance and Standards

### PCI DSS Compliance

**Requirements met:**
- ✅ No card data stored on server (Requirement 3)
- ✅ Encrypted transmission of cardholder data (Requirement 4)
- ✅ Use and maintain secure systems (Requirement 6)
- ✅ Restrict access to cardholder data (Requirement 7)
- ✅ Track and monitor access (Requirement 10)

**Stripe and Paystack are PCI DSS Level 1 certified.**

### GDPR Compliance

**User rights implemented:**
- Right to access: Users can export their data
- Right to erasure: Users can delete their accounts
- Right to rectification: Users can update their information
- Data minimization: Only necessary data is collected

### WCAG 2.1 AA Accessibility

**Security-related accessibility:**
- Error messages are clear and descriptive
- Security warnings are announced to screen readers
- CAPTCHA alternatives for accessibility

---

## Security Contacts

### Internal Contacts

**Security Team:**
- Security Lead: [Name] - security-lead@eytgaming.com
- Development Lead: [Name] - dev-lead@eytgaming.com
- Operations Lead: [Name] - ops-lead@eytgaming.com

**Escalation Path:**
1. Security Team (immediate)
2. CTO (within 1 hour for P0/P1)
3. CEO (within 4 hours for P0)

### External Contacts

**Payment Providers:**
- Stripe Support: https://support.stripe.com
- Paystack Support: https://paystack.com/support

**Security Researchers:**
- Report vulnerabilities: security@eytgaming.com
- Bug bounty program: [URL if applicable]

**Emergency Services:**
- Hosting provider support: [Contact info]
- Database provider support: [Contact info]

---

## Appendix

### Security Checklist for Deployments

Before deploying to production:

- [ ] All security tests pass
- [ ] Environment variables are set correctly
- [ ] HTTPS is enforced
- [ ] HSTS headers are configured
- [ ] CSRF protection is enabled
- [ ] Rate limiting is active
- [ ] Security logging is configured
- [ ] Database backups are automated
- [ ] Payment webhooks are verified
- [ ] Admin panel requires strong authentication
- [ ] Session cookies are secure
- [ ] File upload validation is active
- [ ] Input validation is comprehensive
- [ ] No sensitive data in logs
- [ ] Dependencies are up to date
- [ ] Security monitoring is active

### Security Resources

**Django Security:**
- https://docs.djangoproject.com/en/stable/topics/security/
- https://django-security.readthedocs.io/

**OWASP:**
- https://owasp.org/www-project-top-ten/
- https://cheatsheetseries.owasp.org/

**Payment Security:**
- https://stripe.com/docs/security
- https://paystack.com/docs/security

**General Security:**
- https://www.sans.org/security-resources/
- https://cwe.mitre.org/

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-09 | Security Team | Initial documentation |

---

**For security concerns or questions, contact:** security@eytgaming.com
