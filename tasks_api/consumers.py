import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import date, timedelta
from .models import Task, TaskView, Project


class TaskCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join task count updates group
        self.group_name = 'task_count_updates'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial count data when client connects
        counts = await self.get_task_counts()
        await self.send(text_data=json.dumps({
            'type': 'task_count_update',
            'data': counts
        }))

    async def disconnect(self, close_code):
        # Leave task count updates group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming messages (if needed)
        # For now, we mainly just push updates from the server
        pass

    # Handle message from group
    async def task_count_update(self, event):
        # Send task count data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'task_count_update',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_task_counts(self):
        """Calculate task counts for all views - matches the API logic exactly."""
        today_date = date.today()

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

        # Completed: totally completed tasks
        completed_count = Task.objects.filter(totally_completed=True).count()

        # Projects: get count for each project (excluding totally completed)
        projects = Project.objects.all()
        project_counts = {}
        for project in projects:
            project_counts[str(project.id)] = active_tasks.filter(project_id=project.id).count()

        return {
            'inbox': inbox_count,
            'today': today_count,
            'upcoming': upcoming_count,
            'completed': completed_count,
            'projects': project_counts
        }