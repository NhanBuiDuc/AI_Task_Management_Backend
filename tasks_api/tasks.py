# File: tasks_api/tasks.py

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from typing import Dict, List, Optional, Any
import json
import traceback
from datetime import timedelta

from .models import Task, Project, Section
from .agents.task_agent import TaskAgent
from .serializers import TaskSerializer
from .utils.notifications import NotificationService
from .utils.analytics import AnalyticsTracker

logger = get_task_logger(__name__)

class TaskProcessingError(Exception):
    """Custom exception for task processing failures"""
    pass

@shared_task(bind=True, max_retries=3, soft_time_limit=60)
def process_ai_intention(
    self,
    intention: str,
    user_id: int,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process natural language intention asynchronously using AI agent.
    
    Args:
        intention: Natural language input from user
        user_id: ID of the user
        session_id: Optional session ID for tracking
        metadata: Additional context data
        
    Returns:
        Dict containing created tasks and processing insights
    """
    try:
        # Check cache for duplicate requests
        cache_key = f"ai_intention:{user_id}:{hash(intention)}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for user {user_id}")
            return cached_result
        
        # Initialize AI agent
        agent = TaskAgent()
        
        # Add user context to agent
        user_context = _get_user_context(user_id)
        
        # Process intention with retry logic
        try:
            processed_data = agent.process_intention(
                intention=intention,
                user_context=user_context
            )
        except Exception as e:
            logger.warning(f"AI processing failed, using fallback: {str(e)}")
            processed_data = _fallback_processing(intention, user_id)
        
        # Create tasks in database
        created_tasks = []
        with transaction.atomic():
            for task_data in processed_data.get('tasks', []):
                task = _create_task_from_ai_data(task_data, user_id)
                created_tasks.append(task)
                
                # Schedule recurring tasks if needed
                if task_data.get('recurring'):
                    schedule_recurring_task.delay(
                        task_id=task.id,
                        pattern=task_data['recurring']
                    )
        
        # Store insights asynchronously
        if processed_data.get('insights'):
            store_ai_insights.delay(
                user_id=user_id,
                insights=processed_data['insights'],
                session_id=session_id
            )
        
        # Prepare response
        result = {
            'status': 'success',
            'tasks': TaskSerializer(created_tasks, many=True).data,
            'insights': processed_data.get('insights', {}),
            'processing_time': processed_data.get('processing_time', 0),
            'ai_confidence': processed_data.get('confidence', 0.0)
        }
        
        # Cache result for 5 minutes
        cache.set(cache_key, result, 300)
        
        # Track analytics
        AnalyticsTracker.track_ai_processing(
            user_id=user_id,
            task_count=len(created_tasks),
            processing_time=result['processing_time']
        )
        
        # Send real-time notification
        NotificationService.notify_tasks_created(
            user_id=user_id,
            tasks=created_tasks,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Task processing failed: {str(e)}\n{traceback.format_exc()}")
        
        # Retry with exponential backoff
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            raise self.retry(countdown=2 ** retry_count)
        
        # Final failure - notify user
        NotificationService.notify_processing_failure(
            user_id=user_id,
            error_message=str(e),
            session_id=session_id
        )
        
        raise TaskProcessingError(f"Failed to process intention: {str(e)}")

@shared_task
def schedule_recurring_task(task_id: int, pattern: Dict[str, Any]) -> None:
    """
    Schedule recurring task instances based on pattern.
    
    Args:
        task_id: ID of the parent task
        pattern: Recurrence pattern (daily, weekly, custom)
    """
    try:
        task = Task.objects.get(id=task_id)
        
        # Parse recurrence pattern
        frequency = pattern.get('frequency', 'daily')
        count = pattern.get('count', 30)  # Default 30 occurrences
        
        # Generate future instances
        current_date = timezone.now().date()
        for i in range(1, count + 1):
            if frequency == 'daily':
                next_date = current_date + timedelta(days=i)
            elif frequency == 'weekly':
                next_date = current_date + timedelta(weeks=i)
            elif frequency == 'custom':
                # Handle custom patterns (e.g., every 3 days)
                interval = pattern.get('interval', 1)
                next_date = current_date + timedelta(days=i * interval)
            
            # Create scheduled instance
            Task.objects.create(
                user_id=task.user_id,
                project_id=task.project_id,
                section_id=task.section_id,
                title=task.title,
                description=task.description,
                due_date=next_date,
                priority=task.priority,
                parent_task_id=task.id,
                is_recurring_instance=True
            )
        
        logger.info(f"Scheduled {count} recurring instances for task {task_id}")
        
    except Task.DoesNotExist:
        logger.error(f"Task {task_id} not found for recurring schedule")
    except Exception as e:
        logger.error(f"Failed to schedule recurring task: {str(e)}")

@shared_task
def store_ai_insights(
    user_id: int,
    insights: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Store AI-generated insights in MongoDB for analytics.
    
    Args:
        user_id: User identifier
        insights: AI-generated insights and recommendations
        session_id: Optional session tracking
    """
    try:
        from .utils.mongodb import get_insights_collection
        
        collection = get_insights_collection()
        
        # Prepare document
        document = {
            'user_id': user_id,
            'insights': insights,
            'session_id': session_id,
            'created_at': timezone.now().isoformat(),
            'type': 'task_processing',
            'confidence_scores': insights.get('confidence_scores', {}),
            'recommendations': insights.get('recommendations', [])
        }
        
        # Store in MongoDB
        collection.insert_one(document)
        
        # Update user's productivity score
        update_productivity_score.delay(user_id=user_id)
        
    except Exception as e:
        logger.error(f"Failed to store insights: {str(e)}")

@shared_task
def update_productivity_score(user_id: int) -> float:
    """
    Calculate and update user's productivity score based on task completion.
    
    Args:
        user_id: User identifier
        
    Returns:
        Updated productivity score
    """
    try:
        # Get user's task statistics
        from django.db.models import Count, Q, Avg
        from datetime import datetime, timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        stats = Task.objects.filter(
            user_id=user_id,
            created_at__gte=thirty_days_ago
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(is_completed=True)),
            overdue=Count('id', filter=Q(
                due_date__lt=timezone.now(),
                is_completed=False
            )),
            avg_completion_time=Avg('completion_time')
        )
        
        # Calculate score (0-100)
        completion_rate = stats['completed'] / stats['total'] if stats['total'] > 0 else 0
        overdue_penalty = stats['overdue'] / stats['total'] if stats['total'] > 0 else 0
        
        score = (completion_rate * 70) + ((1 - overdue_penalty) * 30)
        
        # Store score
        cache.set(f"productivity_score:{user_id}", score, 3600)
        
        # Trigger achievement check
        check_user_achievements.delay(user_id=user_id, score=score)
        
        return score
        
    except Exception as e:
        logger.error(f"Failed to update productivity score: {str(e)}")
        return 0.0

