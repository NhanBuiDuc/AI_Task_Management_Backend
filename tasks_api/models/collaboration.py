# tasks_api/models/collaboration.py
"""Collaboration models for sharing tasks between users."""

from django.db import models
from django.utils import timezone
from .base import BaseModel


class TaskCollaboration(BaseModel):
    """
    Model for task collaboration/sharing between users.
    Links a task to multiple collaborators with different permission levels.
    """

    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Can Edit'),
        ('admin', 'Full Admin'),
    ]

    task = models.ForeignKey(
        'tasks_api.Task',
        on_delete=models.CASCADE,
        related_name='collaborations'
    )
    owner = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='owned_collaborations',
        help_text='The user who owns/shared the task'
    )
    collaborator = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='task_collaborations',
        help_text='The user who has access to the task'
    )
    permission = models.CharField(
        max_length=10,
        choices=PERMISSION_CHOICES,
        default='view'
    )
    is_active = models.BooleanField(default=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['task', 'collaborator']]
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['owner']),
            models.Index(fields=['collaborator']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.collaborator.username} on {self.task.name} ({self.permission})"

    @property
    def task_id(self):
        """Return task ID as string."""
        return str(self.task.id) if self.task else None

    @property
    def owner_id(self):
        """Return owner ID as string."""
        return str(self.owner.id) if self.owner else None

    @property
    def collaborator_id(self):
        """Return collaborator ID as string."""
        return str(self.collaborator.id) if self.collaborator else None

    def can_view(self):
        """Check if collaborator can view the task."""
        return self.is_active and self.permission in ['view', 'edit', 'admin']

    def can_edit(self):
        """Check if collaborator can edit the task."""
        return self.is_active and self.permission in ['edit', 'admin']

    def can_admin(self):
        """Check if collaborator has admin rights."""
        return self.is_active and self.permission == 'admin'


