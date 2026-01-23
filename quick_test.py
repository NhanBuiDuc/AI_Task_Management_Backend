#!/usr/bin/env python3
"""
Quick Test Script for JARVIS Backend
Tests database connectivity and basic API functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')
django.setup()

from tasks_api.models import Project, Section, Task
from datetime import datetime, timedelta

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")

def test_database_connection():
    """Test database connectivity"""
    print_header("Testing Database Connection")
    try:
        # Try to query the database
        count = Project.objects.count()
        print(f"✓ Database connected successfully")
        print(f"✓ Found {count} projects")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_model_creation():
    """Test creating models"""
    print_header("Testing Model Creation")
    try:
        # Create a test project
        project = Project.objects.create(
            name="Test Project",
            icon="🧪",
            color="#FF6B6B"
        )
        print(f"✓ Created project: {project.name} (ID: {project.id})")

        # Create a test section
        section = Section.objects.create(
            name="Test Section",
            project=project
        )
        print(f"✓ Created section: {section.name} (ID: {section.id})")

        # Create a test task
        today = datetime.now().date()
        task = Task.objects.create(
            name="Test Task",
            description="This is a test task",
            project=project,
            section=section,
            due_date=today,
            priority="medium",
            duration_in_minutes=30
        )
        print(f"✓ Created task: {task.name} (ID: {task.id})")
        print(f"✓ Task views: {[tv.view for tv in task.task_views.all()]}")

        return True
    except Exception as e:
        print(f"✗ Model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_view_calculation():
    """Test automatic view calculation"""
    print_header("Testing Task View Auto-Calculation")
    try:
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        last_week = today - timedelta(days=7)

        # Test 1: Task due today (inbox)
        task_today = Task.objects.create(
            name="Today Task",
            due_date=today,
            priority="high",
            duration_in_minutes=30
        )
        views_today = [tv.view for tv in task_today.task_views.all()]
        print(f"✓ Today task views: {views_today}")
        assert 'inbox' in views_today and 'today' in views_today

        # Test 2: Task due next week (inbox)
        task_upcoming = Task.objects.create(
            name="Upcoming Task",
            due_date=next_week,
            priority="medium",
            duration_in_minutes=45
        )
        views_upcoming = [tv.view for tv in task_upcoming.task_views.all()]
        print(f"✓ Upcoming task views: {views_upcoming}")
        assert 'inbox' in views_upcoming and 'upcoming' in views_upcoming

        # Test 3: Overdue task
        task_overdue = Task.objects.create(
            name="Overdue Task",
            due_date=last_week,
            priority="urgent",
            duration_in_minutes=60
        )
        views_overdue = [tv.view for tv in task_overdue.task_views.all()]
        print(f"✓ Overdue task views: {views_overdue}")
        assert 'inbox' in views_overdue and 'overdue' in views_overdue

        print("\n✓ All view calculation tests passed!")
        return True
    except Exception as e:
        print(f"✗ View calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_counts():
    """Test task counts"""
    print_header("Testing Task Counts")
    try:
        from tasks_api.models import TaskView

        # Get counts
        inbox_task_ids = TaskView.objects.filter(view='inbox').values_list('task_id', flat=True)
        project_task_ids = TaskView.objects.filter(view='project').values_list('task_id', flat=True)

        inbox_count = Task.objects.filter(
            id__in=inbox_task_ids,
            totally_completed=False
        ).exclude(
            id__in=project_task_ids
        ).count()

        today_count = Task.objects.filter(
            totally_completed=False,
            due_date=datetime.now().date()
        ).count()

        print(f"✓ Inbox tasks: {inbox_count}")
        print(f"✓ Today tasks: {today_count}")
        print(f"✓ All active tasks: {Task.objects.filter(totally_completed=False).count()}")
        print(f"✓ Total projects: {Project.objects.count()}")
        print(f"✓ Total sections: {Section.objects.count()}")

        return True
    except Exception as e:
        print(f"✗ Counts test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data"""
    print_header("Cleaning Up Test Data")
    try:
        # Delete test tasks
        deleted_tasks = Task.objects.all().delete()
        print(f"✓ Deleted {deleted_tasks[0]} tasks")

        # Delete test sections
        deleted_sections = Section.objects.all().delete()
        print(f"✓ Deleted {deleted_sections[0]} sections")

        # Delete test projects
        deleted_projects = Project.objects.all().delete()
        print(f"✓ Deleted {deleted_projects[0]} projects")

        return True
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header("JARVIS Backend Quick Test")
    print("This script tests basic database and model functionality\n")

    results = []

    # Run tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Model Creation", test_model_creation()))
    results.append(("View Auto-Calculation", test_task_view_calculation()))
    results.append(("Task Counts", test_counts()))
    results.append(("Cleanup", cleanup_test_data()))

    # Print summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Your backend is ready to use.")
        print("\nNext steps:")
        print("1. Run: python manage.py runserver 0.0.0.0:8000")
        print("2. Run: python test_apis.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
