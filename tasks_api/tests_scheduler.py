# tasks_api/tests_scheduler.py

"""
Test cases for the Task Scheduling Algorithm.
Tests scoring functions, task allocation, conflict resolution, and API endpoints.
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import json

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .agents.scheduler import (
    TaskScheduler,
    calculate_deadline_factor,
    calculate_priority_factor,
    calculate_energy_match,
    calculate_time_preference_match,
    calculate_urgency_score,
    generate_schedule_from_list,
    ScheduledTask,
    DaySlot,
    DaySchedule,
    TimeSlot,
    Priority,
    WEIGHTS,
)


# =============================================================================
# MOCK DATA FIXTURES
# =============================================================================

def get_mock_tasks():
    """Generate a set of mock tasks for testing."""
    today = date.today()

    return [
        # High priority, due today - should be scheduled first
        {
            'id': 'task-001',
            'name': 'Urgent deadline project',
            'duration_in_minutes': 120,
            'priority': 'emergency',
            'due_date': today,
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        # Medium priority, due tomorrow
        {
            'id': 'task-002',
            'name': 'Prepare presentation',
            'duration_in_minutes': 90,
            'priority': 'high',
            'due_date': today + timedelta(days=1),
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        # Low priority, due in a week
        {
            'id': 'task-003',
            'name': 'Review documents',
            'duration_in_minutes': 60,
            'priority': 'medium',
            'due_date': today + timedelta(days=7),
            'energy_level': 'medium',
            'time_preference': 'afternoon',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        # Daily recurring task
        {
            'id': 'task-004',
            'name': 'Daily standup',
            'duration_in_minutes': 15,
            'priority': 'medium',
            'due_date': today,
            'energy_level': 'low',
            'time_preference': 'morning',
            'repeat': 'every day',
            'completed': False,
            'totally_completed': False,
        },
        # Evening task with low energy
        {
            'id': 'task-005',
            'name': 'Read articles',
            'duration_in_minutes': 30,
            'priority': 'low',
            'due_date': today + timedelta(days=3),
            'energy_level': 'low',
            'time_preference': 'evening',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        # Overdue task - should have highest urgency
        {
            'id': 'task-006',
            'name': 'Overdue report',
            'duration_in_minutes': 60,
            'priority': 'urgent',
            'due_date': today - timedelta(days=2),
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        # No deadline task
        {
            'id': 'task-007',
            'name': 'Organize files',
            'duration_in_minutes': 45,
            'priority': 'low',
            'due_date': None,
            'energy_level': 'low',
            'time_preference': 'anytime',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
        # Weekly recurring task
        {
            'id': 'task-008',
            'name': 'Weekly review',
            'duration_in_minutes': 60,
            'priority': 'medium',
            'due_date': today + timedelta(days=5),
            'energy_level': 'medium',
            'time_preference': 'afternoon',
            'repeat': 'every week',
            'completed': False,
            'totally_completed': False,
        },
        # Completed task - should be excluded
        {
            'id': 'task-009',
            'name': 'Completed task',
            'duration_in_minutes': 30,
            'priority': 'high',
            'due_date': today,
            'energy_level': 'medium',
            'time_preference': 'morning',
            'repeat': None,
            'completed': True,
            'totally_completed': False,
        },
        # Long task that might overflow
        {
            'id': 'task-010',
            'name': 'Deep work session',
            'duration_in_minutes': 180,
            'priority': 'high',
            'due_date': today,
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        },
    ]


def get_overload_tasks():
    """Generate tasks that will exceed daily capacity."""
    today = date.today()

    return [
        {
            'id': f'overload-{i}',
            'name': f'Task {i}',
            'duration_in_minutes': 120,
            'priority': 'high',
            'due_date': today,
            'energy_level': 'high',
            'time_preference': 'morning',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        }
        for i in range(10)  # 10 tasks × 120 min = 1200 min, way over daily capacity
    ]


# =============================================================================
# UNIT TESTS: SCORING FUNCTIONS
# =============================================================================

class TestDeadlineFactorCalculation(unittest.TestCase):
    """Test cases for deadline factor scoring."""

    def setUp(self):
        self.today = date.today()

    def test_overdue_task_gets_highest_score(self):
        """Overdue tasks should score above 100."""
        overdue_date = self.today - timedelta(days=3)
        score = calculate_deadline_factor(overdue_date, self.today)

        self.assertGreater(score, 100)
        # 100 + (3 days × 5) = 115
        self.assertEqual(score, 115.0)

    def test_due_today_scores_95(self):
        """Tasks due today should score 95."""
        score = calculate_deadline_factor(self.today, self.today)
        self.assertEqual(score, 95.0)

    def test_due_tomorrow_scores_85(self):
        """Tasks due tomorrow should score 85."""
        tomorrow = self.today + timedelta(days=1)
        score = calculate_deadline_factor(tomorrow, self.today)
        self.assertEqual(score, 85.0)

    def test_due_within_3_days_scores_70(self):
        """Tasks due within 3 days should score 70."""
        in_3_days = self.today + timedelta(days=3)
        score = calculate_deadline_factor(in_3_days, self.today)
        self.assertEqual(score, 70.0)

    def test_due_within_week_scores_50(self):
        """Tasks due within a week should score 50."""
        in_week = self.today + timedelta(days=7)
        score = calculate_deadline_factor(in_week, self.today)
        self.assertEqual(score, 50.0)

    def test_due_within_2_weeks_scores_30(self):
        """Tasks due within 2 weeks should score 30."""
        in_2_weeks = self.today + timedelta(days=14)
        score = calculate_deadline_factor(in_2_weeks, self.today)
        self.assertEqual(score, 30.0)

    def test_no_deadline_scores_20(self):
        """Tasks with no deadline should score 20."""
        score = calculate_deadline_factor(None, self.today)
        self.assertEqual(score, 20.0)

    def test_far_future_has_minimum_score(self):
        """Tasks far in future should have low but non-negative score."""
        far_future = self.today + timedelta(days=100)
        score = calculate_deadline_factor(far_future, self.today)
        self.assertGreaterEqual(score, 10.0)

    def test_overdue_penalty_caps_at_150(self):
        """Overdue penalty should cap at 150."""
        very_overdue = self.today - timedelta(days=20)
        score = calculate_deadline_factor(very_overdue, self.today)
        # Should be min(150, 100 + 20*5) = min(150, 200) = 150
        self.assertEqual(score, 150.0)


class TestPriorityFactorCalculation(unittest.TestCase):
    """Test cases for priority factor scoring."""

    def test_emergency_priority(self):
        """Emergency priority should score 100."""
        self.assertEqual(calculate_priority_factor('emergency'), 100)

    def test_urgent_priority(self):
        """Urgent priority should score 80."""
        self.assertEqual(calculate_priority_factor('urgent'), 80)

    def test_high_priority(self):
        """High priority should score 60."""
        self.assertEqual(calculate_priority_factor('high'), 60)

    def test_medium_priority(self):
        """Medium priority should score 40."""
        self.assertEqual(calculate_priority_factor('medium'), 40)

    def test_low_priority(self):
        """Low priority should score 20."""
        self.assertEqual(calculate_priority_factor('low'), 20)

    def test_unknown_priority_defaults_to_medium(self):
        """Unknown priority should default to medium (40)."""
        self.assertEqual(calculate_priority_factor('unknown'), 40)

    def test_case_insensitive(self):
        """Priority matching should be case insensitive."""
        self.assertEqual(calculate_priority_factor('EMERGENCY'), 100)
        self.assertEqual(calculate_priority_factor('Urgent'), 80)


class TestEnergyMatchCalculation(unittest.TestCase):
    """Test cases for energy matching scores."""

    def test_high_energy_task_morning_slot(self):
        """High energy task in morning (high energy slot) should score 100."""
        score = calculate_energy_match('high', 'high')
        self.assertEqual(score, 100)

    def test_low_energy_task_evening_slot(self):
        """Low energy task in evening (low energy slot) should score 100."""
        score = calculate_energy_match('low', 'low')
        self.assertEqual(score, 100)

    def test_medium_energy_task_afternoon_slot(self):
        """Medium energy task in afternoon (medium slot) should score 100."""
        score = calculate_energy_match('medium', 'medium')
        self.assertEqual(score, 100)

    def test_high_energy_task_evening_slot_poor_match(self):
        """High energy task in evening slot should score low."""
        score = calculate_energy_match('high', 'low')
        self.assertEqual(score, 40)

    def test_low_energy_task_morning_slot_poor_match(self):
        """Low energy task in morning slot should score low."""
        score = calculate_energy_match('low', 'high')
        self.assertEqual(score, 40)


class TestTimePreferenceMatch(unittest.TestCase):
    """Test cases for time preference matching."""

    def test_exact_match_scores_100(self):
        """Exact time preference match should score 100."""
        self.assertEqual(calculate_time_preference_match('morning', 'morning'), 100)
        self.assertEqual(calculate_time_preference_match('afternoon', 'afternoon'), 100)
        self.assertEqual(calculate_time_preference_match('evening', 'evening'), 100)

    def test_anytime_preference_scores_80(self):
        """'Anytime' preference should score 80 for any slot."""
        self.assertEqual(calculate_time_preference_match('anytime', 'morning'), 80)
        self.assertEqual(calculate_time_preference_match('anytime', 'afternoon'), 80)
        self.assertEqual(calculate_time_preference_match('anytime', 'evening'), 80)

    def test_mismatch_scores_30(self):
        """Mismatched preference should score 30."""
        self.assertEqual(calculate_time_preference_match('morning', 'evening'), 30)
        self.assertEqual(calculate_time_preference_match('evening', 'morning'), 30)


class TestCombinedUrgencyScore(unittest.TestCase):
    """Test cases for combined urgency score calculation."""

    def setUp(self):
        self.today = date.today()

    def test_weights_sum_to_one(self):
        """Scoring weights should sum to 1.0."""
        total_weight = sum(WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)

    def test_emergency_overdue_task_has_highest_score(self):
        """Emergency priority overdue task should have very high score."""
        overdue = self.today - timedelta(days=2)

        score = calculate_urgency_score(
            due_date=overdue,
            priority='emergency',
            task_energy='high',
            task_time_preference='morning',
            slot_name='morning',
            slot_energy='high',
            reference_date=self.today
        )

        # Should be very high: 110*0.4 + 100*0.35 + 100*0.15 + 100*0.10 = 44+35+15+10 = 104
        self.assertGreater(score, 80)

    def test_low_priority_far_future_has_lowest_score(self):
        """Low priority task due far in future should have low score."""
        far_future = self.today + timedelta(days=30)

        score = calculate_urgency_score(
            due_date=far_future,
            priority='low',
            task_energy='low',
            task_time_preference='evening',
            slot_name='morning',  # Mismatch
            slot_energy='high',    # Mismatch
            reference_date=self.today
        )

        # Should be low due to mismatches and low priority
        self.assertLess(score, 40)


# =============================================================================
# UNIT TESTS: DATA STRUCTURES
# =============================================================================

class TestDaySlot(unittest.TestCase):
    """Test cases for DaySlot data structure."""

    def test_default_capacity(self):
        """DaySlot should have correct default capacity."""
        morning = DaySlot(TimeSlot.MORNING)
        self.assertEqual(morning.capacity, 180)

        afternoon = DaySlot(TimeSlot.AFTERNOON)
        self.assertEqual(afternoon.capacity, 150)

        evening = DaySlot(TimeSlot.EVENING)
        self.assertEqual(evening.capacity, 120)

    def test_custom_capacity(self):
        """DaySlot should accept custom capacity."""
        slot = DaySlot(TimeSlot.MORNING, capacity=240)
        self.assertEqual(slot.capacity, 240)

    def test_remaining_capacity_calculation(self):
        """Remaining capacity should decrease as tasks are added."""
        slot = DaySlot(TimeSlot.MORNING)  # 180 min capacity

        task = ScheduledTask(
            task_id='test-1',
            name='Test Task',
            duration=60,
            priority='medium',
            due_date=date.today(),
            scheduled_date=date.today(),
            scheduled_slot='morning',
            urgency_score=50.0
        )

        slot.add_task(task)
        self.assertEqual(slot.remaining_capacity, 120)  # 180 - 60

    def test_can_fit_check(self):
        """can_fit should correctly check if task fits."""
        slot = DaySlot(TimeSlot.EVENING)  # 120 min capacity

        self.assertTrue(slot.can_fit(60))
        self.assertTrue(slot.can_fit(120))
        self.assertFalse(slot.can_fit(121))

    def test_add_task_returns_false_when_full(self):
        """add_task should return False when slot is full."""
        slot = DaySlot(TimeSlot.EVENING, capacity=60)

        task1 = ScheduledTask(
            task_id='t1', name='T1', duration=60,
            priority='medium', due_date=None,
            scheduled_date=date.today(),
            scheduled_slot='evening', urgency_score=50.0
        )
        task2 = ScheduledTask(
            task_id='t2', name='T2', duration=30,
            priority='medium', due_date=None,
            scheduled_date=date.today(),
            scheduled_slot='evening', urgency_score=50.0
        )

        self.assertTrue(slot.add_task(task1))
        self.assertFalse(slot.add_task(task2))


class TestDaySchedule(unittest.TestCase):
    """Test cases for DaySchedule data structure."""

    def test_utilization_calculation(self):
        """Utilization should be calculated correctly."""
        day = DaySchedule(date=date.today())

        # Total capacity: 180 + 150 + 120 = 450
        self.assertEqual(day.total_capacity, 450)

        # Add a 90-minute task to morning
        task = ScheduledTask(
            task_id='t1', name='Test', duration=90,
            priority='medium', due_date=None,
            scheduled_date=date.today(),
            scheduled_slot='morning', urgency_score=50.0
        )
        day.morning.add_task(task)

        # Utilization: 90/450 = 20%
        self.assertAlmostEqual(day.utilization, 20.0, places=1)

    def test_get_slot(self):
        """get_slot should return correct slot."""
        day = DaySchedule(date=date.today())

        self.assertEqual(day.get_slot('morning'), day.morning)
        self.assertEqual(day.get_slot('afternoon'), day.afternoon)
        self.assertEqual(day.get_slot('evening'), day.evening)
        self.assertIsNone(day.get_slot('invalid'))


# =============================================================================
# INTEGRATION TESTS: SCHEDULER
# =============================================================================

class TestTaskSchedulerBasic(unittest.TestCase):
    """Basic integration tests for TaskScheduler."""

    def setUp(self):
        self.today = date.today()
        self.mock_tasks = get_mock_tasks()

    def test_scheduler_initialization(self):
        """Scheduler should initialize correctly."""
        scheduler = TaskScheduler(
            tasks=self.mock_tasks,
            start_date=self.today,
            planning_horizon_days=14
        )

        self.assertEqual(scheduler.start_date, self.today)
        self.assertEqual(scheduler.horizon, 14)
        self.assertEqual(len(scheduler.tasks), len(self.mock_tasks))

    def test_generate_schedule_returns_structure(self):
        """generate_schedule should return proper structure."""
        scheduler = TaskScheduler(
            tasks=self.mock_tasks,
            start_date=self.today,
            planning_horizon_days=7
        )

        result = scheduler.generate_schedule()

        # Check top-level keys
        self.assertIn('schedule', result)
        self.assertIn('summary', result)
        self.assertIn('insights', result)

        # Check summary keys
        self.assertIn('start_date', result['summary'])
        self.assertIn('end_date', result['summary'])
        self.assertIn('total_tasks_scheduled', result['summary'])
        self.assertIn('total_scheduled_hours', result['summary'])

    def test_schedule_covers_full_horizon(self):
        """Schedule should have entries for each day in horizon."""
        horizon = 7
        scheduler = TaskScheduler(
            tasks=self.mock_tasks,
            start_date=self.today,
            planning_horizon_days=horizon
        )

        result = scheduler.generate_schedule()

        self.assertEqual(len(result['schedule']), horizon)

    def test_completed_tasks_excluded(self):
        """Completed tasks should not be scheduled."""
        scheduler = TaskScheduler(
            tasks=self.mock_tasks,
            start_date=self.today,
            planning_horizon_days=7
        )

        result = scheduler.generate_schedule()

        # Find all scheduled task IDs
        scheduled_ids = set()
        for day_data in result['schedule'].values():
            for slot in ['morning', 'afternoon', 'evening']:
                for task in day_data[slot]['tasks']:
                    scheduled_ids.add(task['task_id'])

        # task-009 is completed and should not appear
        self.assertNotIn('task-009', scheduled_ids)

    def test_overdue_tasks_scheduled_first(self):
        """Overdue tasks should be scheduled on the first day."""
        scheduler = TaskScheduler(
            tasks=self.mock_tasks,
            start_date=self.today,
            planning_horizon_days=7
        )

        result = scheduler.generate_schedule()

        # Get first day's tasks
        first_day = self.today.isoformat()
        first_day_tasks = []
        for slot in ['morning', 'afternoon', 'evening']:
            first_day_tasks.extend(result['schedule'][first_day][slot]['tasks'])

        first_day_task_ids = [t['task_id'] for t in first_day_tasks]

        # task-006 is overdue and should be on first day
        self.assertIn('task-006', first_day_task_ids)


class TestTaskSchedulerPriorityOrdering(unittest.TestCase):
    """Test priority-based task ordering."""

    def setUp(self):
        self.today = date.today()

    def test_higher_priority_scheduled_before_lower(self):
        """Higher priority tasks should generally be scheduled before lower."""
        tasks = [
            {
                'id': 'low-priority',
                'name': 'Low Priority Task',
                'duration_in_minutes': 60,
                'priority': 'low',
                'due_date': self.today,
                'energy_level': 'medium',
                'time_preference': 'morning',
                'repeat': None,
                'completed': False,
                'totally_completed': False,
            },
            {
                'id': 'high-priority',
                'name': 'High Priority Task',
                'duration_in_minutes': 60,
                'priority': 'emergency',
                'due_date': self.today,
                'energy_level': 'medium',
                'time_preference': 'morning',
                'repeat': None,
                'completed': False,
                'totally_completed': False,
            },
        ]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=1)
        result = scheduler.generate_schedule()

        # Get morning tasks in order
        morning_tasks = result['schedule'][self.today.isoformat()]['morning']['tasks']

        if len(morning_tasks) >= 2:
            # High priority should have higher urgency score
            high_idx = next(i for i, t in enumerate(morning_tasks) if t['task_id'] == 'high-priority')
            low_idx = next(i for i, t in enumerate(morning_tasks) if t['task_id'] == 'low-priority')

            # Emergency task should come before low priority
            self.assertLess(high_idx, low_idx)


class TestTaskSchedulerRecurring(unittest.TestCase):
    """Test recurring task expansion."""

    def setUp(self):
        self.today = date.today()

    def test_daily_recurring_expands_to_all_days(self):
        """Daily recurring task should create instance for each day."""
        tasks = [
            {
                'id': 'daily-task',
                'name': 'Daily Standup',
                'duration_in_minutes': 15,
                'priority': 'medium',
                'due_date': self.today,
                'energy_level': 'low',
                'time_preference': 'morning',
                'repeat': 'every day',
                'completed': False,
                'totally_completed': False,
            }
        ]

        horizon = 7
        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=horizon)
        result = scheduler.generate_schedule()

        # Count instances across all days
        daily_instances = 0
        for day_data in result['schedule'].values():
            for slot in ['morning', 'afternoon', 'evening']:
                for task in day_data[slot]['tasks']:
                    if 'daily-task' in task['task_id']:
                        daily_instances += 1

        self.assertEqual(daily_instances, horizon)

    def test_weekly_recurring_expands_correctly(self):
        """Weekly recurring task should create weekly instances."""
        tasks = [
            {
                'id': 'weekly-task',
                'name': 'Weekly Review',
                'duration_in_minutes': 60,
                'priority': 'medium',
                'due_date': self.today,
                'energy_level': 'medium',
                'time_preference': 'afternoon',
                'repeat': 'every week',
                'completed': False,
                'totally_completed': False,
            }
        ]

        horizon = 14
        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=horizon)
        result = scheduler.generate_schedule()

        # Count instances
        weekly_instances = 0
        for day_data in result['schedule'].values():
            for slot in ['morning', 'afternoon', 'evening']:
                for task in day_data[slot]['tasks']:
                    if 'weekly-task' in task['task_id']:
                        weekly_instances += 1

        # Should have ~2-3 instances in 14 days
        self.assertGreaterEqual(weekly_instances, 2)
        self.assertLessEqual(weekly_instances, 3)


class TestTaskSchedulerOverflow(unittest.TestCase):
    """Test overflow handling when daily capacity is exceeded."""

    def setUp(self):
        self.today = date.today()

    def test_overflow_when_exceeds_capacity(self):
        """Tasks exceeding daily capacity should go to overflow."""
        overload_tasks = get_overload_tasks()

        scheduler = TaskScheduler(
            tasks=overload_tasks,
            start_date=self.today,
            planning_horizon_days=1
        )

        result = scheduler.generate_schedule()

        first_day = self.today.isoformat()
        overflow_count = len(result['schedule'][first_day]['overflow'])

        # With 10 tasks × 120 min = 1200 min and 450 min capacity,
        # most tasks should overflow on single day
        # Some will be scheduled, some will overflow
        total_scheduled = result['schedule'][first_day]['total_scheduled_minutes']

        self.assertLessEqual(total_scheduled, 450)
        self.assertGreater(overflow_count, 0)

    def test_overflow_pushed_to_future_days(self):
        """Overflow tasks should be rescheduled to future days."""
        overload_tasks = get_overload_tasks()

        scheduler = TaskScheduler(
            tasks=overload_tasks,
            start_date=self.today,
            planning_horizon_days=7  # More days to absorb overflow
        )

        result = scheduler.generate_schedule()

        # Count tasks scheduled across all days
        total_scheduled = 0
        total_overflow = 0
        for day_data in result['schedule'].values():
            for slot in ['morning', 'afternoon', 'evening']:
                total_scheduled += len(day_data[slot]['tasks'])
            total_overflow += len(day_data['overflow'])

        # Most tasks should be scheduled across multiple days
        self.assertGreater(total_scheduled, 3)


class TestTaskSchedulerEnergyMatching(unittest.TestCase):
    """Test energy-based slot assignment."""

    def setUp(self):
        self.today = date.today()

    def test_high_energy_tasks_prefer_morning(self):
        """High energy tasks should prefer morning slot."""
        tasks = [
            {
                'id': 'high-energy',
                'name': 'Deep Work',
                'duration_in_minutes': 60,
                'priority': 'medium',
                'due_date': self.today + timedelta(days=7),  # Not urgent
                'energy_level': 'high',
                'time_preference': 'anytime',  # No explicit preference
                'repeat': None,
                'completed': False,
                'totally_completed': False,
            }
        ]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=14)
        result = scheduler.generate_schedule()

        # Find where the task was scheduled
        scheduled_slot = None
        for day_data in result['schedule'].values():
            for slot in ['morning', 'afternoon', 'evening']:
                for task in day_data[slot]['tasks']:
                    if task['task_id'] == 'high-energy':
                        scheduled_slot = slot
                        break

        # Should prefer morning for high energy
        self.assertEqual(scheduled_slot, 'morning')

    def test_low_energy_tasks_prefer_evening(self):
        """Low energy tasks should prefer evening slot."""
        tasks = [
            {
                'id': 'low-energy',
                'name': 'Light Reading',
                'duration_in_minutes': 30,
                'priority': 'low',
                'due_date': self.today + timedelta(days=7),
                'energy_level': 'low',
                'time_preference': 'anytime',
                'repeat': None,
                'completed': False,
                'totally_completed': False,
            }
        ]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=14)
        result = scheduler.generate_schedule()

        scheduled_slot = None
        for day_data in result['schedule'].values():
            for slot in ['morning', 'afternoon', 'evening']:
                for task in day_data[slot]['tasks']:
                    if task['task_id'] == 'low-energy':
                        scheduled_slot = slot
                        break

        self.assertEqual(scheduled_slot, 'evening')


class TestTaskSchedulerCustomCapacity(unittest.TestCase):
    """Test custom slot capacity configuration."""

    def setUp(self):
        self.today = date.today()

    def test_custom_slot_capacities(self):
        """Scheduler should respect custom slot capacities."""
        tasks = [
            {
                'id': 't1',
                'name': 'Task 1',
                'duration_in_minutes': 60,
                'priority': 'medium',
                'due_date': self.today,
                'energy_level': 'high',
                'time_preference': 'morning',
                'repeat': None,
                'completed': False,
                'totally_completed': False,
            }
        ]

        custom_capacities = {
            'morning': 30,  # Only 30 min capacity
            'afternoon': 150,
            'evening': 120
        }

        scheduler = TaskScheduler(
            tasks=tasks,
            start_date=self.today,
            planning_horizon_days=1,
            slot_capacities=custom_capacities
        )

        result = scheduler.generate_schedule()

        first_day = self.today.isoformat()
        morning_capacity = result['schedule'][first_day]['morning']['capacity']

        self.assertEqual(morning_capacity, 30)


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestGenerateScheduleFromList(unittest.TestCase):
    """Test convenience function for generating schedule from list."""

    def test_generates_schedule_from_dict_list(self):
        """Should generate schedule from list of task dictionaries."""
        tasks = get_mock_tasks()[:3]  # Use subset

        result = generate_schedule_from_list(
            task_list=tasks,
            start_date=date.today(),
            horizon_days=7
        )

        self.assertIn('schedule', result)
        self.assertIn('summary', result)
        self.assertEqual(result['summary']['planning_horizon_days'], 7)


# =============================================================================
# API ENDPOINT TESTS (Django)
# =============================================================================

class TestSchedulerAPIEndpoints(APITestCase):
    """Test scheduler API endpoints."""

    def setUp(self):
        self.today = date.today()

    @patch('tasks_api.views_scheduler.Task.objects')
    def test_generate_schedule_endpoint(self, mock_task_objects):
        """Test /scheduler/generate/ endpoint."""
        # Mock queryset
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.__iter__ = lambda self: iter([])
        mock_task_objects.all.return_value = mock_queryset
        mock_task_objects.filter.return_value = mock_queryset

        url = reverse('tasks_api:scheduler-generate')
        response = self.client.get(url, {'horizon_days': 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('schedule', response.data)
        self.assertIn('summary', response.data)

    @patch('tasks_api.views_scheduler.Task.objects')
    def test_generate_schedule_with_post(self, mock_task_objects):
        """Test POST to /scheduler/generate/ with custom parameters."""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.__iter__ = lambda self: iter([])
        mock_task_objects.all.return_value = mock_queryset
        mock_task_objects.filter.return_value = mock_queryset

        url = reverse('tasks_api:scheduler-generate')
        data = {
            'start_date': self.today.isoformat(),
            'horizon_days': 14,
            'slot_capacities': {
                'morning': 120,
                'afternoon': 120,
                'evening': 120
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('tasks_api.views_scheduler.Task.objects')
    def test_schedule_preview_endpoint(self, mock_task_objects):
        """Test /scheduler/preview/ endpoint."""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.__iter__ = lambda self: iter([])
        mock_task_objects.filter.return_value = mock_queryset

        url = reverse('tasks_api:scheduler-preview')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('date', response.data)
        self.assertIn('schedule', response.data)

    def test_score_task_endpoint(self):
        """Test /scheduler/score/ endpoint."""
        url = reverse('tasks_api:scheduler-score')
        data = {
            'due_date': self.today.isoformat(),
            'priority': 'high',
            'energy_level': 'high',
            'time_preference': 'morning'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('urgency_score', response.data)
        self.assertIn('breakdown', response.data)
        self.assertIn('recommendation', response.data)

    @patch('tasks_api.views_scheduler.Task.objects')
    def test_workload_analysis_endpoint(self, mock_task_objects):
        """Test /scheduler/workload/ endpoint."""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 0
        mock_queryset.__iter__ = lambda self: iter([])
        mock_task_objects.filter.return_value = mock_queryset

        url = reverse('tasks_api:scheduler-workload')
        response = self.client.get(url, {'horizon_days': 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('daily_breakdown', response.data)
        self.assertIn('aggregate', response.data)
        self.assertIn('insights', response.data)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestSchedulerEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        self.today = date.today()

    def test_empty_task_list(self):
        """Scheduler should handle empty task list."""
        scheduler = TaskScheduler(
            tasks=[],
            start_date=self.today,
            planning_horizon_days=7
        )

        result = scheduler.generate_schedule()

        self.assertEqual(result['summary']['total_tasks_scheduled'], 0)
        self.assertEqual(len(result['schedule']), 7)

    def test_single_task(self):
        """Scheduler should handle single task."""
        tasks = [{
            'id': 'single',
            'name': 'Single Task',
            'duration_in_minutes': 30,
            'priority': 'medium',
            'due_date': self.today,
            'energy_level': 'medium',
            'time_preference': 'anytime',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        }]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=1)
        result = scheduler.generate_schedule()

        self.assertEqual(result['summary']['total_tasks_scheduled'], 1)

    def test_all_completed_tasks(self):
        """Scheduler should handle all completed tasks."""
        tasks = [{
            'id': 'completed',
            'name': 'Completed Task',
            'duration_in_minutes': 30,
            'priority': 'medium',
            'due_date': self.today,
            'energy_level': 'medium',
            'time_preference': 'anytime',
            'repeat': None,
            'completed': True,
            'totally_completed': False,
        }]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=1)
        result = scheduler.generate_schedule()

        self.assertEqual(result['summary']['total_tasks_scheduled'], 0)

    def test_horizon_of_one_day(self):
        """Scheduler should handle single day horizon."""
        tasks = get_mock_tasks()[:3]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=1)
        result = scheduler.generate_schedule()

        self.assertEqual(len(result['schedule']), 1)

    def test_very_long_task(self):
        """Scheduler should handle task longer than any single slot."""
        tasks = [{
            'id': 'very-long',
            'name': 'All Day Task',
            'duration_in_minutes': 500,  # Longer than any slot
            'priority': 'medium',
            'due_date': self.today,
            'energy_level': 'medium',
            'time_preference': 'anytime',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        }]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=7)
        result = scheduler.generate_schedule()

        # Task should go to overflow since it doesn't fit any slot
        first_day = self.today.isoformat()
        overflow = result['schedule'][first_day]['overflow']

        # Either scheduled in multiple days or in overflow
        self.assertTrue(
            len(overflow) > 0 or result['summary']['total_tasks_scheduled'] == 0
        )

    def test_zero_duration_task(self):
        """Scheduler should handle zero duration tasks."""
        tasks = [{
            'id': 'zero-duration',
            'name': 'Instant Task',
            'duration_in_minutes': 0,
            'priority': 'medium',
            'due_date': self.today,
            'energy_level': 'medium',
            'time_preference': 'anytime',
            'repeat': None,
            'completed': False,
            'totally_completed': False,
        }]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=1)
        result = scheduler.generate_schedule()

        # Should still be scheduled (0 duration fits anywhere)
        self.assertEqual(result['summary']['total_tasks_scheduled'], 1)

    def test_task_with_missing_fields(self):
        """Scheduler should handle tasks with missing optional fields."""
        tasks = [{
            'id': 'minimal',
            'name': 'Minimal Task',
            'duration_in_minutes': 30,
            'priority': 'medium',
            # Missing: due_date, energy_level, time_preference, repeat
            'completed': False,
            'totally_completed': False,
        }]

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=1)

        # Should not raise exception
        result = scheduler.generate_schedule()
        self.assertIn('schedule', result)


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestSchedulerPerformance(unittest.TestCase):
    """Performance tests for scheduler."""

    def setUp(self):
        self.today = date.today()

    def test_handles_large_task_list(self):
        """Scheduler should handle large number of tasks efficiently."""
        # Generate 100 tasks
        tasks = [
            {
                'id': f'task-{i}',
                'name': f'Task {i}',
                'duration_in_minutes': 30,
                'priority': ['low', 'medium', 'high', 'urgent', 'emergency'][i % 5],
                'due_date': self.today + timedelta(days=i % 14),
                'energy_level': ['low', 'medium', 'high'][i % 3],
                'time_preference': ['morning', 'afternoon', 'evening', 'anytime'][i % 4],
                'repeat': None,
                'completed': False,
                'totally_completed': False,
            }
            for i in range(100)
        ]

        import time
        start_time = time.time()

        scheduler = TaskScheduler(tasks=tasks, start_date=self.today, planning_horizon_days=14)
        result = scheduler.generate_schedule()

        end_time = time.time()
        elapsed = end_time - start_time

        # Should complete in under 5 seconds
        self.assertLess(elapsed, 5.0)
        self.assertGreater(result['summary']['total_tasks_scheduled'], 0)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    unittest.main()
