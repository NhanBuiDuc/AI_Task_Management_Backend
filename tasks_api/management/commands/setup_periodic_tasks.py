# tasks_api\management\commands\setup_periodic_tasks.py

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json

class Command(BaseCommand):
    help = 'Set up periodic tasks for automatic task categorization'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up periodic tasks for task categorization...')
        )

        # Create interval schedule for every hour
        hourly_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created hourly interval schedule')
            )

        # Create periodic task for task categorization (runs every hour)
        categorize_task, created = PeriodicTask.objects.get_or_create(
            name='Categorize tasks by due date',
            defaults={
                'task': 'tasks_api.tasks.categorize_tasks_by_due_date',
                'interval': hourly_schedule,
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True,
                'description': 'Automatically categorizes tasks based on their due dates - runs every hour',
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created periodic task: Categorize tasks by due date (hourly)')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Periodic task already exists: Categorize tasks by due date')
            )

        # Create cron schedule for daily task (every day at midnight)
        daily_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=0,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created daily cron schedule (midnight)')
            )

        # Create periodic task for daily section maintenance
        section_task, created = PeriodicTask.objects.get_or_create(
            name='Daily section maintenance',
            defaults={
                'task': 'tasks_api.tasks.daily_section_maintenance',
                'crontab': daily_schedule,
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True,
                'description': 'Creates Today sections and maintains daily views - runs daily at midnight',
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created periodic task: Daily section maintenance (daily at midnight)')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Periodic task already exists: Daily section maintenance')
            )

        # Create a real-time schedule for immediate updates (every 10 seconds)
        realtime_schedule, created = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.SECONDS,
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created 10-second interval schedule for real-time updates')
            )

        # Create real-time task for immediate view updates (ENABLED for production)
        realtime_task, created = PeriodicTask.objects.get_or_create(
            name='Real-time task view updates (10 sec)',
            defaults={
                'task': 'tasks_api.tasks.categorize_tasks_by_due_date',
                'interval': realtime_schedule,
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': True,  # Enabled for real-time updates
                'description': 'Real-time task view updates - runs every 10 seconds for immediate today/upcoming categorization',
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created real-time periodic task: Real-time task view updates (10 sec) - ENABLED')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Real-time periodic task already exists: Real-time task view updates (10 sec)')
            )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('Periodic tasks setup complete!')
        )
        self.stdout.write('')
        self.stdout.write('Created tasks:')
        self.stdout.write('1. "Categorize tasks by due date" - runs every hour')
        self.stdout.write('2. "Daily section maintenance" - runs daily at midnight')
        self.stdout.write('3. "Real-time task view updates" - runs every 10 seconds (ENABLED)')
        self.stdout.write('')
        self.stdout.write('Real-time updates are now ENABLED by default!')
        self.stdout.write('Tasks will automatically move between Today/Upcoming views every 10 seconds.')
        self.stdout.write('')
        self.stdout.write('To disable real-time updates if needed:')
        self.stdout.write('- Go to Django Admin (/admin/)')
        self.stdout.write('- Navigate to Periodic Tasks > Periodic tasks')
        self.stdout.write('- Find "Real-time task view updates (10 sec)" and disable it')
        self.stdout.write('')
        self.stdout.write('To start Celery workers and beat scheduler:')
        self.stdout.write('1. Redis: redis-server (make sure Redis is running)')
        self.stdout.write('2. Celery Worker: celery -A jarvis_backend worker --loglevel=info')
        self.stdout.write('3. Celery Beat: celery -A jarvis_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler')
        self.stdout.write('='*60)