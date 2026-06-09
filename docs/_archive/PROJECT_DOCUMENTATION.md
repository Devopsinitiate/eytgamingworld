# EYTGaming – High-Level Project Documentation (Security-Enhanced Edition)

**Platform**: Web Application for a Local/Online Gaming League & Education Company  
**Tech Stack**: Django (Python) + Django REST Framework (DRF) + TailwindCSS + Vanilla JavaScript + PostgreSQL (recommended)  

### 1. Project Vision  
EYTGaming is a gaming organization platform that combines four core pillars:  
1. Competitive Gaming (local & online leagues/tournaments)  
2. Esports Education (coaching/tutoring system)  
3. Community & Player Management  
4. **Security & Compliance** (protecting user data, ensuring fair play, and maintaining trust through robust authentication, encryption, and audit trails)  

**Security as Core**: All features prioritize security by design (e.g., zero-trust permissions, encrypted sessions, and proactive threat modeling). This pillar ensures GDPR/CCPA compliance, prevents cheating in tournaments, and safeguards minors' data for parental oversight.  

Target users:  
- Gamers / Players  
- Coaches / Tutors  
- Tournament Organizers / Admins  
- Team Managers  
- Parents (optional minor accounts)  

### 2. Core Features & Modules (MVP + Future-Proof)  

| Module                  | Key Features                                                                 | Priority | Security Integrations |
|-------------------------|------------------------------------------------------------------------------|----------|-----------------------|
| Authentication & Profiles | Social login (Discord, Steam, Google), Email verification, Role-based access (Player, Coach, Admin, Parent, TO) | MVP | JWT/OAuth tokens via DRF, 2FA (optional), Session encryption, Audit logs for login attempts |
| Gamer Dashboard         | Personal stats, registered tournaments, upcoming matches, coaching sessions, wallet/points | MVP | Data access scoped to user only; encrypted wallet storage; CSRF/XSS protection on JS interactions |
| Tournament Engine       | Bracket generation (Single/Double elim, Swiss, Round-robin), Auto & manual seeding, Check-in system, Match reporting, Live bracket view | MVP | Rate-limited reporting (anti-cheat), Signed check-ins (QR/JWT), Immutable match logs |
| League Management       | Seasonal leagues, Local venue support, Team registration, Standings, Scheduling | MVP | Permission checks on edits; Encrypted venue data; Tamper-proof standings via blockchain-inspired hashing (future) |
| Coaching / Tutoring     | Tutor profiles & availability, Booking system with calendar, Payment integration (Stripe/PayPal), Session history & reviews, Video call integration (Whereby, Jitsi, or Daily.co) | MVP+ | End-to-end encrypted sessions; PII redaction in reviews; Secure payment webhooks with HMAC verification |
| Session Management      | Separate areas for: Tournament sessions, Coaching sessions, Class/Lesson sessions | MVP | Role-scoped views; Session timeouts; Logging of all access for dispute resolution |
| Admin Dashboard         | User management, Tournament creation wizard, Financial overview, Match dispute resolution, Content moderation | MVP | Granular RBAC via DRF permissions; Admin 2FA mandatory; Audit trails for all actions |
| Team Management         | Create/join teams, Team roster, Captain permissions, Team stats | High | Invite-only joins with token expiration; Roster verification to prevent impersonation |
| Notification System     | Email + In-app + Push (Firebase or OneSignal), Discord webhook support | High | Opt-in only; Encrypted payloads; Anti-spam rate limits |
| Venue & Local Events    | Venue directory, Event calendar, QR check-in for local tournaments | Medium | Geofenced check-ins; Venue owner verification; Data minimization for location sharing |
| Analytics & Leaderboards| Global & game-specific rankings, Player performance graphs | Medium | Anonymized aggregates; Opt-out for public leaderboards; Secure API endpoints via DRF throttling |
| Shop / Merch (future)   | Basic store integration | Low | PCI-compliant payments; Inventory access controls |

