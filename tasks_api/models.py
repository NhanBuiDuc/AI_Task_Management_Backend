from django.db import models
import uuid


class BaseModel(models.Model):
    """Base model with UUID primary key and timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(BaseModel):
    """Project model matching ProjectItem interface."""
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

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

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


class Section(BaseModel):
    """Section model matching SectionItem interface."""
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
            models.Index(fields=['project']),
        ]

    def __str__(self):
        return f"{self.project.name if self.project else 'Inbox'} - {self.name}"

    @property
    def project_id(self):
        """Return project ID as string to match TypeScript interface."""
        return str(self.project.id) if self.project else None


class Task(BaseModel):
    """Task model matching TaskItem interface."""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]

    VIEW_CHOICES = [
        ('calendar', 'Calendar'),
        ('inbox', 'Inbox'),
        ('today', 'Today'),
        ('upcoming', 'Upcoming'),
        ('overdue', 'Overdue'),
        ('project', 'Project'),
    ]

    REPEAT_CHOICES = [
        ('every day', 'Every Day'),
        ('every week', 'Every Week'),
        ('every month', 'Every Month'),
        ('every year', 'Every Year'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tasks'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tasks'
    )
    due_date = models.DateField()
    completed = models.BooleanField(default=False)
    totally_completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=9,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    reminder_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    duration_in_minutes = models.PositiveIntegerField(default=15, help_text="Duration in minutes")
    repeat = models.CharField(
        max_length=12,
        choices=REPEAT_CHOICES,
        null=True,
        blank=True,
        help_text="Repeat pattern for the task"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['section']),
            models.Index(fields=['due_date']),
            models.Index(fields=['completed']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return self.name

    @property
    def project_id(self):
        """Return project ID as string to match TypeScript interface."""
        return str(self.project.id) if self.project else None

    @property
    def section_id(self):
        """Return section ID as string to match TypeScript interface."""
        return str(self.section.id) if self.section else None

    @property
    def piority(self):
        """Return priority (matching typo in TypeScript interface)."""
        return self.priority

    def calculate_views_from_due_date(self):
        """Calculate current_view based on due_date and project_id automatically."""
        from datetime import date, timedelta

        views = []
        today = date.today()

        # Base view determination
        if self.project_id:
            # Task belongs to a project
            views.append('project')
        else:
            # Task is in inbox (no project)
            views.append('inbox')

        # Add date-based views if due_date exists
        if self.due_date:
            # Check if overdue (due before today)
            if self.due_date < today:
                views.append('overdue')
            # Check if due today
            elif self.due_date == today:
                views.append('today')
            else:
                # Check if due in upcoming range (current day to current day + 14)
                upcoming_start = today
                upcoming_end = today + timedelta(days=14)

                if upcoming_start <= self.due_date <= upcoming_end:
                    views.append('upcoming')

        return views

    def update_task_views(self):
        """Update TaskView relationships based on calculated views."""
        # Calculate what views this task should have
        calculated_views = self.calculate_views_from_due_date()

        # Get current views
        current_views = list(self.task_views.values_list('view', flat=True))

        # Add missing views
        for view in calculated_views:
            if view not in current_views:
                TaskView.objects.get_or_create(task=self, view=view)

        # Remove outdated views (except when task is completed in a specific section)
        # Keep views that are still valid or if task is completed and in a completed section
        for view in current_views:
            if view not in calculated_views:
                # Don't remove view if task is completed and in a completed section of that view
                if not (self.completed and self.section and
                       self.section.name == 'Completed' and
                       view in ['today', 'upcoming', 'inbox', 'project']):
                    TaskView.objects.filter(task=self, view=view).delete()

    def save(self, *args, **kwargs):
        """Override save to handle completion date, section detachment, and auto-update views."""
        if self.completed and not self.completed_date:
            from django.utils import timezone
            self.completed_date = timezone.now()
        elif not self.completed:
            self.completed_date = None

        # Detach from section when task is totally completed
        if self.totally_completed:
            self.section = None

        # Save first to ensure the task has an ID
        super().save(*args, **kwargs)

        # Auto-update views based on due_date and project_id
        # Only update views if task is not totally completed
        if not self.totally_completed:
            self.update_task_views()


class TaskView(models.Model):
    """Many-to-many relationship for task views."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_views')
    view = models.CharField(max_length=10, choices=Task.VIEW_CHOICES)

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
    view = models.CharField(max_length=10, choices=Task.VIEW_CHOICES)

    class Meta:
        unique_together = ['section', 'view']
        indexes = [
            models.Index(fields=['view']),
        ]

    def __str__(self):
        return f"{self.section.name} - {self.view}"
