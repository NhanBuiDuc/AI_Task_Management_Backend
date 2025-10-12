from rest_framework import serializers
from .models import Project, Section, Task, TaskView, SectionView


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model matching ProjectItem interface."""
    parent_id = serializers.CharField(read_only=True)
    taskCount = serializers.IntegerField(source='task_count', read_only=True)
    hasChildren = serializers.BooleanField(source='has_children', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'parent_id', 'taskCount', 'hasChildren', 'icon', 'color']
        read_only_fields = ['id']

    def to_representation(self, instance):
        """Convert UUIDs to strings to match TypeScript interface."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for Section model matching SectionItem interface."""
    project_id = serializers.CharField(read_only=True)
    current_view = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ['id', 'name', 'project_id', 'current_view']
        read_only_fields = ['id']

    def get_current_view(self, obj):
        """Get list of views for this section."""
        return [sv.view for sv in obj.section_views.all()]

    def to_representation(self, instance):
        """Convert UUIDs to strings to match TypeScript interface."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model matching TaskItem interface."""
    project_id = serializers.CharField(read_only=True)
    section_id = serializers.CharField(read_only=True)
    piority = serializers.CharField(source='priority')  # Match typo in TypeScript interface
    current_view = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'name', 'description', 'project_id', 'section_id',
            'due_date', 'completed', 'totally_completed', 'current_view',
            'piority', 'reminder_date', 'completed_date', 'duration_in_minutes', 'repeat'
        ]
        read_only_fields = ['id', 'completed_date']

    def get_current_view(self, obj):
        """Get list of views for this task."""
        return [tv.view for tv in obj.task_views.all()]

    def to_representation(self, instance):
        """Convert UUIDs to strings and format dates to match TypeScript interface."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)

        # Convert UUID foreign keys to strings
        if instance.project:
            data['project_id'] = str(instance.project.id)
        else:
            data['project_id'] = None

        if instance.section:
            data['section_id'] = str(instance.section.id)
        else:
            data['section_id'] = None

        # Format dates as ISO strings
        if data['due_date']:
            data['due_date'] = instance.due_date.isoformat()
        if data['reminder_date']:
            data['reminder_date'] = instance.reminder_date.isoformat()
        if data['completed_date']:
            data['completed_date'] = instance.completed_date.isoformat()
        else:
            data['completed_date'] = ""  # Match TypeScript interface

        return data

    def create(self, validated_data):
        """Create task with view relationships."""
        current_view = validated_data.pop('current_view', [])
        priority = validated_data.pop('priority', 'medium')

        task = Task.objects.create(priority=priority, **validated_data)

        # Create task views
        for view in current_view:
            TaskView.objects.create(task=task, view=view)

        return task

    def update(self, instance, validated_data):
        """Update task and handle view relationships."""
        current_view = validated_data.pop('current_view', None)
        priority = validated_data.pop('priority', None)

        if priority is not None:
            instance.priority = priority

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update task views if provided
        if current_view is not None:
            instance.task_views.all().delete()
            for view in current_view:
                TaskView.objects.create(task=instance, view=view)

        return instance


class CreateTaskSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks with required fields."""
    project_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    section_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    piority = serializers.CharField(source='priority', required=False)

    class Meta:
        model = Task
        fields = [
            'name', 'description', 'project_id', 'section_id',
            'due_date', 'piority', 'reminder_date', 'duration_in_minutes', 'repeat'
        ]

    def create(self, validated_data):
        """Create task with proper foreign key relationships. Views are auto-calculated by model."""
        project_id = validated_data.pop('project_id', None)
        section_id = validated_data.pop('section_id', None)
        priority = validated_data.pop('priority', 'medium')

        # Set project and section instances
        if project_id:
            validated_data['project'] = Project.objects.get(id=project_id)
        if section_id:
            validated_data['section'] = Section.objects.get(id=section_id)

        # Create task - the model's save() method will automatically calculate and set current_view
        task = Task.objects.create(priority=priority, **validated_data)

        # No need to manually create TaskView objects - the model handles this automatically
        return task


class CreateSectionSerializer(serializers.ModelSerializer):
    """Serializer for creating sections."""
    project_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    current_view = serializers.ListField(
        child=serializers.ChoiceField(choices=Task.VIEW_CHOICES),
        required=False,
        default=list
    )

    class Meta:
        model = Section
        fields = ['name', 'project_id', 'current_view']

    def create(self, validated_data):
        """Create section with proper project relationship and views."""
        project_id = validated_data.pop('project_id', None)
        current_view = validated_data.pop('current_view', [])

        if project_id:
            project = Project.objects.get(id=project_id)
            section = Section.objects.create(project=project, **validated_data)
        else:
            # Create section without project (for Inbox, Today, etc.)
            section = Section.objects.create(project=None, **validated_data)

        # Create section views
        for view in current_view:
            SectionView.objects.create(section=section, view=view)

        return section