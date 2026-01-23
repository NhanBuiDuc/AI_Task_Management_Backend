#!/usr/bin/env python
"""
Test Cases for Intent-Action System
Tests natural language prompts against expected intents and parameters
"""

import requests
import json
import sys
import os

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')
import django
django.setup()

from tasks_api.models import Account, Task
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# Colors
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    R = '\033[0m'

# =============================================================================
# TEST CASES DEFINITION
# =============================================================================

TODAY = datetime.now().strftime('%Y-%m-%d')
TOMORROW = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

TEST_CASES = [
    # =========================================================================
    # QUERY INTENTS - Reading/listing tasks
    # =========================================================================
    {
        "category": "QUERY - Today's Tasks",
        "tests": [
            {
                "input": "What tasks do I have today?",
                "expected_intent": "tasks-today-list",
                "expected_params": {}
            },
            {
                "input": "Show me today's tasks",
                "expected_intent": "tasks-today-list",
                "expected_params": {}
            },
            {
                "input": "what's on my plate today",
                "expected_intent": "tasks-today-list",
                "expected_params": {}
            },
            {
                "input": "today tasks",
                "expected_intent": "tasks-today-list",
                "expected_params": {}
            },
            {
                "input": "How many tasks do I have today?",
                "expected_intent": "tasks-today-count",
                "expected_params": {}
            },
            {
                "input": "count today's tasks",
                "expected_intent": "tasks-today-count",
                "expected_params": {}
            },
        ]
    },
    {
        "category": "QUERY - All/Overdue/Upcoming",
        "tests": [
            {
                "input": "Show all my tasks",
                "expected_intent": "tasks-all-list",
                "expected_params": {}
            },
            {
                "input": "list all tasks",
                "expected_intent": "tasks-all-list",
                "expected_params": {}
            },
            {
                "input": "What are my overdue tasks?",
                "expected_intent": "tasks-overdue-list",
                "expected_params": {}
            },
            {
                "input": "show overdue",
                "expected_intent": "tasks-overdue-list",
                "expected_params": {}
            },
            {
                "input": "what tasks are late",
                "expected_intent": "tasks-overdue-list",
                "expected_params": {}
            },
            {
                "input": "Show upcoming tasks",
                "expected_intent": "tasks-upcoming-list",
                "expected_params": {}
            },
            {
                "input": "what's coming up this week",
                "expected_intent": "tasks-upcoming-list",
                "expected_params": {}
            },
            {
                "input": "tasks for next week",
                "expected_intent": "tasks-upcoming-list",
                "expected_params": {}
            },
        ]
    },
    {
        "category": "QUERY - Inbox/Projects",
        "tests": [
            {
                "input": "Show my inbox",
                "expected_intent": "tasks-inbox-list",
                "expected_params": {}
            },
            {
                "input": "inbox tasks",
                "expected_intent": "tasks-inbox-list",
                "expected_params": {}
            },
            {
                "input": "List my projects",
                "expected_intent": "projects-list",
                "expected_params": {}
            },
            {
                "input": "show all projects",
                "expected_intent": "projects-list",
                "expected_params": {}
            },
            {
                "input": "tasks in project Work",
                "expected_intent": "tasks-by-project",
                "expected_params": {"project_name": "Work"}
            },
        ]
    },
    {
        "category": "QUERY - Search/Specific",
        "tests": [
            {
                "input": "Find task about groceries",
                "expected_intent": "task-search",
                "expected_params": {"search_term": "groceries"}
            },
            {
                "input": "search for meeting tasks",
                "expected_intent": "task-search",
                "expected_params": {"search_term": "meeting"}
            },
            {
                "input": "When is my homework due?",
                "expected_intent": "task-due-date-query",
                "expected_params": {"task_name": "homework"}
            },
            {
                "input": "when is the report due",
                "expected_intent": "task-due-date-query",
                "expected_params": {"task_name": "report"}
            },
            {
                "input": "show high priority tasks",
                "expected_intent": "tasks-by-priority",
                "expected_params": {"priority": "high"}
            },
            {
                "input": "urgent tasks",
                "expected_intent": "tasks-by-priority",
                "expected_params": {"priority": "urgent"}
            },
        ]
    },

    # =========================================================================
    # CREATE INTENTS - Adding new tasks
    # =========================================================================
    {
        "category": "CREATE - Simple Tasks",
        "tests": [
            {
                "input": "Add task buy groceries",
                "expected_intent": "task-create-simple",
                "expected_params": {"title": "buy groceries"}
            },
            {
                "input": "Create task to call mom",
                "expected_intent": "task-create-simple",
                "expected_params": {"title": "call mom"}
            },
            {
                "input": "new task: finish report",
                "expected_intent": "task-create-simple",
                "expected_params": {"title": "finish report"}
            },
            {
                "input": "remind me to take medicine",
                "expected_intent": "task-create-simple",
                "expected_params": {"title": "take medicine"}
            },
            {
                "input": "insert task clean the house",
                "expected_intent": "task-create-simple",
                "expected_params": {"title": "clean the house"}
            },
            {
                "input": "make a task to review documents",
                "expected_intent": "task-create-simple",
                "expected_params": {"title": "review documents"}
            },
        ]
    },
    {
        "category": "CREATE - Tasks with Date",
        "tests": [
            {
                "input": "Add task buy groceries tomorrow",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "buy groceries", "due_date": TOMORROW}
            },
            {
                "input": "Create task to call mom on Monday",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "call mom"}  # due_date should be next Monday
            },
            {
                "input": "schedule meeting for next week",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "meeting"}
            },
            {
                "input": "add task submit report by Friday",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "submit report"}
            },
            {
                "input": "insert a task for today to take out the trash",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "take out the trash", "due_date": TODAY}
            },
        ]
    },
    {
        "category": "CREATE - Tasks with Time",
        "tests": [
            {
                "input": "Add task meeting at 3pm",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "meeting", "due_time": "3pm"}
            },
            {
                "input": "insert a task for me at 10pm today to take out the trash",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "take out the trash", "due_date": TODAY, "due_time": "10pm"}
            },
            {
                "input": "remind me at 9am to call the doctor",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "call the doctor", "due_time": "9am"}
            },
            {
                "input": "schedule standup at 10:00 tomorrow",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "standup", "due_date": TOMORROW, "due_time": "10:00"}
            },
            {
                "input": "add task lunch with John at 12pm on Friday",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "lunch with John", "due_time": "12pm"}
            },
        ]
    },
    {
        "category": "CREATE - Multiple Tasks",
        "tests": [
            {
                "input": "Add tasks: buy milk, clean room, do laundry",
                "expected_intent": "tasks-create-multiple",
                "expected_params": {"tasks": ["buy milk", "clean room", "do laundry"]}
            },
            {
                "input": "create tasks go to gym and buy groceries and call mom",
                "expected_intent": "tasks-create-multiple",
                "expected_params": {"tasks": ["go to gym", "buy groceries", "call mom"]}
            },
            {
                "input": "add buy eggs, bread, and cheese",
                "expected_intent": "tasks-create-multiple",
                "expected_params": {}  # should extract tasks from list
            },
        ]
    },
    {
        "category": "CREATE - With Priority",
        "tests": [
            {
                "input": "Add urgent task: fix production bug",
                "expected_intent": "task-create-with-priority",
                "expected_params": {"title": "fix production bug", "priority": "urgent"}
            },
            {
                "input": "create high priority task to review PR",
                "expected_intent": "task-create-with-priority",
                "expected_params": {"title": "review PR", "priority": "high"}
            },
            {
                "input": "add important task prepare presentation",
                "expected_intent": "task-create-with-priority",
                "expected_params": {"title": "prepare presentation"}
            },
        ]
    },

    # =========================================================================
    # COMPLETE INTENTS - Marking tasks done
    # =========================================================================
    {
        "category": "COMPLETE - Single Task",
        "tests": [
            {
                "input": "Mark buy groceries as done",
                "expected_intent": "task-complete",
                "expected_params": {"task_name": "buy groceries"}
            },
            {
                "input": "Complete the homework task",
                "expected_intent": "task-complete",
                "expected_params": {"task_name": "homework"}
            },
            {
                "input": "I finished the report",
                "expected_intent": "task-complete",
                "expected_params": {"task_name": "report"}
            },
            {
                "input": "done with cleaning",
                "expected_intent": "task-complete",
                "expected_params": {"task_name": "cleaning"}
            },
            {
                "input": "check off buy milk",
                "expected_intent": "task-complete",
                "expected_params": {"task_name": "buy milk"}
            },
            {
                "input": "groceries is done",
                "expected_intent": "task-complete",
                "expected_params": {"task_name": "groceries"}
            },
        ]
    },
    {
        "category": "COMPLETE - Multiple Tasks",
        "tests": [
            {
                "input": "Mark buy milk and clean room as done",
                "expected_intent": "tasks-complete-multiple",
                "expected_params": {"task_names": ["buy milk", "clean room"]}
            },
            {
                "input": "Complete tasks: laundry, dishes, vacuuming",
                "expected_intent": "tasks-complete-multiple",
                "expected_params": {"task_names": ["laundry", "dishes", "vacuuming"]}
            },
        ]
    },

    # =========================================================================
    # UPDATE INTENTS - Modifying tasks
    # =========================================================================
    {
        "category": "UPDATE - Reschedule",
        "tests": [
            {
                "input": "Move groceries to tomorrow",
                "expected_intent": "task-update-due-date",
                "expected_params": {"task_name": "groceries", "new_due_date": TOMORROW}
            },
            {
                "input": "Reschedule meeting to Friday",
                "expected_intent": "task-update-due-date",
                "expected_params": {"task_name": "meeting"}
            },
            {
                "input": "Change due date of report to next week",
                "expected_intent": "task-update-due-date",
                "expected_params": {"task_name": "report"}
            },
        ]
    },
    {
        "category": "UPDATE - Postpone",
        "tests": [
            {
                "input": "Postpone groceries by 1 day",
                "expected_intent": "task-postpone",
                "expected_params": {"task_name": "groceries", "postpone_days": 1}
            },
            {
                "input": "Delay the meeting by 3 days",
                "expected_intent": "task-postpone",
                "expected_params": {"task_name": "meeting", "postpone_days": 3}
            },
            {
                "input": "Push back homework by a week",
                "expected_intent": "task-postpone",
                "expected_params": {"task_name": "homework", "postpone_days": 7}
            },
        ]
    },
    {
        "category": "UPDATE - Priority",
        "tests": [
            {
                "input": "Make report high priority",
                "expected_intent": "task-update-priority",
                "expected_params": {"task_name": "report", "new_priority": "high"}
            },
            {
                "input": "Set groceries to low priority",
                "expected_intent": "task-update-priority",
                "expected_params": {"task_name": "groceries", "new_priority": "low"}
            },
            {
                "input": "Change priority of bug fix to urgent",
                "expected_intent": "task-update-priority",
                "expected_params": {"task_name": "bug fix", "new_priority": "urgent"}
            },
        ]
    },

    # =========================================================================
    # DELETE INTENTS - Removing tasks
    # =========================================================================
    {
        "category": "DELETE - Single Task",
        "tests": [
            {
                "input": "Delete task buy groceries",
                "expected_intent": "task-delete",
                "expected_params": {"task_name": "buy groceries"}
            },
            {
                "input": "Remove the meeting task",
                "expected_intent": "task-delete",
                "expected_params": {"task_name": "meeting"}
            },
            {
                "input": "Cancel my dentist appointment",
                "expected_intent": "task-delete",
                "expected_params": {"task_name": "dentist appointment"}
            },
        ]
    },

    # =========================================================================
    # ANALYTICS INTENTS - Stats and insights
    # =========================================================================
    {
        "category": "ANALYTICS - Statistics",
        "tests": [
            {
                "input": "Show my task stats",
                "expected_intent": "stats-summary",
                "expected_params": {}
            },
            {
                "input": "How am I doing?",
                "expected_intent": "stats-summary",
                "expected_params": {}
            },
            {
                "input": "Give me a productivity summary",
                "expected_intent": "stats-summary",
                "expected_params": {}
            },
            {
                "input": "task statistics",
                "expected_intent": "stats-summary",
                "expected_params": {}
            },
        ]
    },

    # =========================================================================
    # EDGE CASES - Ambiguous/Complex inputs
    # =========================================================================
    {
        "category": "EDGE CASES - Ambiguous",
        "tests": [
            {
                "input": "I want to be more productive",
                "expected_intent": "clarify-ambiguous",
                "expected_params": {}
            },
            {
                "input": "Help me plan my week",
                "expected_intent": "clarify-ambiguous",
                "expected_params": {}
            },
            {
                "input": "I need to get healthier",
                "expected_intent": "clarify-ambiguous",
                "expected_params": {}
            },
        ]
    },
    {
        "category": "EDGE CASES - General Chat",
        "tests": [
            {
                "input": "Hello",
                "expected_intent": "chat-general",
                "expected_params": {}
            },
            {
                "input": "What can you do?",
                "expected_intent": "chat-general",
                "expected_params": {}
            },
            {
                "input": "Thanks for your help",
                "expected_intent": "chat-general",
                "expected_params": {}
            },
        ]
    },
    {
        "category": "EDGE CASES - Complex Sentences",
        "tests": [
            {
                "input": "I need to add a task to buy groceries and also show me what I have for tomorrow",
                "expected_intent": "task-create-simple",  # Should handle the primary intent
                "expected_params": {"title": "buy groceries"}
            },
            {
                "input": "Can you please add a reminder for me to call my mom tomorrow afternoon around 3pm?",
                "expected_intent": "task-create-with-date",
                "expected_params": {"title": "call my mom", "due_date": TOMORROW, "due_time": "3pm"}
            },
        ]
    },
]


