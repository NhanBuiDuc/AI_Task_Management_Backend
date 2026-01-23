#!/usr/bin/env python
"""
Test script for AI Intent-based Chat endpoints
Tests the new intent-based task agent API
"""

import requests
import json
import sys
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')
django.setup()

from tasks_api.models import Account

BASE_URL = "http://localhost:8000"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def get_or_create_test_account():
    """Get or create a test account for API testing."""
    account, created = Account.objects.get_or_create(
        username='ai_chat_test_user',
        defaults={
            'email': 'ai_chat_test@example.com',
            'is_active': True
        }
    )
    if created:
        account.set_password('testpassword123')
        account.save()
    return str(account.id)

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}[FAIL] {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}[INFO] {text}{Colors.RESET}")

# =============================================================================
# Intent List Test
# =============================================================================

def test_intent_list(headers):
    """Test listing all available intents"""
    print_header("Test 1: List Available Intents")

    try:
        response = requests.get(f"{BASE_URL}/ai/intent/list/", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Intent list retrieved successfully")
            print(f"  Total intents: {data.get('total')}")
            print(f"  Categories: {data.get('categories')}")

            # Show sample intents
            for cat, intents in data.get('grouped', {}).items():
                print(f"  [{cat}]: {len(intents)} intents")
                for intent in intents[:2]:
                    print(f"    - {intent['id']}: {intent['description'][:40]}...")

            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server. Is Django running?")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

# =============================================================================
# Intent Chat Tests
# =============================================================================

def test_intent_query_today(headers):
    """Test querying today's tasks via intent"""
    print_header("Test 2: Query Today's Tasks (Intent)")

    payload = {
        "message": "What tasks do I have today?"
    }

    try:
        response = requests.post(f"{BASE_URL}/ai/intent/", json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Intent query processed")
            print(f"  Intent ID: {data.get('intent_id')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Success: {data.get('success')}")

            if data.get('execution'):
                exec_data = data['execution']
                print(f"  Execution: {exec_data.get('action_type')} - {exec_data.get('message')}")
                if exec_data.get('data', {}).get('count') is not None:
                    print(f"  Tasks count: {exec_data['data']['count']}")

            return data.get('session_id'), True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None, False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None, False

def test_intent_create_task(headers, session_id=None):
    """Test creating a task via intent"""
    print_header("Test 3: Create Task (Intent)")

    payload = {
        "message": "Add a task to buy groceries tomorrow",
        "session_id": session_id
    }

    try:
        response = requests.post(f"{BASE_URL}/ai/intent/", json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Task creation intent processed")
            print(f"  Intent ID: {data.get('intent_id')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Params: {data.get('extracted_params')}")

            if data.get('execution'):
                exec_data = data['execution']
                print(f"  Execution: {exec_data.get('success')} - {exec_data.get('message')}")
                if exec_data.get('data', {}).get('task_id'):
                    print(f"  Created task ID: {exec_data['data']['task_id']}")

            return data.get('session_id'), True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return session_id, False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return session_id, False

def test_intent_create_multiple(headers):
    """Test creating multiple tasks via intent"""
    print_header("Test 4: Create Multiple Tasks (Intent)")

    payload = {
        "message": "Add tasks: go to gym, call mom, finish report"
    }

    try:
        response = requests.post(f"{BASE_URL}/ai/intent/", json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Multiple tasks intent processed")
            print(f"  Intent ID: {data.get('intent_id')}")
            print(f"  Message: {data.get('message')}")

            if data.get('execution'):
                exec_data = data['execution']
                print(f"  Execution: {exec_data.get('success')}")
                if exec_data.get('data', {}).get('count'):
                    print(f"  Created: {exec_data['data']['count']} tasks")

            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_intent_complete_task(headers):
    """Test completing a task via intent"""
    print_header("Test 5: Complete Task (Intent)")

    payload = {
        "message": "Mark buy groceries as done"
    }

    try:
        response = requests.post(f"{BASE_URL}/ai/intent/", json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Complete task intent processed")
            print(f"  Intent ID: {data.get('intent_id')}")
            print(f"  Message: {data.get('message')}")

            if data.get('execution'):
                exec_data = data['execution']
                print(f"  Execution: {exec_data.get('success')} - {exec_data.get('message')}")

            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_intent_execute_direct(headers):
    """Test direct intent execution"""
    print_header("Test 6: Direct Intent Execution")

    payload = {
        "intent_id": "tasks-today-count",
        "params": {}
    }

    try:
        response = requests.post(f"{BASE_URL}/ai/intent/execute/", json=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Direct execution successful")
            print(f"  Intent ID: {data.get('intent_id')}")
            print(f"  Action: {data.get('action_type')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Data: {data.get('data')}")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_intent_stats(headers):
    """Test getting task statistics"""
    print_header("Test 7: Task Statistics (Intent)")

    payload = {
        "message": "Show me my task stats"
    }

    try:
        response = requests.post(f"{BASE_URL}/ai/intent/", json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Stats intent processed")
            print(f"  Intent ID: {data.get('intent_id')}")
            print(f"  Message: {data.get('message')}")

            if data.get('execution', {}).get('data'):
                stats = data['execution']['data']
                print(f"  Total active: {stats.get('total_active')}")
                print(f"  Today: {stats.get('today')}")
                print(f"  Overdue: {stats.get('overdue')}")
                print(f"  Completed: {stats.get('completed')}")

            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_ollama_connection():
    """Check if Ollama is running"""
    print_header("Checking Ollama Connection")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_success("Ollama is running")
            data = response.json()
            models = [m.get('name') for m in data.get('models', [])]
            print(f"  Available models: {', '.join(models) if models else 'None'}")
            return True
        else:
            print_error("Ollama returned unexpected status")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Ollama is not running at localhost:11434")
        print_info("Start Ollama with: ollama serve")
        return False
    except Exception as e:
        print_error(f"Error checking Ollama: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BOLD}AI Intent-Based Chat API Test Suite{Colors.RESET}")
    print("Testing the intent-based task agent endpoints\n")

    # Setup account and headers
    print_header("Setting Up Test Account")
    try:
        account_id = get_or_create_test_account()
        headers = {
            'X-Account-ID': account_id,
            'Content-Type': 'application/json'
        }
        print_success(f"Test account ready (ID: {account_id[:8]}...)")
    except Exception as e:
        print_error(f"Failed to setup test account: {e}")
        return 1

    # Check Ollama first
    ollama_ok = test_ollama_connection()

    if not ollama_ok:
        print_info("\nOllama is required for full AI functionality.")
        print_info("Tests will run using fallback processing.\n")

    # Run tests
    results = []

    # Test 1: List intents
    ok = test_intent_list(headers)
    results.append(("Intent List", ok))

    # Test 2: Query today
    session_id, ok = test_intent_query_today(headers)
    results.append(("Query Today", ok))

    # Test 3: Create task
    session_id, ok = test_intent_create_task(headers, session_id)
    results.append(("Create Task", ok))

    # Test 4: Create multiple
    ok = test_intent_create_multiple(headers)
    results.append(("Create Multiple", ok))

    # Test 5: Complete task
    ok = test_intent_complete_task(headers)
    results.append(("Complete Task", ok))

    # Test 6: Direct execute
    ok = test_intent_execute_direct(headers)
    results.append(("Direct Execute", ok))

    # Test 7: Stats
    ok = test_intent_stats(headers)
    results.append(("Task Stats", ok))

    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if ok else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {name}: {status}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")

    if passed == total:
        print_success("All tests passed!")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
