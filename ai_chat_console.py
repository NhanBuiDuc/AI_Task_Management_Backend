#!/usr/bin/env python
"""
Interactive AI Chat Console
Test the intent-based AI system with real-time JSON output
"""

import requests
import json
import sys
import os

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')
import django
django.setup()

from tasks_api.models import Account

BASE_URL = "http://localhost:8000"

# Colors
class C:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    R = '\033[0m'  # Reset


def get_account():
    """Get or create test account"""
    account, _ = Account.objects.get_or_create(
        username='console_test_user',
        defaults={'email': 'console@test.com', 'is_active': True}
    )
    return str(account.id)


def print_json(data, indent=2):
    """Pretty print JSON with colors"""
    def colorize(obj, depth=0):
        if isinstance(obj, dict):
            if not obj:
                return "{}"
            items = []
            for k, v in obj.items():
                key_str = f'{C.CYAN}"{k}"{C.R}'
                val_str = colorize(v, depth + 1)
                items.append(f'{"  " * (depth + 1)}{key_str}: {val_str}')
            return "{\n" + ",\n".join(items) + f'\n{"  " * depth}}}'
        elif isinstance(obj, list):
            if not obj:
                return "[]"
            items = [f'{"  " * (depth + 1)}{colorize(v, depth + 1)}' for v in obj]
            return "[\n" + ",\n".join(items) + f'\n{"  " * depth}]'
        elif isinstance(obj, str):
            return f'{C.GREEN}"{obj}"{C.R}'
        elif isinstance(obj, bool):
            return f'{C.MAGENTA}{str(obj).lower()}{C.R}'
        elif obj is None:
            return f'{C.DIM}null{C.R}'
        else:
            return f'{C.YELLOW}{obj}{C.R}'

    print(colorize(data))


def chat(message, headers, session_id=None):
    """Send chat message and return response"""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    try:
        response = requests.post(
            f"{BASE_URL}/ai/intent/",
            json=payload,
            headers=headers,
            timeout=60
        )
        return response.json(), response.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to server. Is Django running?"}, 0
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}, 0
    except Exception as e:
        return {"error": str(e)}, 0


