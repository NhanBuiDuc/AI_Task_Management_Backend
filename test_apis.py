#!/usr/bin/env python3
"""
JARVIS API Testing Script
Tests all API endpoints by creating sample data and verifying responses
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class APITester:
    def __init__(self):
        self.project_ids = []
        self.section_ids = []
        self.task_ids = []
        self.test_results = []
        
    def print_header(self, text: str):
        print(f"\n{BLUE}{'=' * 60}{NC}")
        print(f"{BLUE}{text}{NC}")
        print(f"{BLUE}{'=' * 60}{NC}\n")
    
    def print_success(self, text: str):
        print(f"{GREEN}✓ {text}{NC}")
    
    def print_warning(self, text: str):
        print(f"{YELLOW}⚠ {text}{NC}")
    
    def print_error(self, text: str):
        print(f"{RED}✗ {text}{NC}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> tuple:
        """Make HTTP request and return response"""
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=HEADERS)
            elif method == "POST":
                response = requests.post(url, headers=HEADERS, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=HEADERS, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=HEADERS)
            else:
                return None, f"Invalid method: {method}"
            
            return response, None
        except Exception as e:
            return None, str(e)
    
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Dict = None, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        print(f"\nTesting: {name}")
        print(f"  Method: {method} {endpoint}")
        if data:
            print(f"  Data: {json.dumps(data, indent=2)}")
        
        response, error = self.make_request(method, endpoint, data)
        
        if error:
            self.print_error(f"Request failed: {error}")
            self.test_results.append((name, False, error))
            return False
        
        if response.status_code != expected_status:
            self.print_error(
                f"Expected status {expected_status}, got {response.status_code}"
            )
            self.print_error(f"Response: {response.text}")
            self.test_results.append(
                (name, False, f"Status {response.status_code}")
            )
            return False
        
        try:
            response_data = response.json()
            print(f"  Response: {json.dumps(response_data, indent=2)[:200]}...")
            self.print_success(f"Test passed!")
            self.test_results.append((name, True, "Success"))
            return response_data
        except:
            self.print_success(f"Test passed! (No JSON response)")
            self.test_results.append((name, True, "Success"))
            return True
    
    # ==================================================================
    # PROJECT API TESTS
    # ==================================================================
    
    def test_projects(self):
        self.print_header("TESTING PROJECT APIs")
        
        # 1. Create parent project
        project1_data = {
            "name": "Personal Life",
            "parent_id": None,
            "icon": "🏠",
            "color": "#FF6B6B"
        }
        result = self.test_endpoint(
            "Create Parent Project",
            "POST",
            "/projects/",
            project1_data,
            201
        )
        if result:
            self.project_ids.append(result['id'])
        
        # 2. Create child project
        project2_data = {
            "name": "Health & Fitness",
            "parent_id": self.project_ids[0] if self.project_ids else None,
            "icon": "💪",
            "color": "#4ECDC4"
        }
        result = self.test_endpoint(
            "Create Child Project",
            "POST",
            "/projects/",
            project2_data,
            201
        )
        if result:
            self.project_ids.append(result['id'])
        
        # 3. Create another parent project
        project3_data = {
            "name": "Work Projects",
            "parent_id": None,
            "icon": "💼",
            "color": "#95E1D3"
        }
        result = self.test_endpoint(
            "Create Another Parent Project",
            "POST",
            "/projects/",
            project3_data,
            201
        )
        if result:
            self.project_ids.append(result['id'])
        
        # 4. List all projects
        self.test_endpoint("List All Projects", "GET", "/projects/")
        
        # 5. Get single project
        if self.project_ids:
            self.test_endpoint(
                "Get Single Project",
                "GET",
                f"/projects/{self.project_ids[0]}/"
            )
        
        # 6. Check project name
        self.test_endpoint(
            "Check Project Name (exists)",
            "GET",
            f"/projects/check_name/?name=Personal%20Life"
        )
        
        # 7. Get project task count
        if self.project_ids:
            self.test_endpoint(
                "Get Project Task Count",
                "GET",
                f"/projects/{self.project_ids[0]}/task_count/"
            )
        
        # 8. Check if project is independent
        if self.project_ids:
            self.test_endpoint(
                "Check If Project Is Independent",
                "GET",
                f"/projects/{self.project_ids[0]}/independent/"
            )
        
        # 9. Get project children
        if self.project_ids:
            self.test_endpoint(
                "Get Project Children",
                "GET",
                f"/projects/{self.project_ids[0]}/children/"
            )
        
        # 10. Update project
        if self.project_ids:
            update_data = {
                "name": "Personal Life (Updated)",
                "color": "#FF8787"
            }
            self.test_endpoint(
                "Update Project",
                "PATCH",
                f"/projects/{self.project_ids[0]}/",
                update_data
            )
    
    # ==================================================================
    # SECTION API TESTS
    # ==================================================================
    
    def test_sections(self):
        self.print_header("TESTING SECTION APIs")
        
        if not self.project_ids:
            self.print_warning("Skipping section tests - no projects created")
            return
        
        # 1. Create section in first project
        section1_data = {
            "name": "To Do",
            "project_id": self.project_ids[0]
        }
        result = self.test_endpoint(
            "Create Section",
            "POST",
            "/sections/",
            section1_data,
            201
        )
        if result:
            self.section_ids.append(result['id'])
        
        # 2. Create another section
        section2_data = {
            "name": "In Progress",
            "project_id": self.project_ids[0]
        }
        result = self.test_endpoint(
            "Create Another Section",
            "POST",
            "/sections/",
            section2_data,
            201
        )
        if result:
            self.section_ids.append(result['id'])
        
        # 3. Create Inbox section (no project)
        section3_data = {
            "name": "Quick Tasks",
            "project_id": None
        }
        result = self.test_endpoint(
            "Create Inbox Section",
            "POST",
            "/sections/",
            section3_data,
            201
        )
        if result:
            self.section_ids.append(result['id'])
        
        # 4. List all sections
        self.test_endpoint("List All Sections", "GET", "/sections/")
        
        # 5. List sections for specific project
        self.test_endpoint(
            "List Project Sections",
            "GET",
            f"/sections/?project_id={self.project_ids[0]}"
        )
        
        # 6. Get single section
        if self.section_ids:
            self.test_endpoint(
                "Get Single Section",
                "GET",
                f"/sections/{self.section_ids[0]}/"
            )
        
        # 7. Check section name
        self.test_endpoint(
            "Check Section Name (exists)",
            "GET",
            f"/sections/check_name/?project_id={self.project_ids[0]}&name=To%20Do"
        )
        
        # 8. Get or create completed section
        self.test_endpoint(
            "Get Or Create Completed Section",
            "POST",
            "/sections/get_or_create_completed/",
            {"project_id": self.project_ids[0]}
        )
        
        # 9. Update section
        if self.section_ids:
            update_data = {"name": "To Do (Updated)"}
            self.test_endpoint(
                "Update Section",
                "PATCH",
                f"/sections/{self.section_ids[0]}/",
                update_data
            )
    
    # ==================================================================
    # TASK API TESTS
    # ==================================================================
    
    def test_tasks(self):
        self.print_header("TESTING TASK APIs")
        
        # Calculate dates
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        last_week = today - timedelta(days=7)
        
        # 1. Create task due today (inbox)
        task1_data = {
            "name": "Review email",
            "description": "Check and respond to important emails",
            "project_id": None,
            "section_id": None,
            "due_date": today.isoformat(),
            "piority": "high",
            "duration_in_minutes": 30
        }
        result = self.test_endpoint(
            "Create Task (Today - Inbox)",
            "POST",
            "/tasks/",
            task1_data,
            201
        )
        if result:
            self.task_ids.append(result['id'])
        
        # 2. Create task in project (upcoming)
        if self.project_ids:
            task2_data = {
                "name": "Gym workout",
                "description": "Upper body strength training",
                "project_id": self.project_ids[0],
                "section_id": self.section_ids[0] if self.section_ids else None,
                "due_date": next_week.isoformat(),
                "piority": "medium",
                "duration_in_minutes": 60,
                "repeat": "every week"
            }
            result = self.test_endpoint(
                "Create Task (Upcoming - Project)",
                "POST",
                "/tasks/",
                task2_data,
                201
            )
            if result:
                self.task_ids.append(result['id'])
        
        # 3. Create overdue task
        task3_data = {
            "name": "Finish report",
            "description": "Complete quarterly report",
            "project_id": self.project_ids[1] if len(self.project_ids) > 1 else None,
            "section_id": None,
            "due_date": last_week.isoformat(),
            "piority": "urgent",
            "duration_in_minutes": 120
        }
        result = self.test_endpoint(
            "Create Task (Overdue)",
            "POST",
            "/tasks/",
            task3_data,
            201
        )
        if result:
            self.task_ids.append(result['id'])
        
        # 4. List all tasks
        self.test_endpoint("List All Tasks", "GET", "/tasks/")
        
        # 5. List tasks by project
        if self.project_ids:
            self.test_endpoint(
                "List Tasks By Project",
                "GET",
                f"/tasks/?project_id={self.project_ids[0]}"
            )
        
        # 6. Get single task
        if self.task_ids:
            self.test_endpoint(
                "Get Single Task",
                "GET",
                f"/tasks/{self.task_ids[0]}/"
            )
        
        # 7. Update task
        if self.task_ids:
            update_data = {
                "name": "Review email (Updated)",
                "piority": "medium"
            }
            self.test_endpoint(
                "Update Task",
                "PATCH",
                f"/tasks/{self.task_ids[0]}/",
                update_data
            )
        
        # 8. Mark task as completed
        if self.task_ids:
            self.test_endpoint(
                "Mark Task As Completed",
                "PATCH",
                f"/tasks/{self.task_ids[0]}/completion/",
                {"completed": True}
            )
        
        # 9. Move task to different project (before totally completing it)
        if len(self.task_ids) > 2 and len(self.project_ids) > 1:
            self.test_endpoint(
                "Move Task To Different Project",
                "PATCH",
                f"/tasks/{self.task_ids[2]}/move_to_project/",
                {"project_id": self.project_ids[1]}
            )

        # 10. Mark task as totally completed
        if len(self.task_ids) > 1:
            self.test_endpoint(
                "Mark Task As Totally Completed",
                "PATCH",
                f"/tasks/{self.task_ids[1]}/total_completion/",
                {"totally_completed": True}
            )
        
        # 11. Move task to section
        if self.task_ids and self.section_ids:
            self.test_endpoint(
                "Move Task To Section",
                "PATCH",
                f"/tasks/{self.task_ids[0]}/move_to_section/",
                {"section_id": self.section_ids[0]}
            )
        
        # 12. Make task unsectioned
        if self.task_ids:
            self.test_endpoint(
                "Make Task Unsectioned",
                "PATCH",
                f"/tasks/{self.task_ids[0]}/make_unsectioned/"
            )
    
    # ==================================================================
    # VIEW FILTER TESTS
    # ==================================================================

    def test_views(self):
        self.print_header("TESTING VIEW FILTERS")

        # Today's date
        today = datetime.now().date()
        next_week = today + timedelta(days=7)

        # 1. Get today's tasks
        self.test_endpoint(
            "Get Today's Tasks",
            "GET",
            f"/tasks/by_due_date/?due_date={today.isoformat()}"
        )

        # 2. Get inbox tasks
        self.test_endpoint("Get Inbox Tasks", "GET", "/tasks/by_view/?view=inbox")

        # 3. Get upcoming tasks
        self.test_endpoint(
            "Get Upcoming Tasks",
            "GET",
            f"/tasks/by_date_range/?start_date={today.isoformat()}&end_date={next_week.isoformat()}"
        )

        # 4. Get overdue tasks
        self.test_endpoint("Get Overdue Tasks", "GET", "/tasks/overdue/")

        # 5. Get completed tasks
        self.test_endpoint("Get Completed Tasks", "GET", "/tasks/completed/")

        # 6. Get task counts
        self.test_endpoint(
            "Get Task Counts",
            "GET",
            f"/tasks/counts/?today_date={today.isoformat()}"
        )
    
    # ==================================================================
    # SUMMARY
    # ==================================================================
    
    def print_summary(self):
        self.print_header("TEST SUMMARY")
        
        total = len(self.test_results)
        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {passed}{NC}")
        print(f"{RED}Failed: {failed}{NC}")
        print(f"\nSuccess Rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0:
            self.print_error("\nFailed Tests:")
            for name, success, message in self.test_results:
                if not success:
                    print(f"  • {name}: {message}")
        
        print(f"\n{BLUE}{'=' * 60}{NC}")
        print(f"{BLUE}Created Resources:{NC}")
        print(f"  Projects: {len(self.project_ids)}")
        print(f"  Sections: {len(self.section_ids)}")
        print(f"  Tasks: {len(self.task_ids)}")
        print(f"{BLUE}{'=' * 60}{NC}\n")
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"{GREEN}{'=' * 60}{NC}")
        print(f"{GREEN}JARVIS API Testing Suite{NC}")
        print(f"{GREEN}{'=' * 60}{NC}")
        print(f"\nBase URL: {BASE_URL}")
        print(f"Testing started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        try:
            # Check if server is running
            response, error = self.make_request("GET", "/projects/")
            if error:
                self.print_error(
                    f"Cannot connect to server at {BASE_URL}. "
                    "Please make sure the Django server is running."
                )
                sys.exit(1)
            
            # Run test suites
            self.test_projects()
            self.test_sections()
            self.test_tasks()
            self.test_views()
            
            # Print summary
            self.print_summary()
            
        except KeyboardInterrupt:
            self.print_warning("\n\nTests interrupted by user")
            self.print_summary()
            sys.exit(1)
        except Exception as e:
            self.print_error(f"\n\nUnexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()