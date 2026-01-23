from rest_framework import serializers
from .models import (
    Account, Project, Section, Task, TaskView, SectionView,
    TaskCollaboration, TaskInvitation, ProjectCollaboration, ProjectInvitation
)


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model (read operations)."""

    class Meta:
        model = Account
        fields = [
            'id', 'username', 'email', 'display_name', 'avatar_url',
            'is_active', 'last_login', 'timezone', 'theme', 'created_at'
        ]
        read_only_fields = ['id', 'last_login', 'created_at']

    def to_representation(self, instance):
        """Convert UUIDs to strings."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data


class AccountRegisterSerializer(serializers.Serializer):
    """Serializer for account registration."""
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    display_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_username(self, value):
        """Check username is unique."""
        if Account.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        """Check email is unique."""
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        """Create account with hashed password."""
        password = validated_data.pop('password')
        account = Account(**validated_data)
        account.set_password(password)
        account.save()
        return account


class AccountLoginSerializer(serializers.Serializer):
    """Serializer for account login."""
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating account profile."""

    class Meta:
        model = Account
        fields = ['display_name', 'avatar_url', 'timezone', 'theme']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model matching ProjectItem interface."""
    user_id = serializers.CharField(read_only=True)
    owner_id = serializers.CharField(read_only=True)
    parent_id = serializers.CharField(read_only=True)
    taskCount = serializers.IntegerField(source='task_count', read_only=True)
    hasChildren = serializers.BooleanField(source='has_children', read_only=True)
    collaborator_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'user_id', 'owner_id', 'name', 'parent_id', 'taskCount',
            'hasChildren', 'icon', 'color', 'access_id', 'is_collaborative',
            'collaborator_count'
        ]
        read_only_fields = ['id', 'user_id', 'owner_id', 'access_id']

    def get_collaborator_count(self, obj):
        """Get count of active collaborators."""
        return obj.collaborations.filter(is_active=True).count()

    def to_representation(self, instance):
        """Convert UUIDs to strings to match TypeScript interface."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        if instance.user:
            data['user_id'] = str(instance.user.id)
            data['owner_id'] = str(instance.user.id)
        return data


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for Section model matching SectionItem interface."""
    user_id = serializers.CharField(read_only=True)
    project_id = serializers.CharField(read_only=True)
    current_view = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ['id', 'user_id', 'name', 'project_id', 'current_view']
        read_only_fields = ['id', 'user_id']

    def get_current_view(self, obj):
        """Get list of views for this section."""
        return [sv.view for sv in obj.section_views.all()]

    def to_representation(self, instance):
        """Convert UUIDs to strings to match TypeScript interface."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        if instance.user:
            data['user_id'] = str(instance.user.id)
        return data


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model matching TaskItem interface."""
    user_id = serializers.CharField(read_only=True)
    project_id = serializers.CharField(read_only=True)
    section_id = serializers.CharField(read_only=True)
    piority = serializers.CharField(source='priority')  # Match typo in TypeScript interface
    current_view = serializers.SerializerMethodField()
    assigned_to_ids = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'user_id', 'name', 'description', 'project_id', 'section_id',
            'due_date', 'completed', 'totally_completed', 'current_view',
            'piority', 'reminder_date', 'completed_date', 'duration_in_minutes',
            'repeat', 'assigned_to_ids'
        ]
        read_only_fields = ['id', 'user_id', 'completed_date']

    def get_current_view(self, obj):
        """Get list of views for this task."""
        return [tv.view for tv in obj.task_views.all()]

    def get_assigned_to_ids(self, obj):
        """Get list of assigned user IDs."""
        return [str(user.id) for user in obj.assigned_to.all()]

    def to_representation(self, instance):
        """Convert UUIDs to strings and format dates to match TypeScript interface."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)

        # Convert user_id to string
        if instance.user:
            data['user_id'] = str(instance.user.id)
        else:
            data['user_id'] = None

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
    user_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    project_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    section_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    piority = serializers.CharField(source='priority', required=False)

    class Meta:
        model = Task
        fields = [
            'user_id', 'name', 'description', 'project_id', 'section_id',
            'due_date', 'piority', 'reminder_date', 'duration_in_minutes', 'repeat'
        ]

    def create(self, validated_data):
        """Create task with proper foreign key relationships. Views are auto-calculated by model."""
        user_id = validated_data.pop('user_id', None)
        project_id = validated_data.pop('project_id', None)
        section_id = validated_data.pop('section_id', None)
        priority = validated_data.pop('priority', 'medium')

        # Set user instance
        if user_id:
            validated_data['user'] = Account.objects.get(id=user_id)

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
    user_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    project_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    current_view = serializers.ListField(
        child=serializers.ChoiceField(choices=Task.VIEW_CHOICES),
        required=False,
        default=list
    )

    class Meta:
        model = Section
        fields = ['user_id', 'name', 'project_id', 'current_view']

    def create(self, validated_data):
        """Create section with proper project relationship and views."""
        user_id = validated_data.pop('user_id', None)
        project_id = validated_data.pop('project_id', None)
        current_view = validated_data.pop('current_view', [])

        # Set user instance
        if user_id:
            validated_data['user'] = Account.objects.get(id=user_id)

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


class CreateProjectSerializer(serializers.ModelSerializer):
    """Serializer for creating projects."""
    user_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Project
        fields = ['user_id', 'name', 'parent_id', 'icon', 'color']

    def create(self, validated_data):
        """Create project with proper user and parent relationships."""
        user_id = validated_data.pop('user_id', None)
        parent_id = validated_data.pop('parent_id', None)

        # Set user instance
        if user_id:
            validated_data['user'] = Account.objects.get(id=user_id)

        # Set parent project
        if parent_id:
            validated_data['parent'] = Project.objects.get(id=parent_id)

        project = Project.objects.create(**validated_data)
        return project


# ============================================
# Collaboration Serializers
# ============================================

class CollaboratorSerializer(serializers.ModelSerializer):
    """Serializer for collaborator info (subset of Account)."""

    class Meta:
        model = Account
        fields = ['id', 'username', 'email', 'display_name', 'avatar_url']
        read_only_fields = ['id', 'username', 'email', 'display_name', 'avatar_url']

    def to_representation(self, instance):
        """Convert UUID to string."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data


