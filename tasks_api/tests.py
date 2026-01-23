# tasks_api/tests.py
"""
Django Unit Tests for Task API CRUD Operations
Run with: python manage.py test tasks_api
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
from .models import Task, Project, Section, TaskView


class TaskModelTestCase(TestCase):
    """Test cases for Task model"""

    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(
            name="Test Project",
            icon="📁",
            color="#3B82F6"
        )
        self.section = Section.objects.create(
            name="Test Section",
            project=self.project
        )
        self.today = date.today()

    def test_create_task_basic(self):
        """Test creating a basic task"""
        task = Task.objects.create(
            name="Test Task",
            description="Test Description",
            due_date=self.today,
            priority="medium"
        )
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.description, "Test Description")
        self.assertEqual(task.due_date, self.today)
        self.assertEqual(task.priority, "medium")
        self.assertFalse(task.completed)
        self.assertFalse(task.totally_completed)

    def test_create_task_with_project(self):
        """Test creating a task with project"""
        task = Task.objects.create(
            name="Project Task",
            due_date=self.today,
            project=self.project
        )
        self.assertEqual(task.project, self.project)
        self.assertEqual(task.project_id, str(self.project.id))

    def test_create_task_with_section(self):
        """Test creating a task with section"""
        task = Task.objects.create(
            name="Section Task",
            due_date=self.today,
            project=self.project,
            section=self.section
        )
        self.assertEqual(task.section, self.section)
        self.assertEqual(task.section_id, str(self.section.id))

    def test_task_auto_view_calculation_inbox(self):
        """Test that inbox tasks get 'inbox' view automatically"""
        task = Task.objects.create(
            name="Inbox Task",
            due_date=self.today,
            project=None
        )
        views = list(task.task_views.values_list('view', flat=True))
        self.assertIn('inbox', views)
        self.assertNotIn('project', views)

    def test_task_auto_view_calculation_project(self):
        """Test that project tasks get 'project' view automatically"""
        task = Task.objects.create(
            name="Project Task",
            due_date=self.today,
            project=self.project
        )
        views = list(task.task_views.values_list('view', flat=True))
        self.assertIn('project', views)
        self.assertNotIn('inbox', views)

    def test_task_auto_view_calculation_today(self):
        """Test that tasks due today get 'today' view"""
        task = Task.objects.create(
            name="Today Task",
            due_date=self.today,
            project=None
        )
        views = list(task.task_views.values_list('view', flat=True))
        self.assertIn('today', views)

    def test_task_auto_view_calculation_upcoming(self):
        """Test that tasks due in next 14 days get 'upcoming' view"""
        task = Task.objects.create(
            name="Upcoming Task",
            due_date=self.today + timedelta(days=7),
            project=None
        )
        views = list(task.task_views.values_list('view', flat=True))
        self.assertIn('upcoming', views)

    def test_task_auto_view_calculation_overdue(self):
        """Test that overdue tasks get 'overdue' view"""
        task = Task.objects.create(
            name="Overdue Task",
            due_date=self.today - timedelta(days=3),
            project=None
        )
        views = list(task.task_views.values_list('view', flat=True))
        self.assertIn('overdue', views)

    def test_task_completion_sets_completed_date(self):
        """Test that completing a task sets completed_date"""
        task = Task.objects.create(
            name="Complete Me",
            due_date=self.today
        )
        self.assertIsNone(task.completed_date)

        task.completed = True
        task.save()

        self.assertIsNotNone(task.completed_date)

    def test_task_total_completion_detaches_section(self):
        """Test that totally completing a task removes section"""
        task = Task.objects.create(
            name="Archive Me",
            due_date=self.today,
            project=self.project,
            section=self.section
        )
        self.assertEqual(task.section, self.section)

        task.totally_completed = True
        task.save()

        self.assertIsNone(task.section)


class TaskAPITestCase(APITestCase):
    """Test cases for Task API endpoints"""

    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        self.today = date.today()

        # Create a project for testing
        self.project = Project.objects.create(
            name="API Test Project",
            icon="📁",
            color="#3B82F6"
        )

        # Create a section
        self.section = Section.objects.create(
            name="API Test Section",
            project=self.project
        )

    # ===================
    # CREATE Tests
    # ===================

    def test_create_task_success(self):
        """Test POST /tasks/ - Create task successfully"""
        data = {
            "name": "New Task",
            "description": "Task description",
            "due_date": self.today.isoformat(),
            "piority": "high",
            "duration_in_minutes": 30
        }
        response = self.client.post('/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "New Task")
        self.assertEqual(response.data['piority'], "high")
        self.assertIsNotNone(response.data['id'])

    def test_create_task_with_project(self):
        """Test POST /tasks/ - Create task with project"""
        data = {
            "name": "Project Task",
            "due_date": self.today.isoformat(),
            "project_id": str(self.project.id),
            "piority": "medium"
        }
        response = self.client.post('/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['project_id'], str(self.project.id))

    def test_create_task_with_section(self):
        """Test POST /tasks/ - Create task with section"""
        data = {
            "name": "Section Task",
            "due_date": self.today.isoformat(),
            "project_id": str(self.project.id),
            "section_id": str(self.section.id),
            "piority": "low"
        }
        response = self.client.post('/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['section_id'], str(self.section.id))

    def test_create_task_missing_required_field(self):
        """Test POST /tasks/ - Fail without required fields"""
        data = {
            "description": "No name provided"
        }
        response = self.client.post('/tasks/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ===================
    # READ Tests
    # ===================

    def test_list_tasks(self):
        """Test GET /tasks/ - List all tasks"""
        # Create some tasks
        Task.objects.create(name="Task 1", due_date=self.today)
        Task.objects.create(name="Task 2", due_date=self.today)

        response = self.client.get('/tasks/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_task(self):
        """Test GET /tasks/{id}/ - Retrieve single task"""
        task = Task.objects.create(
            name="Retrieve Me",
            description="Test description",
            due_date=self.today,
            priority="high"
        )

        response = self.client.get(f'/tasks/{task.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Retrieve Me")
        self.assertEqual(response.data['id'], str(task.id))

    def test_retrieve_task_not_found(self):
        """Test GET /tasks/{id}/ - Task not found"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f'/tasks/{fake_uuid}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_tasks_by_project(self):
        """Test GET /tasks/?project_id= - Filter by project"""
        Task.objects.create(name="Project Task", due_date=self.today, project=self.project)
        Task.objects.create(name="Inbox Task", due_date=self.today, project=None)

        response = self.client.get(f'/tasks/?project_id={self.project.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Project Task")

    # ===================
    # UPDATE Tests
    # ===================

    def test_update_task_partial(self):
        """Test PATCH /tasks/{id}/ - Partial update"""
        task = Task.objects.create(
            name="Original Name",
            due_date=self.today,
            priority="low"
        )

        data = {"name": "Updated Name"}
        response = self.client.patch(f'/tasks/{task.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Updated Name")

        # Verify in database
        task.refresh_from_db()
        self.assertEqual(task.name, "Updated Name")

    def test_update_task_priority(self):
        """Test PATCH /tasks/{id}/ - Update priority"""
        task = Task.objects.create(name="Priority Test", due_date=self.today, priority="low")

        data = {"priority": "urgent"}
        response = self.client.patch(f'/tasks/{task.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.priority, "urgent")

    def test_mark_task_completed(self):
        """Test PATCH /tasks/{id}/completion/ - Mark completed"""
        task = Task.objects.create(name="Complete Me", due_date=self.today)

        response = self.client.patch(
            f'/tasks/{task.id}/completion/',
            {"completed": True},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['completed'])

        task.refresh_from_db()
        self.assertTrue(task.completed)
        self.assertIsNotNone(task.completed_date)

    def test_mark_task_totally_completed(self):
        """Test PATCH /tasks/{id}/total_completion/ - Archive task"""
        task = Task.objects.create(
            name="Archive Me",
            due_date=self.today,
            section=self.section,
            project=self.project
        )

        response = self.client.patch(
            f'/tasks/{task.id}/total_completion/',
            {"totally_completed": True},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['totally_completed'])

        task.refresh_from_db()
        self.assertTrue(task.totally_completed)
        self.assertIsNone(task.section)

    def test_move_task_to_project(self):
        """Test PATCH /tasks/{id}/move_to_project/ - Move to project"""
        task = Task.objects.create(name="Move Me", due_date=self.today)

        response = self.client.patch(
            f'/tasks/{task.id}/move_to_project/',
            {"project_id": str(self.project.id)},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.project, self.project)

    def test_move_task_to_section(self):
        """Test PATCH /tasks/{id}/move_to_section/ - Move to section"""
        task = Task.objects.create(name="Section Move", due_date=self.today)

        response = self.client.patch(
            f'/tasks/{task.id}/move_to_section/',
            {"section_id": str(self.section.id)},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.section, self.section)
        self.assertEqual(task.project, self.project)  # Should also set project

    def test_make_task_unsectioned(self):
        """Test PATCH /tasks/{id}/make_unsectioned/ - Remove section"""
        task = Task.objects.create(
            name="Unsection Me",
            due_date=self.today,
            section=self.section,
            project=self.project
        )

        response = self.client.patch(f'/tasks/{task.id}/make_unsectioned/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertIsNone(task.section)

    # ===================
    # DELETE Tests
    # ===================

    def test_delete_task(self):
        """Test DELETE /tasks/{id}/ - Delete task"""
        task = Task.objects.create(name="Delete Me", due_date=self.today)
        task_id = task.id

        response = self.client.delete(f'/tasks/{task.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_delete_task_not_found(self):
        """Test DELETE /tasks/{id}/ - Task not found"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.delete(f'/tasks/{fake_uuid}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskViewFiltersTestCase(APITestCase):
    """Test cases for Task view filters"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.today = date.today()
        self.project = Project.objects.create(name="Filter Test Project")

    def test_get_tasks_by_view_inbox(self):
        """Test GET /tasks/by_view/?view=inbox"""
        # Create inbox task
        Task.objects.create(name="Inbox Task", due_date=self.today, project=None)
        # Create project task (should not appear in inbox)
        Task.objects.create(name="Project Task", due_date=self.today, project=self.project)

        response = self.client.get('/tasks/by_view/?view=inbox')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Inbox Task")

    def test_get_tasks_by_due_date(self):
        """Test GET /tasks/by_due_date/?due_date="""
        Task.objects.create(name="Today Task", due_date=self.today)
        Task.objects.create(name="Tomorrow Task", due_date=self.today + timedelta(days=1))

        response = self.client.get(f'/tasks/by_due_date/?due_date={self.today.isoformat()}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Today Task")

    def test_get_tasks_by_date_range(self):
        """Test GET /tasks/by_date_range/?start_date=&end_date="""
        Task.objects.create(name="Task 1", due_date=self.today)
        Task.objects.create(name="Task 2", due_date=self.today + timedelta(days=3))
        Task.objects.create(name="Task 3", due_date=self.today + timedelta(days=10))

        start = self.today.isoformat()
        end = (self.today + timedelta(days=5)).isoformat()

        response = self.client.get(f'/tasks/by_date_range/?start_date={start}&end_date={end}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_overdue_tasks(self):
        """Test GET /tasks/overdue/"""
        Task.objects.create(name="Overdue", due_date=self.today - timedelta(days=5))
        Task.objects.create(name="Today", due_date=self.today)

        response = self.client.get('/tasks/overdue/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Overdue")

    def test_get_completed_tasks(self):
        """Test GET /tasks/completed/"""
        task = Task.objects.create(name="Completed Task", due_date=self.today)
        task.totally_completed = True
        task.save()

        Task.objects.create(name="Active Task", due_date=self.today)

        response = self.client.get('/tasks/completed/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Completed Task")

    def test_get_task_counts(self):
        """Test GET /tasks/counts/"""
        # Create various tasks
        Task.objects.create(name="Inbox Today", due_date=self.today, project=None)
        Task.objects.create(name="Project Task", due_date=self.today, project=self.project)
        Task.objects.create(name="Overdue", due_date=self.today - timedelta(days=3))

        response = self.client.get(f'/tasks/counts/?today_date={self.today.isoformat()}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('inbox', response.data)
        self.assertIn('today', response.data)
        self.assertIn('upcoming', response.data)
        self.assertIn('overdue', response.data)
        self.assertIn('completed', response.data)


class ProjectAPITestCase(APITestCase):
    """Test cases for Project API endpoints"""

    def test_create_project(self):
        """Test POST /projects/ - Create project"""
        data = {
            "name": "New Project",
            "icon": "📁",
            "color": "#FF6B6B"
        }
        response = self.client.post('/projects/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "New Project")

    def test_list_projects(self):
        """Test GET /projects/ - List all projects"""
        Project.objects.create(name="Project 1")
        Project.objects.create(name="Project 2")

        response = self.client.get('/projects/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_project(self):
        """Test GET /projects/{id}/ - Retrieve single project"""
        project = Project.objects.create(name="Test Project")

        response = self.client.get(f'/projects/{project.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Project")

    def test_update_project(self):
        """Test PATCH /projects/{id}/ - Update project"""
        project = Project.objects.create(name="Original")

        response = self.client.patch(
            f'/projects/{project.id}/',
            {"name": "Updated"},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Updated")

    def test_delete_project(self):
        """Test DELETE /projects/{id}/ - Delete project"""
        project = Project.objects.create(name="Delete Me")

        response = self.client.delete(f'/projects/{project.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SectionAPITestCase(APITestCase):
    """Test cases for Section API endpoints"""

    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    def test_create_section(self):
        """Test POST /sections/ - Create section"""
        data = {
            "name": "New Section",
            "project_id": str(self.project.id)
        }
        response = self.client.post('/sections/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "New Section")

    def test_list_sections(self):
        """Test GET /sections/ - List all sections"""
        Section.objects.create(name="Section 1", project=self.project)
        Section.objects.create(name="Section 2", project=self.project)

        response = self.client.get('/sections/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_sections_by_project(self):
        """Test GET /sections/?project_id= - Filter by project"""
        Section.objects.create(name="Project Section", project=self.project)
        Section.objects.create(name="Inbox Section", project=None)

        response = self.client.get(f'/sections/?project_id={self.project.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_section(self):
        """Test PATCH /sections/{id}/ - Update section"""
        section = Section.objects.create(name="Original", project=self.project)

        response = self.client.patch(
            f'/sections/{section.id}/',
            {"name": "Updated"},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Updated")

    def test_delete_section(self):
        """Test DELETE /sections/{id}/ - Delete section"""
        section = Section.objects.create(name="Delete Me", project=self.project)

        response = self.client.delete(f'/sections/{section.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
