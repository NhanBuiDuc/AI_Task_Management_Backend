# File: tasks_api/consumers.py

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, Any, Optional, List
import json
import logging
import asyncio
from datetime import datetime, timedelta

from .models import Task, Project, User
from .serializers import TaskSerializer, ProjectSerializer
from .utils.notifications import NotificationService, NotificationPreferences
from .agents.task_agent import TaskAgent

logger = logging.getLogger(__name__)

class TaskManagementConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time task management features.
    Handles live updates, collaborative features, and AI streaming.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.user_groups = []
        self.session_id = None
        self.ai_agent = None
        self.active_subscriptions = set()
        
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Get user from scope
            self.user = self.scope.get("user")
            
            if not self.user or not self.user.is_authenticated:
                await self.close(code=4001, reason="Authentication required")
                return
            
            self.user_id = self.user.id
            self.session_id = f"ws_{self.user_id}_{timezone.now().timestamp()}"
            
            # Accept connection
            await self.accept()
            
            # Add user to personal channel
            self.user_groups.append(f"user_{self.user_id}")
            await self.channel_layer.group_add(
                f"user_{self.user_id}",
                self.channel_name
            )
            
            # Add to active connections tracking
            await self._track_connection("connect")
            
            # Send connection success
            await self.send_json({
                "type": "connection.established",
                "session_id": self.session_id,
                "timestamp": timezone.now().isoformat()
            })
            
            # Send offline notifications if any
            await self._send_offline_notifications()
            
            logger.info(f"WebSocket connected for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close(code=4002, reason="Connection error")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            if self.user_id:
                # Remove from all groups
                for group in self.user_groups:
                    await self.channel_layer.group_discard(
                        group,
                        self.channel_name
                    )
                
                # Update connection tracking
                await self._track_connection("disconnect")
                
                # Clean up subscriptions
                await self._cleanup_subscriptions()
                
                logger.info(f"WebSocket disconnected for user {self.user_id}")
                
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {str(e)}")
    
    async def receive_json(self, content, **kwargs):
        """
        Handle incoming WebSocket messages.
        
        Args:
            content: JSON message from client
        """
        try:
            message_type = content.get("type")
            data = content.get("data", {})
            
            # Route to appropriate handler
            handlers = {
                "subscribe": self.handle_subscribe,
                "unsubscribe": self.handle_unsubscribe,
                "task.create": self.handle_task_create,
                "task.update": self.handle_task_update,
                "task.delete": self.handle_task_delete,
                "ai.process": self.handle_ai_process,
                "ai.stream": self.handle_ai_stream,
                "collaboration.join": self.handle_collaboration_join,
                "collaboration.leave": self.handle_collaboration_leave,
                "presence.update": self.handle_presence_update,
                "ping": self.handle_ping
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self.send_error(
                    f"Unknown message type: {message_type}",
                    request_id=content.get("id")
                )
                
        except Exception as e:
            logger.error(f"WebSocket receive error: {str(e)}")
            await self.send_error(
                "Message processing error",
                request_id=content.get("id")
            )
    
    async def handle_subscribe(self, data: Dict[str, Any]) -> None:
        """
        Handle subscription requests.
        
        Args:
            data: Subscription data
        """
        subscription_type = data.get("subscription_type")
        target_id = data.get("target_id")
        
        if subscription_type == "project":
            # Subscribe to project updates
            project_id = target_id
            if await self._user_has_project_access(project_id):
                group_name = f"project_{project_id}"
                self.user_groups.append(group_name)
                await self.channel_layer.group_add(
                    group_name,
                    self.channel_name
                )
                self.active_subscriptions.add(f"project:{project_id}")
                
                await self.send_json({
                    "type": "subscription.confirmed",
                    "subscription": f"project:{project_id}"
                })
        
        elif subscription_type == "workspace":
            # Subscribe to workspace updates
            workspace_id = target_id
            if await self._user_has_workspace_access(workspace_id):
                group_name = f"workspace_{workspace_id}"
                self.user_groups.append(group_name)
                await self.channel_layer.group_add(
                    group_name,
                    self.channel_name
                )
                self.active_subscriptions.add(f"workspace:{workspace_id}")
                
                await self.send_json({
                    "type": "subscription.confirmed",
                    "subscription": f"workspace:{workspace_id}"
                })
    
    async def handle_unsubscribe(self, data: Dict[str, Any]) -> None:
        """Handle unsubscribe requests"""
        subscription = data.get("subscription")
        
        if subscription in self.active_subscriptions:
            self.active_subscriptions.remove(subscription)
            
            # Parse subscription type and ID
            sub_type, sub_id = subscription.split(":")
            group_name = f"{sub_type}_{sub_id}"
            
            if group_name in self.user_groups:
                self.user_groups.remove(group_name)
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name
                )
            
            await self.send_json({
                "type": "subscription.removed",
                "subscription": subscription
            })
    
    async def handle_task_create(self, data: Dict[str, Any]) -> None:
        """
        Handle real-time task creation.
        
        Args:
            data: Task data
        """
        try:
            # Create task in database
            task = await self._create_task(data)
            
            # Broadcast to relevant groups
            await self._broadcast_task_update(
                task,
                "task.created",
                data.get("request_id")
            )
            
        except Exception as e:
            logger.error(f"Task creation error: {str(e)}")
            await self.send_error(
                "Failed to create task",
                request_id=data.get("request_id")
            )
    
    async def handle_task_update(self, data: Dict[str, Any]) -> None:
        """Handle real-time task updates"""
        try:
            task_id = data.get("task_id")
            updates = data.get("updates", {})
            
            # Update task
            task = await self._update_task(task_id, updates)
            
            # Broadcast update
            await self._broadcast_task_update(
                task,
                "task.updated",
                data.get("request_id")
            )
            
            # Handle collaborative editing
            if data.get("collaborative"):
                await self._handle_collaborative_edit(task, updates)
                
        except Exception as e:
            logger.error(f"Task update error: {str(e)}")
            await self.send_error(
                "Failed to update task",
                request_id=data.get("request_id")
            )
    
    async def handle_task_delete(self, data: Dict[str, Any]) -> None:
        """Handle real-time task deletion"""
        try:
            task_id = data.get("task_id")
            
            # Get task for broadcasting before deletion
            task = await self._get_task(task_id)
            
            # Delete task
            await self._delete_task(task_id)
            
            # Broadcast deletion
            await self._broadcast_task_update(
                task,
                "task.deleted",
                data.get("request_id")
            )
            
        except Exception as e:
            logger.error(f"Task deletion error: {str(e)}")
            await self.send_error(
                "Failed to delete task",
                request_id=data.get("request_id")
            )
    
    async def handle_ai_process(self, data: Dict[str, Any]) -> None:
        """
        Handle AI processing requests with streaming.
        
        Args:
            data: AI processing request data
        """
        try:
            intention = data.get("intention")
            stream = data.get("stream", False)
            request_id = data.get("request_id")
            
            # Send processing started notification
            await self.send_json({
                "type": "ai.processing.started",
                "request_id": request_id,
                "timestamp": timezone.now().isoformat()
            })
            
            if stream:
                # Process with streaming
                await self._stream_ai_response(intention, request_id)
            else:
                # Process normally
                result = await self._process_ai_intention(intention)
                
                await self.send_json({
                    "type": "ai.processing.completed",
                    "request_id": request_id,
                    "result": result,
                    "timestamp": timezone.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"AI processing error: {str(e)}")
            await self.send_json({
                "type": "ai.processing.failed",
                "request_id": request_id,
                "error": str(e),
                "timestamp": timezone.now().isoformat()
            })
    
    async def handle_ai_stream(self, data: Dict[str, Any]) -> None:
        """Handle streaming AI responses"""
        # Implementation for streaming AI responses
        # This would integrate with LangChain streaming callbacks
        pass
    
    async def handle_collaboration_join(self, data: Dict[str, Any]) -> None:
        """Handle joining collaborative session"""
        session_type = data.get("type")  # task, project, planning
        session_id = data.get("session_id")
        
        group_name = f"collab_{session_type}_{session_id}"
        self.user_groups.append(group_name)
        
        await self.channel_layer.group_add(
            group_name,
            self.channel_name
        )
        
        # Notify other collaborators
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "collaboration.user.joined",
                "user_id": self.user_id,
                "user_name": await self._get_user_name(),
                "timestamp": timezone.now().isoformat()
            }
        )
        
        # Send current collaborators list
        collaborators = await self._get_session_collaborators(
            session_type,
            session_id
        )
        
        await self.send_json({
            "type": "collaboration.joined",
            "session_id": f"{session_type}:{session_id}",
            "collaborators": collaborators
        })
    
    async def handle_collaboration_leave(self, data: Dict[str, Any]) -> None:
        """Handle leaving collaborative session"""
        session_type = data.get("type")
        session_id = data.get("session_id")
        
        group_name = f"collab_{session_type}_{session_id}"
        
        if group_name in self.user_groups:
            self.user_groups.remove(group_name)
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name
            )
            
            # Notify other collaborators
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "collaboration.user.left",
                    "user_id": self.user_id,
                    "user_name": await self._get_user_name(),
                    "timestamp": timezone.now().isoformat()
                }
            )
    
    async def handle_presence_update(self, data: Dict[str, Any]) -> None:
        """Handle user presence updates"""
        status = data.get("status")  # active, idle, away
        
        # Update presence in cache
        cache_key = f"user_presence:{self.user_id}"
        presence_data = {
            "status": status,
            "last_seen": timezone.now().isoformat(),
            "session_id": self.session_id
        }
        
        await database_sync_to_async(cache.set)(
            cache_key,
            presence_data,
            300  # 5 minute TTL
        )
        
        # Broadcast to relevant groups
        for group in self.user_groups:
            if group.startswith("collab_"):
                await self.channel_layer.group_send(
                    group,
                    {
                        "type": "presence.update",
                        "user_id": self.user_id,
                        "status": status,
                        "timestamp": timezone.now().isoformat()
                    }
                )
    
    async def handle_ping(self, data: Dict[str, Any]) -> None:
        """Handle ping for connection keep-alive"""
        await self.send_json({
            "type": "pong",
            "timestamp": timezone.now().isoformat()
        })
    
    # Channel layer message handlers
    async def notification_send(self, event: Dict[str, Any]) -> None:
        """Send notification to client"""
        await self.send_json({
            "type": "notification",
            "notification": event["notification"]
        })
    
    async def notification_batch(self, event: Dict[str, Any]) -> None:
        """Send batch notifications"""
        await self.send_json({
            "type": "notification.batch",
            "notifications": event["notifications"]
        })
    
    async def task_update(self, event: Dict[str, Any]) -> None:
        """Handle task update broadcasts"""
        await self.send_json(event)
    
    async def collaboration_user_joined(self, event: Dict[str, Any]) -> None:
        """Handle user joined collaboration"""
        await self.send_json({
            "type": "collaboration.user.joined",
            "user_id": event["user_id"],
            "user_name": event["user_name"],
            "timestamp": event["timestamp"]
        })
    
    async def collaboration_user_left(self, event: Dict[str, Any]) -> None:
        """Handle user left collaboration"""
        await self.send_json({
            "type": "collaboration.user.left",
            "user_id": event["user_id"],
            "user_name": event["user_name"],
            "timestamp": event["timestamp"]
        })
    
    async def presence_update(self, event: Dict[str, Any]) -> None:
        """Handle presence update broadcasts"""
        if event["user_id"] != self.user_id:  # Don't echo own presence
            await self.send_json({
                "type": "presence.update",
                "user_id": event["user_id"],
                "status": event["status"],
                "timestamp": event["timestamp"]
            })
    
    # Helper methods
    async def send_error(
        self,
        message: str,
        request_id: Optional[str] = None
    ) -> None:
        """Send error message to client"""
        await self.send_json({
            "type": "error",
            "message": message,
            "request_id": request_id,
            "timestamp": timezone.now().isoformat()
        })
    
    @database_sync_to_async
    def _create_task(self, data: Dict[str, Any]) -> Task:
        """Create task in database"""
        task = Task.objects.create(
            user_id=self.user_id,
            title=data["title"],
            description=data.get("description", ""),
            project_id=data.get("project_id"),
            section_id=data.get("section_id"),
            priority=data.get("priority", 2),
            due_date=data.get("due_date"),
            labels=data.get("labels", [])
        )
        return task
    
    @database_sync_to_async
    def _update_task(self, task_id: int, updates: Dict[str, Any]) -> Task:
        """Update task in database"""
        task = Task.objects.get(id=task_id, user_id=self.user_id)
        
        for field, value in updates.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        task.updated_at = timezone.now()
        task.save()
        
        return task
    
    @database_sync_to_async
    def _delete_task(self, task_id: int) -> None:
        """Delete task from database"""
        Task.objects.filter(
            id=task_id,
            user_id=self.user_id
        ).delete()
    
    @database_sync_to_async
    def _get_task(self, task_id: int) -> Task:
        """Get task from database"""
        return Task.objects.get(id=task_id, user_id=self.user_id)
    
    @database_sync_to_async
    def _user_has_project_access(self, project_id: int) -> bool:
        """Check if user has access to project"""
        return Project.objects.filter(
            id=project_id,
            user_id=self.user_id
        ).exists()
    
    @database_sync_to_async
    def _user_has_workspace_access(self, workspace_id: int) -> bool:
        """Check if user has access to workspace"""
        # Implement workspace access check
        return True
    
    @database_sync_to_async
    def _get_user_name(self) -> str:
        """Get user's display name"""
        return self.user.get_full_name() or self.user.username
    
    async def _broadcast_task_update(
        self,
        task: Task,
        update_type: str,
        request_id: Optional[str] = None
    ) -> None:
        """Broadcast task update to relevant groups"""
        task_data = await database_sync_to_async(
            lambda: TaskSerializer(task).data
        )()
        
        message = {
            "type": "task.update",
            "update_type": update_type,
            "task": task_data,
            "user_id": self.user_id,
            "request_id": request_id,
            "timestamp": timezone.now().isoformat()
        }
        
        # Send to user's personal channel
        await self.channel_layer.group_send(
            f"user_{self.user_id}",
            message
        )
        
        # Send to project channel if applicable
        if task.project_id:
            await self.channel_layer.group_send(
                f"project_{task.project_id}",
                message
            )
    
    async def _stream_ai_response(
        self,
        intention: str,
        request_id: str
    ) -> None:
        """Stream AI response in chunks"""
        try:
            # Initialize AI agent if not already
            if not self.ai_agent:
                self.ai_agent = TaskAgent()
            
            # Process with streaming callback
            async for chunk in self._process_ai_stream(intention):
                await self.send_json({
                    "type": "ai.stream.chunk",
                    "request_id": request_id,
                    "chunk": chunk,
                    "timestamp": timezone.now().isoformat()
                })
                
                # Small delay to prevent overwhelming client
                await asyncio.sleep(0.05)
            
            # Send completion
            await self.send_json({
                "type": "ai.stream.completed",
                "request_id": request_id,
                "timestamp": timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"AI streaming error: {str(e)}")
            await self.send_json({
                "type": "ai.stream.error",
                "request_id": request_id,
                "error": str(e),
                "timestamp": timezone.now().isoformat()
            })
    
    async def _process_ai_stream(self, intention: str):
        """Process AI intention with streaming"""
        # This would integrate with LangChain streaming
        # For now, simulate streaming
        chunks = [
            "Processing your request...",
            "Analyzing intention...",
            "Creating tasks...",
            "Done!"
        ]
        
        for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.5)
    
    @database_sync_to_async
    def _process_ai_intention(self, intention: str) -> Dict[str, Any]:
        """Process AI intention synchronously"""
        # This would call the actual AI processing
        return {
            "tasks_created": 0,
            "insights": {},
            "processing_time": 1.5
        }
    
    async def _handle_collaborative_edit(
        self,
        task: Task,
        updates: Dict[str, Any]
    ) -> None:
        """Handle collaborative editing features"""
        # Implement operational transform or CRDT logic
        pass
    
    async def _get_session_collaborators(
        self,
        session_type: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get current collaborators in session"""
        # Implementation to get active collaborators
        return []
    
    async def _track_connection(self, action: str) -> None:
        """Track WebSocket connections for monitoring"""
        try:
            redis_client = await self._get_redis_client()
            
            if action == "connect":
                await redis_client.sadd(f"ws:active:{self.user_id}", self.session_id)
                await redis_client.incr("ws:total_connections")
            else:
                await redis_client.srem(f"ws:active:{self.user_id}", self.session_id)
                await redis_client.decr("ws:total_connections")
                
        except Exception as e:
            logger.error(f"Connection tracking error: {str(e)}")
    
    async def _send_offline_notifications(self) -> None:
        """Send any offline notifications to user"""
        notifications = await database_sync_to_async(
            NotificationService.get_offline_notifications
        )(self.user_id)
        
        if notifications:
            await self.send_json({
                "type": "notification.offline",
                "notifications": notifications
            })
    
    async def _cleanup_subscriptions(self) -> None:
        """Clean up active subscriptions on disconnect"""
        # Implementation for subscription cleanup
        pass
    
    async def _get_redis_client(self):
        """Get Redis client for real-time features"""
        # Implementation to get Redis client
        pass

class CollaborativePlanningConsumer(AsyncJsonWebsocketConsumer):
    """
    Specialized consumer for collaborative planning sessions.
    Supports real-time brainstorming, voting, and task distribution.
    """
    
    async def connect(self):
        """Handle connection to planning session"""
        # Implementation for collaborative planning
        pass
    
    async def receive_json(self, content, **kwargs):
        """Handle planning-specific messages"""
        # Implementation for planning features
        pass

class DashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer for real-time dashboard updates.
    Streams analytics, metrics, and activity feeds.
    """
    
    async def connect(self):
        """Handle dashboard connection"""
        # Implementation for dashboard streaming
        pass
    
    async def receive_json(self, content, **kwargs):
        """Handle dashboard-specific requests"""
        # Implementation for dashboard features
        pass