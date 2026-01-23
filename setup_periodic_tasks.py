"""
Setup periodic tasks for Celery Beat
Can be piped into: python manage.py shell < setup_periodic_tasks.py
"""

from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from django.utils import timezone
import json

print("Setting up periodic tasks...")

try:
    # Create schedules
    hourly_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )

    daily_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='0',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )

    five_min_schedule, _ = IntervalSchedule.objects.get_or_create(
        every=5,
        period=IntervalSchedule.MINUTES,
    )

    # Create periodic tasks
    PeriodicTask.objects.get_or_create(
        name='Categorize tasks by due date (hourly)',
        defaults={
            'task': 'tasks_api.tasks.categorize_tasks_by_due_date',
            'crontab': hourly_schedule,
            'enabled': True,
        }
    )

    PeriodicTask.objects.get_or_create(
        name='Daily section maintenance',
        defaults={
            'task': 'tasks_api.tasks.daily_section_maintenance',
            'crontab': daily_schedule,
            'enabled': True,
        }
    )

    PeriodicTask.objects.get_or_create(
        name='Test task categorization (5 min)',
        defaults={
            'task': 'tasks_api.tasks.categorize_tasks_by_due_date',
            'interval': five_min_schedule,
            'enabled': False,
        }
    )

    print("✓ Periodic tasks created successfully!")
    
except Exception as e:
    print(f"✗ Error setting up periodic tasks: {e}")
    import traceback
    traceback.print_exc()