# File: tasks_api/utils/notifications.py

from typing import List, Dict, Any, Optional
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Notification types for different events"""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_DELETED = "task_deleted"
    TASKS_BATCH_CREATED = "tasks_batch_created"
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"
    AI_PROCESSING_FAILED = "ai_processing_failed"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    REMINDER = "reminder"
    INSIGHT_GENERATED = "insight_generated"
    PRODUCTIVITY_UPDATE = "productivity_update"
    # Collaboration notification types
    COLLABORATION_STARTED = "collaboration_started"
    COLLABORATION_ENDED = "collaboration_ended"
    PROJECT_SHARED = "project_shared"
    PERMISSIONS_UPDATED = "permissions_updated"
    REMOVED_FROM_PROJECT = "removed_from_project"
    TASK_SHARED = "task_shared"
    INVITATION_ACCEPTED = "invitation_accepted"
    INVITATION_DECLINED = "invitation_declined"

@dataclass
class Notification:
    """Notification data structure"""
    type: NotificationType
    user_id: int
    data: Dict[str, Any]
    timestamp: str = None
    priority: str = "normal"  # low, normal, high, urgent
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = timezone.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['type'] = self.type.value
        return result

class NotificationService:
    """
    Service for handling real-time notifications via WebSockets and other channels.
    """
    
    @staticmethod
    def send_notification(notification: Notification) -> bool:
        """
        Send notification through appropriate channels.
        
        Args:
            notification: Notification object to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                logger.warning("Channel layer not configured")
                return False
            
            # Send via WebSocket to user's channel
            group_name = f"user_{notification.user_id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification.send",
                    "notification": notification.to_dict()
                }
            )
            
            # Store notification for offline users
            NotificationService._store_offline_notification(notification)
            
            # Send push notification if enabled
            if notification.priority in ["high", "urgent"]:
                NotificationService._send_push_notification(notification)
            
            # Log notification
            NotificationService._log_notification(notification)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    @staticmethod
    def notify_tasks_created(
        user_id: int,
        tasks: List[Any],
        session_id: Optional[str] = None
    ) -> None:
        """
        Notify user about newly created tasks.
        
        Args:
            user_id: User ID
            tasks: List of created task objects
            session_id: Optional session ID
        """
        try:
            from ..serializers import TaskSerializer
            
            notification = Notification(
                type=NotificationType.TASKS_BATCH_CREATED,
                user_id=user_id,
                session_id=session_id,
                data={
                    "count": len(tasks),
                    "tasks": TaskSerializer(tasks, many=True).data,
                    "message": f"{len(tasks)} task(s) created successfully"
                }
            )
            
            NotificationService.send_notification(notification)
            
            # Send individual notifications for high-priority tasks
            for task in tasks:
                if hasattr(task, 'priority') and task.priority >= 4:
                    NotificationService.notify_high_priority_task(user_id, task)
                    
        except Exception as e:
            logger.error(f"Failed to notify task creation: {str(e)}")
    
    @staticmethod
    def notify_processing_failure(
        user_id: int,
        error_message: str,
        session_id: Optional[str] = None
    ) -> None:
        """
        Notify user about AI processing failure.
        
        Args:
            user_id: User ID
            error_message: Error description
            session_id: Optional session ID
        """
        notification = Notification(
            type=NotificationType.AI_PROCESSING_FAILED,
            user_id=user_id,
            session_id=session_id,
            priority="high",
            data={
                "error": error_message,
                "message": "Failed to process your request. Please try again.",
                "suggestions": [
                    "Try rephrasing your input",
                    "Break down complex requests into simpler ones",
                    "Check if the service is available"
                ]
            }
        )
        
        NotificationService.send_notification(notification)
    
    @staticmethod
    def notify_achievements(
        user_id: int,
        achievements: List[str]
    ) -> None:
        """
        Notify user about unlocked achievements.
        
        Args:
            user_id: User ID
            achievements: List of achievement names
        """
        for achievement in achievements:
            notification = Notification(
                type=NotificationType.ACHIEVEMENT_UNLOCKED,
                user_id=user_id,
                priority="normal",
                data={
                    "achievement": achievement,
                    "message": f"Achievement Unlocked: {achievement}",
                    "icon": NotificationService._get_achievement_icon(achievement)
                }
            )
            
            NotificationService.send_notification(notification)
    
    @staticmethod
    def notify_ai_processing_started(
        user_id: int,
        session_id: Optional[str] = None,
        estimated_time: Optional[int] = None
    ) -> None:
        """
        Notify that AI processing has started.
        
        Args:
            user_id: User ID
            session_id: Optional session ID
            estimated_time: Estimated processing time in seconds
        """
        notification = Notification(
            type=NotificationType.AI_PROCESSING_STARTED,
            user_id=user_id,
            session_id=session_id,
            data={
                "message": "Processing your request...",
                "estimated_time": estimated_time or 5
            }
        )
        
        NotificationService.send_notification(notification)
    
    @staticmethod
    def notify_task_reminder(
        user_id: int,
        task: Any,
        reminder_type: str = "due_soon"
    ) -> None:
        """
        Send task reminder notification.
        
        Args:
            user_id: User ID
            task: Task object
            reminder_type: Type of reminder (due_soon, overdue, etc.)
        """
        from ..serializers import TaskSerializer
        
        messages = {
            "due_soon": f"Task '{task.title}' is due soon",
            "overdue": f"Task '{task.title}' is overdue",
            "scheduled": f"Time to work on '{task.title}'"
        }
        
        notification = Notification(
            type=NotificationType.REMINDER,
            user_id=user_id,
            priority="high" if reminder_type == "overdue" else "normal",
            data={
                "task": TaskSerializer(task).data,
                "reminder_type": reminder_type,
                "message": messages.get(reminder_type, f"Reminder: {task.title}")
            }
        )
        
        NotificationService.send_notification(notification)
    
    @staticmethod
    def notify_productivity_update(
        user_id: int,
        score: float,
        trend: str = "stable"
    ) -> None:
        """
        Notify user about productivity score update.
        
        Args:
            user_id: User ID
            score: New productivity score
            trend: Score trend (improving, declining, stable)
        """
        notification = Notification(
            type=NotificationType.PRODUCTIVITY_UPDATE,
            user_id=user_id,
            data={
                "score": round(score, 2),
                "trend": trend,
                "message": f"Your productivity score is {round(score, 2)}%",
                "emoji": NotificationService._get_productivity_emoji(score)
            }
        )
        
        NotificationService.send_notification(notification)
    
    @staticmethod
    def notify_high_priority_task(user_id: int, task: Any) -> None:
        """
        Special notification for high-priority tasks.
        
        Args:
            user_id: User ID
            task: High-priority task object
        """
        from ..serializers import TaskSerializer
        
        notification = Notification(
            type=NotificationType.TASK_CREATED,
            user_id=user_id,
            priority="high",
            data={
                "task": TaskSerializer(task).data,
                "message": f"High Priority: {task.title}",
                "action_required": True
            }
        )
        
        NotificationService.send_notification(notification)
    
    @staticmethod
    def batch_notify(notifications: List[Notification]) -> Dict[str, int]:
        """
        Send multiple notifications efficiently.
        
        Args:
            notifications: List of notifications to send
            
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0}
        
        # Group by user for efficiency
        user_notifications = {}
        for notification in notifications:
            if notification.user_id not in user_notifications:
                user_notifications[notification.user_id] = []
            user_notifications[notification.user_id].append(notification)
        
        # Send batched notifications
        for user_id, user_notifs in user_notifications.items():
            try:
                channel_layer = get_channel_layer()
                group_name = f"user_{user_id}"
                
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "notification.batch",
                        "notifications": [n.to_dict() for n in user_notifs]
                    }
                )
                
                results["success"] += len(user_notifs)
                
            except Exception as e:
                logger.error(f"Failed to batch notify user {user_id}: {str(e)}")
                results["failed"] += len(user_notifs)
        
        return results
    
    @staticmethod
    def _store_offline_notification(notification: Notification) -> None:
        """Store notification for offline users"""
        try:
            cache_key = f"offline_notifications:{notification.user_id}"
            notifications = cache.get(cache_key, [])
            
            # Limit stored notifications
            notifications.append(notification.to_dict())
            if len(notifications) > 50:
                notifications = notifications[-50:]
            
            # Store for 7 days
            cache.set(cache_key, notifications, 604800)
            
        except Exception as e:
            logger.error(f"Failed to store offline notification: {str(e)}")
    
    @staticmethod
    def get_offline_notifications(user_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve stored notifications for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of notification dictionaries
        """
        cache_key = f"offline_notifications:{user_id}"
        notifications = cache.get(cache_key, [])
        
        # Clear after retrieval
        cache.delete(cache_key)
        
        return notifications
    
    @staticmethod
    def _send_push_notification(notification: Notification) -> None:
        """Send push notification for mobile/desktop"""
        # Implement based on your push notification service
        # Example: Firebase, OneSignal, etc.
        pass
    
    @staticmethod
    def _log_notification(notification: Notification) -> None:
        """Log notification for analytics"""
        try:
            # Log to monitoring system
            logger.info(
                f"Notification sent",
                extra={
                    "user_id": notification.user_id,
                    "type": notification.type.value,
                    "priority": notification.priority,
                    "session_id": notification.session_id
                }
            )
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
    
    @staticmethod
    def _get_achievement_icon(achievement: str) -> str:
        """Get icon for achievement"""
        icons = {
            "First Step": "🎯",
            "Productive Week": "🔥",
            "Task Master": "👑",
            "Early Bird": "🌅",
            "Night Owl": "🦉"
        }
        return icons.get(achievement, "🏆")
    
    @staticmethod
    def _get_productivity_emoji(score: float) -> str:
        """Get emoji based on productivity score"""
        if score >= 90:
            return "🚀"
        elif score >= 70:
            return "💪"
        elif score >= 50:
            return "📈"
        else:
            return "💡"

class NotificationPreferences:
    """Manage user notification preferences"""
    
    @staticmethod
    def get_user_preferences(user_id: int) -> Dict[str, bool]:
        """Get user's notification preferences"""
        cache_key = f"notification_prefs:{user_id}"
        prefs = cache.get(cache_key)
        
        if not prefs:
            # Default preferences
            prefs = {
                "task_reminders": True,
                "achievements": True,
                "productivity_updates": True,
                "ai_processing": True,
                "push_notifications": False,
                "email_notifications": False
            }
            cache.set(cache_key, prefs, 86400)  # 24 hours
        
        return prefs
    
    @staticmethod
    def update_preferences(
        user_id: int,
        preferences: Dict[str, bool]
    ) -> None:
        """Update user's notification preferences"""
        cache_key = f"notification_prefs:{user_id}"
        current_prefs = NotificationPreferences.get_user_preferences(user_id)
        current_prefs.update(preferences)
        cache.set(cache_key, current_prefs, 86400)