@shared_task
def check_user_achievements(user_id: int, score: float) -> None:
    """
    Check and award user achievements based on activity.
    
    Args:
        user_id: User identifier
        score: Current productivity score
    """
    try:
        from .models import UserAchievement
        
        achievements_earned = []
        
        # Define achievement criteria
        achievements = [
            {'id': 'first_task', 'name': 'First Step', 'criteria': lambda: Task.objects.filter(user_id=user_id).count() >= 1},
            {'id': 'productive_week', 'name': 'Productive Week', 'criteria': lambda: score >= 80},
            {'id': 'task_master', 'name': 'Task Master', 'criteria': lambda: Task.objects.filter(user_id=user_id, is_completed=True).count() >= 100},
        ]
        
        for achievement in achievements:
            if achievement['criteria']():
                obj, created = UserAchievement.objects.get_or_create(
                    user_id=user_id,
                    achievement_id=achievement['id'],
                    defaults={'name': achievement['name']}
                )
                if created:
                    achievements_earned.append(achievement['name'])
        
        # Notify user of new achievements
        if achievements_earned:
            NotificationService.notify_achievements(
                user_id=user_id,
                achievements=achievements_earned
            )
            
    except Exception as e:
        logger.error(f"Failed to check achievements: {str(e)}")

def _get_user_context(user_id: int) -> Dict[str, Any]:
    """Get user's context for AI processing"""
    try:
        # Get user's recent tasks and patterns
        recent_tasks = Task.objects.filter(
            user_id=user_id
        ).order_by('-created_at')[:20]
        
        # Get user's projects
        projects = Project.objects.filter(user_id=user_id)
        
        return {
            'recent_task_titles': [t.title for t in recent_tasks],
            'project_names': [p.name for p in projects],
            'preferred_categories': _get_preferred_categories(user_id),
            'typical_priority': _get_typical_priority(user_id),
            'timezone': _get_user_timezone(user_id)
        }
    except Exception as e:
        logger.error(f"Failed to get user context: {str(e)}")
        return {}

