#!/usr/bin/env python
"""
Test LLM Task Extraction + Scheduling Pipeline

This script demonstrates the full flow:
1. Natural language input (words only)
2. LLM extracts structured tasks with due dates
3. Scheduler creates optimized schedule
"""

import sys
from datetime import date, datetime
from typing import List, Dict

# Test natural language inputs - words only, mixed deadlines
TEST_INPUTS = [
    """
    I need to submit my quarterly report by Friday,
    URGENT prepare the presentation for Monday meeting,
    call mom sometime soon,
    buy groceries tomorrow morning,
    learn Spanish when I have time,
    submit taxes by April 15,
    go to gym three times a week,
    finish reading that book eventually,
    schedule dentist appointment next Tuesday,
    ASAP fix the bug in production
    """,
]


def test_llm_extraction():
    """Test LLM task extraction"""
    print("=" * 60)
    print("STEP 1: LLM TASK EXTRACTION")
    print("=" * 60)

    from tasks_api.agents.task_agent import TaskAgent, LANGCHAIN_AVAILABLE

    if not LANGCHAIN_AVAILABLE:
        print("ERROR: LangChain not available!")
        return None

    agent = TaskAgent(model_name='llama3.2')

    if not agent.validate_ollama_connection():
        print("ERROR: Ollama not running or model not available!")
        return None

    print(f"Today: {date.today().strftime('%Y-%m-%d (%A)')}")
    print()

    # Process natural language input
    user_input = TEST_INPUTS[0]
    print("INPUT (natural language):")
    print("-" * 40)
    for line in user_input.strip().split('\n'):
        line = line.strip()
        if line:
            print(f"  - {line.strip(',')}")
    print()

    print("Processing with LLM...")
    result = agent.process_intentions(user_input)

    print()
    print("EXTRACTED TASKS:")
    print("-" * 40)

    tasks_for_scheduler = []
    for i, task in enumerate(result.tasks, 1):
        print(f"{i}. {task.title}")
        print(f"   Category: {task.category} | Priority: {task.priority}")
        print(f"   Due: {task.due_date or 'None'} {task.due_time or ''}")
        print(f"   Duration: {task.duration} min | Frequency: {task.frequency}")
        print()

        # Convert to scheduler format
        tasks_for_scheduler.append({
            'id': f'task_{i}',
            'name': task.title,
            'duration': task.duration,
            'priority': _convert_priority(task.priority),
            'due_date': _parse_due_date(task.due_date),
            'energy_level': task.energy_level,
            'time_preference': task.time_preference,
            'repeat': _convert_frequency(task.frequency),
            'completed': False,
            'totally_completed': False
        })

    print(f"Total: {len(result.tasks)} tasks extracted")
    return tasks_for_scheduler


def _convert_priority(priority_num: int) -> str:
    """Convert numeric priority (1-5) to string"""
    mapping = {
        1: 'low',
        2: 'low',
        3: 'medium',
        4: 'high',
        5: 'urgent'
    }
    return mapping.get(priority_num, 'medium')


def _convert_frequency(frequency: str) -> str:
    """Convert frequency to repeat pattern"""
    mapping = {
        'daily': 'every day',
        'weekly': 'every week',
        'monthly': 'every month',
        'once': None
    }
    return mapping.get(frequency)


def _parse_due_date(due_date_str: str) -> date:
    """Parse due date string to date object"""
    if not due_date_str:
        return None

    # Handle relative formats like "+3days"
    if due_date_str.startswith('+'):
        try:
            if 'day' in due_date_str:
                days = int(due_date_str.replace('+', '').replace('days', '').replace('day', ''))
                return date.today() + __import__('datetime').timedelta(days=days)
        except:
            pass
        return None

    # Handle YYYY-MM-DD format
    try:
        return datetime.strptime(due_date_str, '%Y-%m-%d').date()
    except:
        return None


def test_scheduler(tasks: List[Dict]):
    """Test task scheduling"""
    print()
    print("=" * 60)
    print("STEP 2: TASK SCHEDULING")
    print("=" * 60)

    if not tasks:
        print("No tasks to schedule!")
        return

    from tasks_api.agents.scheduler import TaskScheduler

    scheduler = TaskScheduler(
        tasks=tasks,
        start_date=date.today(),
        planning_horizon_days=7
    )

    result = scheduler.generate_schedule()

    # Display schedule
    print()
    print("GENERATED SCHEDULE (7 days):")
    print("-" * 40)

    for day_str, day_data in result['schedule'].items():
        task_count = day_data['task_count']
        if task_count == 0:
            continue

        print(f"\n{day_str} ({day_data['utilization']} utilized)")

        for slot_name in ['morning', 'afternoon', 'evening']:
            slot = day_data[slot_name]
            if slot['tasks']:
                print(f"  {slot_name.upper()} ({slot['start_time']}-{slot['end_time']}):")
                for task in slot['tasks']:
                    due_info = f" [due: {task['due_date']}]" if task['due_date'] else ""
                    print(f"    - {task['name']} ({task['duration']}min, {task['priority']}){due_info}")

        if day_data['overflow']:
            print(f"  OVERFLOW:")
            for task in day_data['overflow']:
                print(f"    - {task['name']} (could not fit)")

    # Summary
    print()
    print("SUMMARY:")
    print("-" * 40)
    summary = result['summary']
    print(f"  Period: {summary['start_date']} to {summary['end_date']}")
    print(f"  Tasks scheduled: {summary['total_tasks_scheduled']}")
    print(f"  Tasks overflow: {summary['total_tasks_overflow']}")
    print(f"  Total hours: {summary['total_scheduled_hours']}")
    print(f"  Avg daily: {summary['average_daily_minutes']} min")

    # Insights
    print()
    print("INSIGHTS:")
    print("-" * 40)
    for insight in result['insights']:
        # Remove emojis for Windows console compatibility
        clean_insight = insight.encode('ascii', 'ignore').decode('ascii').strip()
        if clean_insight:
            print(f"  {clean_insight}")


def main():
    print()
    print("=" * 60)
    print("  LLM TASK EXTRACTION + SCHEDULING DEMO")
    print("=" * 60)
    print()

    # Step 1: Extract tasks from natural language
    tasks = test_llm_extraction()

    if tasks:
        # Step 2: Schedule the extracted tasks
        test_scheduler(tasks)

    print()
    print("=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
