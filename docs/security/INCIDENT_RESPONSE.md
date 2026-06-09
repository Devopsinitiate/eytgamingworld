# EYTGaming Security Incident Response Plan

## Severity Levels

| Level | Description | Examples | Response Time |
|-------|-------------|----------|---------------|
| **SEV1** (Critical) | Active data breach, payment fraud, service outage | Stolen API keys, database compromise, Stripe chargebacks | < 15 min |
| **SEV2** (High) | Account compromise, exploitable vulnerability | XSS/CSRF confirmed, rate limit bypass, 2FA bypass | < 1 hour |
| **SEV3** (Medium) | Non-exploitable vulnerability, policy violation | Dependency CVE announced, logging gap, weak config | < 24 hours |
| **SEV4** (Low) | Best practice gap, minor misconfiguration | Missing header, outdated package, doc gap | < 1 week |

## Response Steps

### SEV1 — Critical Incident

1. **Acknowledge** (5 min) — Page on-call engineer
2. **Triage** (15 min) — Determine scope and impact:
   - What systems are affected?
   - What user data is at risk?
   - Is the attack ongoing?
3. **Contain** (30 min):
   - Revoke compromised credentials/API keys
   - Block attacking IPs
   - Disable affected feature
   - Take affected services offline if necessary
   - Rotate secrets and force re-authentication
4. **Eradicate** — Deploy fix to remove root cause
5. **Recover** — Restore from clean backup if needed
6. **Post-mortem** (within 72 hours):
   - Timeline of events
   - Root cause analysis
   - Action items with owners and deadlines

### SEV2 — High Incident

1. **Acknowledge** (15 min)
2. **Triage** (30 min) — Confirm exploitability and impact
3. **Contain** (2 hours) — Apply hotfix or disable vulnerable feature
4. **Remediate** — Deploy permanent fix
5. **Post-mortem** (within 1 week)

### SEV3 — Medium Incident

1. **Log** — Create issue tracking the finding
2. **Assess** — Determine if exploit path exists with current configuration
3. **Remediate** — Fix in next sprint
4. **Review** — Close issue when fix is deployed

### SEV4 — Low Incident

1. **Log** — Create issue
2. **Schedule** — Fix as part of regular maintenance

## Contact Tree

```
Primary Security Contact: security@eytgaming.com
On-Call Engineer: [PagerDuty/OpsGenie integration TBD]
```

## Post-Mortem Template

```markdown
## Incident Post-Mortem

**Date:** YYYY-MM-DD
**Severity:** SEV#
**Duration:** Start time → End time
**Impacted Users:** #
**Summary:**

### Timeline
- HH:MM — Detection
- HH:MM — Triage
- HH:MM — Containment
- HH:MM — Eradication
- HH:MM — Recovery

### Root Cause

### What Went Well

### What Went Wrong

### Action Items
- [ ] Item 1 (Owner, Due Date)
- [ ] Item 2 (Owner, Due Date)

### Lessons Learned
```

## Tabletop Exercises

Conduct quarterly tabletop exercises simulating a SEV1 scenario. Rotate scenarios:

1. Q1: API key leak / credential exposure
2. Q2: Database compromise / ransomware
3. Q3: Social engineering / phishing attack
4. Q4: Third-party dependency zero-day
