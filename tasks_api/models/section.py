# tasks_api/models/section.py
"""Section model for grouping tasks within projects."""

from django.db import models
from .base import BaseModel
from .project import Project


class Section(BaseModel):
    """Section model matching SectionItem interface."""
    user = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='sections',
        null=True,  # Allow null for migration, remove later
        blank=True
    )
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sections'
    )

    class Meta:
        ordering = ['name']
        unique_together = ['project', 'name']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project']),
        ]

    def __str__(self):
        return f"{self.project.name if self.project else 'Inbox'} - {self.name}"

    @property
    def user_id(self):
        """Return user ID as string."""
        return str(self.user.id) if self.user else None

    @property
    def project_id(self):
        """Return project ID as string to match TypeScript interface."""
        return str(self.project.id) if self.project else None
