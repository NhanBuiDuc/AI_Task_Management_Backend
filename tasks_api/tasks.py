from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from .models import Task, TaskView, Project
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


def calculate_and_broadcast_task_counts():
    """Calculate task counts and broadcast to WebSocket clients."""
    today_date = timezone.now().date()

    # Calculate upcoming boundaries (matches frontend and model logic)
    upcoming_start = today_date
    upcoming_end = today_date + timedelta(days=14)

    # Count tasks for each view (excluding totally completed tasks)
    active_tasks = Task.objects.filter(totally_completed=False)

    # Inbox: tasks with inbox view BUT NOT project view (non-project tasks only)
    inbox_task_ids = TaskView.objects.filter(view='inbox').values_list('task_id', flat=True)
    project_task_ids = TaskView.objects.filter(view='project').values_list('task_id', flat=True)
    inbox_count = active_tasks.filter(
        id__in=inbox_task_ids
    ).exclude(
        id__in=project_task_ids
    ).count()

    # Today: tasks due today (matching Today page logic)
    today_count = active_tasks.filter(due_date=today_date).count()

    # Upcoming: tasks due between current day and current day + 14
    upcoming_count = active_tasks.filter(
        due_date__gte=upcoming_start,
        due_date__lte=upcoming_end
    ).count()

    # Overdue: tasks due before today
    overdue_count = active_tasks.filter(due_date__lt=today_date).count()

    # Completed: totally completed tasks
    completed_count = Task.objects.filter(totally_completed=True).count()

    # Projects: get count for each project (excluding totally completed)
    projects = Project.objects.all()
    project_counts = {}
    for project in projects:
        project_counts[str(project.id)] = active_tasks.filter(project_id=project.id).count()

    counts = {
        'inbox': inbox_count,
        'today': today_count,
        'upcoming': upcoming_count,
        'overdue': overdue_count,
        'completed': completed_count,
        'projects': project_counts
    }

    # Broadcast to WebSocket clients
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'task_count_updates',
        {
            'type': 'task_count_update',
            'data': counts
        }
    )

    return counts

@shared_task
def categorize_tasks_by_due_date():
    """
    Periodic task that automatically categorizes tasks based on their due dates.
    This runs every 10 seconds for real-time updates of task views based on due date.

    Example: If today is 22/Sep/2025 2:00 PM and a task due date is 23/Sep/2025 2:00 PM,
    the task should be in ["today", "upcoming"] or ["project", "today", "upcoming"] if it belongs to a project.
    """
    now = timezone.now()
    today_date = now.date()

    # Calculate upcoming range: current day to current day + 14 (matches frontend logic)
    upcoming_start = today_date
    upcoming_end = today_date + timedelta(days=14)

    # Get all active tasks (not totally completed)
    active_tasks = Task.objects.filter(totally_completed=False)

    categorized_count = 0

    for task in active_tasks:
        if not task.due_date:
            continue

        task_due_date = task.due_date
        new_views = []

        # Determine base view (inbox or project)
        if task.project_id:
            new_views.append("project")
        else:
            new_views.append("inbox")

        # Add time-based views based on due date
        if task_due_date < today_date:
            new_views.append("overdue")
        elif task_due_date == today_date:
            new_views.append("today")
        elif upcoming_start <= task_due_date <= upcoming_end:
            new_views.append("upcoming")

        # Update task views if they've changed
        current_views = list(task.task_views.values_list('view', flat=True))

        if set(new_views) != set(current_views):
            # Clear existing views
            task.task_views.all().delete()

            # Add new views
            for view in new_views:
                TaskView.objects.create(task=task, view=view)

            categorized_count += 1

    # Broadcast updated counts to WebSocket clients if any tasks were updated
    if categorized_count > 0:
        counts = calculate_and_broadcast_task_counts()
        return f"Successfully categorized {categorized_count} tasks and broadcast counts: {counts}"
    else:
        return f"No tasks needed categorization update"

@shared_task
def update_task_current_view():
    """
    Alternative implementation that directly updates the current_view field if it exists.
    This is a backup approach in case we decide to use a direct field instead of TaskView model.
    """
    now = timezone.now()
    today_date = now.date()

    # Calculate upcoming range: current day to current day + 14 (matches frontend logic)
    upcoming_start = today_date
    upcoming_end = today_date + timedelta(days=14)

    # Get all active tasks
    active_tasks = Task.objects.filter(totally_completed=False)

    updated_count = 0

    for task in active_tasks:
        if not task.due_date:
            continue

        task_due_date = task.due_date
        new_views = []

        # Base view
        if task.project_id:
            new_views.append("project")
        else:
            new_views.append("inbox")

        # Time-based views
        if task_due_date < today_date:
            new_views.append("overdue")
        elif task_due_date == today_date:
            new_views.append("today")
        elif upcoming_start <= task_due_date <= upcoming_end:
            new_views.append("upcoming")

        # Update if there's a current_view field in the Task model
        # Note: This would require adding a current_view field to the Task model
        # For now, we'll use the TaskView approach above

        updated_count += 1

    return f"Processed {updated_count} tasks for view updates"

@shared_task
def daily_section_maintenance():
    """
    Daily task to ensure Today sections exist and clean up old sections.
    This runs once per day to maintain the Today view sections.
    """
    from .models import Section

    now = timezone.now()
    today_date = now.date()

    # Create today's section if it doesn't exist
    today_section_name = today_date.strftime("%d %B %Y")

    section, created = Section.objects.get_or_create(
        name=today_section_name,
        project_id=None,
        defaults={'name': today_section_name}
    )

    # Add today view to the section if needed
    if created:
        from .models import SectionView
        SectionView.objects.get_or_create(section=section, view="today")

    result = f"Today section '{today_section_name}' "
    result += "created" if created else "already exists"

    return result

@shared_task
def check_and_update_overdue_tasks():
    """
    Specifically focused task to check for tasks that have become overdue.
    This runs more frequently to ensure timely updates of overdue status.
    """
    now = timezone.now()
    today_date = now.date()

    # Find all tasks that are due before today but not marked as overdue yet
    tasks_to_update = Task.objects.filter(
        totally_completed=False,
        due_date__lt=today_date
    ).exclude(
        task_views__view='overdue'
    )

    updated_count = 0

    for task in tasks_to_update:
        # Add overdue view if not already present
        if not task.task_views.filter(view='overdue').exists():
            TaskView.objects.create(task=task, view='overdue')
            updated_count += 1

        # Remove today and upcoming views if present (since task is now overdue)
        task.task_views.filter(view__in=['today', 'upcoming']).delete()

    # Broadcast updated counts to WebSocket clients if any tasks were updated
    if updated_count > 0:
        counts = calculate_and_broadcast_task_counts()
        return f"Successfully marked {updated_count} tasks as overdue and broadcast counts: {counts}"
    else:
        return "No new overdue tasks found"