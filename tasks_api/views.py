from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Project, Section, Task, TaskView
from .serializers import (
    ProjectSerializer, SectionSerializer, TaskSerializer,
    CreateTaskSerializer, CreateSectionSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project model with all required endpoints."""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=False, methods=['get'])
    def check_name(self, request):
        """Check if project name exists."""
        name = request.query_params.get('name')
        parent_id = request.query_params.get('parent_id')

        if not name:
            return Response({'error': 'Name parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        query = Q(name=name)
        if parent_id:
            query &= Q(parent_id=parent_id)
        else:
            query &= Q(parent__isnull=True)

        exists = Project.objects.filter(query).exists()
        return Response({'exists': exists})

    @action(detail=True, methods=['get'])
    def independent(self, request, pk=None):
        """Check if project is independent."""
        project = self.get_object()
        return Response({'independent': project.is_independent()})

    @action(detail=True, methods=['get'])
    def task_count(self, request, pk=None):
        """Get task count for project."""
        project = self.get_object()
        return Response({'count': project.task_count})

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get sub projects."""
        project = self.get_object()
        children = project.children.all()
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        """Move project to become child of another project."""
        project = self.get_object()
        parent_id = request.data.get('parent_id')

        try:
            if parent_id:
                parent = Project.objects.get(id=parent_id)
                project.parent = parent
            else:
                project.parent = None
            project.save()

            serializer = self.get_serializer(project)
            return Response(serializer.data)
        except Project.DoesNotExist:
            return Response({'error': 'Parent project not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'])
    def make_independent(self, request, pk=None):
        """Make project independent."""
        project = self.get_object()
        project.parent = None
        project.save()

        serializer = self.get_serializer(project)
        return Response(serializer.data)


class SectionViewSet(viewsets.ModelViewSet):
    """ViewSet for Section model with all required endpoints."""
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def get_queryset(self):
        """Filter sections by project and current_view if specified."""
        queryset = Section.objects.all()
        project_id = self.request.query_params.get('project_id')
        current_view = self.request.query_params.get('current_view')

        if project_id is not None:
            if project_id.lower() == 'null':
                # Handle special sections (project_id = null) - Inbox, Today, etc
                queryset = queryset.filter(project__isnull=True)
            else:
                queryset = queryset.filter(project_id=project_id)

        # Filter by current_view using SectionView relationships
        if current_view:
            from .models import SectionView
            section_ids = SectionView.objects.filter(view=current_view).values_list('section_id', flat=True)
            queryset = queryset.filter(id__in=section_ids)

        return queryset

    def get_serializer_class(self):
        """Use CreateSectionSerializer for creation."""
        if self.action == 'create':
            return CreateSectionSerializer
        return SectionSerializer

    def create(self, request, *args, **kwargs):
        """Create section and return properly formatted response."""
        # Use CreateSectionSerializer for validation and creation
        create_serializer = CreateSectionSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        section = create_serializer.save()

        # Use SectionSerializer for response to ensure proper formatting
        response_serializer = SectionSerializer(section)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def check_name(self, request):
        """Check if section name exists within project."""
        project_id = request.query_params.get('project_id')
        name = request.query_params.get('name')

        if project_id is None or not name:
            return Response({'error': 'project_id and name parameters required'}, status=status.HTTP_400_BAD_REQUEST)

        if project_id.lower() == 'null':
            # Check for Inbox sections (project_id = null)
            exists = Section.objects.filter(project__isnull=True, name=name).exists()
        else:
            exists = Section.objects.filter(project_id=project_id, name=name).exists()

        return Response({'exists': exists})

    @action(detail=False, methods=['post'])
    def get_or_create_completed(self, request):
        """Get or create the 'Completed' section for a project."""
        project_id = request.data.get('project_id')

        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if 'Completed' section already exists for this project
            completed_section, created = Section.objects.get_or_create(
                project_id=project_id,
                name='Completed',
                defaults={'name': 'Completed'}
            )

            serializer = SectionSerializer(completed_section)
            return Response({
                'section': serializer.data,
                'created': created
            }, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task model with all required endpoints."""
    queryset = Task.objects.filter(totally_completed=False)
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Filter tasks by project if specified, excluding totally completed tasks."""
        queryset = Task.objects.filter(totally_completed=False)
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def get_serializer_class(self):
        """Use CreateTaskSerializer for creation."""
        if self.action == 'create':
            return CreateTaskSerializer
        return TaskSerializer

    def create(self, request, *args, **kwargs):
        """Create task and return properly formatted response."""
        # Use CreateTaskSerializer for validation and creation
        create_serializer = CreateTaskSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        task = create_serializer.save()

        # Use TaskSerializer for response to ensure proper formatting
        response_serializer = TaskSerializer(task)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks."""
        now = timezone.now()
        queryset = Task.objects.filter(due_date__lt=now, completed=False, totally_completed=False)

        project_id = request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def due_in_days(self, request):
        """Get tasks due in specified number of days."""
        days = request.query_params.get('days')
        if not days or days not in ['3', '7', '14']:
            return Response({'error': 'days parameter must be 3, 7, or 14'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        target_date = now + timedelta(days=int(days))

        queryset = Task.objects.filter(
            due_date__gte=now,
            due_date__lte=target_date,
            completed=False,
            totally_completed=False
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def move_to_project(self, request, pk=None):
        """Move task to another project."""
        task = self.get_object()
        project_id = request.data.get('project_id')

        try:
            if project_id:
                project = Project.objects.get(id=project_id)
                task.project = project
                task.section = None  # Clear section when moving to different project
            else:
                task.project = None
            task.save()

            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'])
    def move_to_section(self, request, pk=None):
        """Move task to another section."""
        task = self.get_object()
        section_id = request.data.get('section_id')

        try:
            if section_id:
                section = Section.objects.get(id=section_id)
                task.section = section
                task.project = section.project  # Ensure task belongs to section's project
            else:
                task.section = None
            task.save()

            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except Section.DoesNotExist:
            return Response({'error': 'Section not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'])
    def make_unsectioned(self, request, pk=None):
        """Make task unsectioned."""
        task = self.get_object()
        task.section = None
        task.save()

        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def completion(self, request, pk=None):
        """Update task completion status."""
        task = self.get_object()
        completed = request.data.get('completed')

        if completed is not None:
            task.completed = completed
            task.save()

        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def total_completion(self, request, pk=None):
        """Update task total completion status."""
        task = self.get_object()
        totally_completed = request.data.get('totally_completed')

        if totally_completed is not None:
            task.totally_completed = totally_completed
            task.save()

        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def views(self, request, pk=None):
        """Update task views."""
        task = self.get_object()
        current_view = request.data.get('current_view', [])

        # Clear existing views
        task.task_views.all().delete()

        # Add new views
        for view in current_view:
            TaskView.objects.create(task=task, view=view)

        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_view(self, request):
        """Get tasks by view."""
        view = request.query_params.get('view')
        if not view:
            return Response({'error': 'view parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        # Special handling for inbox view to match counting logic
        if view == 'inbox':
            # Inbox: tasks with inbox view BUT NOT project view (non-project tasks only)
            inbox_task_ids = TaskView.objects.filter(view='inbox').values_list('task_id', flat=True)
            project_task_ids = TaskView.objects.filter(view='project').values_list('task_id', flat=True)
            queryset = Task.objects.filter(
                id__in=inbox_task_ids,
                totally_completed=False
            ).exclude(
                id__in=project_task_ids
            )
        else:
            # For other views, use standard logic
            task_ids = TaskView.objects.filter(view=view).values_list('task_id', flat=True)
            queryset = Task.objects.filter(id__in=task_ids, totally_completed=False)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_priority(self, request):
        """Get tasks by priority."""
        priority = request.query_params.get('priority')
        if not priority:
            return Response({'error': 'priority parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Task.objects.filter(priority=priority, totally_completed=False)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_due_date(self, request):
        """Get tasks by due date (for Today view)."""
        due_date = request.query_params.get('due_date')
        if not due_date:
            return Response({'error': 'due_date parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Parse date string (YYYY-MM-DD format)
            from datetime import datetime
            target_date = datetime.strptime(due_date, '%Y-%m-%d').date()

            queryset = Task.objects.filter(due_date=target_date, totally_completed=False)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get all totally completed tasks for the Completed page."""
        queryset = Task.objects.filter(totally_completed=True)

        # Optional filter by project
        project_id = request.query_params.get('project_id')
        if project_id:
            if project_id.lower() == 'null':
                queryset = queryset.filter(project__isnull=True)
            else:
                queryset = queryset.filter(project_id=project_id)

        # Optional filter by section
        section_id = request.query_params.get('section_id')
        if section_id:
            queryset = queryset.filter(section_id=section_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Get tasks due in a date range (for Upcoming view)."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date parameters required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Parse date strings (YYYY-MM-DD format)
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

            queryset = Task.objects.filter(
                due_date__gte=start_date_obj,
                due_date__lte=end_date_obj,
                totally_completed=False
            )

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def counts(self, request):
        """Get task counts for all navigation views."""
        from datetime import datetime, timedelta

        # Get current date for today and upcoming calculations
        # Accept optional today_date parameter to match frontend logic
        today_param = request.query_params.get('today_date')
        if today_param:
            try:
                today_date = datetime.strptime(today_param, '%Y-%m-%d').date()
            except ValueError:
                # Fall back to server date if invalid format
                now = timezone.now()
                today_date = now.date()
        else:
            now = timezone.now()
            today_date = now.date()

        # Calculate current-day-based week boundaries for upcoming (matching frontend logic)
        # This Week: current day to current day + 7
        this_week_start = today_date
        this_week_end = today_date + timedelta(days=7)

        # Next Week: current day + 7 + 1 to current day + 7 + 7
        next_week_start = today_date + timedelta(days=8)
        next_week_end = today_date + timedelta(days=14)

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

        # Upcoming: tasks due between current day and current day + 14 (both weeks)
        upcoming_count = active_tasks.filter(
            due_date__gte=this_week_start,
            due_date__lte=next_week_end
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

        return Response({
            'inbox': inbox_count,
            'today': today_count,
            'upcoming': upcoming_count,
            'overdue': overdue_count,
            'completed': completed_count,
            'projects': project_counts
        })
