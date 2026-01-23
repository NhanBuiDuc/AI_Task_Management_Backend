# tasks_api/models/project.py
"""Project model for organizing tasks."""

from django.db import models
from django.utils.crypto import get_random_string
from .base import BaseModel


def generate_access_id():
    """Generate a unique 8-character access ID for project sharing."""
    return get_random_string(8, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789')


class Project(BaseModel):
    """Project model matching ProjectItem interface."""
    user = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='projects',
        null=True,  # Allow null for migration, remove later
        blank=True,
        help_text='The owner of the project'
    )
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    icon = models.CharField(max_length=50, default='folder')
    color = models.CharField(max_length=7, default='#3B82F6')  # Default blue color

    # Collaboration fields
    access_id = models.CharField(
        max_length=8,
        unique=True,
        default=generate_access_id,
        help_text='Unique shareable code for joining the project'
    )
    is_collaborative = models.BooleanField(
        default=False,
        help_text='Whether the project is in collaboration mode'
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['parent']),
            models.Index(fields=['name']),
            models.Index(fields=['access_id']),
        ]

    def __str__(self):
        return self.name

    @property
    def user_id(self):
        """Return user ID as string."""
        return str(self.user.id) if self.user else None

    @property
    def owner_id(self):
        """Alias for user_id - returns owner ID as string."""
        return self.user_id

    @property
    def parent_id(self):
        """Return parent ID as string to match TypeScript interface."""
        return str(self.parent.id) if self.parent else None

    @property
    def task_count(self):
        """Calculate total number of tasks in this project."""
        return self.tasks.count()

    @property
    def has_children(self):
        """Check if project has sub-projects."""
        return self.children.exists()

    def is_independent(self):
        """Check if project is independent (no parent and no children)."""
        return self.parent is None and not self.has_children

    def regenerate_access_id(self):
        """Generate a new access ID for the project."""
        self.access_id = generate_access_id()
        self.save(update_fields=['access_id', 'updated_at'])
        return self.access_id

    def transfer_ownership(self, new_owner):
        """Transfer project ownership to another user."""
        from .collaboration import ProjectCollaboration

        old_owner = self.user

        # Update project owner
        self.user = new_owner
        self.save(update_fields=['user', 'updated_at'])

        # Update collaboration records
        # Remove new owner from collaborators if exists
        ProjectCollaboration.objects.filter(
            project=self, collaborator=new_owner
        ).delete()

        # Add old owner as moderator if collaborative
        if self.is_collaborative and old_owner:
            ProjectCollaboration.objects.get_or_create(
                project=self,
                collaborator=old_owner,
                defaults={'role': 'moderator', 'is_active': True}
            )

        return self
