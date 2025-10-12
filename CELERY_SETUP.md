# Celery Setup for Automatic Task Categorization

This document explains how to set up and run the Celery-based automatic task categorization system.

## Overview

The system automatically categorizes tasks based on their due dates using server-side background processing:

- **Tasks due today**: Added to `["today"]` view (or `["project", "today"]` for project tasks)
- **Tasks due this week/next week**: Added to `["upcoming"]` view (or `["project", "upcoming"]` for project tasks)
- **Inbox tasks**: Always include `["inbox"]` view
- **Project tasks**: Always include `["project"]` view

## Prerequisites

1. **Redis Server**: Celery uses Redis as a message broker
   ```bash
   # Install Redis (Windows - download from https://redis.io/download)
   # Or use Docker:
   docker run -d -p 6379:6379 redis:alpine

   # Start Redis server
   redis-server
   ```

2. **Python packages**: Already installed
   - celery
   - redis
   - django-celery-beat

## Setup Steps

### 1. Database Migration (Already Done)
```bash
cd back-end
python manage.py migrate
```

### 2. Set up Periodic Tasks (Already Done)
```bash
python manage.py setup_periodic_tasks
```

This creates:
- **Hourly task**: Categorizes tasks based on due dates (runs every hour)
- **Daily task**: Creates Today sections and maintains daily views (runs at midnight)
- **Test task**: 5-minute interval for testing (disabled by default)

## Running the System

### Option 1: Full Production Setup

1. **Start Redis server**:
   ```bash
   redis-server
   ```

2. **Start Django development server**:
   ```bash
   cd back-end
   python manage.py runserver 0.0.0.0:8000
   ```

3. **Start Celery worker** (in new terminal):
   ```bash
   cd back-end
   celery -A jarvis_backend worker --loglevel=info
   ```

4. **Start Celery Beat scheduler** (in new terminal):
   ```bash
   cd back-end
   celery -A jarvis_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

### Option 2: Quick Testing

1. **Manual test** (without Celery):
   ```bash
   cd back-end
   python manage.py test_categorize_tasks
   ```

2. **Enable 5-minute test task**:
   - Go to Django Admin: http://localhost:8000/admin/
   - Navigate to: Periodic Tasks > Periodic tasks
   - Find "Test task categorization (5 min)"
   - Check "Enabled" and save
   - Start Celery worker and beat (steps 3-4 above)

## How It Works

### Automatic Categorization Logic

The system checks each task's `due_date` and updates the `TaskView` records:

```python
# Example: Task due today (22/Sep/2025)
if task_due_date == today_date:
    new_views.append("today")

# Example: Task due this week or next week
if task_due_date in upcoming_range:
    new_views.append("upcoming")

# Base view depends on project
if task.project_id:
    new_views.append("project")
else:
    new_views.append("inbox")
```

### Task Views Update

For each task, the system:
1. Calculates new views based on due date
2. Compares with current `TaskView` records
3. Updates only if views have changed
4. Deletes old `TaskView` records and creates new ones

### Example Scenarios

**Scenario 1**: Task due today with project
- Before: `current_view = ["project"]`
- After: `current_view = ["project", "today"]`

**Scenario 2**: Task due next week without project
- Before: `current_view = ["inbox"]`
- After: `current_view = ["inbox", "upcoming"]`

**Scenario 3**: Task due date changes from today to next week
- Before: `current_view = ["project", "today"]`
- After: `current_view = ["project", "upcoming"]`

## Monitoring

### Check Periodic Tasks Status
```bash
# View all periodic tasks
cd back-end
python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask
for task in PeriodicTask.objects.all():
    print(f"{task.name}: {'Enabled' if task.enabled else 'Disabled'}")
```

### Check Task Execution
- Celery worker logs show task execution
- Django admin shows task run history

### Manual Execution
```bash
# Test the categorization function
python manage.py test_categorize_tasks

# Run specific Celery task
celery -A jarvis_backend call tasks_api.tasks.categorize_tasks_by_due_date
```

## Configuration

### Celery Settings (already in settings.py)
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### Periodic Task Schedule
- **Hourly**: Every hour for continuous categorization
- **Daily**: Midnight for section maintenance
- **Test**: Every 5 minutes (disabled by default)

## Troubleshooting

### Common Issues

1. **Redis not running**:
   ```
   Error: Error 61 connecting to localhost:6379. Connection refused.
   ```
   Solution: Start Redis server

2. **Celery worker not running**:
   ```
   Task never executes
   ```
   Solution: Start Celery worker

3. **Tasks not categorizing**:
   - Check if tasks have due dates
   - Check if periodic tasks are enabled in Django admin
   - Check Celery worker logs for errors

### Logs

- **Celery worker**: Shows task execution and results
- **Celery beat**: Shows task scheduling
- **Django logs**: Application-level errors

## User Experience

From the user's perspective:

1. **Create task with due date**: Task automatically appears in appropriate views
2. **Due date changes**: Task moves between Today/Upcoming views automatically
3. **No manual refresh needed**: Views update based on server time
4. **Works offline**: Categorization happens server-side

The system fulfills the original requirement: "as long as the server is running, if it run, then it must run a function internally to run a function, such as set the task categorical as reminder one day category, without the use going to the website click on some view then call this function."