def execute_intent(intent_id, params, headers):
    """Execute a specific intent"""
    payload = {"intent_id": intent_id, "params": params}

    try:
        response = requests.post(
            f"{BASE_URL}/ai/intent/execute/",
            json=payload,
            headers=headers,
            timeout=30
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 0


def list_intents(headers, category=None):
    """List available intents"""
    url = f"{BASE_URL}/ai/intent/list/"
    if category:
        url += f"?category={category}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 0


def print_help():
    """Print help message"""
    print(f"""
{C.BOLD}Available Commands:{C.R}
  {C.CYAN}/help{C.R}              - Show this help
  {C.CYAN}/intents{C.R}           - List all available intents
  {C.CYAN}/intents <cat>{C.R}     - List intents by category (query, create, modify, complete, delete, analytics)
  {C.CYAN}/exec <id> <json>{C.R}  - Execute intent directly (e.g., /exec task-create-simple {{"title":"test"}})
  {C.CYAN}/clear{C.R}             - Clear session
  {C.CYAN}/quit{C.R}              - Exit

{C.BOLD}Example Messages (Multi-Task Extraction):{C.R}
  {C.DIM}I want to learn coding, go to gym, and call mom{C.R}
  {C.DIM}remind me to buy groceries and pick up laundry tomorrow{C.R}
  {C.DIM}add task finish report by friday and review docs{C.R}

{C.BOLD}Single Task Examples:{C.R}
  {C.DIM}What tasks do I have today?{C.R}
  {C.DIM}Add a task to buy groceries tomorrow{C.R}
  {C.DIM}Mark grocery shopping as done{C.R}
  {C.DIM}Show my stats{C.R}
""")


def main():
    print(f"""
{C.BOLD}{C.BLUE}╔══════════════════════════════════════════════════════════╗
║           AI Intent Chat Console                         ║
║     Test the intent-based task management system         ║
╚══════════════════════════════════════════════════════════╝{C.R}
""")

    # Setup account
    try:
        account_id = get_account()
        headers = {
            'X-Account-ID': account_id,
            'Content-Type': 'application/json'
        }
        print(f"{C.GREEN}[OK]{C.R} Account ready: {account_id[:8]}...")
    except Exception as e:
        print(f"{C.RED}[ERROR]{C.R} Failed to setup account: {e}")
        return 1

    # Check server
    try:
        r = requests.get(f"{BASE_URL}/ai/intent/list/", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"{C.GREEN}[OK]{C.R} Server connected - {data.get('total', 0)} intents available")
        else:
            print(f"{C.YELLOW}[WARN]{C.R} Server returned {r.status_code}")
    except:
        print(f"{C.YELLOW}[WARN]{C.R} Server not reachable at {BASE_URL}")
        print(f"{C.DIM}       Start with: python manage.py runserver 0.0.0.0:8000{C.R}")

    print(f"\nType {C.CYAN}/help{C.R} for commands or just type a message.\n")

    session_id = None

    while True:
        try:
            user_input = input(f"{C.BOLD}{C.BLUE}You>{C.R} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{C.DIM}Goodbye!{C.R}")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith('/'):
            parts = user_input.split(maxsplit=2)
            cmd = parts[0].lower()

            if cmd in ['/quit', '/exit', '/q']:
                print(f"{C.DIM}Goodbye!{C.R}")
                break

            elif cmd == '/help':
                print_help()

            elif cmd == '/clear':
                session_id = None
                print(f"{C.GREEN}Session cleared{C.R}")

            elif cmd == '/intents':
                category = parts[1] if len(parts) > 1 else None
                print(f"\n{C.DIM}Fetching intents...{C.R}")
                data, status = list_intents(headers, category)

                if status == 200:
                    print(f"\n{C.BOLD}Available Intents ({data.get('total', 0)} total):{C.R}\n")
                    for cat, intents in data.get('grouped', {}).items():
                        print(f"  {C.CYAN}[{cat}]{C.R}")
                        for intent in intents:
                            params = f" {C.DIM}({', '.join(intent.get('requires_params', []))}){C.R}" if intent.get('requires_params') else ""
                            print(f"    {C.YELLOW}{intent['id']}{C.R}: {intent['description']}{params}")
                        print()
                else:
                    print(f"\n{C.RED}Error:{C.R}")
                    print_json(data)

            elif cmd == '/exec':
                if len(parts) < 3:
                    print(f"{C.RED}Usage: /exec <intent_id> <params_json>{C.R}")
                    print(f'{C.DIM}Example: /exec task-create-simple {{"title":"My task"}}{C.R}')
                    continue

                intent_id = parts[1]
                try:
                    params = json.loads(parts[2])
                except json.JSONDecodeError as e:
                    print(f"{C.RED}Invalid JSON:{C.R} {e}")
                    continue

                print(f"\n{C.DIM}Executing {intent_id}...{C.R}")
                data, status = execute_intent(intent_id, params, headers)
                print(f"\n{C.BOLD}Response (HTTP {status}):{C.R}\n")
                print_json(data)
                print()

            else:
                print(f"{C.RED}Unknown command:{C.R} {cmd}")
                print(f"Type {C.CYAN}/help{C.R} for available commands")

        else:
            # Regular chat message
            print(f"\n{C.DIM}Processing...{C.R}")
            data, status = chat(user_input, headers, session_id)

            # Update session
            if data.get('session_id'):
                session_id = data['session_id']

            # Print response
            print(f"\n{C.BOLD}Response (HTTP {status}):{C.R}\n")
            print_json(data)

            # Print summary
            if status == 200:
                print(f"\n{C.BOLD}Summary:{C.R}")
                print(f"  Intent: {C.CYAN}{data.get('intent', data.get('intent_id', 'N/A'))}{C.R}")
                print(f"  Message: {C.GREEN}{data.get('message', 'N/A')}{C.R}")

                # Print extracted tasks (new format)
                if data.get('tasks'):
                    print(f"\n{C.BOLD}Extracted Tasks ({len(data['tasks'])}):{C.R}")
                    for i, task in enumerate(data['tasks'], 1):
                        title = task.get('title', 'Untitled')
                        due = task.get('due_date', '')
                        time = task.get('due_time', '')
                        priority = task.get('priority', 'medium')

                        due_str = f" {C.YELLOW}@{due}{C.R}" if due else ""
                        time_str = f" {C.YELLOW}{time}{C.R}" if time else ""
                        prio_str = f" [{priority}]" if priority != 'medium' else ""

                        print(f"  {C.CYAN}{i}.{C.R} {title}{due_str}{time_str}{prio_str}")

                # Legacy params (fallback)
                elif data.get('extracted_params') and data['extracted_params'].get('title'):
                    print(f"  Params: {C.YELLOW}{data.get('extracted_params')}{C.R}")

                # Print execution result
                if data.get('execution'):
                    exec_data = data['execution']
                    status_icon = f"{C.GREEN}OK{C.R}" if exec_data.get('success') else f"{C.RED}FAIL{C.R}"
                    print(f"\n{C.BOLD}Execution:{C.R} [{status_icon}] {exec_data.get('action_type', 'N/A')}")

                    # Show created tasks
                    if exec_data.get('created_tasks'):
                        print(f"  {C.GREEN}Created {len(exec_data['created_tasks'])} task(s):{C.R}")
                        for t in exec_data['created_tasks']:
                            due_str = f" (due: {t.get('due_date')})" if t.get('due_date') else ""
                            print(f"    - {t.get('task_name')}{due_str}")

                    # Show query data
                    elif exec_data.get('data'):
                        if exec_data['data'].get('tasks'):
                            print(f"  Found {len(exec_data['data']['tasks'])} task(s)")
                            for t in exec_data['data']['tasks'][:5]:
                                print(f"    - {t.get('name', 'Untitled')}")
                        elif exec_data['data'].get('count') is not None:
                            print(f"  Count: {exec_data['data']['count']}")

                    # Show errors
                    if exec_data.get('errors'):
                        print(f"  {C.RED}Errors: {exec_data['errors']}{C.R}")

                # Print token report
                if data.get('token_report'):
                    tr = data['token_report']
                    print(f"\n{C.BOLD}Token Report:{C.R}")
                    print(f"  {C.MAGENTA}Prompt:{C.R}     {tr.get('prompt_tokens', 0):,} tokens")
                    print(f"  {C.MAGENTA}Completion:{C.R} {tr.get('completion_tokens', 0):,} tokens")
                    print(f"  {C.MAGENTA}Total:{C.R}      {tr.get('total_tokens', 0):,} tokens")
                    print(f"  {C.MAGENTA}Latency:{C.R}    {tr.get('latency_ms', 0):,.0f} ms")
                    print(f"  {C.MAGENTA}Model:{C.R}      {tr.get('model', 'N/A')}")

            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
