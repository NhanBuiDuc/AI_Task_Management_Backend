import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')

app = Celery('jarvis_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Check and update overdue tasks every 5 minutes (more frequent for responsiveness)
    'check-and-update-overdue-tasks': {
        'task': 'tasks_api.tasks.check_and_update_overdue_tasks',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {'queue': 'default'}
    },
    # Full categorization of all tasks every 10 minutes (broader check)
    'categorize-tasks-by-due-date': {
        'task': 'tasks_api.tasks.categorize_tasks_by_due_date',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
        'options': {'queue': 'default'}
    },
    # Daily section maintenance at midnight
    'daily-section-maintenance': {
        'task': 'tasks_api.tasks.daily_section_maintenance',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        'options': {'queue': 'default'}
    },
}

# Set the timezone for Celery Beat
app.conf.timezone = 'UTC'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')