### 3. User Roles & Permissions  
Security is enforced via Django's built-in permissions + DRF's permission classes for API endpoints. All roles follow least-privilege principle.

| Role                | Permissions | Security Notes |
|---------------------|-------------|----------------|
| Guest               | View public tournaments, venue list, tutor directory | No PII access; CAPTCHA on forms |
| Player              | Register for tournaments, join teams, book coaching, view own dashboard | Scoped queries (e.g., `user=request.user`); Input sanitization |
| Coach/Tutor         | Manage availability, accept bookings, access student notes | Consent-based note access; Encrypted storage for sensitive feedback |
| Tournament Organizer (TO) | Create & manage tournaments in allowed scopes | Scope-limited (e.g., per-region); Approval workflow for new TOs |
| Admin               | Full access | Elevated logging; IP whitelisting for sensitive ops |
| Parent (optional)   | View child’s activity & bookings | Linked accounts with consent; No edit rights |

### 4. Recommended Project Structure (Django + DRF)  

```
eytgaming/
├── core/                  # Custom user model, utils, context processors, security mixins (e.g., audit log decorators)
├── accounts/              # Profiles, social auth, DRF token auth
├── tournaments/           # Models: Tournament, Bracket, Match, Participant; DRF serializers/views
├── teams/
├── coaching/              # TutorProfile, Session, Booking, Reviews; Secure serializers
├── venues/
├── payments/              # Stripe webhooks, invoice history; HMAC validation
├── notifications/
├── dashboard/             # Player & Admin dashboards; HTMX + DRF for AJAX
├── api/                   # DRF endpoints (v1/ for tournaments, coaching, etc.); Permissions & throttling classes
│   ├── urls.py
│   ├── permissions.py    # Custom DRF permissions (e.g., IsOwnerOrReadOnly)
│   └── serializers.py    # Model serializers with security fields (e.g., exclude sensitive data)
├── frontend/              # Tailwind + Vanilla JS components
│   ├── components/
│   ├── brackets/         # Dynamic bracket renderer (pure JS)
│   └── calendar/
├── templates/             # Base layouts, HTMX partials; CSP headers for security
└── security/             # Dedicated module: Rate limiting, audit models, encryption utils
    ├── middleware.py     # Custom security middleware (e.g., HSTS, secure headers)
    └── tasks.py          # Celery tasks for log rotation
```

### 5. Key Third-Party Services (Recommended)  

