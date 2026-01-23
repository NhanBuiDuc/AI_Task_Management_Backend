#!/usr/bin/env python
"""
Schedule Visualizer
Displays tasks and their scheduled calendar in a split-view terminal interface.

Usage:
    python visualize_schedule.py [--days N] [--mock]
"""

import os
import sys
import argparse
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

# Add Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarvis_backend.settings')

import django
django.setup()

from tasks_api.agents.scheduler import TaskScheduler, generate_schedule_from_list


# =============================================================================
# TERMINAL COLORS (ANSI)
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_GRAY = '\033[100m'


PRIORITY_COLORS = {
    'emergency': Colors.RED + Colors.BOLD,
    'urgent': Colors.RED,
    'high': Colors.YELLOW,
    'medium': Colors.CYAN,
    'low': Colors.GRAY,
}

SLOT_COLORS = {
    'morning': Colors.YELLOW,
    'afternoon': Colors.CYAN,
    'evening': Colors.MAGENTA,
}


# =============================================================================
# MOCK DATA
# =============================================================================

def get_mock_tasks() -> List[Dict]:
    """Generate mock tasks for demonstration."""
    today = date.today()

    return [
        {
            'id': 'TSK-001',
            'name': 'Complete project proposal',
            'duration_in_minutes': 120,
            'priority': 'emergency',
            'due_date': today,
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-002',
            'name': 'Review pull requests',
            'duration_in_minutes': 60,
            'priority': 'high',
            'due_date': today,
            'energy_level': 'medium',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-003',
            'name': 'Team standup meeting',
            'duration_in_minutes': 15,
            'priority': 'medium',
            'due_date': today,
            'energy_level': 'low',
            'time_preference': 'morning',
            'repeat': 'every day',
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-004',
            'name': 'Write documentation',
            'duration_in_minutes': 90,
            'priority': 'medium',
            'due_date': today + timedelta(days=1),
            'energy_level': 'medium',
            'time_preference': 'afternoon',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-005',
            'name': 'Gym workout',
            'duration_in_minutes': 60,
            'priority': 'medium',
            'due_date': today + timedelta(days=1),
            'energy_level': 'high',
            'time_preference': 'evening',
            'repeat': 'every day',
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-006',
            'name': 'Read technical articles',
            'duration_in_minutes': 30,
            'priority': 'low',
            'due_date': today + timedelta(days=2),
            'energy_level': 'low',
            'time_preference': 'evening',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-007',
            'name': 'Client presentation prep',
            'duration_in_minutes': 120,
            'priority': 'urgent',
            'due_date': today + timedelta(days=2),
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-008',
            'name': 'Code review session',
            'duration_in_minutes': 45,
            'priority': 'high',
            'due_date': today + timedelta(days=3),
            'energy_level': 'medium',
            'time_preference': 'afternoon',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-009',
            'name': 'Weekly planning',
            'duration_in_minutes': 60,
            'priority': 'medium',
            'due_date': today + timedelta(days=4),
            'energy_level': 'medium',
            'time_preference': 'morning',
            'repeat': 'every week',
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-010',
            'name': 'Database optimization',
            'duration_in_minutes': 180,
            'priority': 'high',
            'due_date': today + timedelta(days=5),
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-011',
            'name': 'Respond to emails',
            'duration_in_minutes': 30,
            'priority': 'low',
            'due_date': today + timedelta(days=1),
            'energy_level': 'low',
            'time_preference': 'afternoon',
            'repeat': 'every day',
            'completed': False,
            'totally_completed': False,
        },
        {
            'id': 'TSK-012',
            'name': 'API integration testing',
            'duration_in_minutes': 90,
            'priority': 'high',
            'due_date': today + timedelta(days=3),
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
    ]


def get_tasks_from_db() -> List[Dict]:
    """Fetch tasks from the database."""
    from tasks_api.models import Task

    tasks = Task.objects.filter(
        completed=False,
        totally_completed=False
    ).order_by('due_date', '-priority')

    task_list = []
    for task in tasks:
        task_list.append({
            'id': str(task.id)[:8],
            'name': task.name,
            'duration_in_minutes': task.duration_in_minutes,
            'priority': task.priority,
            'due_date': task.due_date,
            'energy_level': getattr(task, 'energy_level', 'medium'),
            'time_preference': getattr(task, 'time_preference', 'anytime'),
            'repeat': task.repeat,
            'completed': task.completed,
            'totally_completed': task.totally_completed,
        })

    return task_list


# =============================================================================
# VISUALIZATION HELPERS
# =============================================================================

def get_terminal_size() -> tuple:
    """Get terminal width and height."""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 120, 40  # Default fallback


def truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + '...'


def pad_right(text: str, width: int) -> str:
    """Pad text to fixed width."""
    visible_len = len(text.replace(Colors.RESET, '').replace(Colors.BOLD, '')
                       .replace(Colors.DIM, '').replace(Colors.RED, '')
                       .replace(Colors.GREEN, '').replace(Colors.YELLOW, '')
                       .replace(Colors.BLUE, '').replace(Colors.CYAN, '')
                       .replace(Colors.MAGENTA, '').replace(Colors.GRAY, '')
                       .replace(Colors.WHITE, ''))
    padding = width - visible_len
    if padding > 0:
        return text + ' ' * padding
    return text


def format_duration(minutes: int) -> str:
    """Format duration in human readable format."""
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h{mins}m"


def format_date_short(d: date) -> str:
    """Format date as short string."""
    today = date.today()
    if d == today:
        return "Today"
    elif d == today + timedelta(days=1):
        return "Tomorrow"
    else:
        return d.strftime("%a %m/%d")


def get_priority_indicator(priority: str) -> str:
    """Get colored priority indicator."""
    indicators = {
        'emergency': Colors.RED + '●●●' + Colors.RESET,
        'urgent': Colors.RED + '●●○' + Colors.RESET,
        'high': Colors.YELLOW + '●○○' + Colors.RESET,
        'medium': Colors.CYAN + '○○○' + Colors.RESET,
        'low': Colors.GRAY + '···' + Colors.RESET,
    }
    return indicators.get(priority, '○○○')


# =============================================================================
# VISUALIZATION COMPONENTS
# =============================================================================

def render_header(width: int) -> List[str]:
    """Render the header section."""
    lines = []
    border = '═' * width

    lines.append(f"{Colors.CYAN}╔{border}╗{Colors.RESET}")

    title = "📅 TASK SCHEDULE VISUALIZER"
    title_padded = title.center(width)
    lines.append(f"{Colors.CYAN}║{Colors.BOLD}{Colors.WHITE}{title_padded}{Colors.RESET}{Colors.CYAN}║{Colors.RESET}")

    subtitle = f"Generated: {date.today().strftime('%A, %B %d, %Y')}"
    subtitle_padded = subtitle.center(width)
    lines.append(f"{Colors.CYAN}║{Colors.DIM}{subtitle_padded}{Colors.RESET}{Colors.CYAN}║{Colors.RESET}")

    lines.append(f"{Colors.CYAN}╠{border}╣{Colors.RESET}")

    return lines


def render_task_list(tasks: List[Dict], width: int, height: int) -> List[str]:
    """Render the task list panel."""
    lines = []

    # Header
    header = f"{Colors.BOLD} 📋 TASK LIST ({len(tasks)} tasks){Colors.RESET}"
    lines.append(pad_right(header, width))
    lines.append('─' * width)

    # Column headers
    col_header = f"{'Pri':4} {'Task Name':<25} {'Dur':>6} {'Due':<10}"
    lines.append(f"{Colors.DIM}{col_header}{Colors.RESET}")
    lines.append('─' * width)

    # Task rows
    available_rows = height - 5  # Account for headers

    for i, task in enumerate(tasks[:available_rows]):
        priority_ind = get_priority_indicator(task['priority'])
        name = truncate(task['name'], 25)
        duration = format_duration(task['duration_in_minutes'])
        due = format_date_short(task['due_date']) if task['due_date'] else 'No date'

        # Color based on priority
        color = PRIORITY_COLORS.get(task['priority'], '')

        row = f"{priority_ind} {color}{name:<25}{Colors.RESET} {duration:>6} {due:<10}"
        lines.append(row)

    # Show overflow indicator
    if len(tasks) > available_rows:
        remaining = len(tasks) - available_rows
        lines.append(f"{Colors.DIM}  ... and {remaining} more tasks{Colors.RESET}")

    # Pad remaining lines
    while len(lines) < height:
        lines.append(' ' * width)

    return lines[:height]


def render_calendar(schedule: Dict, width: int, height: int, days: int) -> List[str]:
    """Render the calendar panel."""
    lines = []
    today = date.today()

    # Header
    header = f"{Colors.BOLD} 📆 SCHEDULE CALENDAR{Colors.RESET}"
    lines.append(pad_right(header, width))
    lines.append('═' * width)

    # Calculate day column width
    day_width = (width - 2) // min(days, 7)

    # Day headers
    day_headers = ""
    for i in range(min(days, 7)):
        day = today + timedelta(days=i)
        day_name = day.strftime("%a")
        day_num = day.strftime("%d")

        if day == today:
            day_header = f"{Colors.GREEN}{Colors.BOLD}{day_name} {day_num}{Colors.RESET}"
        else:
            day_header = f"{day_name} {day_num}"

        day_headers += day_header.center(day_width)

    lines.append(day_headers)
    lines.append('─' * width)

    # Time slots
    slots = ['morning', 'afternoon', 'evening']
    slot_labels = {
        'morning': '🌅 Morning (6-12)',
        'afternoon': '☀️ Afternoon (12-17)',
        'evening': '🌙 Evening (17-22)'
    }

    rows_per_slot = (height - 6) // 3

    for slot in slots:
        # Slot header
        slot_header = f"{SLOT_COLORS[slot]}{slot_labels[slot]}{Colors.RESET}"
        lines.append(slot_header)

        # Tasks for each day in this slot
        for row in range(rows_per_slot - 1):
            day_row = ""
            for i in range(min(days, 7)):
                day = today + timedelta(days=i)
                day_str = day.isoformat()

                day_data = schedule.get('schedule', {}).get(day_str, {})
                slot_data = day_data.get(slot, {})
                tasks_in_slot = slot_data.get('tasks', [])

                if row < len(tasks_in_slot):
                    task = tasks_in_slot[row]
                    task_name = truncate(task['name'], day_width - 3)
                    priority = task.get('priority', 'medium')
                    color = PRIORITY_COLORS.get(priority, '')
                    cell = f"{color}▸{task_name}{Colors.RESET}"
                else:
                    cell = ""

                day_row += cell.ljust(day_width)

            lines.append(day_row)

        lines.append('·' * width)

    # Pad remaining lines
    while len(lines) < height:
        lines.append(' ' * width)

    return lines[:height]


def render_summary(schedule: Dict, width: int) -> List[str]:
    """Render the summary section."""
    lines = []
    summary = schedule.get('summary', {})

    lines.append('─' * width)

    total_tasks = summary.get('total_tasks_scheduled', 0)
    total_hours = summary.get('total_scheduled_hours', 0)
    overflow = summary.get('total_tasks_overflow', 0)

    stats = (
        f"  📊 {Colors.BOLD}Summary:{Colors.RESET} "
        f"{Colors.GREEN}{total_tasks} tasks scheduled{Colors.RESET} │ "
        f"{Colors.CYAN}{total_hours:.1f} hours total{Colors.RESET}"
    )

    if overflow > 0:
        stats += f" │ {Colors.RED}{overflow} overflow{Colors.RESET}"

    lines.append(stats)

    # Insights
    insights = schedule.get('insights', [])
    if insights:
        lines.append('')
        lines.append(f"  💡 {Colors.BOLD}Insights:{Colors.RESET}")
        for insight in insights[:3]:
            lines.append(f"     {insight}")

    return lines


def render_footer(width: int) -> List[str]:
    """Render the footer section."""
    lines = []
    border = '═' * width

    lines.append(f"{Colors.CYAN}╚{border}╝{Colors.RESET}")
    lines.append(f"{Colors.DIM}Press Ctrl+C to exit │ Use --help for options{Colors.RESET}")

    return lines


# =============================================================================
# MAIN VISUALIZATION
# =============================================================================

def visualize(tasks: List[Dict], days: int = 7):
    """Main visualization function."""
    # Generate schedule
    schedule = generate_schedule_from_list(
        task_list=tasks,
        start_date=date.today(),
        horizon_days=days
    )

    # Get terminal size
    term_width, term_height = get_terminal_size()

    # Calculate panel dimensions
    total_width = min(term_width - 2, 140)
    task_list_width = 50
    calendar_width = total_width - task_list_width - 3  # 3 for separator
    content_height = term_height - 15  # Reserve space for header/footer

    # Clear screen
    print('\033[2J\033[H', end='')

    # Render header
    for line in render_header(total_width):
        print(line)

    # Render task list and calendar side by side
    task_lines = render_task_list(tasks, task_list_width, content_height)
    calendar_lines = render_calendar(schedule, calendar_width, content_height, days)

    for i in range(content_height):
        task_part = task_lines[i] if i < len(task_lines) else ' ' * task_list_width
        calendar_part = calendar_lines[i] if i < len(calendar_lines) else ' ' * calendar_width

        # Pad task part
        task_visible_len = len(task_part.replace('\033[', '').split('m')[-1]) if '\033[' in task_part else len(task_part)

        print(f"{Colors.CYAN}║{Colors.RESET} {task_part} {Colors.CYAN}│{Colors.RESET} {calendar_part}")

    # Render summary
    for line in render_summary(schedule, total_width):
        print(f"{Colors.CYAN}║{Colors.RESET}{line}")

    # Render footer
    for line in render_footer(total_width):
        print(line)


def visualize_simple(tasks: List[Dict], days: int = 7):
    """Simplified visualization for terminals without full Unicode support."""
    # Generate schedule
    schedule = generate_schedule_from_list(
        task_list=tasks,
        start_date=date.today(),
        horizon_days=days
    )

    today = date.today()

    print("\n" + "=" * 80)
    print("                    TASK SCHEDULE VISUALIZER")
    print("=" * 80)
    print(f"Generated: {today.strftime('%A, %B %d, %Y')}")
    print("=" * 80)

    # Task List
    print("\n[TASK LIST]")
    print("-" * 60)
    print(f"{'#':<4} {'Priority':<10} {'Task Name':<30} {'Duration':<10}")
    print("-" * 60)

    for i, task in enumerate(tasks, 1):
        priority = task['priority'].upper()
        name = truncate(task['name'], 30)
        duration = format_duration(task['duration_in_minutes'])
        print(f"{i:<4} {priority:<10} {name:<30} {duration:<10}")

    print("-" * 60)
    print(f"Total: {len(tasks)} tasks\n")

    # Calendar View
    print("[CALENDAR VIEW]")
    print("=" * 80)

    for day_offset in range(days):
        day = today + timedelta(days=day_offset)
        day_str = day.isoformat()
        day_label = format_date_short(day)

        print(f"\n>>> {day_label} ({day.strftime('%Y-%m-%d')}) {'[TODAY]' if day == today else ''}")
        print("-" * 40)

        day_data = schedule.get('schedule', {}).get(day_str, {})

        for slot in ['morning', 'afternoon', 'evening']:
            slot_data = day_data.get(slot, {})
            tasks_in_slot = slot_data.get('tasks', [])
            remaining = slot_data.get('remaining_capacity', 0)

            slot_label = f"  {slot.upper():<12}"

            if tasks_in_slot:
                print(f"{slot_label} ({remaining}m free)")
                for task in tasks_in_slot:
                    duration = format_duration(task['duration'])
                    print(f"    - [{task['priority'][:3].upper()}] {task['name']} ({duration})")
            else:
                print(f"{slot_label} (empty)")

        # Show overflow
        overflow = day_data.get('overflow', [])
        if overflow:
            print(f"  {'OVERFLOW':<12}")
            for task in overflow:
                print(f"    ! {task['name']} (could not schedule)")

    # Summary
    print("\n" + "=" * 80)
    print("[SUMMARY]")
    summary = schedule.get('summary', {})
    print(f"  Total tasks scheduled: {summary.get('total_tasks_scheduled', 0)}")
    print(f"  Total hours: {summary.get('total_scheduled_hours', 0):.1f}")
    print(f"  Overflow tasks: {summary.get('total_tasks_overflow', 0)}")

    # Insights
    insights = schedule.get('insights', [])
    if insights:
        print("\n[INSIGHTS]")
        for insight in insights:
            # Remove emoji characters for ASCII compatibility
            clean_insight = ''.join(c for c in insight if ord(c) < 128)
            print(f"  * {clean_insight}")

    print("\n" + "=" * 80)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Visualize task schedule in terminal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python visualize_schedule.py                # Use database tasks, 7 days
  python visualize_schedule.py --mock         # Use mock data for demo
  python visualize_schedule.py --days 14      # Show 14 days
  python visualize_schedule.py --simple       # Simple ASCII output
        '''
    )

    parser.add_argument(
        '--days', '-d',
        type=int,
        default=7,
        help='Number of days to display (default: 7)'
    )

    parser.add_argument(
        '--mock', '-m',
        action='store_true',
        help='Use mock data instead of database'
    )

    parser.add_argument(
        '--simple', '-s',
        action='store_true',
        help='Use simple ASCII visualization (better compatibility)'
    )

    args = parser.parse_args()

    # Get tasks
    if args.mock:
        print("Using mock data for demonstration...")
        tasks = get_mock_tasks()
    else:
        try:
            tasks = get_tasks_from_db()
            if not tasks:
                print("No tasks found in database. Using mock data...")
                tasks = get_mock_tasks()
        except Exception as e:
            print(f"Could not fetch tasks from database: {e}")
            print("Using mock data...")
            tasks = get_mock_tasks()

    # Visualize
    try:
        if args.simple:
            visualize_simple(tasks, args.days)
        else:
            visualize(tasks, args.days)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)


if __name__ == '__main__':
    main()
