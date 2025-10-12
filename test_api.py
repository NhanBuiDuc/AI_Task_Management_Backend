#!/usr/bin/env python
"""
Simple script to test the API endpoints and create sample data.
Run this after starting the Django server with: python manage.py runserver 8000
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = 'http://localhost:8000/api'

def test_projects():
    """Test project endpoints."""
    print("Testing Projects API...")

    # Create a project
    project_data = {
        "name": "Test Project",
        "icon": "folder",
        "color": "#FF6B6B"
    }

    response = requests.post(f'{API_BASE}/projects/', json=project_data)
    print(f"Create Project: {response.status_code}")
    if response.status_code == 201:
        project = response.json()
        print(f"Created project: {project['name']} (ID: {project['id']})")

        # Test get all projects
        response = requests.get(f'{API_BASE}/projects/')
        print(f"Get All Projects: {response.status_code}")

        # Test check name
        response = requests.get(f'{API_BASE}/projects/check-name/?name=Test Project')
        print(f"Check Name Exists: {response.status_code} - {response.json()}")

        return project['id']
    return None

def test_sections(project_id):
    """Test section endpoints."""
    if not project_id:
        return None

    print("\nTesting Sections API...")

    # Create a section
    section_data = {
        "name": "Test Section",
        "project_id": project_id
    }

    response = requests.post(f'{API_BASE}/sections/', json=section_data)
    print(f"Create Section: {response.status_code}")
    if response.status_code == 201:
        section = response.json()
        print(f"Created section: {section['name']} (ID: {section['id']})")

        # Test get sections by project
        response = requests.get(f'{API_BASE}/sections/?project_id={project_id}')
        print(f"Get Sections by Project: {response.status_code}")

        return section['id']
    return None

def test_tasks(project_id, section_id):
    """Test task endpoints."""
    if not project_id:
        return None

    print("\nTesting Tasks API...")

    # Create a task
    due_date = (datetime.now() + timedelta(days=7)).isoformat()
    task_data = {
        "name": "Test Task",
        "description": "A test task for API validation",
        "project_id": project_id,
        "section_id": section_id,
        "due_date": due_date,
        "piority": "high",
        "current_view": ["inbox", "project"]
    }

    response = requests.post(f'{API_BASE}/tasks/', json=task_data)
    print(f"Create Task: {response.status_code}")
    if response.status_code == 201:
        task = response.json()
        print(f"Created task: {task['name']} (ID: {task['id']})")

        # Test get tasks by project
        response = requests.get(f'{API_BASE}/tasks/?project_id={project_id}')
        print(f"Get Tasks by Project: {response.status_code}")

        # Test get tasks by priority
        response = requests.get(f'{API_BASE}/tasks/by-priority/?priority=high')
        print(f"Get Tasks by Priority: {response.status_code}")

        # Test update task completion
        response = requests.patch(f'{API_BASE}/tasks/{task["id"]}/completion/',
                                json={"completed": True})
        print(f"Update Task Completion: {response.status_code}")

        return task['id']
    return None

def main():
    """Run all API tests."""
    print("Starting API Tests...")
    print("Make sure Django server is running on port 8000!")
    print("-" * 50)

    try:
        # Test projects
        project_id = test_projects()

        # Test sections
        section_id = test_sections(project_id)

        # Test tasks
        task_id = test_tasks(project_id, section_id)

        print("\n" + "=" * 50)
        print("API Tests Completed Successfully!")
        print(f"Created:")
        print(f"  - Project ID: {project_id}")
        print(f"  - Section ID: {section_id}")
        print(f"  - Task ID: {task_id}")

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Django server.")
        print("Please start the server with: python manage.py runserver 8000")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()