| Purpose                  | Service (Free tier available)                  | Alternative | Security Focus |
|--------------------------|------------------------------------------------|-------------|----------------|
| Database                 | PostgreSQL (Supabase / Railway / Neon)         | Local Postgres | Row-level security; Encrypted at rest |
| Authentication           | Django-allauth + Social (Discord, Steam) + DRF SimpleJWT | Custom | Token revocation; Social token validation |
| Payments                 | Stripe                                         | PayPal | SCA compliance; Webhook signatures |
| File/Image Storage       | Cloudinary or AWS S3                           | Local (not for prod) | Signed URLs; Access policies |
| Real-time notifications  | Channels (Django Channels) + Redis             | Pusher | Secure WebSockets (wss://); Payload encryption |
| Video calls (coaching)   | Daily.co or Whereby embedded                   | Jitsi Meet | End-to-end encryption; Room isolation |
| Live bracket updates     | HTMX + WebSockets or Server-Sent Events        | Full React/Vue | CSP for JS; Rate-limited updates |
| Push notifications       | Firebase Cloud Messaging or OneSignal          | - | Device token encryption |
| Error tracking           | Sentry                                         | - | Secure error reporting (no PII) |
| Security Scanning        | Django-security-checklist + Bandit             | - | Automated vuln scans in CI/CD |

### 6. Development Approach Recommendation  

**Phase 1 – Foundation (4–6 weeks)**  
- Set up Django + DRF + Tailwind (use django-tailwind or Flowbite + Tailwind)  
- Custom User model + allauth + social logins + DRF JWT auth  
- Basic profiles & role system with permissions testing  
- Admin dashboard (use django-admin or build custom with Tailwind); Integrate security middleware early  

**Phase 2 – Tournament Core (4–8 weeks)**  
- Tournament creation wizard with DRF API for mobile extensibility  
- Bracket generation library → Use open-source: https://github.com/tehsphinx/bracket-generator or https://github.com/Draco18s/Bracket (or write simple single/double elim yourself)  
- Check-in + match reporting flow with rate limiting and audit logs  
- Live bracket page with auto-refresh (HTMX or WebSockets); Enforce secure headers  

**Phase 3 – Coaching System (3–5 weeks)**  
- Tutor profiles & calendar (use FullCalendar.js)  
- Booking + Stripe payment with secure webhooks  
- Session management dashboard with encrypted notes  

**Phase 4 – Teams, Venues, Polish**  
- Team system with secure invites  
- Local venue & event check-in with geofencing  
- Notifications everywhere (opt-in compliant)  
- Mobile-responsive design; Full security audit  

**Why Django + DRF + Tailwind + Vanilla JS is perfect here:**  
- Rapid admin interface (you’ll need it a lot for TOs)  
- Batteries-included auth, ORM, admin + DRF for secure APIs  
- Tailwind gives beautiful UI fast without fighting CSS  
- Vanilla JS + HTMX keeps it lightweight and SEO-friendly (brackets & live pages work great); DRF adds scalable, permissioned backends  

### 7. Must-Have Non-Functional Requirements  
- **GDPR/CCPA-compliant** (especially if minors play): Consent management, data export/deletion, PII minimization  
- **Rate limiting** on match reporting/forms (anti-cheat via django-ratelimit)  
- **Dispute system** with admin resolution and immutable logs  
- **Timezone-aware scheduling** with secure calendar access  
- **Responsive design** (many gamers browse on phone)  
- **Security Headers**: HSTS, CSP, X-Frame-Options enforced via middleware  
- **Encryption**: HTTPS everywhere; Sensitive fields (e.g., notes) encrypted with django-fernet-fields  
- **Auditing**: Log all critical actions (e.g., via django-auditlog) for compliance  

### 8. Suggested Development Tools  
- Django + DRF + django-tailwind or daisyUI + Flowbite  
- HTMX (huge productivity boost for live updates)  
- Alpine.js (lightweight interactivity)  
- django-braces or django-rules for permissions; DRF's permission_classes for APIs  
- Celery + Redis for bracket generation & emails; Security scans in pipelines  
- Docker + docker-compose for local dev; OWASP ZAP for testing  
- **Security Tools**: django-security, Black (code style), pre-commit hooks for vuln checks  

### 9. Security Framework (Core Pillar Details)  
Security is not an afterthought—it's embedded via:  
- **Authentication**: Multi-factor (TOTP via django-otp), token-based for APIs (DRF JWT with refresh/revocation).  
- **Authorization**: RBAC with object-level permissions (e.g., users can only edit own tournaments).  
- **Data Protection**: Encrypt sensitive data (e.g., payment info, chat logs); Use PostgreSQL's row-level security.  
- **Threat Mitigation**: OWASP Top 10 coverage (e.g., SQLi via ORM, XSS via Django templates, CSRF built-in).  
- **Monitoring**: Sentry for errors; Custom logs for anomalies (e.g., failed logins >5/min trigger alerts).  
- **Compliance**: Annual audits; Parental consent flows for minors.  
- **Incident Response**: Defined playbook for breaches (e.g., notify users within 72h per GDPR).  

### Final Recommendation Order of Build  
1. Auth + Profiles (with DRF endpoints and security middleware)  
2. Tournament creation & bracket system (this is your core selling point; secure reporting first)  
3. Player dashboard + registration flow (scoped access)  
4. Coaching booking system (encrypted sessions)  
5. Admin/TO tools (audit everything)  
6. Teams & notifications (secure invites/opt-ins)  
7. Local venue features (geofenced security)  

Start with one game (e.g., Street Fighter league) to keep scope tight, then make the tournament system game-agnostic.  