class TaskInvitation(BaseModel):
    """
    Model for task collaboration invitations.
    Tracks pending, accepted, and declined invitations.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    PERMISSION_CHOICES = TaskCollaboration.PERMISSION_CHOICES

    task = models.ForeignKey(
        'tasks_api.Task',
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    invited_by = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        help_text='The user who sent the invitation'
    )
    invitee = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='received_invitations',
        help_text='The user who received the invitation'
    )
    invitee_email = models.EmailField(
        blank=True,
        null=True,
        help_text='Email for inviting non-registered users'
    )
    permission = models.CharField(
        max_length=10,
        choices=PERMISSION_CHOICES,
        default='view'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    message = models.TextField(
        blank=True,
        null=True,
        help_text='Optional message from the inviter'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the invitation expires'
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the invitee responded to the invitation'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['invited_by']),
            models.Index(fields=['invitee']),
            models.Index(fields=['status']),
            models.Index(fields=['invitee_email']),
        ]

    def __str__(self):
        invitee_name = self.invitee.username if self.invitee else self.invitee_email
        return f"Invitation to {invitee_name} for {self.task.name} ({self.status})"

    @property
    def task_id(self):
        """Return task ID as string."""
        return str(self.task.id) if self.task else None

    @property
    def invited_by_id(self):
        """Return invited_by ID as string."""
        return str(self.invited_by.id) if self.invited_by else None

    @property
    def invitee_id(self):
        """Return invitee ID as string."""
        return str(self.invitee.id) if self.invitee else None

    def is_pending(self):
        """Check if invitation is still pending."""
        if self.status != 'pending':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
        return True

    def accept(self):
        """Accept the invitation and create collaboration."""
        if not self.is_pending():
            return None

        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])

        # Create the collaboration
        collaboration, created = TaskCollaboration.objects.get_or_create(
            task=self.task,
            collaborator=self.invitee,
            defaults={
                'owner': self.invited_by,
                'permission': self.permission,
                'is_active': True,
                'accepted_at': timezone.now()
            }
        )

        if not created:
            # Update existing collaboration
            collaboration.permission = self.permission
            collaboration.is_active = True
            collaboration.accepted_at = timezone.now()
            collaboration.save()

        return collaboration

    def decline(self):
        """Decline the invitation."""
        if not self.is_pending():
            return False

        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        return True

    def cancel(self):
        """Cancel the invitation (by the inviter)."""
        if self.status not in ['pending']:
            return False

        self.status = 'cancelled'
        self.save(update_fields=['status'])
        return True


class ProjectCollaboration(BaseModel):
    """
    Model for project-level collaboration with role-based access control.

    Roles:
    - owner: Project creator. Highest level. Can delete collaboration, transfer ownership.
             (Note: Owner is stored in Project.user, not here)
    - moderator: Manager/leader. Can assign tasks, full CRUD on all tasks.
    - collaborator: Can only modify tasks they are assigned to (full CRUD on assigned tasks).

    All roles can read all tasks in the project.
    """

    ROLE_CHOICES = [
        ('moderator', 'Moderator'),
        ('collaborator', 'Collaborator'),
    ]

    project = models.ForeignKey(
        'tasks_api.Project',
        on_delete=models.CASCADE,
        related_name='collaborations'
    )
    collaborator = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='project_collaborations',
        help_text='The user who has access to the project'
    )
    role = models.CharField(
        max_length=12,
        choices=ROLE_CHOICES,
        default='collaborator',
        help_text='Role determines permissions within the project'
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['project', 'collaborator']]
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['collaborator']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.collaborator.username} on {self.project.name} ({self.role})"

    @property
    def project_id(self):
        """Return project ID as string."""
        return str(self.project.id) if self.project else None

    @property
    def collaborator_id(self):
        """Return collaborator ID as string."""
        return str(self.collaborator.id) if self.collaborator else None

    def is_owner(self):
        """Check if this user is the project owner."""
        return self.project.user == self.collaborator

    def is_moderator(self):
        """Check if this user is a moderator."""
        return self.is_active and self.role == 'moderator'

    def can_assign_tasks(self):
        """Check if user can assign tasks to others."""
        # Owner and moderators can assign tasks
        return self.is_owner() or self.is_moderator()

    def can_manage_collaborators(self):
        """Check if user can add/remove collaborators."""
        # Only owner can manage collaborators
        return self.is_owner()

    def can_delete_project(self):
        """Check if user can delete the project."""
        return self.is_owner()

    def can_modify_all_tasks(self):
        """Check if user can modify all tasks in the project."""
        # Owner and moderators can modify all tasks
        return self.is_owner() or self.is_moderator()

    def can_modify_task(self, task):
        """
        Check if user can modify a specific task.

        Args:
            task: Task instance to check

        Returns:
            bool: True if user can modify the task
        """
        # Owner and moderators can modify all tasks
        if self.is_owner() or self.is_moderator():
            return True

        # Collaborators can only modify tasks assigned to them
        if self.role == 'collaborator':
            return task.assigned_to.filter(id=self.collaborator.id).exists()

        return False


class ProjectInvitation(BaseModel):
    """
    Model for project collaboration invitations.
    Users can join a project via access_id or invitation.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    ROLE_CHOICES = ProjectCollaboration.ROLE_CHOICES

    project = models.ForeignKey(
        'tasks_api.Project',
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    invited_by = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        related_name='sent_project_invitations',
        help_text='The user who sent the invitation'
    )
    invitee = models.ForeignKey(
        'tasks_api.Account',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_project_invitations',
        help_text='The user who received the invitation'
    )
    invitee_email = models.EmailField(
        blank=True,
        null=True,
        help_text='Email for inviting non-registered users'
    )
    role = models.CharField(
        max_length=12,
        choices=ROLE_CHOICES,
        default='collaborator'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    message = models.TextField(
        blank=True,
        null=True,
        help_text='Optional message from the inviter'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the invitation expires'
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['invited_by']),
            models.Index(fields=['invitee']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        invitee_name = self.invitee.username if self.invitee else self.invitee_email
        return f"Project invite to {invitee_name} for {self.project.name} ({self.status})"

    def is_pending(self):
        """Check if invitation is still pending."""
        if self.status != 'pending':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
        return True

    def accept(self):
        """Accept the invitation and create project collaboration."""
        if not self.is_pending():
            return None

        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])

        # Enable collaborative mode on project
        if not self.project.is_collaborative:
            self.project.is_collaborative = True
            self.project.save(update_fields=['is_collaborative', 'updated_at'])

        # Create the collaboration
        collaboration, created = ProjectCollaboration.objects.get_or_create(
            project=self.project,
            collaborator=self.invitee,
            defaults={
                'role': self.role,
                'is_active': True,
                'joined_at': timezone.now()
            }
        )

        if not created:
            collaboration.role = self.role
            collaboration.is_active = True
            collaboration.joined_at = timezone.now()
            collaboration.save()

        return collaboration

    def decline(self):
        """Decline the invitation."""
        if not self.is_pending():
            return False

        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        return True

    def cancel(self):
        """Cancel the invitation."""
        if self.status != 'pending':
            return False

        self.status = 'cancelled'
        self.save(update_fields=['status'])
        return True
