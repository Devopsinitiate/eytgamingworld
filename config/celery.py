import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('eytgaming')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'check-tournament-start-times': {
        'task': 'tournaments.tasks.check_tournament_start_times',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'send-match-reminders': {
        'task': 'tournaments.tasks.send_match_reminders',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'send-session-reminders': {
        'task': 'coaching.tasks.send_session_reminders',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'auto-complete-sessions': {
        'task': 'coaching.tasks.auto_complete_sessions',
        'schedule': crontab(minute=0),  # Every hour
    },
    'mark-no-shows': {
        'task': 'coaching.tasks.mark_no_shows',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'expire-packages': {
        'task': 'coaching.tasks.expire_packages',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'send-review-requests': {
        'task': 'coaching.tasks.send_review_requests',
        'schedule': crontab(hour=10, minute=0),  # Daily at 10 AM
    },
    'refresh-all-user-recommendations': {
        'task': 'dashboard.tasks.refresh_all_user_recommendations',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'cleanup-old-activities': {
        'task': 'dashboard.tasks.cleanup_old_activities',
        'schedule': crontab(hour=3, minute=30, day_of_week=0),  # Weekly on Sunday at 3:30 AM
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')