# =============================================================================
# TEST RUNNER
# =============================================================================

def get_account():
    """Get or create test account"""
    account, _ = Account.objects.get_or_create(
        username='intent_test_user',
        defaults={'email': 'intent_test@test.com', 'is_active': True}
    )
    return str(account.id)


def run_test(test_input: str, headers: dict) -> dict:
    """Run a single test and return the response"""
    try:
        response = requests.post(
            f"{BASE_URL}/ai/intent/",
            json={"message": test_input},
            headers=headers,
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def check_intent_match(expected: str, actual: str) -> bool:
    """Check if intent matches (exact or acceptable alternative)"""
    if expected == actual:
        return True

    # Some acceptable alternatives
    alternatives = {
        "task-create-simple": ["task-create-with-date", "task-create-with-time"],
        "task-create-with-date": ["task-create-with-time", "task-create-simple"],
        "task-create-with-time": ["task-create-with-date"],
        "tasks-today-list": ["tasks-today-count"],
        "tasks-today-count": ["tasks-today-list"],
    }

    return actual in alternatives.get(expected, [])


def check_params_match(expected: dict, actual: dict) -> tuple:
    """Check if required params are present and return (match, details)"""
    if not expected:
        return True, "No params required"

    missing = []
    wrong = []

    for key, expected_val in expected.items():
        actual_val = actual.get(key)

        if actual_val is None or actual_val == "":
            missing.append(key)
        elif isinstance(expected_val, str):
            # Check if the expected value is contained in actual (fuzzy match)
            if expected_val.lower() not in str(actual_val).lower():
                wrong.append(f"{key}: expected '{expected_val}', got '{actual_val}'")
        elif isinstance(expected_val, list):
            # For lists, just check if it's a non-empty list
            if not isinstance(actual_val, list) or len(actual_val) == 0:
                wrong.append(f"{key}: expected list, got {actual_val}")

    if missing or wrong:
        details = []
        if missing:
            details.append(f"Missing: {missing}")
        if wrong:
            details.append(f"Wrong: {wrong}")
        return False, "; ".join(details)

    return True, "All params OK"


def run_all_tests(headers: dict, verbose: bool = True):
    """Run all test cases"""
    total = 0
    passed = 0
    failed_tests = []
    total_tokens = 0
    total_latency = 0

    for category_tests in TEST_CASES:
        category = category_tests["category"]
        tests = category_tests["tests"]

        print(f"\n{C.BOLD}{C.BLUE}{'='*60}{C.R}")
        print(f"{C.BOLD}{C.CYAN}{category}{C.R}")
        print(f"{C.BLUE}{'='*60}{C.R}")

        for test in tests:
            total += 1
            test_input = test["input"]
            expected_intent = test["expected_intent"]
            expected_params = test.get("expected_params", {})

            print(f"\n{C.DIM}Testing:{C.R} \"{test_input}\"")
            print(f"{C.DIM}Expected:{C.R} {expected_intent}")

            # Run the test
            result = run_test(test_input, headers)

            if "error" in result:
                print(f"{C.RED}[ERROR]{C.R} {result['error']}")
                failed_tests.append({
                    "input": test_input,
                    "expected": expected_intent,
                    "error": result['error']
                })
                continue

            actual_intent = result.get("intent_id", "unknown")
            actual_params = result.get("extracted_params", {})

            # Track token usage
            if result.get('token_report'):
                total_tokens += result['token_report'].get('total_tokens', 0)
                total_latency += result['token_report'].get('latency_ms', 0)

            # Check intent match
            intent_match = check_intent_match(expected_intent, actual_intent)
            params_match, params_details = check_params_match(expected_params, actual_params)

            if intent_match and params_match:
                passed += 1
                print(f"{C.GREEN}[PASS]{C.R} Intent: {actual_intent}")
                if verbose and actual_params:
                    print(f"       Params: {actual_params}")
                # Show token report if available
                if verbose and result.get('token_report'):
                    tr = result['token_report']
                    print(f"       {C.DIM}Tokens: {tr.get('total_tokens', 0)} ({tr.get('latency_ms', 0):.0f}ms){C.R}")
            elif intent_match and not params_match:
                print(f"{C.YELLOW}[PARTIAL]{C.R} Intent OK: {actual_intent}")
                print(f"          Params: {params_details}")
                print(f"          Got: {actual_params}")
                passed += 0.5  # Half credit
                failed_tests.append({
                    "input": test_input,
                    "expected_intent": expected_intent,
                    "actual_intent": actual_intent,
                    "params_issue": params_details
                })
            else:
                print(f"{C.RED}[FAIL]{C.R} Expected: {expected_intent}, Got: {actual_intent}")
                if verbose:
                    print(f"       Params: {actual_params}")
                    print(f"       Message: {result.get('message', 'N/A')}")
                failed_tests.append({
                    "input": test_input,
                    "expected": expected_intent,
                    "actual": actual_intent,
                    "params": actual_params
                })

    # Summary
    print(f"\n{C.BOLD}{'='*60}{C.R}")
    print(f"{C.BOLD}TEST SUMMARY{C.R}")
    print(f"{'='*60}")
    print(f"Total: {total}")
    print(f"Passed: {C.GREEN}{int(passed)}{C.R}")
    print(f"Failed: {C.RED}{total - int(passed)}{C.R}")
    print(f"Score: {C.BOLD}{passed/total*100:.1f}%{C.R}")

    # Token summary
    if total_tokens > 0:
        print(f"\n{C.BOLD}TOKEN USAGE{C.R}")
        print(f"{'='*60}")
        print(f"Total Tokens: {C.CYAN}{total_tokens:,}{C.R}")
        print(f"Total Latency: {C.CYAN}{total_latency/1000:.1f}s{C.R}")
        print(f"Avg Tokens/Request: {C.CYAN}{total_tokens/total:,.0f}{C.R}")
        print(f"Avg Latency/Request: {C.CYAN}{total_latency/total:,.0f}ms{C.R}")

    if failed_tests:
        print(f"\n{C.RED}Failed Tests:{C.R}")
        for ft in failed_tests[:10]:  # Show first 10
            print(f"  - \"{ft['input'][:50]}...\"")
            if 'error' in ft:
                print(f"    Error: {ft['error']}")
            else:
                print(f"    Expected: {ft.get('expected', ft.get('expected_intent'))}, Got: {ft.get('actual', ft.get('actual_intent'))}")

    return passed, total


def run_interactive(headers: dict):
    """Run tests interactively one by one"""
    print(f"\n{C.BOLD}Interactive Test Mode{C.R}")
    print("Press Enter to run next test, 'q' to quit, 's' to skip category\n")

    for category_tests in TEST_CASES:
        category = category_tests["category"]
        tests = category_tests["tests"]

        print(f"\n{C.BOLD}{C.CYAN}Category: {category}{C.R}")
        cmd = input("Press Enter to test this category (s=skip, q=quit): ").strip().lower()

        if cmd == 'q':
            break
        if cmd == 's':
            continue

        for test in tests:
            test_input = test["input"]
            expected_intent = test["expected_intent"]

            print(f"\n{C.DIM}Input:{C.R} \"{test_input}\"")
            print(f"{C.DIM}Expected:{C.R} {expected_intent}")

            cmd = input("Press Enter to run (s=skip, q=quit): ").strip().lower()
            if cmd == 'q':
                return
            if cmd == 's':
                continue

            result = run_test(test_input, headers)

            print(f"\n{C.BOLD}Result:{C.R}")
            print(json.dumps(result, indent=2))

            actual_intent = result.get("intent_id", "unknown")
            if actual_intent == expected_intent:
                print(f"\n{C.GREEN}[MATCH]{C.R}")
            else:
                print(f"\n{C.RED}[MISMATCH]{C.R} Expected: {expected_intent}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test Intent-Action System')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--category', '-c', type=str, help='Run only specific category')
    args = parser.parse_args()

    print(f"\n{C.BOLD}{C.BLUE}Intent-Action Test Suite{C.R}")
    print(f"Testing natural language -> intent mapping\n")

    # Setup
    try:
        account_id = get_account()
        headers = {
            'X-Account-ID': account_id,
            'Content-Type': 'application/json'
        }
        print(f"{C.GREEN}[OK]{C.R} Account ready: {account_id[:8]}...")
    except Exception as e:
        print(f"{C.RED}[ERROR]{C.R} Failed to setup: {e}")
        return 1

    # Check server
    try:
        r = requests.get(f"{BASE_URL}/ai/intent/list/", headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"{C.GREEN}[OK]{C.R} Server connected")
        else:
            print(f"{C.RED}[ERROR]{C.R} Server error: {r.status_code}")
            return 1
    except Exception as e:
        print(f"{C.RED}[ERROR]{C.R} Cannot connect to server: {e}")
        print(f"{C.DIM}Start server with: python manage.py runserver 0.0.0.0:8000{C.R}")
        return 1

    # Filter by category if specified
    if args.category:
        global TEST_CASES
        TEST_CASES = [tc for tc in TEST_CASES if args.category.lower() in tc["category"].lower()]
        if not TEST_CASES:
            print(f"{C.RED}No matching category found{C.R}")
            return 1

    # Run tests
    if args.interactive:
        run_interactive(headers)
    else:
        passed, total = run_all_tests(headers, verbose=args.verbose)
        return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
