# File: tasks_api/agents/intent_handlers.py
"""
Intent Handlers - Execute database operations for each predicted intent.
Maps intent IDs to actual Django ORM operations.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count

from .intent_registry import (
    ActionType,
    IntentCategory,
    IntentExecutionResult,
    get_intent_by_id,
)

import logging
logger = logging.getLogger(__name__)


class IntentHandlers:
    """
    Handlers for executing intent actions on the database.
    Each method corresponds to an intent_id in the registry.
    """

    def __init__(self, account, task_model, project_model, section_model):
        """
        Initialize with models and account.

        Args:
            account: The authenticated Account object
            task_model: Task model class
            project_model: Project model class
            section_model: Section model class
        """
        self.account = account
        self.Task = task_model
        self.Project = project_model
        self.Section = section_model

    def execute(self, intent_id: str, params: Dict[str, Any]) -> IntentExecutionResult:
        """
        Execute an intent by ID with given params.

        Args:
            intent_id: The intent ID to execute
            params: Extracted parameters from user input

        Returns:
            IntentExecutionResult with success status and data
        """
        intent = get_intent_by_id(intent_id)
        if not intent:
            return IntentExecutionResult(
                success=False,
                intent_id=intent_id,
                action_type=ActionType.READ,
                error=f"Unknown intent: {intent_id}"
            )

        # Get handler method
        handler_name = f"handle_{intent_id.replace('-', '_')}"
        handler = getattr(self, handler_name, None)

        if not handler:
            # Try generic handlers based on pattern
            handler = self._get_generic_handler(intent_id)

        if not handler:
            return IntentExecutionResult(
                success=False,
                intent_id=intent_id,
                action_type=intent.action_type,
                error=f"No handler for intent: {intent_id}"
            )

        try:
            result = handler(params)
            result.intent_id = intent_id
            result.action_type = intent.action_type
            return result
        except Exception as e:
            logger.error(f"Handler error for {intent_id}: {e}")
            return IntentExecutionResult(
                success=False,
                intent_id=intent_id,
                action_type=intent.action_type,
                error=str(e)
            )

    def _get_generic_handler(self, intent_id: str) -> Optional[Callable]:
        """Get a generic handler based on intent pattern"""
        if intent_id.startswith('tasks-') and intent_id.endswith('-list'):
            return self._generic_list_handler
        if intent_id.startswith('tasks-') and intent_id.endswith('-count'):
            return self._generic_count_handler
        return None

    # =========================================================================
    # QUERY HANDLERS - Read operations
    # =========================================================================

    def handle_tasks_today_list(self, params: Dict) -> IntentExecutionResult:
        """List tasks due today"""
        today = timezone.now().date()
        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            due_date=today
        ).values('id', 'name', 'due_date', 'priority', 'completed')

        task_list = list(tasks)
        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': task_list,
                'count': len(task_list),
                'date': today.isoformat()
            },
            message=f"You have {len(task_list)} task{'s' if len(task_list) != 1 else ''} for today."
        )

    def handle_tasks_today_count(self, params: Dict) -> IntentExecutionResult:
        """Count tasks due today"""
        today = timezone.now().date()
        count = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            due_date=today
        ).count()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={'count': count, 'date': today.isoformat()},
            message=f"You have {count} task{'s' if count != 1 else ''} for today."
        )

    def handle_tasks_all_list(self, params: Dict) -> IntentExecutionResult:
        """List all active tasks"""
        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False
        ).values('id', 'name', 'due_date', 'priority', 'completed')[:50]

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': list(tasks),
                'count': len(tasks)
            },
            message=f"Found {len(tasks)} active tasks."
        )

    def handle_tasks_overdue_list(self, params: Dict) -> IntentExecutionResult:
        """List overdue tasks"""
        today = timezone.now().date()
        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            completed=False,
            due_date__lt=today
        ).values('id', 'name', 'due_date', 'priority')

        task_list = list(tasks)
        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': task_list,
                'count': len(task_list)
            },
            message=f"You have {len(task_list)} overdue task{'s' if len(task_list) != 1 else ''}."
        )

    def handle_tasks_upcoming_list(self, params: Dict) -> IntentExecutionResult:
        """List upcoming tasks (next 7 days)"""
        today = timezone.now().date()
        end_date = today + timedelta(days=7)

        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            due_date__gte=today,
            due_date__lte=end_date
        ).values('id', 'name', 'due_date', 'priority', 'completed').order_by('due_date')

        task_list = list(tasks)
        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': task_list,
                'count': len(task_list),
                'date_range': f"{today} to {end_date}"
            },
            message=f"You have {len(task_list)} task{'s' if len(task_list) != 1 else ''} in the next 7 days."
        )

    def handle_tasks_inbox_list(self, params: Dict) -> IntentExecutionResult:
        """List inbox tasks (no project)"""
        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            project__isnull=True
        ).values('id', 'name', 'due_date', 'priority', 'completed')

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': list(tasks),
                'count': tasks.count()
            },
            message=f"You have {tasks.count()} tasks in your inbox."
        )

    def handle_task_search(self, params: Dict) -> IntentExecutionResult:
        """Search for tasks by name"""
        search_term = params.get('search_term', '')
        if not search_term:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.READ,
                error="No search term provided"
            )

        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            name__icontains=search_term
        ).values('id', 'name', 'due_date', 'priority', 'completed')

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': list(tasks),
                'count': tasks.count(),
                'search_term': search_term
            },
            message=f"Found {tasks.count()} task{'s' if tasks.count() != 1 else ''} matching '{search_term}'."
        )

    def handle_task_due_date_query(self, params: Dict) -> IntentExecutionResult:
        """Query when a specific task is due"""
        task_name = params.get('task_name', '')
        if not task_name:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.READ,
                error="No task name provided"
            )

        task = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            name__icontains=task_name
        ).first()

        if not task:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.READ,
                error=f"Task '{task_name}' not found"
            )

        due_str = task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else "No due date"

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'task_id': str(task.id),
                'task_name': task.name,
                'due_date': task.due_date.isoformat() if task.due_date else None
            },
            message=f"'{task.name}' is due: {due_str}"
        )

    def handle_tasks_by_priority(self, params: Dict) -> IntentExecutionResult:
        """List tasks by priority"""
        priority = params.get('priority', 'high')
        priority_map = {'low': 'low', 'medium': 'medium', 'high': 'high', 'urgent': 'urgent'}
        db_priority = priority_map.get(priority.lower(), 'high')

        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            priority=db_priority
        ).values('id', 'name', 'due_date', 'priority', 'completed')

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': list(tasks),
                'count': tasks.count(),
                'priority': db_priority
            },
            message=f"Found {tasks.count()} {db_priority} priority task{'s' if tasks.count() != 1 else ''}."
        )

    def handle_tasks_by_project(self, params: Dict) -> IntentExecutionResult:
        """List tasks in a specific project"""
        project_name = params.get('project_name', '')
        if not project_name:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.READ,
                error="No project name provided"
            )

        project = self.Project.objects.filter(
            user=self.account,
            name__icontains=project_name
        ).first()

        if not project:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.READ,
                error=f"Project '{project_name}' not found"
            )

        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            project=project
        ).values('id', 'name', 'due_date', 'priority', 'completed')

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'tasks': list(tasks),
                'count': tasks.count(),
                'project_id': str(project.id),
                'project_name': project.name
            },
            message=f"Found {tasks.count()} task{'s' if tasks.count() != 1 else ''} in '{project.name}'."
        )

    def handle_projects_list(self, params: Dict) -> IntentExecutionResult:
        """List all projects"""
        projects = self.Project.objects.filter(
            user=self.account
        ).annotate(
            task_count=Count('task')
        ).values('id', 'name', 'color', 'task_count')

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'projects': list(projects),
                'count': projects.count()
            },
            message=f"You have {projects.count()} project{'s' if projects.count() != 1 else ''}."
        )

    # =========================================================================
    # CREATE HANDLERS - Insert operations
    # =========================================================================

    def handle_task_create_simple(self, params: Dict) -> IntentExecutionResult:
        """Create a simple task"""
        title = params.get('title', '').strip()
        if not title:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.INSERT,
                error="No task title provided"
            )

        task = self.Task.objects.create(
            user=self.account,
            name=title,
            priority='medium'
        )
        task.update_task_views()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.INSERT,
            data={
                'task_id': str(task.id),
                'task_name': task.name
            },
            message=f"Created task: '{task.name}'"
        )

    def handle_task_create_with_date(self, params: Dict) -> IntentExecutionResult:
        """Create a task with due date and/or time"""
        title = params.get('title', '').strip()
        due_date_str = params.get('due_date', '')
        due_time_str = params.get('due_time', '')

        if not title:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.INSERT,
                error="No task title provided"
            )

        # Parse the due date (handles 'tomorrow', 'Monday', '2026-01-24', etc.)
        due_date = self._parse_relative_date(due_date_str)

        # If no date but we have a time, default to today
        if not due_date and due_time_str:
            due_date = timezone.now().date()

        # Parse time if provided
        hour, minute = self._parse_time(due_time_str)

        # Create task
        task = self.Task.objects.create(
            user=self.account,
            name=title,
            due_date=due_date,
            priority='medium'
        )
        task.update_task_views()

        # Build response message
        date_msg = ""
        if due_date:
            date_msg = f" due {due_date.strftime('%Y-%m-%d')}"
            if hour is not None:
                time_formatted = f"{hour:02d}:{minute:02d}"
                date_msg += f" at {time_formatted}"

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.INSERT,
            data={
                'task_id': str(task.id),
                'task_name': task.name,
                'due_date': due_date.isoformat() if due_date else None,
                'due_time': f"{hour:02d}:{minute:02d}" if hour is not None else None
            },
            message=f"Created task: '{task.name}'{date_msg}"
        )

    def handle_task_create_with_time(self, params: Dict) -> IntentExecutionResult:
        """Create a task with specific time"""
        return self.handle_task_create_with_date(params)

    def handle_task_create_with_priority(self, params: Dict) -> IntentExecutionResult:
        """Create a task with priority"""
        title = params.get('title', '').strip()
        priority = params.get('priority', 3)

        if not title:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.INSERT,
                error="No task title provided"
            )

        # Map numeric to string priority
        priority_map = {1: 'low', 2: 'low', 3: 'medium', 4: 'high', 5: 'urgent'}
        db_priority = priority_map.get(int(priority), 'medium')

        task = self.Task.objects.create(
            user=self.account,
            name=title,
            priority=db_priority
        )
        task.update_task_views()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.INSERT,
            data={
                'task_id': str(task.id),
                'task_name': task.name,
                'priority': db_priority
            },
            message=f"Created {db_priority} priority task: '{task.name}'"
        )

    def handle_task_create_in_project(self, params: Dict) -> IntentExecutionResult:
        """Create a task in a specific project"""
        title = params.get('title', '').strip()
        project_name = params.get('project_name', '')

        if not title:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.INSERT,
                error="No task title provided"
            )

        project = None
        if project_name:
            project = self.Project.objects.filter(
                user=self.account,
                name__icontains=project_name
            ).first()

        task = self.Task.objects.create(
            user=self.account,
            name=title,
            project=project,
            priority='medium'
        )
        task.update_task_views()

        project_msg = f" in '{project.name}'" if project else ""
        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.INSERT,
            data={
                'task_id': str(task.id),
                'task_name': task.name,
                'project_id': str(project.id) if project else None
            },
            message=f"Created task: '{task.name}'{project_msg}"
        )

    def handle_tasks_create_multiple(self, params: Dict) -> IntentExecutionResult:
        """Create multiple tasks at once"""
        tasks_list = params.get('tasks', [])
        if not tasks_list:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.INSERT,
                error="No tasks provided"
            )

        created = []
        for title in tasks_list:
            if title.strip():
                task = self.Task.objects.create(
                    user=self.account,
                    name=title.strip(),
                    priority='medium'
                )
                task.update_task_views()
                created.append({'id': str(task.id), 'name': task.name})

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.INSERT,
            data={
                'tasks': created,
                'count': len(created)
            },
            message=f"Created {len(created)} task{'s' if len(created) != 1 else ''}: {', '.join(t['name'] for t in created)}"
        )

    def handle_project_create(self, params: Dict) -> IntentExecutionResult:
        """Create a new project"""
        name = params.get('name', '').strip()
        if not name:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.INSERT,
                error="No project name provided"
            )

        project = self.Project.objects.create(
            user=self.account,
            name=name
        )

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.INSERT,
            data={
                'project_id': str(project.id),
                'project_name': project.name
            },
            message=f"Created project: '{project.name}'"
        )

    # =========================================================================
    # UPDATE HANDLERS - Modify operations
    # =========================================================================

    def handle_task_update_due_date(self, params: Dict) -> IntentExecutionResult:
        """Change a task's due date"""
        task_name = params.get('task_name', '')
        new_due_date_str = params.get('new_due_date', '')

        task = self._find_task(task_name)
        if not task:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.UPDATE,
                error=f"Task '{task_name}' not found"
            )

        # Parse the new due date (handles 'tomorrow', 'Monday', '2026-01-24', etc.)
        new_due_date = self._parse_relative_date(new_due_date_str)

        if not new_due_date:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.UPDATE,
                error=f"Could not parse date: {new_due_date_str}"
            )

        task.due_date = new_due_date
        task.save()
        task.update_task_views()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.UPDATE,
            data={
                'task_id': str(task.id),
                'task_name': task.name,
                'new_due_date': new_due_date.isoformat()
            },
            message=f"Updated '{task.name}' due date to {new_due_date.strftime('%Y-%m-%d')}"
        )

    def handle_task_postpone(self, params: Dict) -> IntentExecutionResult:
        """Postpone a task by N days"""
        task_name = params.get('task_name', '')
        days = int(params.get('postpone_days', 1))

        task = self._find_task(task_name)
        if not task:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.UPDATE,
                error=f"Task '{task_name}' not found"
            )

        if task.due_date:
            task.due_date = task.due_date + timedelta(days=days)
        else:
            task.due_date = timezone.now() + timedelta(days=days)

        task.save()
        task.update_task_views()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.UPDATE,
            data={
                'task_id': str(task.id),
                'task_name': task.name,
                'new_due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                'postponed_days': days
            },
            message=f"Postponed '{task.name}' by {days} day{'s' if days != 1 else ''}"
        )

    def handle_task_update_priority(self, params: Dict) -> IntentExecutionResult:
        """Change a task's priority"""
        task_name = params.get('task_name', '')
        new_priority = params.get('new_priority', 'medium')

        task = self._find_task(task_name)
        if not task:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.UPDATE,
                error=f"Task '{task_name}' not found"
            )

        # Map string priority
        if isinstance(new_priority, int):
            priority_map = {1: 'low', 2: 'low', 3: 'medium', 4: 'high', 5: 'urgent'}
            new_priority = priority_map.get(new_priority, 'medium')

        task.priority = new_priority
        task.save()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.UPDATE,
            data={
                'task_id': str(task.id),
                'task_name': task.name,
                'new_priority': new_priority
            },
            message=f"Updated '{task.name}' to {new_priority} priority"
        )

    # =========================================================================
    # COMPLETE HANDLERS
    # =========================================================================

    def handle_task_complete(self, params: Dict) -> IntentExecutionResult:
        """Mark a task as complete"""
        task_name = params.get('task_name', '')

        task = self._find_task(task_name)
        if not task:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.COMPLETE,
                error=f"Task '{task_name}' not found"
            )

        task.completed = True
        task.completed_date = timezone.now()
        task.save()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.COMPLETE,
            data={
                'task_id': str(task.id),
                'task_name': task.name
            },
            message=f"Completed: '{task.name}'"
        )

    def handle_tasks_complete_multiple(self, params: Dict) -> IntentExecutionResult:
        """Mark multiple tasks as complete"""
        task_names = params.get('task_names', [])

        completed = []
        not_found = []

        for name in task_names:
            task = self._find_task(name)
            if task:
                task.completed = True
                task.completed_date = timezone.now()
                task.save()
                completed.append(task.name)
            else:
                not_found.append(name)

        msg = f"Completed {len(completed)} task{'s' if len(completed) != 1 else ''}"
        if not_found:
            msg += f". Not found: {', '.join(not_found)}"

        return IntentExecutionResult(
            success=len(completed) > 0,
            intent_id='',
            action_type=ActionType.COMPLETE,
            data={
                'completed': completed,
                'not_found': not_found
            },
            message=msg
        )

    # =========================================================================
    # DELETE HANDLERS
    # =========================================================================

    def handle_task_delete(self, params: Dict) -> IntentExecutionResult:
        """Delete a task"""
        task_name = params.get('task_name', '')

        task = self._find_task(task_name)
        if not task:
            return IntentExecutionResult(
                success=False,
                intent_id='',
                action_type=ActionType.DELETE,
                error=f"Task '{task_name}' not found"
            )

        task_name_saved = task.name
        task.delete()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.DELETE,
            data={
                'deleted_task': task_name_saved
            },
            message=f"Deleted: '{task_name_saved}'"
        )

    # =========================================================================
    # ANALYTICS HANDLERS
    # =========================================================================

    def handle_stats_summary(self, params: Dict) -> IntentExecutionResult:
        """Get task summary statistics"""
        today = timezone.now().date()

        total = self.Task.objects.filter(user=self.account, totally_completed=False).count()
        today_count = self.Task.objects.filter(user=self.account, totally_completed=False, due_date=today).count()
        overdue = self.Task.objects.filter(user=self.account, totally_completed=False, completed=False, due_date__lt=today).count()
        completed = self.Task.objects.filter(user=self.account, completed=True).count()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={
                'total_active': total,
                'today': today_count,
                'overdue': overdue,
                'completed': completed
            },
            message=f"You have {total} active task{'s' if total != 1 else ''} ({today_count} today, {overdue} overdue). {completed} completed."
        )

    # =========================================================================
    # SPECIAL HANDLERS
    # =========================================================================

    def handle_clarify_ambiguous(self, params: Dict) -> IntentExecutionResult:
        """Handle ambiguous input - just return clarification"""
        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={'needs_clarification': True},
            message="I'd like to help! Could you be more specific about what you'd like to do?"
        )

    def handle_chat_general(self, params: Dict) -> IntentExecutionResult:
        """Handle general chat"""
        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={'type': 'chat'},
            message="I can help you manage tasks. Try: 'add task', 'show today', or 'mark X as done'."
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _parse_relative_date(self, date_str: str) -> datetime:
        """
        Parse relative date strings like 'tomorrow', 'today', 'Monday', etc.
        Returns a datetime object or None if parsing fails.
        """
        if not date_str:
            return None

        date_str = date_str.lower().strip()
        today = timezone.now().date()

        # Direct relative dates
        if date_str in ['today', 'tonight', 'this evening']:
            return today
        if date_str in ['tomorrow', 'tmr', 'tmrw']:
            return today + timedelta(days=1)
        if date_str == 'yesterday':
            return today - timedelta(days=1)

        # Next week variations
        if date_str in ['next week', 'nextweek']:
            return today + timedelta(days=7)

        # Day names
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(day_names):
            if date_str == day or date_str == day[:3]:
                # Find next occurrence of this day
                current_day = today.weekday()  # Monday = 0
                days_ahead = i - current_day
                if days_ahead <= 0:  # Already passed this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)

        # Try standard date formats
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def _parse_time(self, time_str: str) -> tuple:
        """
        Parse time strings like '10pm', '14:00', '9am'.
        Returns (hour, minute) tuple or (None, None).
        """
        if not time_str:
            return None, None

        time_str = time_str.lower().strip().replace(' ', '')

        # Handle am/pm format (10pm, 9am, 10:30pm)
        import re
        match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3)

            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0

            return hour, minute

        return None, None

    def _find_task(self, name_or_id: str):
        """Find a task by name or ID"""
        if not name_or_id:
            return None

        # Try by ID first
        try:
            return self.Task.objects.get(id=name_or_id, user=self.account)
        except:
            pass

        # Try by name (partial match)
        return self.Task.objects.filter(
            user=self.account,
            totally_completed=False,
            name__icontains=name_or_id
        ).first()

    def _generic_list_handler(self, params: Dict) -> IntentExecutionResult:
        """Generic handler for list intents"""
        tasks = self.Task.objects.filter(
            user=self.account,
            totally_completed=False
        ).values('id', 'name', 'due_date', 'priority')[:20]

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={'tasks': list(tasks), 'count': len(tasks)},
            message=f"Found {len(tasks)} tasks."
        )

    def _generic_count_handler(self, params: Dict) -> IntentExecutionResult:
        """Generic handler for count intents"""
        count = self.Task.objects.filter(
            user=self.account,
            totally_completed=False
        ).count()

        return IntentExecutionResult(
            success=True,
            intent_id='',
            action_type=ActionType.READ,
            data={'count': count},
            message=f"You have {count} tasks."
        )
