# EYTGaming Disaster Recovery Plan

## Recovery Objectives

| Metric | Target |
|--------|--------|
| **RPO** (Recovery Point Objective) | < 24 hours |
| **RTO** (Recovery Time Objective) | < 1 hour |

## Backup Procedures

### Database Backup (Automated)

```bash
# Daily backup script (scripts/backup_db.sh)
pg_dump -d eytgaming_db | gzip | aws s3 cp - s3://eytgaming-backups/db/$(date +%Y%m%d_%H%M%S).sql.gz
```

### Media Files Backup

```bash
# Media backup script (scripts/backup_media.sh)
aws s3 sync /app/media s3://eytgaming-backups/media/$(date +%Y%m%d)/
```

### Configuration Backup

- `.env` file backed up to encrypted password manager
- `docker-compose.yml` and `Dockerfile` in version control

## Restore Procedures

### Database Restore

1. Identify the target backup from S3:
   ```bash
   aws s3 ls s3://eytgaming-backups/db/ | sort | tail -1
   ```
2. Download and restore:
   ```bash
   aws s3 cp s3://eytgaming-backups/db/LATEST_BACKUP - | gunzip | psql -d eytgaming_db
   ```
3. Verify data integrity:
   ```bash
   python manage.py check
   python manage.py shell -c "from core.models import User; print(f'Users: {User.objects.count()}')"
   ```

### Full Infrastructure Restore

1. **Provision infrastructure** — Deploy from `docker-compose.yml` or IaC scripts
2. **Restore configuration** — Apply `.env` from password manager
3. **Restore database** — Follow database restore procedure
4. **Restore media** — `aws s3 sync s3://eytgaming-backups/media/LATEST /app/media`
5. **Verify** — Run smoke tests:
   - [ ] Health check endpoint responds
   - [ ] Database is accessible
   - [ ] Static files load
   - [ ] User can log in
   - [ ] Tournaments display correctly

## Automated Backup Schedule

| Task | Schedule | Tool |
|------|----------|------|
| Database dump | Daily at 02:00 UTC | Celery Beat or system cron |
| Media sync | Daily at 03:00 UTC | Celery Beat or system cron |
| Backup restore drill | Quarterly | Manual |

## Disaster Scenarios

### Scenario 1: Database Corruption

1. Stop the application: `docker-compose stop web`
2. Restore from latest backup (see restore procedures)
3. Verify data integrity
4. Restart the application: `docker-compose start web`

### Scenario 2: Full Infrastructure Loss

1. Provision new infrastructure (Docker Compose / cloud provider)
2. Restore configuration from password manager
3. Restore database from S3 backup
4. Restore media files from S3
5. Update DNS to point to new infrastructure
6. Verify all services

### Scenario 3: Security Breach

1. Follow [Security Incident Response Plan](../security/INCIDENT_RESPONSE.md)
2. Isolate compromised systems
3. Rotate all secrets
4. Restore from pre-compromise backup
5. Audit for persistence mechanisms

## Validation

Restore procedures must be tested quarterly:

1. Spin up a staging environment
2. Restore the most recent backup
3. Run integrity checks
4. Document any issues found
