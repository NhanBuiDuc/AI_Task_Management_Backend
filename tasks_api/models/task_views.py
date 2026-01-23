# tasks_api/models/task_views.py
"""View relationship models for tasks and sections."""

from django.db import models
from .task import Task, VIEW_CHOICES
from .section import Section


class TaskView(models.Model):
    """Many-to-many relationship for task views."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_views')
    view = models.CharField(max_length=10, choices=VIEW_CHOICES)

    class Meta:
        unique_together = ['task', 'view']
        indexes = [
            models.Index(fields=['view']),
        ]

    def __str__(self):
        return f"{self.task.name} - {self.view}"


class SectionView(models.Model):
    """Many-to-many relationship for section views."""
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='section_views')
    view = models.CharField(max_length=10, choices=VIEW_CHOICES)

    class Meta:
        unique_together = ['section', 'view']
        indexes = [
            models.Index(fields=['view']),
        ]

    def __str__(self):
        return f"{self.section.name} - {self.view}"
