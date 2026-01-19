# File: tasks_api/utils/analytics.py

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Avg, Sum, Q, F
from dataclasses import dataclass, asdict
import json
import logging
from collections import defaultdict
import redis
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_type: str
    user_id: int
    data: Dict[str, Any]
    timestamp: datetime = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = timezone.now()

class AnalyticsTracker:
    """
    Central analytics tracking for user behavior, AI performance, and system metrics.
    """
    
    # Redis connection for real-time metrics
    _redis_client = None
    
    @classmethod
    def _get_redis(cls) -> redis.Redis:
        """Get Redis client for analytics"""
        if not cls._redis_client:
            cls._redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=2,  # Separate DB for analytics
                decode_responses=True
            )
        return cls._redis_client
    
    @classmethod
    def track_event(cls, event: AnalyticsEvent) -> None:
        """
        Track generic analytics event.
        
        Args:
            event: AnalyticsEvent object
        """
        try:
            # Store in Redis for real-time processing
            redis_client = cls._get_redis()
            
            # Create event key
            event_key = f"analytics:{event.event_type}:{event.user_id}:{event.timestamp.timestamp()}"
            
            # Store event data
            redis_client.setex(
                event_key,
                86400,  # 24 hour TTL
                json.dumps({
                    'event_type': event.event_type,
                    'user_id': event.user_id,
                    'data': event.data,
                    'timestamp': event.timestamp.isoformat(),
                    'session_id': event.session_id
                })
            )
            
            # Update counters
            cls._update_counters(event)
            
            # Queue for batch processing
            redis_client.lpush('analytics_queue', event_key)
            
        except Exception as e:
            logger.error(f"Failed to track event: {str(e)}")
    
    @classmethod
    def track_ai_processing(
        cls,
        user_id: int,
        task_count: int,
        processing_time: float,
        success: bool = True,
        model_used: str = "ollama",
        confidence: float = 1.0
    ) -> None:
        """
        Track AI processing metrics.
        
        Args:
            user_id: User identifier
            task_count: Number of tasks created
            processing_time: Time taken in seconds
            success: Whether processing succeeded
            model_used: AI model used
            confidence: AI confidence score
        """
        event = AnalyticsEvent(
            event_type='ai_processing',
            user_id=user_id,
            data={
                'task_count': task_count,
                'processing_time': processing_time,
                'success': success,
                'model_used': model_used,
                'confidence': confidence,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        cls.track_event(event)
        
        # Update AI performance metrics
        cls._update_ai_metrics(user_id, processing_time, success, confidence)
    
    @classmethod
    def track_task_activity(
        cls,
        user_id: int,
        action: str,  # created, completed, updated, deleted
        task_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track task-related activities.
        
        Args:
            user_id: User identifier
            action: Type of action performed
            task_id: Task identifier
            metadata: Additional context
        """
        event = AnalyticsEvent(
            event_type='task_activity',
            user_id=user_id,
            data={
                'action': action,
                'task_id': task_id,
                'metadata': metadata or {},
                'timestamp': timezone.now().isoformat()
            }
        )
        
        cls.track_event(event)
        
        # Update user activity score
        cls._update_user_activity(user_id, action)
    
    @classmethod
    def get_user_analytics(
        cls,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a user.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dictionary containing user analytics
        """
        try:
            from ..models import Task
            
            start_date = timezone.now() - timedelta(days=days)
            
            # Task statistics
            task_stats = Task.objects.filter(
                user_id=user_id,
                created_at__gte=start_date
            ).aggregate(
                total_tasks=Count('id'),
                completed_tasks=Count('id', filter=Q(is_completed=True)),
                avg_completion_time=Avg(
                    F('completed_at') - F('created_at'),
                    filter=Q(is_completed=True)
                ),
                overdue_tasks=Count(
                    'id',
                    filter=Q(due_date__lt=timezone.now(), is_completed=False)
                )
            )
            
            # Productivity metrics
            productivity_data = cls._calculate_productivity_metrics(user_id, days)
            
            # AI usage statistics
            ai_stats = cls._get_ai_usage_stats(user_id, days)
            
            # Activity patterns
            activity_patterns = cls._analyze_activity_patterns(user_id, days)
            
            # Project distribution
            project_distribution = cls._get_project_distribution(user_id)
            
            return {
                'user_id': user_id,
                'period_days': days,
                'task_statistics': task_stats,
                'productivity': productivity_data,
                'ai_usage': ai_stats,
                'activity_patterns': activity_patterns,
                'project_distribution': project_distribution,
                'insights': cls._generate_insights(
                    task_stats, productivity_data, ai_stats
                ),
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            return {}
    
    @classmethod
    def get_system_metrics(cls) -> Dict[str, Any]:
        """
        Get system-wide metrics for monitoring.
        
        Returns:
            Dictionary containing system metrics
        """
        try:
            redis_client = cls._get_redis()
            
            # Get real-time metrics from Redis
            metrics = {
                'active_users': redis_client.scard('active_users'),
                'ai_requests_per_minute': cls._get_rate('ai_requests', 60),
                'task_creation_rate': cls._get_rate('task_creations', 3600),
                'average_ai_processing_time': cls._get_average_metric(
                    'ai_processing_times', 3600
                ),
                'error_rate': cls._get_rate('errors', 3600),
                'cache_hit_rate': cls._get_cache_hit_rate(),
                'websocket_connections': redis_client.get('websocket_connections') or 0,
                'queue_size': redis_client.llen('analytics_queue'),
                'timestamp': timezone.now().isoformat()
            }
            
            # Add health status
            metrics['health_status'] = cls._calculate_health_status(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {'error': str(e)}
    
    @classmethod
    def generate_daily_report(cls, user_id: int) -> Dict[str, Any]:
        """
        Generate daily productivity report for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Daily report data
        """
        try:
            from ..models import Task
            
            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            
            # Today's progress
            today_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__date=today
            )
            
            completed_today = today_tasks.filter(
                is_completed=True,
                completed_at__date=today
            ).count()
            
            # Compare with yesterday
            yesterday_completed = Task.objects.filter(
                user_id=user_id,
                is_completed=True,
                completed_at__date=yesterday
            ).count()
            
            # Calculate trends
            completion_trend = 'improving' if completed_today > yesterday_completed else 'stable'
            
            # Get focus time
            focus_time = cls._calculate_focus_time(user_id, today)
            
            # Get achievements
            achievements = cls._check_daily_achievements(user_id)
            
            return {
                'date': today.isoformat(),
                'tasks_completed': completed_today,
                'tasks_created': today_tasks.count(),
                'completion_rate': (
                    completed_today / today_tasks.count() * 100
                    if today_tasks.count() > 0 else 0
                ),
                'trend': completion_trend,
                'focus_time_minutes': focus_time,
                'achievements': achievements,
                'top_categories': cls._get_top_categories(user_id, 1),
                'ai_assistance_used': cls._get_daily_ai_usage(user_id),
                'recommendations': cls._generate_daily_recommendations(
                    user_id, completed_today, focus_time
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to generate daily report: {str(e)}")
            return {}
    
    @classmethod
    def _update_counters(cls, event: AnalyticsEvent) -> None:
        """Update Redis counters for real-time metrics"""
        try:
            redis_client = cls._get_redis()
            
            # Update event type counter
            redis_client.hincrby(
                f"counters:{event.event_type}",
                event.timestamp.strftime('%Y-%m-%d-%H'),
                1
            )
            
            # Update user activity
            redis_client.zadd(
                'active_users',
                {str(event.user_id): event.timestamp.timestamp()}
            )
            
            # Update global counters
            redis_client.incr(f"global:{event.event_type}")
            
        except Exception as e:
            logger.error(f"Failed to update counters: {str(e)}")
    
    @classmethod
    def _update_ai_metrics(
        cls,
        user_id: int,
        processing_time: float,
        success: bool,
        confidence: float
    ) -> None:
        """Update AI-specific metrics"""
        try:
            redis_client = cls._get_redis()
            
            # Track processing times
            redis_client.lpush('ai_processing_times', processing_time)
            redis_client.ltrim('ai_processing_times', 0, 999)  # Keep last 1000
            
            # Track success rate
            if success:
                redis_client.incr('ai_success_count')
            else:
                redis_client.incr('ai_failure_count')
            
            # Track confidence scores
            redis_client.lpush('ai_confidence_scores', confidence)
            redis_client.ltrim('ai_confidence_scores', 0, 999)
            
            # Update user-specific AI metrics
            redis_client.hincrby(f"user_ai_usage:{user_id}", 'count', 1)
            redis_client.hincrbyfloat(
                f"user_ai_usage:{user_id}",
                'total_time',
                processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to update AI metrics: {str(e)}")
    
    @classmethod
    def _calculate_productivity_metrics(
        cls,
        user_id: int,
        days: int
    ) -> Dict[str, Any]:
        """Calculate detailed productivity metrics"""
        from ..models import Task
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Daily completion rates
        daily_rates = []
        for i in range(days):
            date = start_date.date() + timedelta(days=i)
            
            day_tasks = Task.objects.filter(
                user_id=user_id,
                created_at__date=date
            )
            
            completed = day_tasks.filter(is_completed=True).count()
            total = day_tasks.count()
            
            if total > 0:
                daily_rates.append(completed / total * 100)
        
        # Calculate statistics
        if daily_rates:
            return {
                'average_completion_rate': np.mean(daily_rates),
                'completion_rate_trend': cls._calculate_trend(daily_rates),
                'consistency_score': cls._calculate_consistency(daily_rates),
                'peak_productivity_day': cls._find_peak_day(user_id, days),
                'productivity_score': cls._calculate_productivity_score(
                    daily_rates
                )
            }
        
        return {'no_data': True}
    
    @classmethod
    def _get_ai_usage_stats(
        cls,
        user_id: int,
        days: int
    ) -> Dict[str, Any]:
        """Get AI usage statistics for user"""
        try:
            redis_client = cls._get_redis()
            
            # Get user AI usage
            usage_data = redis_client.hgetall(f"user_ai_usage:{user_id}")
            
            if usage_data:
                count = int(usage_data.get('count', 0))
                total_time = float(usage_data.get('total_time', 0))
                
                return {
                    'total_requests': count,
                    'average_processing_time': total_time / count if count > 0 else 0,
                    'requests_per_day': count / days if days > 0 else 0,
                    'ai_dependency_score': min(count / (days * 5), 1.0) * 100
                }
            
            return {'no_ai_usage': True}
            
        except Exception as e:
            logger.error(f"Failed to get AI usage stats: {str(e)}")
            return {}
    
    @classmethod
    def _analyze_activity_patterns(
        cls,
        user_id: int,
        days: int
    ) -> Dict[str, Any]:
        """Analyze user's activity patterns"""
        from ..models import Task
        
        # Get task creation times
        tasks = Task.objects.filter(
            user_id=user_id,
            created_at__gte=timezone.now() - timedelta(days=days)
        ).values_list('created_at', flat=True)
        
        if not tasks:
            return {'no_activity': True}
        
        # Analyze by hour of day
        hour_distribution = defaultdict(int)
        day_distribution = defaultdict(int)
        
        for task_time in tasks:
            hour_distribution[task_time.hour] += 1
            day_distribution[task_time.weekday()] += 1
        
        # Find peak hours
        peak_hours = sorted(
            hour_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Find most active days
        peak_days = sorted(
            day_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            'peak_hours': [h for h, _ in peak_hours],
            'peak_days': [cls._day_name(d) for d, _ in peak_days],
            'activity_distribution': dict(hour_distribution),
            'consistency': cls._calculate_activity_consistency(
                list(hour_distribution.values())
            )
        }
    
    @classmethod
    def _generate_insights(
        cls,
        task_stats: Dict[str, Any],
        productivity_data: Dict[str, Any],
        ai_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable insights from analytics"""
        insights = []
        
        # Task completion insights
        if task_stats.get('total_tasks', 0) > 0:
            completion_rate = (
                task_stats['completed_tasks'] / task_stats['total_tasks'] * 100
            )
            
            if completion_rate < 50:
                insights.append(
                    "Your task completion rate is below 50%. "
                    "Consider breaking down large tasks into smaller ones."
                )
            elif completion_rate > 80:
                insights.append(
                    "Excellent completion rate! You're staying on top of your tasks."
                )
        
        # Overdue task insights
        if task_stats.get('overdue_tasks', 0) > 5:
            insights.append(
                f"You have {task_stats['overdue_tasks']} overdue tasks. "
                "Consider reviewing and updating their priorities."
            )
        
        # AI usage insights
        if ai_stats.get('ai_dependency_score', 0) > 80:
            insights.append(
                "You're making great use of AI assistance! "
                "This is helping you stay organized."
            )
        
        # Productivity trend insights
        if productivity_data.get('completion_rate_trend') == 'improving':
            insights.append(
                "Your productivity is trending upward. Keep up the momentum!"
            )
        
        return insights
    
    @classmethod
    def _calculate_health_status(cls, metrics: Dict[str, Any]) -> str:
        """Calculate system health status"""
        issues = 0
        
        if metrics.get('error_rate', 0) > 5:
            issues += 2
        
        if metrics.get('average_ai_processing_time', 0) > 10:
            issues += 1
        
        if metrics.get('queue_size', 0) > 1000:
            issues += 1
        
        if issues == 0:
            return 'healthy'
        elif issues <= 2:
            return 'degraded'
        else:
            return 'unhealthy'
    
    @classmethod
    def _get_rate(cls, metric_name: str, window_seconds: int) -> float:
        """Calculate rate for a metric over time window"""
        try:
            redis_client = cls._get_redis()
            count = redis_client.get(f"rate:{metric_name}:{window_seconds}")
            return float(count or 0) / window_seconds
        except Exception:
            return 0.0
    
    @classmethod
    def _calculate_trend(cls, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear regression
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    @classmethod
    def _day_name(cls, day_num: int) -> str:
        """Convert day number to name"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                'Friday', 'Saturday', 'Sunday']
        return days[day_num]
    
    @classmethod
    def _calculate_consistency(cls, rates: List[float]) -> float:
        """Calculate consistency score from completion rates"""
        if not rates:
            return 0.0
        
        # Lower standard deviation = higher consistency
        std_dev = np.std(rates)
        return max(0, 100 - std_dev * 2)
    
    @classmethod
    def _calculate_productivity_score(cls, daily_rates: List[float]) -> float:
        """Calculate overall productivity score"""
        if not daily_rates:
            return 0.0
        
        # Weighted average with recent days having more weight
        weights = np.linspace(0.5, 1.0, len(daily_rates))
        return np.average(daily_rates, weights=weights)
    
    @classmethod
    def _get_cache_hit_rate(cls) -> float:
        """Calculate cache hit rate"""
        try:
            hits = cache.get('cache_hits', 0)
            misses = cache.get('cache_misses', 0)
            total = hits + misses
            return (hits / total * 100) if total > 0 else 0.0
        except Exception:
            return 0.0