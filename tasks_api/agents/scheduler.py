# tasks_api/agents/scheduler.py

"""
Task Scheduling Algorithm
Generates optimized schedules from unsorted tasks based on:
- Deadline/due date proximity
- Priority level (emergency, urgent, high, medium, low)
- Energy level requirements
- Time preferences
- Task duration
- Recurring patterns
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

class Priority(Enum):
    """Priority levels with numeric scores"""
    EMERGENCY = ('emergency', 100)
    URGENT = ('urgent', 80)
    HIGH = ('high', 60)
    MEDIUM = ('medium', 40)
    LOW = ('low', 20)

    def __init__(self, label: str, score: int):
        self.label = label
        self.score = score

    @classmethod
    def from_string(cls, value: str) -> 'Priority':
        """Convert string to Priority enum"""
        for p in cls:
            if p.label == value.lower():
                return p
        return cls.MEDIUM  # Default


class TimeSlot(Enum):
    """Time slots with capacity and energy profile"""
    MORNING = ('morning', '06:00', '12:00', 180, 'high')
    AFTERNOON = ('afternoon', '12:00', '17:00', 150, 'medium')
    EVENING = ('evening', '17:00', '22:00', 120, 'low')

    def __init__(self, label: str, start: str, end: str, capacity: int, energy: str):
        self.label = label
        self.start_time = start
        self.end_time = end
        self.default_capacity = capacity  # minutes
        self.energy_profile = energy


# Scoring weights
WEIGHTS = {
    'deadline': 0.40,
    'priority': 0.35,
    'energy_match': 0.15,
    'time_preference': 0.10
}

# Energy matching scores: slot_energy -> task_energy -> score
ENERGY_MATCH_SCORES = {
    'high': {'high': 100, 'medium': 70, 'low': 40},
    'medium': {'high': 60, 'medium': 100, 'low': 70},
    'low': {'high': 40, 'medium': 70, 'low': 100}
}

# Default daily capacity in minutes
DEFAULT_DAILY_CAPACITY = 450  # 7.5 hours


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ScheduledTask:
    """A task instance scheduled to a specific slot"""
    task_id: str
    name: str
    duration: int  # minutes
    priority: str
    due_date: Optional[date]
    scheduled_date: date
    scheduled_slot: str
    urgency_score: float
    is_recurring_instance: bool = False
    original_task_id: Optional[str] = None
    energy_level: str = 'medium'
    time_preference: str = 'anytime'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'duration': self.duration,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'scheduled_date': self.scheduled_date.isoformat(),
            'scheduled_slot': self.scheduled_slot,
            'urgency_score': round(self.urgency_score, 2),
            'is_recurring_instance': self.is_recurring_instance,
            'energy_level': self.energy_level,
            'time_preference': self.time_preference
        }


@dataclass
class DaySlot:
    """Represents a time slot within a day"""
    slot: TimeSlot
    tasks: List[ScheduledTask] = field(default_factory=list)
    capacity: int = 0  # Set in __post_init__

    def __post_init__(self):
        if self.capacity == 0:
            self.capacity = self.slot.default_capacity

    @property
    def remaining_capacity(self) -> int:
        used = sum(t.duration for t in self.tasks)
        return max(0, self.capacity - used)

    @property
    def total_minutes(self) -> int:
        return sum(t.duration for t in self.tasks)

    def can_fit(self, duration: int) -> bool:
        return self.remaining_capacity >= duration

    def add_task(self, task: ScheduledTask) -> bool:
        if self.can_fit(task.duration):
            self.tasks.append(task)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'slot': self.slot.label,
            'start_time': self.slot.start_time,
            'end_time': self.slot.end_time,
            'tasks': [t.to_dict() for t in self.tasks],
            'total_minutes': self.total_minutes,
            'remaining_capacity': self.remaining_capacity,
            'capacity': self.capacity
        }


@dataclass
class DaySchedule:
    """Represents a full day's schedule"""
    date: date
    morning: DaySlot = field(default_factory=lambda: DaySlot(TimeSlot.MORNING))
    afternoon: DaySlot = field(default_factory=lambda: DaySlot(TimeSlot.AFTERNOON))
    evening: DaySlot = field(default_factory=lambda: DaySlot(TimeSlot.EVENING))
    overflow: List[ScheduledTask] = field(default_factory=list)

    def get_slot(self, slot_name: str) -> Optional[DaySlot]:
        return {
            'morning': self.morning,
            'afternoon': self.afternoon,
            'evening': self.evening
        }.get(slot_name)

    @property
    def total_scheduled_minutes(self) -> int:
        return (self.morning.total_minutes +
                self.afternoon.total_minutes +
                self.evening.total_minutes)

    @property
    def total_capacity(self) -> int:
        return (self.morning.capacity +
                self.afternoon.capacity +
                self.evening.capacity)

    @property
    def utilization(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        return (self.total_scheduled_minutes / self.total_capacity) * 100

    @property
    def all_tasks(self) -> List[ScheduledTask]:
        return (self.morning.tasks +
                self.afternoon.tasks +
                self.evening.tasks)

    def to_dict(self) -> Dict[str, Any]:
        warnings = []
        if self.overflow:
            warnings.append(f"{len(self.overflow)} task(s) could not be scheduled")
        if self.utilization > 90:
            warnings.append("Day is heavily loaded (>90% utilization)")

        return {
            'date': self.date.isoformat(),
            'morning': self.morning.to_dict(),
            'afternoon': self.afternoon.to_dict(),
            'evening': self.evening.to_dict(),
            'overflow': [t.to_dict() for t in self.overflow],
            'total_scheduled_minutes': self.total_scheduled_minutes,
            'total_capacity': self.total_capacity,
            'utilization': f"{self.utilization:.1f}%",
            'task_count': len(self.all_tasks),
            'warnings': warnings
        }


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def calculate_deadline_factor(due_date: Optional[date], reference_date: date) -> float:
    """
    Calculate urgency score based on deadline proximity.

    Returns a score from 0-100+ where:
    - Overdue tasks: 100+ (with penalty for days overdue)
    - Due today: 95
    - Due tomorrow: 85
    - Due within 3 days: 70
    - Due within a week: 50
    - Due within 2 weeks: 30
    - No deadline or far future: 10-20
    """
    if due_date is None:
        return 20.0  # No deadline = low urgency

    days_until_due = (due_date - reference_date).days

    if days_until_due < 0:  # Overdue
        # 100 base + 5 points per day overdue (max 150)
        return min(150.0, 100.0 + abs(days_until_due) * 5)
    elif days_until_due == 0:  # Due today
        return 95.0
    elif days_until_due == 1:  # Due tomorrow
        return 85.0
    elif days_until_due <= 3:  # Due within 3 days
        return 70.0
    elif days_until_due <= 7:  # Due this week
        return 50.0
    elif days_until_due <= 14:  # Due within 2 weeks
        return 30.0
    else:
        # Decreasing urgency for far future tasks (min 10)
        return max(10.0, 30.0 - (days_until_due - 14) * 0.5)


def calculate_priority_factor(priority: str) -> float:
    """Convert priority string to numeric score (0-100)"""
    return Priority.from_string(priority).score


def calculate_energy_match(task_energy: str, slot_energy: str) -> float:
    """
    Calculate how well task energy requirements match slot energy profile.

    Best matches:
    - High energy tasks → Morning (high energy time)
    - Medium energy tasks → Afternoon
    - Low energy tasks → Evening (wind down time)
    """
    task_energy = task_energy.lower() if task_energy else 'medium'
    slot_energy = slot_energy.lower() if slot_energy else 'medium'

    return ENERGY_MATCH_SCORES.get(slot_energy, {}).get(task_energy, 50.0)


def calculate_time_preference_match(task_preference: str, slot_name: str) -> float:
    """
    Calculate how well task time preference matches the slot.

    Returns:
    - 100: Perfect match (task prefers this slot)
    - 80: Task has no preference (anytime)
    - 30: Mismatch (task prefers different slot)
    """
    task_preference = task_preference.lower() if task_preference else 'anytime'

    if task_preference == 'anytime':
        return 80.0
    if task_preference == slot_name:
        return 100.0
    return 30.0


def calculate_urgency_score(
    due_date: Optional[date],
    priority: str,
    task_energy: str,
    task_time_preference: str,
    slot_name: str,
    slot_energy: str,
    reference_date: date
) -> float:
    """
    Calculate combined urgency score for a task in a specific slot.

    Formula:
    URGENCY = (Deadline × 0.40) + (Priority × 0.35) +
              (Energy Match × 0.15) + (Time Pref × 0.10)
    """
    deadline_score = calculate_deadline_factor(due_date, reference_date) * WEIGHTS['deadline']
    priority_score = calculate_priority_factor(priority) * WEIGHTS['priority']
    energy_score = calculate_energy_match(task_energy, slot_energy) * WEIGHTS['energy_match']
    time_pref_score = calculate_time_preference_match(task_time_preference, slot_name) * WEIGHTS['time_preference']

    return deadline_score + priority_score + energy_score + time_pref_score


# =============================================================================
# MAIN SCHEDULER CLASS
# =============================================================================

class TaskScheduler:
    """
    Main scheduler class that generates optimized schedules from unsorted tasks.

    Usage:
        scheduler = TaskScheduler(tasks, planning_horizon_days=14)
        schedule = scheduler.generate_schedule()
    """

    def __init__(
        self,
        tasks: List[Any],
        start_date: Optional[date] = None,
        planning_horizon_days: int = 14,
        slot_capacities: Optional[Dict[str, int]] = None
    ):
        """
        Initialize the scheduler.

        Args:
            tasks: List of task objects (Django Task model instances or dicts)
            start_date: Starting date for schedule (defaults to today)
            planning_horizon_days: How many days to schedule ahead
            slot_capacities: Optional custom capacities for slots
        """
        self.tasks = tasks
        self.start_date = start_date or date.today()
        self.horizon = planning_horizon_days
        self.slot_capacities = slot_capacities or {}
        self.schedule: Dict[date, DaySchedule] = {}

    def generate_schedule(self) -> Dict[str, Any]:
        """
        Main scheduling pipeline.

        Returns:
            Complete schedule with tasks allocated to time slots
        """
        logger.info(f"Generating schedule for {len(self.tasks)} tasks over {self.horizon} days")

        # Step 1: Initialize empty schedule structure
        self._initialize_schedule()

        # Step 2: Separate and expand tasks
        one_time_tasks, recurring_instances = self._process_tasks()
        all_task_instances = one_time_tasks + recurring_instances

        logger.info(f"Processing {len(one_time_tasks)} one-time tasks and {len(recurring_instances)} recurring instances")

        # Step 3: Score and sort tasks
        scored_tasks = self._score_tasks(all_task_instances)
        sorted_tasks = sorted(scored_tasks, key=lambda x: x['score'], reverse=True)

        # Step 4: Allocate tasks to slots
        self._allocate_tasks(sorted_tasks)

        # Step 5: Resolve conflicts and overflow
        self._resolve_conflicts()

        # Step 6: Generate output
        return self._generate_output()

    def _initialize_schedule(self):
        """Create empty schedule structure for each day in the horizon"""
        for day_offset in range(self.horizon):
            day = self.start_date + timedelta(days=day_offset)

            # Apply custom slot capacities if provided
            morning = DaySlot(
                TimeSlot.MORNING,
                capacity=self.slot_capacities.get('morning', TimeSlot.MORNING.default_capacity)
            )
            afternoon = DaySlot(
                TimeSlot.AFTERNOON,
                capacity=self.slot_capacities.get('afternoon', TimeSlot.AFTERNOON.default_capacity)
            )
            evening = DaySlot(
                TimeSlot.EVENING,
                capacity=self.slot_capacities.get('evening', TimeSlot.EVENING.default_capacity)
            )

            self.schedule[day] = DaySchedule(
                date=day,
                morning=morning,
                afternoon=afternoon,
                evening=evening
            )

    def _process_tasks(self) -> tuple:
        """Separate one-time tasks and expand recurring tasks into instances"""
        one_time_tasks = []
        recurring_instances = []

        for task in self.tasks:
            task_data = self._normalize_task(task)

            if task_data.get('repeat'):
                instances = self._expand_recurring_task(task_data)
                recurring_instances.extend(instances)
            else:
                one_time_tasks.append(task_data)

        return one_time_tasks, recurring_instances

    def _normalize_task(self, task: Any) -> Dict[str, Any]:
        """
        Normalize task to dictionary format.
        Handles both Django model instances and dictionaries.
        """
        if isinstance(task, dict):
            return {
                'id': str(task.get('id', '')),
                'name': task.get('name', 'Untitled Task'),
                'duration': task.get('duration_in_minutes', task.get('duration', 30)),
                'priority': task.get('priority', 'medium'),
                'due_date': self._parse_date(task.get('due_date')),
                'repeat': task.get('repeat'),
                'energy_level': task.get('energy_level', 'medium'),
                'time_preference': task.get('time_preference', 'anytime'),
                'completed': task.get('completed', False),
                'totally_completed': task.get('totally_completed', False)
            }
        else:
            # Django model instance
            return {
                'id': str(task.id),
                'name': task.name,
                'duration': getattr(task, 'duration_in_minutes', 30),
                'priority': task.priority,
                'due_date': task.due_date,
                'repeat': task.repeat,
                'energy_level': getattr(task, 'energy_level', 'medium'),
                'time_preference': getattr(task, 'time_preference', 'anytime'),
                'completed': task.completed,
                'totally_completed': task.totally_completed
            }

    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parse date from various formats"""
        if date_value is None:
            return None
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
            except ValueError:
                try:
                    return datetime.strptime(date_value, '%Y-%m-%d').date()
                except ValueError:
                    return None
        return None

    def _expand_recurring_task(self, task_data: Dict) -> List[Dict]:
        """Generate instances for recurring tasks within the planning horizon"""
        instances = []
        repeat_pattern = task_data.get('repeat', '')

        if repeat_pattern == 'every day':
            for day_offset in range(self.horizon):
                instance = task_data.copy()
                instance['scheduled_for'] = self.start_date + timedelta(days=day_offset)
                instance['is_recurring_instance'] = True
                instance['original_task_id'] = task_data['id']
                instance['id'] = f"{task_data['id']}_day_{day_offset}"
                instances.append(instance)

        elif repeat_pattern == 'every week':
            for week in range((self.horizon // 7) + 1):
                target_date = self.start_date + timedelta(weeks=week)
                if target_date < self.start_date + timedelta(days=self.horizon):
                    instance = task_data.copy()
                    instance['scheduled_for'] = target_date
                    instance['is_recurring_instance'] = True
                    instance['original_task_id'] = task_data['id']
                    instance['id'] = f"{task_data['id']}_week_{week}"
                    instances.append(instance)

        elif repeat_pattern == 'every month':
            # Only one instance within typical 14-day horizon
            instance = task_data.copy()
            instance['scheduled_for'] = self.start_date
            instance['is_recurring_instance'] = True
            instance['original_task_id'] = task_data['id']
            instance['id'] = f"{task_data['id']}_month_0"
            instances.append(instance)

        elif repeat_pattern == 'every year':
            # Only include if due date falls within horizon
            if task_data.get('due_date'):
                due = task_data['due_date']
                if self.start_date <= due < self.start_date + timedelta(days=self.horizon):
                    instance = task_data.copy()
                    instance['scheduled_for'] = due
                    instance['is_recurring_instance'] = True
                    instance['original_task_id'] = task_data['id']
                    instance['id'] = f"{task_data['id']}_year_0"
                    instances.append(instance)

        return instances

    def _score_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Calculate urgency scores for all tasks"""
        scored = []

        for task_data in tasks:
            # Skip completed tasks
            if task_data.get('completed') or task_data.get('totally_completed'):
                continue

            # Determine target date
            target_date = task_data.get('scheduled_for') or task_data.get('due_date')
            if target_date is None:
                target_date = self.start_date  # No date = schedule ASAP

            # Ensure target is within horizon
            end_date = self.start_date + timedelta(days=self.horizon - 1)
            if target_date > end_date:
                target_date = end_date
            if target_date < self.start_date:
                target_date = self.start_date  # Overdue = schedule ASAP

            # Get preferred slot
            preferred_slot = self._get_preferred_slot(task_data)
            slot_energy = TimeSlot.MORNING.energy_profile
            for slot in TimeSlot:
                if slot.label == preferred_slot:
                    slot_energy = slot.energy_profile
                    break

            # Calculate score
            score = calculate_urgency_score(
                due_date=task_data.get('due_date'),
                priority=task_data.get('priority', 'medium'),
                task_energy=task_data.get('energy_level', 'medium'),
                task_time_preference=task_data.get('time_preference', 'anytime'),
                slot_name=preferred_slot,
                slot_energy=slot_energy,
                reference_date=self.start_date
            )

            scored.append({
                'task_data': task_data,
                'score': score,
                'target_date': target_date,
                'preferred_slot': preferred_slot
            })

        return scored

    def _get_preferred_slot(self, task_data: Dict) -> str:
        """Determine best slot based on task attributes"""

        # Explicit time preference takes precedence
        time_pref = task_data.get('time_preference', 'anytime')
        if time_pref and time_pref != 'anytime':
            return time_pref

        # Infer from energy level
        energy = task_data.get('energy_level', 'medium')
        if energy == 'high':
            return 'morning'
        elif energy == 'low':
            return 'evening'

        # Infer from priority (high priority = morning for focus)
        priority = task_data.get('priority', 'medium')
        if priority in ['emergency', 'urgent']:
            return 'morning'

        return 'afternoon'  # Default

    def _allocate_tasks(self, sorted_tasks: List[Dict]):
        """Allocate tasks to time slots using greedy algorithm"""

        for item in sorted_tasks:
            task_data = item['task_data']
            target_date = item['target_date']
            preferred_slot = item['preferred_slot']
            score = item['score']

            # Create ScheduledTask object
            scheduled_task = ScheduledTask(
                task_id=task_data['id'],
                name=task_data['name'],
                duration=task_data['duration'],
                priority=task_data['priority'],
                due_date=task_data.get('due_date'),
                scheduled_date=target_date,
                scheduled_slot=preferred_slot,
                urgency_score=score,
                is_recurring_instance=task_data.get('is_recurring_instance', False),
                original_task_id=task_data.get('original_task_id'),
                energy_level=task_data.get('energy_level', 'medium'),
                time_preference=task_data.get('time_preference', 'anytime')
            )

            allocated = False

            # Try preferred slot on target date first
            if target_date in self.schedule:
                day_schedule = self.schedule[target_date]
                slot = day_schedule.get_slot(preferred_slot)
                if slot and slot.add_task(scheduled_task):
                    scheduled_task.scheduled_slot = preferred_slot
                    allocated = True

            # Try other slots on same day
            if not allocated and target_date in self.schedule:
                day_schedule = self.schedule[target_date]
                for slot_name in ['morning', 'afternoon', 'evening']:
                    if slot_name != preferred_slot:
                        slot = day_schedule.get_slot(slot_name)
                        if slot and slot.add_task(scheduled_task):
                            scheduled_task.scheduled_slot = slot_name
                            allocated = True
                            break

            # For urgent/emergency tasks, try earlier days
            if not allocated and task_data.get('priority') in ['urgent', 'emergency']:
                for day_offset in range((target_date - self.start_date).days):
                    earlier_date = self.start_date + timedelta(days=day_offset)
                    if earlier_date in self.schedule:
                        day_schedule = self.schedule[earlier_date]
                        for slot_name in ['morning', 'afternoon', 'evening']:
                            slot = day_schedule.get_slot(slot_name)
                            if slot and slot.add_task(scheduled_task):
                                scheduled_task.scheduled_date = earlier_date
                                scheduled_task.scheduled_slot = slot_name
                                allocated = True
                                break
                    if allocated:
                        break

            # Add to overflow if still not allocated
            if not allocated:
                if target_date in self.schedule:
                    self.schedule[target_date].overflow.append(scheduled_task)
                else:
                    # Target date outside horizon, add to first day overflow
                    self.schedule[self.start_date].overflow.append(scheduled_task)

    def _resolve_conflicts(self):
        """Handle overflowed tasks by trying to reschedule to future days"""

        for current_date in sorted(self.schedule.keys()):
            day_schedule = self.schedule[current_date]
            overflow = day_schedule.overflow.copy()

            if not overflow:
                continue

            for task in overflow:
                # Try to push to future days (within 7 days)
                for future_offset in range(1, min(8, self.horizon)):
                    future_date = current_date + timedelta(days=future_offset)
                    if future_date not in self.schedule:
                        continue

                    future_schedule = self.schedule[future_date]
                    allocated = False

                    for slot_name in ['morning', 'afternoon', 'evening']:
                        slot = future_schedule.get_slot(slot_name)
                        if slot and slot.add_task(task):
                            task.scheduled_date = future_date
                            task.scheduled_slot = slot_name
                            day_schedule.overflow.remove(task)
                            allocated = True
                            break

                    if allocated:
                        break

    def _generate_output(self) -> Dict[str, Any]:
        """Generate the final schedule output"""

        schedule_output = {}
        total_tasks = 0
        total_overflow = 0
        total_minutes = 0

        for day, day_schedule in sorted(self.schedule.items()):
            schedule_output[day.isoformat()] = day_schedule.to_dict()
            total_tasks += len(day_schedule.all_tasks)
            total_overflow += len(day_schedule.overflow)
            total_minutes += day_schedule.total_scheduled_minutes

        # Generate summary and insights
        insights = self._generate_insights()

        return {
            'schedule': schedule_output,
            'summary': {
                'start_date': self.start_date.isoformat(),
                'end_date': (self.start_date + timedelta(days=self.horizon - 1)).isoformat(),
                'planning_horizon_days': self.horizon,
                'total_tasks_scheduled': total_tasks,
                'total_tasks_overflow': total_overflow,
                'total_scheduled_minutes': total_minutes,
                'total_scheduled_hours': round(total_minutes / 60, 1),
                'average_daily_minutes': round(total_minutes / self.horizon, 1) if self.horizon > 0 else 0
            },
            'insights': insights
        }

    def _generate_insights(self) -> List[str]:
        """Generate scheduling insights and recommendations"""
        insights = []

        # Calculate statistics
        total_overflow = sum(len(day.overflow) for day in self.schedule.values())
        total_tasks = sum(len(day.all_tasks) for day in self.schedule.values())
        high_utilization_days = sum(1 for day in self.schedule.values() if day.utilization > 80)
        low_utilization_days = sum(1 for day in self.schedule.values() if day.utilization < 30)

        # Overflow warning
        if total_overflow > 0:
            insights.append(f"⚠️ {total_overflow} task(s) could not be scheduled within capacity limits. Consider extending deadlines or reducing task durations.")

        # Utilization insights
        if high_utilization_days > self.horizon * 0.5:
            insights.append(f"🔥 {high_utilization_days} days have high workload (>80% capacity). Risk of burnout - consider redistributing tasks.")

        if low_utilization_days > self.horizon * 0.3 and total_tasks > 0:
            insights.append(f"✅ {low_utilization_days} days have light workload. Good buffer for unexpected tasks.")

        # Priority distribution
        all_tasks = []
        for day in self.schedule.values():
            all_tasks.extend(day.all_tasks)

        urgent_count = len([t for t in all_tasks if t.priority in ['urgent', 'emergency']])
        if urgent_count > total_tasks * 0.3 and total_tasks > 0:
            insights.append(f"🚨 {urgent_count} urgent/emergency tasks ({round(urgent_count/total_tasks*100)}%). Consider reviewing priorities.")

        # Morning load
        morning_minutes = sum(day.morning.total_minutes for day in self.schedule.values())
        total_minutes = sum(day.total_scheduled_minutes for day in self.schedule.values())
        if total_minutes > 0 and morning_minutes / total_minutes > 0.5:
            insights.append("☀️ Heavy morning workload. High-energy tasks are well-positioned for peak productivity.")

        # Success message
        if total_overflow == 0 and total_tasks > 0:
            insights.append(f"✅ Successfully scheduled all {total_tasks} tasks within the {self.horizon}-day horizon.")

        return insights


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_schedule_from_queryset(
    queryset,
    start_date: Optional[date] = None,
    horizon_days: int = 14,
    slot_capacities: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate schedule from Django QuerySet.

    Args:
        queryset: Django QuerySet of Task objects
        start_date: Starting date (defaults to today)
        horizon_days: Number of days to plan
        slot_capacities: Optional custom slot capacities

    Returns:
        Complete schedule dictionary
    """
    tasks = list(queryset)
    scheduler = TaskScheduler(
        tasks=tasks,
        start_date=start_date,
        planning_horizon_days=horizon_days,
        slot_capacities=slot_capacities
    )
    return scheduler.generate_schedule()


def generate_schedule_from_list(
    task_list: List[Dict],
    start_date: Optional[date] = None,
    horizon_days: int = 14,
    slot_capacities: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate schedule from list of task dictionaries.

    Args:
        task_list: List of task dictionaries
        start_date: Starting date (defaults to today)
        horizon_days: Number of days to plan
        slot_capacities: Optional custom slot capacities

    Returns:
        Complete schedule dictionary
    """
    scheduler = TaskScheduler(
        tasks=task_list,
        start_date=start_date,
        planning_horizon_days=horizon_days,
        slot_capacities=slot_capacities
    )
    return scheduler.generate_schedule()
