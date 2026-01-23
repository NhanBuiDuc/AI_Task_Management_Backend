# tasks_api/views_scheduler.py

"""
API Views for Task Scheduling
Provides endpoints for generating optimized schedules from tasks
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import date, datetime, timedelta
from .models import Task
from .agents.scheduler import (
    TaskScheduler,
    generate_schedule_from_queryset,
    calculate_deadline_factor,
    calculate_priority_factor
)
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
def generate_schedule(request):
    """
    Generate an optimized schedule from tasks.

    GET Parameters:
        - start_date: Starting date (YYYY-MM-DD), defaults to today
        - horizon_days: Number of days to plan (default: 14, max: 90)
        - project_id: Filter tasks by project (optional)
        - include_completed: Include completed tasks (default: false)
        - morning_capacity: Morning slot capacity in minutes (default: 180)
        - afternoon_capacity: Afternoon slot capacity in minutes (default: 150)
        - evening_capacity: Evening slot capacity in minutes (default: 120)

    POST Body:
        {
            "start_date": "2026-01-20",
            "horizon_days": 14,
            "project_id": "uuid-string",  // optional
            "include_completed": false,
            "slot_capacities": {
                "morning": 180,
                "afternoon": 150,
                "evening": 120
            },
            "task_ids": ["uuid1", "uuid2"]  // optional, specific tasks to schedule
        }

    Returns:
        {
            "schedule": {
                "2026-01-20": {
                    "morning": { tasks: [...], total_minutes: 150, ... },
                    "afternoon": { ... },
                    "evening": { ... },
                    "overflow": [...],
                    "utilization": "60%"
                },
                ...
            },
            "summary": {
                "start_date": "2026-01-20",
                "end_date": "2026-02-02",
                "total_tasks_scheduled": 25,
                "total_scheduled_hours": 18.5,
                ...
            },
            "insights": [
                "Successfully scheduled all tasks",
                ...
            ]
        }
    """
    try:
        # Parse parameters from GET or POST
        if request.method == 'POST':
            data = request.data
            start_date_str = data.get('start_date')
            horizon_days = data.get('horizon_days', 14)
            project_id = data.get('project_id')
            include_completed = data.get('include_completed', False)
            slot_capacities = data.get('slot_capacities', {})
            task_ids = data.get('task_ids')
        else:
            start_date_str = request.query_params.get('start_date')
            horizon_days = int(request.query_params.get('horizon_days', 14))
            project_id = request.query_params.get('project_id')
            include_completed = request.query_params.get('include_completed', 'false').lower() == 'true'
            slot_capacities = {
                'morning': int(request.query_params.get('morning_capacity', 180)),
                'afternoon': int(request.query_params.get('afternoon_capacity', 150)),
                'evening': int(request.query_params.get('evening_capacity', 120))
            }
            task_ids = request.query_params.getlist('task_ids')

        # Parse start date
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            start_date = date.today()

        # Validate horizon
        horizon_days = min(max(1, horizon_days), 90)  # Clamp between 1-90 days

        # Build task queryset
        queryset = Task.objects.all()

        # Filter by specific task IDs if provided
        if task_ids:
            queryset = queryset.filter(id__in=task_ids)

        # Filter by project
        if project_id:
            if project_id.lower() == 'null':
                queryset = queryset.filter(project__isnull=True)
            else:
                queryset = queryset.filter(project_id=project_id)

        # Exclude completed tasks unless requested
        if not include_completed:
            queryset = queryset.filter(completed=False, totally_completed=False)

        # Generate schedule
        schedule_result = generate_schedule_from_queryset(
            queryset=queryset,
            start_date=start_date,
            horizon_days=horizon_days,
            slot_capacities=slot_capacities if slot_capacities else None
        )

        return Response(schedule_result)

    except Exception as e:
        logger.error(f"Error generating schedule: {str(e)}")
        return Response(
            {'error': f'Failed to generate schedule: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def schedule_preview(request):
    """
    Preview schedule for a single day without persisting.

    Query Parameters:
        - date: Target date (YYYY-MM-DD), defaults to today
        - project_id: Filter tasks by project (optional)

    Returns:
        Single day schedule with task allocation
    """
    try:
        date_str = request.query_params.get('date')
        project_id = request.query_params.get('project_id')

        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = date.today()

        # Build queryset
        queryset = Task.objects.filter(
            completed=False,
            totally_completed=False
        )

        if project_id:
            if project_id.lower() == 'null':
                queryset = queryset.filter(project__isnull=True)
            else:
                queryset = queryset.filter(project_id=project_id)

        # Filter to tasks relevant for target date
        # Include: overdue tasks, tasks due on target date, tasks due soon
        queryset = queryset.filter(
            due_date__lte=target_date + timedelta(days=7)
        )

        # Generate single-day schedule
        schedule_result = generate_schedule_from_queryset(
            queryset=queryset,
            start_date=target_date,
            horizon_days=1
        )

        # Extract just the single day
        day_schedule = schedule_result.get('schedule', {}).get(target_date.isoformat())

        return Response({
            'date': target_date.isoformat(),
            'schedule': day_schedule,
            'task_count': len(list(queryset))
        })

    except Exception as e:
        logger.error(f"Error generating schedule preview: {str(e)}")
        return Response(
            {'error': f'Failed to generate preview: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def score_task(request):
    """
    Calculate urgency score for a single task.

    POST Body:
        {
            "due_date": "2026-01-25",
            "priority": "high",
            "energy_level": "medium",
            "time_preference": "morning"
        }

    Returns:
        {
            "urgency_score": 72.5,
            "breakdown": {
                "deadline_factor": 28.0,
                "priority_factor": 21.0,
                "energy_match": 15.0,
                "time_preference": 8.5
            },
            "recommendation": "morning"
        }
    """
    try:
        data = request.data
        today = date.today()

        # Parse due date
        due_date_str = data.get('due_date')
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                due_date = None
        else:
            due_date = None

        priority = data.get('priority', 'medium')
        energy_level = data.get('energy_level', 'medium')
        time_preference = data.get('time_preference', 'anytime')

        # Calculate individual factors
        deadline_raw = calculate_deadline_factor(due_date, today)
        priority_raw = calculate_priority_factor(priority)

        # Calculate weighted scores
        deadline_weighted = deadline_raw * 0.40
        priority_weighted = priority_raw * 0.35

        # Determine best slot based on energy
        if energy_level == 'high':
            recommended_slot = 'morning'
            energy_match = 100
        elif energy_level == 'low':
            recommended_slot = 'evening'
            energy_match = 100
        else:
            recommended_slot = 'afternoon'
            energy_match = 100

        energy_weighted = energy_match * 0.15

        # Time preference score
        if time_preference == 'anytime':
            time_pref_score = 80
        else:
            time_pref_score = 100
            recommended_slot = time_preference

        time_pref_weighted = time_pref_score * 0.10

        total_score = deadline_weighted + priority_weighted + energy_weighted + time_pref_weighted

        return Response({
            'urgency_score': round(total_score, 2),
            'breakdown': {
                'deadline_factor': round(deadline_weighted, 2),
                'deadline_raw': round(deadline_raw, 2),
                'priority_factor': round(priority_weighted, 2),
                'priority_raw': round(priority_raw, 2),
                'energy_match': round(energy_weighted, 2),
                'time_preference': round(time_pref_weighted, 2)
            },
            'recommendation': {
                'slot': recommended_slot,
                'days_until_due': (due_date - today).days if due_date else None,
                'is_overdue': due_date < today if due_date else False
            }
        })

    except Exception as e:
        logger.error(f"Error scoring task: {str(e)}")
        return Response(
            {'error': f'Failed to score task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def workload_analysis(request):
    """
    Analyze workload distribution across the planning horizon.

    Query Parameters:
        - horizon_days: Number of days to analyze (default: 14)
        - project_id: Filter by project (optional)

    Returns:
        Workload statistics and recommendations
    """
    try:
        horizon_days = int(request.query_params.get('horizon_days', 14))
        project_id = request.query_params.get('project_id')

        horizon_days = min(max(1, horizon_days), 90)
        today = date.today()

        # Build queryset
        queryset = Task.objects.filter(
            completed=False,
            totally_completed=False
        )

        if project_id:
            if project_id.lower() == 'null':
                queryset = queryset.filter(project__isnull=True)
            else:
                queryset = queryset.filter(project_id=project_id)

        # Generate full schedule
        schedule_result = generate_schedule_from_queryset(
            queryset=queryset,
            start_date=today,
            horizon_days=horizon_days
        )

        # Analyze workload by day
        schedule = schedule_result.get('schedule', {})
        daily_stats = []

        for day_offset in range(horizon_days):
            day = today + timedelta(days=day_offset)
            day_str = day.isoformat()
            day_data = schedule.get(day_str, {})

            daily_stats.append({
                'date': day_str,
                'day_name': day.strftime('%A'),
                'scheduled_minutes': day_data.get('total_scheduled_minutes', 0),
                'capacity': day_data.get('total_capacity', 450),
                'utilization': day_data.get('utilization', '0%'),
                'task_count': day_data.get('task_count', 0),
                'overflow_count': len(day_data.get('overflow', []))
            })

        # Calculate aggregate statistics
        total_minutes = sum(d['scheduled_minutes'] for d in daily_stats)
        total_capacity = sum(d['capacity'] for d in daily_stats)
        avg_utilization = (total_minutes / total_capacity * 100) if total_capacity > 0 else 0

        # Identify peak and light days
        busiest_day = max(daily_stats, key=lambda x: x['scheduled_minutes'])
        lightest_day = min(daily_stats, key=lambda x: x['scheduled_minutes'])

        # Priority breakdown
        priority_counts = {
            'emergency': 0,
            'urgent': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        for task in queryset:
            if task.priority in priority_counts:
                priority_counts[task.priority] += 1

        return Response({
            'horizon_days': horizon_days,
            'daily_breakdown': daily_stats,
            'aggregate': {
                'total_scheduled_minutes': total_minutes,
                'total_scheduled_hours': round(total_minutes / 60, 1),
                'total_capacity_minutes': total_capacity,
                'average_utilization': f"{avg_utilization:.1f}%",
                'average_daily_minutes': round(total_minutes / horizon_days, 1),
                'total_tasks': queryset.count()
            },
            'highlights': {
                'busiest_day': {
                    'date': busiest_day['date'],
                    'day_name': busiest_day['day_name'],
                    'minutes': busiest_day['scheduled_minutes']
                },
                'lightest_day': {
                    'date': lightest_day['date'],
                    'day_name': lightest_day['day_name'],
                    'minutes': lightest_day['scheduled_minutes']
                }
            },
            'priority_distribution': priority_counts,
            'insights': schedule_result.get('insights', [])
        })

    except Exception as e:
        logger.error(f"Error analyzing workload: {str(e)}")
        return Response(
            {'error': f'Failed to analyze workload: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