class TaskCollaborationSerializer(serializers.ModelSerializer):
    """Serializer for TaskCollaboration model."""
    task_id = serializers.CharField(read_only=True)
    owner_id = serializers.CharField(read_only=True)
    collaborator_id = serializers.CharField(read_only=True)
    owner = CollaboratorSerializer(read_only=True)
    collaborator = CollaboratorSerializer(read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = TaskCollaboration
        fields = [
            'id', 'task_id', 'task_name', 'owner_id', 'owner',
            'collaborator_id', 'collaborator', 'permission',
            'is_active', 'accepted_at', 'created_at'
        ]
        read_only_fields = ['id', 'task_id', 'owner_id', 'collaborator_id', 'accepted_at', 'created_at']

    def to_representation(self, instance):
        """Convert UUIDs to strings."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data


class TaskInvitationSerializer(serializers.ModelSerializer):
    """Serializer for TaskInvitation model."""
    task_id = serializers.CharField(read_only=True)
    invited_by_id = serializers.CharField(read_only=True)
    invitee_id = serializers.CharField(read_only=True)
    invited_by = CollaboratorSerializer(read_only=True)
    invitee = CollaboratorSerializer(read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = TaskInvitation
        fields = [
            'id', 'task_id', 'task_name', 'invited_by_id', 'invited_by',
            'invitee_id', 'invitee', 'invitee_email', 'permission',
            'status', 'message', 'expires_at', 'responded_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'task_id', 'invited_by_id', 'invitee_id',
            'status', 'responded_at', 'created_at'
        ]

    def to_representation(self, instance):
        """Convert UUIDs to strings."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data


class CreateTaskInvitationSerializer(serializers.Serializer):
    """Serializer for creating task invitations."""
    task_id = serializers.UUIDField()
    invitee_id = serializers.UUIDField(required=False, allow_null=True)
    invitee_email = serializers.EmailField(required=False, allow_null=True)
    permission = serializers.ChoiceField(
        choices=TaskCollaboration.PERMISSION_CHOICES,
        default='view'
    )
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Ensure either invitee_id or invitee_email is provided."""
        if not data.get('invitee_id') and not data.get('invitee_email'):
            raise serializers.ValidationError(
                "Either invitee_id or invitee_email must be provided."
            )
        return data


class InvitationResponseSerializer(serializers.Serializer):
    """Serializer for responding to an invitation."""
    action = serializers.ChoiceField(choices=['accept', 'decline'])


class UpdateCollaborationPermissionSerializer(serializers.Serializer):
    """Serializer for updating collaboration permission."""
    permission = serializers.ChoiceField(choices=TaskCollaboration.PERMISSION_CHOICES)


class ProjectCollaborationSerializer(serializers.ModelSerializer):
    """Serializer for ProjectCollaboration model with role-based access."""
    project_id = serializers.CharField(read_only=True)
    collaborator_id = serializers.CharField(read_only=True)
    collaborator = CollaboratorSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_owner = CollaboratorSerializer(source='project.user', read_only=True)

    class Meta:
        model = ProjectCollaboration
        fields = [
            'id', 'project_id', 'project_name', 'project_owner',
            'collaborator_id', 'collaborator', 'role',
            'is_active', 'joined_at', 'created_at'
        ]
        read_only_fields = ['id', 'project_id', 'collaborator_id', 'joined_at', 'created_at']

    def to_representation(self, instance):
        """Convert UUIDs to strings."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        return data


class ProjectInvitationSerializer(serializers.ModelSerializer):
    """Serializer for ProjectInvitation model."""
    project_id = serializers.CharField(source='project.id', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    invited_by = CollaboratorSerializer(read_only=True)
    invitee = CollaboratorSerializer(read_only=True)

    class Meta:
        model = ProjectInvitation
        fields = [
            'id', 'project_id', 'project_name', 'invited_by',
            'invitee', 'invitee_email', 'role', 'status',
            'message', 'expires_at', 'responded_at', 'created_at'
        ]
        read_only_fields = ['id', 'project_id', 'status', 'responded_at', 'created_at']

    def to_representation(self, instance):
        """Convert UUIDs to strings."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        if instance.project:
            data['project_id'] = str(instance.project.id)
        return data


class JoinProjectSerializer(serializers.Serializer):
    """Serializer for joining a project via access_id."""
    access_id = serializers.CharField(max_length=8)


class CreateProjectInvitationSerializer(serializers.Serializer):
    """Serializer for creating project invitations."""
    project_id = serializers.UUIDField()
    invitee_id = serializers.UUIDField(required=False, allow_null=True)
    invitee_email = serializers.EmailField(required=False, allow_null=True)
    role = serializers.ChoiceField(
        choices=ProjectCollaboration.ROLE_CHOICES,
        default='collaborator'
    )
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Ensure either invitee_id or invitee_email is provided."""
        if not data.get('invitee_id') and not data.get('invitee_email'):
            raise serializers.ValidationError(
                "Either invitee_id or invitee_email must be provided."
            )
        return data


class UpdateProjectRoleSerializer(serializers.Serializer):
    """Serializer for updating collaborator role in a project."""
    role = serializers.ChoiceField(choices=ProjectCollaboration.ROLE_CHOICES)


class AssignTaskSerializer(serializers.Serializer):
    """Serializer for assigning users to a task."""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=True
    )


class TransferOwnershipSerializer(serializers.Serializer):
    """Serializer for transferring project ownership."""
    new_owner_id = serializers.UUIDField()


class SharedTaskSerializer(serializers.ModelSerializer):
    """Serializer for tasks that are shared with the user."""
    user_id = serializers.CharField(read_only=True)
    project_id = serializers.CharField(read_only=True)
    section_id = serializers.CharField(read_only=True)
    piority = serializers.CharField(source='priority')
    current_view = serializers.SerializerMethodField()
    owner = CollaboratorSerializer(source='user', read_only=True)
    my_role = serializers.SerializerMethodField()
    assigned_to_ids = serializers.SerializerMethodField()
    is_assigned_to_me = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'user_id', 'name', 'description', 'project_id', 'section_id',
            'due_date', 'completed', 'totally_completed', 'current_view',
            'piority', 'reminder_date', 'completed_date', 'duration_in_minutes',
            'repeat', 'owner', 'my_role', 'assigned_to_ids', 'is_assigned_to_me'
        ]
        read_only_fields = ['id', 'user_id', 'completed_date']

    def get_current_view(self, obj):
        """Get list of views for this task."""
        return [tv.view for tv in obj.task_views.all()]

    def get_my_role(self, obj):
        """Get the current user's role for this task's project."""
        request = self.context.get('request')
        if not request or not hasattr(request, 'account'):
            return None

        # Check if user is the task owner
        if obj.user == request.account:
            return 'owner'

        # Check project collaboration role
        if obj.project:
            if obj.project.user == request.account:
                return 'owner'
            collab = ProjectCollaboration.objects.filter(
                project=obj.project,
                collaborator=request.account,
                is_active=True
            ).first()
            return collab.role if collab else None
        return None

    def get_assigned_to_ids(self, obj):
        """Get list of assigned user IDs."""
        return [str(user.id) for user in obj.assigned_to.all()]

    def get_is_assigned_to_me(self, obj):
        """Check if task is assigned to the current user."""
        request = self.context.get('request')
        if not request or not hasattr(request, 'account'):
            return False
        return obj.assigned_to.filter(id=request.account.id).exists()

    def to_representation(self, instance):
        """Convert UUIDs to strings."""
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        if instance.user:
            data['user_id'] = str(instance.user.id)
        if instance.project:
            data['project_id'] = str(instance.project.id)
        if instance.section:
            data['section_id'] = str(instance.section.id)
        if data['due_date']:
            data['due_date'] = instance.due_date.isoformat()
        if data['reminder_date']:
            data['reminder_date'] = instance.reminder_date.isoformat()
        if data['completed_date']:
            data['completed_date'] = instance.completed_date.isoformat()
        else:
            data['completed_date'] = ""
        return data