def _fallback_processing(intention: str, user_id: int) -> Dict[str, Any]:
    """Fallback processing when AI fails"""
    # Simple keyword-based extraction
    keywords = {
        'daily': {'recurring': {'frequency': 'daily'}},
        'weekly': {'recurring': {'frequency': 'weekly'}},
        'urgent': {'priority': 4},
        'important': {'priority': 3}
    }
    
    task_data = {
        'title': intention[:100],  # Truncate to title length
        'description': intention,
        'priority': 2,  # Default medium priority
        'category': 'personal'
    }
    
    # Check for keywords
    intention_lower = intention.lower()
    for keyword, attributes in keywords.items():
        if keyword in intention_lower:
            task_data.update(attributes)
    
    return {
        'tasks': [task_data],
        'insights': {'fallback_used': True},
        'confidence': 0.3
    }

def _create_task_from_ai_data(task_data: Dict[str, Any], user_id: int) -> Task:
    """Create task instance from AI-processed data"""
    # Get or create project
    project_name = task_data.get('project', 'Inbox')
    project, _ = Project.objects.get_or_create(
        user_id=user_id,
        name=project_name,
        defaults={'color': '#808080'}
    )
    
    # Get or create section
    section = None
    if task_data.get('section'):
        section, _ = Section.objects.get_or_create(
            project=project,
            name=task_data['section']
        )
    
    # Create task
    return Task.objects.create(
        user_id=user_id,
        project=project,
        section=section,
        title=task_data['title'],
        description=task_data.get('description', ''),
        priority=task_data.get('priority', 2),
        due_date=task_data.get('due_date'),
        labels=task_data.get('labels', []),
        estimated_duration=task_data.get('duration'),
        ai_generated=True,
        ai_confidence=task_data.get('confidence', 1.0)
    )

def _get_preferred_categories(user_id: int) -> List[str]:
    """Get user's most used categories"""
    # Implementation depends on your category tracking
    return ['work', 'personal', 'health']

def _get_typical_priority(user_id: int) -> int:
    """Get user's typical priority level"""
    return 2  # Default medium

def _get_user_timezone(user_id: int) -> str:
    """Get user's timezone"""
    return 'UTC'  # Default, should get from user profile


@shared_task
def analyze_user_patterns(
    user_id: int,
    analysis_type: str = 'full',
    focus_area: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze user's task patterns for insights.

    Args:
        user_id: User identifier
        analysis_type: Type of analysis (full, quick, specific)
        focus_area: Optional focus area (time, category, productivity)

    Returns:
        Dict containing pattern analysis results
    """
    try:
        logger.info(f"Analyzing patterns for user {user_id}, type: {analysis_type}")

        # Get user's recent tasks
        thirty_days_ago = timezone.now() - timedelta(days=30)
        tasks = Task.objects.filter(
            created_at__gte=thirty_days_ago
        )

        # Basic pattern analysis
        patterns = {
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(completed=True).count(),
            'analysis_type': analysis_type,
            'focus_area': focus_area,
            'patterns_found': [],
            'recommendations': [
                'Consider scheduling high-priority tasks in the morning',
                'Break large tasks into smaller subtasks'
            ]
        }

        # Store results
        cache_key = f"user_patterns:{user_id}"
        cache.set(cache_key, patterns, 3600)  # Cache for 1 hour

        return patterns

    except Exception as e:
        logger.error(f"Failed to analyze patterns: {str(e)}")
        return {'error': str(e), 'patterns_found': []}