# File: tasks_api/views_agent.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime, timedelta

from .models import Task, Project, Section, Account
from .serializers import TaskSerializer
from .agents.task_agent import (
    TaskAgent, AgentResponse, ResponseType, ActionType,
    TaskAction, TaskSuggestion
)
from .agents.intent_agent import IntentAgent
from .agents.intent_handlers import IntentHandlers
from .agents.intent_registry import get_intent_by_id, ActionType as IntentActionType
from .tasks import process_ai_intention, analyze_user_patterns
from .utils.analytics import AnalyticsTracker, AnalyticsEvent
from .utils.mongodb import InsightsRepository, TaskPatternsRepository
from .utils.notifications import NotificationService, Notification, NotificationType


def get_account_from_request(request):
    """Get account from X-Account-ID header."""
    account_id = request.headers.get('X-Account-ID')
    if not account_id:
        return None
    try:
        return Account.objects.get(id=account_id, is_active=True)
    except (Account.DoesNotExist, ValueError):
        return None


# =============================================================================
# NEW: Conversation-based Chat API
# =============================================================================

class AIChatView(APIView):
    """
    Conversation-based AI chat for task management.

    Supports:
    - Multi-turn conversations with context
    - CRUD operations via natural language (read, insert, update, delete, complete)
    - Task suggestions with approval workflow
    - Clarification requests for ambiguous input
    """
    permission_classes = [AllowAny]  # Uses X-Account-ID header

    # Singleton agent instance
    _agent = None

    @classmethod
    def get_agent(cls):
        """Get or create TaskAgent singleton."""
        if cls._agent is None:
            cls._agent = TaskAgent()
        return cls._agent

    def post(self, request):
        """
        POST /api/ai/chat/
        Send a message to the AI assistant.

        Body:
        {
            "message": "User's natural language input",
            "session_id": "optional-session-id-for-context"
        }

        Returns:
        {
            "type": "actions|clarify|suggest|chat",
            "message": "User-friendly response",
            "actions": [...],       // Database actions to execute
            "suggestions": [...],   // Tasks waiting for approval
            "clarify_options": [...], // Options for clarification
            "session_id": "session-id"
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')

        if not message:
            return Response(
                {'error': 'Message cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get user's tasks for context
            user_tasks = list(Task.objects.filter(
                user=account,
                totally_completed=False
            ).values('id', 'name', 'due_date', 'completed')[:20])

            # Process through agent
            agent = self.get_agent()
            response = agent.chat(
                user_input=message,
                session_id=session_id,
                user_tasks=user_tasks
            )

            # Execute actions if any
            action_results = []
            if response.type == ResponseType.ACTIONS and response.actions:
                action_results = self._execute_actions(account, response.actions)
                # Update message with results
                response.message = self._build_result_message(response.actions, action_results)

            # Track analytics
            try:
                AnalyticsTracker.track_event(AnalyticsEvent(
                    event_type='ai_chat_message',
                    user_id=account.id,
                    data={
                        'message_length': len(message),
                        'response_type': response.type.value,
                        'actions_count': len(response.actions),
                        'suggestions_count': len(response.suggestions)
                    }
                ))
            except Exception:
                pass  # Analytics failure shouldn't break the API

            return Response({
                'type': response.type.value,
                'message': response.message,
                'actions': [self._action_to_dict(a) for a in response.actions],
                'action_results': action_results,
                'suggestions': [self._suggestion_to_dict(s) for s in response.suggestions],
                'clarify_options': response.clarify_options,
                'session_id': response.context_key
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to process message: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _execute_actions(
        self,
        account: Account,
        actions: List[TaskAction]
    ) -> List[Dict]:
        """Execute database actions and return results."""
        results = []

        for action in actions:
            try:
                if action.action == ActionType.READ:
                    result = self._execute_read(account, action)
                elif action.action == ActionType.INSERT:
                    result = self._execute_insert(account, action)
                elif action.action == ActionType.UPDATE:
                    result = self._execute_update(account, action)
                elif action.action == ActionType.DELETE:
                    result = self._execute_delete(account, action)
                elif action.action == ActionType.COMPLETE:
                    result = self._execute_complete(account, action)
                else:
                    result = {'status': 'unknown_action'}

                results.append({
                    'action': action.action.value,
                    'success': True,
                    **result
                })

            except Exception as e:
                results.append({
                    'action': action.action.value,
                    'success': False,
                    'error': str(e)
                })

        return results

    def _execute_read(self, account: Account, action: TaskAction) -> Dict:
        """Execute read query."""
        tasks = Task.objects.filter(user=account, totally_completed=False)

        if action.query_filter == 'today':
            today = timezone.now().date()
            tasks = tasks.filter(due_date__date=today)
        elif action.query_filter == 'overdue':
            tasks = tasks.filter(due_date__lt=timezone.now(), completed=False)
        elif action.query_filter and action.query_filter not in ['all', 'today', 'overdue']:
            # Search by task name
            tasks = tasks.filter(name__icontains=action.query_filter)

        if action.query_type == 'count':
            return {'count': tasks.count()}
        elif action.query_type == 'due_date':
            task = tasks.first()
            if task:
                return {
                    'task_name': task.name,
                    'due_date': task.due_date.isoformat() if task.due_date else None
                }
            return {'task_name': None, 'due_date': None}
        else:  # list
            return {
                'tasks': list(tasks.values('id', 'name', 'due_date', 'completed')[:10]),
                'count': tasks.count()
            }

    def _execute_insert(self, account: Account, action: TaskAction) -> Dict:
        """Execute insert action."""
        task_data = {
            'user': account,
            'name': action.title or 'New Task',
            'description': action.description or '',
            'priority': self._map_priority(action.priority),
        }

        if action.due_date:
            try:
                task_data['due_date'] = datetime.strptime(action.due_date, '%Y-%m-%d')
            except ValueError:
                pass

        if action.duration:
            task_data['duration_in_minutes'] = action.duration

        task = Task.objects.create(**task_data)
        task.update_task_views()

        return {
            'task_id': str(task.id),
            'task_name': task.name
        }

    def _execute_update(self, account: Account, action: TaskAction) -> Dict:
        """Execute update action."""
        # Find task by ID or title
        if action.task_id:
            task = Task.objects.filter(id=action.task_id, user=account).first()
        elif action.title:
            task = Task.objects.filter(
                name__icontains=action.title,
                user=account,
                totally_completed=False
            ).first()
        else:
            return {'error': 'No task identifier provided'}

        if not task:
            return {'error': 'Task not found'}

        # Update fields
        updated_fields = []
        if action.title and action.task_id:  # Only update title if task found by ID
            task.name = action.title
            updated_fields.append('name')

        if action.due_date:
            try:
                task.due_date = datetime.strptime(action.due_date, '%Y-%m-%d')
                updated_fields.append('due_date')
            except ValueError:
                pass

        if action.priority is not None:
            task.priority = self._map_priority(action.priority)
            updated_fields.append('priority')

        if action.description is not None:
            task.description = action.description
            updated_fields.append('description')

        task.save()
        task.update_task_views()

        return {
            'task_id': str(task.id),
            'task_name': task.name,
            'updated_fields': updated_fields
        }

    def _execute_delete(self, account: Account, action: TaskAction) -> Dict:
        """Execute delete action."""
        if action.task_id:
            task = Task.objects.filter(id=action.task_id, user=account).first()
        elif action.title:
            task = Task.objects.filter(
                name__icontains=action.title,
                user=account,
                totally_completed=False
            ).first()
        else:
            return {'error': 'No task identifier provided'}

        if not task:
            return {'error': 'Task not found'}

        task_name = task.name
        task.delete()

        return {
            'deleted_task': task_name
        }

    def _execute_complete(self, account: Account, action: TaskAction) -> Dict:
        """Execute complete action."""
        if action.task_id:
            task = Task.objects.filter(id=action.task_id, user=account).first()
        elif action.title:
            task = Task.objects.filter(
                name__icontains=action.title,
                user=account,
                totally_completed=False
            ).first()
        else:
            return {'error': 'No task identifier provided'}

        if not task:
            return {'error': 'Task not found'}

        task.completed = True
        task.completed_date = timezone.now()
        task.save()

        return {
            'task_id': str(task.id),
            'task_name': task.name,
            'completed': True
        }

    def _map_priority(self, priority: Optional[int]) -> str:
        """Map numeric priority to string."""
        if priority is None:
            return 'medium'
        mapping = {1: 'low', 2: 'low', 3: 'medium', 4: 'high', 5: 'urgent'}
        return mapping.get(priority, 'medium')

    def _build_result_message(
        self,
        actions: List[TaskAction],
        results: List[Dict]
    ) -> str:
        """Build user-friendly message from action results."""
        parts = []

        for action, result in zip(actions, results):
            if not result.get('success'):
                parts.append(f"Failed: {result.get('error', 'Unknown error')}")
                continue

            if action.action == ActionType.READ:
                if 'count' in result:
                    parts.append(f"You have {result['count']} tasks")
                elif result.get('due_date'):
                    parts.append(f"{result.get('task_name')} is due {result['due_date']}")
            elif action.action == ActionType.INSERT:
                parts.append(f"Added '{result.get('task_name')}'")
            elif action.action == ActionType.UPDATE:
                parts.append(f"Updated '{result.get('task_name')}'")
            elif action.action == ActionType.DELETE:
                parts.append(f"Deleted '{result.get('deleted_task')}'")
            elif action.action == ActionType.COMPLETE:
                parts.append(f"Marked '{result.get('task_name')}' as done")

        return '. '.join(parts) if parts else 'Done.'

    def _action_to_dict(self, action: TaskAction) -> Dict:
        """Convert TaskAction to dict."""
        return {
            'action': action.action.value,
            'task_id': action.task_id,
            'title': action.title,
            'description': action.description,
            'category': action.category,
            'priority': action.priority,
            'due_date': action.due_date,
            'due_time': action.due_time,
            'duration': action.duration,
            'frequency': action.frequency,
            'query_type': action.query_type,
            'query_filter': action.query_filter
        }

    def _suggestion_to_dict(self, suggestion: TaskSuggestion) -> Dict:
        """Convert TaskSuggestion to dict."""
        return {
            'id': suggestion.id,
            'title': suggestion.title,
            'description': suggestion.description,
            'category': suggestion.category,
            'priority': suggestion.priority,
            'due_date': suggestion.due_date,
            'duration': suggestion.duration,
            'frequency': suggestion.frequency,
            'reason': suggestion.reason
        }


class AISuggestionsManageView(APIView):
    """
    Manage pending task suggestions from AI conversations.
    """
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        """
        GET /api/ai/suggestions/<session_id>/
        Get pending suggestions for a session.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        agent = AIChatView.get_agent()
        suggestions = agent.get_pending_suggestions(session_id)

        return Response({
            'suggestions': [
                {
                    'id': s.id,
                    'title': s.title,
                    'description': s.description,
                    'category': s.category,
                    'priority': s.priority,
                    'due_date': s.due_date,
                    'duration': s.duration,
                    'frequency': s.frequency,
                    'reason': s.reason
                }
                for s in suggestions
            ],
            'count': len(suggestions)
        })

    def post(self, request, session_id):
        """
        POST /api/ai/suggestions/<session_id>/
        Accept, modify, or reject suggestions.

        Body:
        {
            "action": "accept_all" | "reject_all" | "accept" | "modify",
            "suggestion_id": "id" (for accept/modify),
            "modifications": {...} (for modify)
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        action = request.data.get('action')
        suggestion_id = request.data.get('suggestion_id')
        modifications = request.data.get('modifications', {})

        agent = AIChatView.get_agent()

        if action == 'accept_all':
            suggestions = agent.get_pending_suggestions(session_id)
            created_tasks = []

            for sug in suggestions:
                task = Task.objects.create(
                    user=account,
                    name=sug.title,
                    description=sug.description or '',
                    priority=self._map_priority(sug.priority)
                )
                task.update_task_views()
                created_tasks.append(task)

            agent.clear_suggestions(session_id)

            return Response({
                'message': f'Created {len(created_tasks)} tasks',
                'tasks': TaskSerializer(created_tasks, many=True).data
            }, status=status.HTTP_201_CREATED)

        elif action == 'reject_all':
            agent.clear_suggestions(session_id)
            return Response({'message': 'All suggestions rejected'})

        elif action == 'accept' and suggestion_id:
            task_action = agent.accept_suggestion(session_id, suggestion_id)
            if not task_action:
                return Response(
                    {'error': 'Suggestion not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create the task
            task = Task.objects.create(
                user=account,
                name=task_action.title or 'Task',
                description=task_action.description or '',
                priority=self._map_priority(task_action.priority)
            )
            task.update_task_views()

            return Response({
                'message': f'Created task: {task.name}',
                'task': TaskSerializer(task).data
            }, status=status.HTTP_201_CREATED)

        elif action == 'modify' and suggestion_id:
            modified = agent.modify_suggestion(session_id, suggestion_id, modifications)
            if not modified:
                return Response(
                    {'error': 'Suggestion not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                'message': 'Suggestion modified',
                'suggestion': {
                    'id': modified.id,
                    'title': modified.title,
                    'description': modified.description,
                    'category': modified.category,
                    'priority': modified.priority,
                    'due_date': modified.due_date,
                    'duration': modified.duration
                }
            })

        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def _map_priority(self, priority: Optional[int]) -> str:
        """Map numeric priority to string."""
        if priority is None:
            return 'medium'
        mapping = {1: 'low', 2: 'low', 3: 'medium', 4: 'high', 5: 'urgent'}
        return mapping.get(priority, 'medium')


class AIChatHistoryView(APIView):
    """
    Get conversation history for a session.
    """
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        """
        GET /api/ai/chat/<session_id>/history/
        Get conversation history.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        agent = AIChatView.get_agent()
        messages = agent.get_session_history(session_id)

        return Response({
            'messages': [
                {
                    'role': m.role,
                    'content': m.content,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in messages
            ],
            'count': len(messages)
        })

    def delete(self, request, session_id):
        """
        DELETE /api/ai/chat/<session_id>/history/
        Clear conversation history.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        agent = AIChatView.get_agent()
        agent.clear_session(session_id)

        return Response({'message': 'Session cleared'})

class AIIntentionView(APIView):
    """
    Process natural language intentions into structured tasks.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/ai/process/
        Process natural language intention.
        """
        try:
            user_id = request.user.id
            intention = request.data.get('intention', '').strip()
            mode = request.data.get('mode', 'create')  # create, suggest, plan
            context = request.data.get('context', {})
            
            if not intention:
                return Response(
                    {'error': 'Intention cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Send processing started notification
            NotificationService.notify_ai_processing_started(
                user_id=user_id,
                session_id=context.get('session_id'),
                estimated_time=5
            )
            
            if mode == 'create':
                # Queue task creation
                task = process_ai_intention.delay(
                    intention=intention,
                    user_id=user_id,
                    session_id=context.get('session_id'),
                    metadata=context
                )
                
                return Response({
                    'task_id': str(task.id),
                    'status': 'processing',
                    'message': 'AI is processing your request'
                }, status=status.HTTP_202_ACCEPTED)
                
            elif mode == 'suggest':
                # Generate suggestions without creating
                suggestions = self._generate_suggestions(intention, user_id, context)
                return Response({
                    'suggestions': suggestions,
                    'status': 'completed'
                })
                
            elif mode == 'plan':
                # Generate a full plan
                plan = self._generate_plan(intention, user_id, context)
                return Response({
                    'plan': plan,
                    'status': 'completed'
                })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to process intention: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_suggestions(
        self,
        intention: str,
        user_id: int,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate task suggestions without creating them"""
        agent = TaskAgent()
        
        # Get user context for personalization
        user_patterns = TaskPatternsRepository.get_user_patterns(user_id)
        recent_tasks = Task.objects.filter(
            user_id=user_id
        ).order_by('-created_at')[:10]
        
        # Generate suggestions
        suggestions = agent.generate_suggestions(
            intention=intention,
            user_context={
                'patterns': user_patterns,
                'recent_tasks': [t.title for t in recent_tasks],
                'preferences': context.get('preferences', {})
            }
        )
        
        # Enhance suggestions with metadata
        enhanced_suggestions = []
        for idx, suggestion in enumerate(suggestions):
            enhanced_suggestions.append({
                'id': str(uuid.uuid4()),
                'title': suggestion.get('title', ''),
                'description': suggestion.get('description', ''),
                'priority': suggestion.get('priority', 2),
                'estimated_duration': suggestion.get('duration', 30),
                'category': suggestion.get('category', 'general'),
                'tags': suggestion.get('tags', []),
                'project_suggestion': suggestion.get('project', 'Inbox'),
                'confidence': suggestion.get('confidence', 0.8),
                'reasoning': suggestion.get('reasoning', ''),
                'order': idx
            })
        
        return enhanced_suggestions
    
    def _generate_plan(
        self,
        intention: str,
        user_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive plan with phases and milestones"""
        agent = TaskAgent()
        
        # Generate structured plan
        plan_data = agent.generate_plan(
            intention=intention,
            timeline=context.get('timeline', 'flexible'),
            complexity=context.get('complexity', 'medium')
        )
        
        # Structure the plan
        plan = {
            'title': plan_data.get('title', 'Generated Plan'),
            'description': plan_data.get('description', ''),
            'phases': [],
            'estimated_total_duration': 0,
            'suggested_start_date': timezone.now().date().isoformat(),
            'milestones': []
        }
        
        # Process phases
        for phase_data in plan_data.get('phases', []):
            phase = {
                'id': str(uuid.uuid4()),
                'name': phase_data.get('name', ''),
                'description': phase_data.get('description', ''),
                'tasks': [],
                'duration_days': phase_data.get('duration_days', 7),
                'order': phase_data.get('order', 0)
            }
            
            # Add tasks to phase
            for task_data in phase_data.get('tasks', []):
                task = {
                    'id': str(uuid.uuid4()),
                    'title': task_data.get('title', ''),
                    'description': task_data.get('description', ''),
                    'priority': task_data.get('priority', 2),
                    'estimated_duration': task_data.get('duration', 60),
                    'dependencies': task_data.get('dependencies', []),
                    'tags': task_data.get('tags', [])
                }
                phase['tasks'].append(task)
            
            plan['phases'].append(phase)
            plan['estimated_total_duration'] += phase['duration_days']
        
        # Add milestones
        for milestone_data in plan_data.get('milestones', []):
            milestone = {
                'id': str(uuid.uuid4()),
                'title': milestone_data.get('title', ''),
                'target_date': milestone_data.get('date', ''),
                'phase_id': milestone_data.get('phase_id', '')
            }
            plan['milestones'].append(milestone)
        
        return plan

class AISuggestionsView(APIView):
    """
    Generate AI-powered task suggestions for drag & drop interface.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/ai/suggestions/
        Generate draggable task suggestions from natural language.
        """
        try:
            user_id = request.user.id
            intention = request.data.get('intention', '').strip()
            suggestion_count = request.data.get('count', 5)
            include_variants = request.data.get('include_variants', True)
            context_type = request.data.get('context_type', 'general')  # general, work, personal
            
            if not intention:
                return Response(
                    {'error': 'Please provide what you want to do'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize AI agent
            agent = TaskAgent()
            
            # Get user patterns for personalization
            user_patterns = self._get_user_patterns(user_id)
            
            # Generate base suggestions
            suggestions = agent.generate_task_suggestions(
                intention=intention,
                count=suggestion_count,
                context={
                    'type': context_type,
                    'user_patterns': user_patterns,
                    'time_of_day': timezone.now().hour,
                    'day_of_week': timezone.now().weekday()
                }
            )
            
            # Enhance suggestions with variants if requested
            enhanced_suggestions = []
            for suggestion in suggestions:
                base_suggestion = {
                    'id': str(uuid.uuid4()),
                    'title': suggestion['title'],
                    'description': suggestion.get('description', ''),
                    'category': suggestion.get('category', 'general'),
                    'priority': suggestion.get('priority', 2),
                    'estimated_minutes': suggestion.get('duration', 30),
                    'tags': suggestion.get('tags', []),
                    'recurring': suggestion.get('recurring', None),
                    'project_suggestion': suggestion.get('project', None),
                    'confidence': suggestion.get('confidence', 0.85),
                    'type': 'base',
                    'group_id': str(uuid.uuid4())
                }
                enhanced_suggestions.append(base_suggestion)
                
                # Add variants if requested
                if include_variants and suggestion.get('variants'):
                    for variant in suggestion['variants']:
                        variant_suggestion = {
                            **base_suggestion,
                            'id': str(uuid.uuid4()),
                            'title': variant['title'],
                            'estimated_minutes': variant.get('duration', base_suggestion['estimated_minutes']),
                            'priority': variant.get('priority', base_suggestion['priority']),
                            'type': 'variant',
                            'variant_type': variant.get('type', 'alternative')  # alternative, breakdown, simplified
                        }
                        enhanced_suggestions.append(variant_suggestion)
            
            # Group suggestions by category
            grouped_suggestions = self._group_suggestions(enhanced_suggestions)
            
            # Generate smart insights
            insights = self._generate_suggestion_insights(
                intention,
                enhanced_suggestions,
                user_patterns
            )
            
            # Track analytics
            try:
                AnalyticsTracker.track_event(AnalyticsEvent(
                    event_type='ai_suggestions_generated',
                    user_id=user_id,
                    data={
                        'intention_length': len(intention),
                        'suggestions_count': len(enhanced_suggestions),
                        'context_type': context_type
                    }
                ))
            except Exception:
                pass
            
            return Response({
                'suggestions': grouped_suggestions,
                'total_count': len(enhanced_suggestions),
                'insights': insights,
                'metadata': {
                    'generated_at': timezone.now().isoformat(),
                    'context_type': context_type,
                    'ai_model': 'ollama-local'
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate suggestions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """
        PUT /api/ai/suggestions/
        Refine suggestions based on user feedback.
        """
        try:
            user_id = request.user.id
            original_intention = request.data.get('original_intention')
            feedback = request.data.get('feedback', {})
            selected_ids = request.data.get('selected_ids', [])
            rejected_ids = request.data.get('rejected_ids', [])
            refinement_prompt = request.data.get('refinement_prompt', '')
            
            # Initialize agent
            agent = TaskAgent()
            
            # Learn from feedback
            feedback_context = {
                'selected_suggestions': selected_ids,
                'rejected_suggestions': rejected_ids,
                'user_notes': feedback.get('notes', ''),
                'preferred_categories': feedback.get('preferred_categories', []),
                'time_constraints': feedback.get('time_constraints', {})
            }
            
            # Generate refined suggestions
            refined_suggestions = agent.refine_suggestions(
                original_intention=original_intention,
                refinement_prompt=refinement_prompt,
                feedback_context=feedback_context
            )
            
            # Format refined suggestions
            formatted_suggestions = []
            for suggestion in refined_suggestions:
                formatted_suggestions.append({
                    'id': str(uuid.uuid4()),
                    'title': suggestion['title'],
                    'description': suggestion.get('description', ''),
                    'category': suggestion.get('category', 'general'),
                    'priority': suggestion.get('priority', 2),
                    'estimated_minutes': suggestion.get('duration', 30),
                    'tags': suggestion.get('tags', []),
                    'improvement_reason': suggestion.get('improvement_reason', ''),
                    'confidence': suggestion.get('confidence', 0.9)
                })
            
            # Store feedback for future improvements
            self._store_suggestion_feedback(
                user_id,
                original_intention,
                feedback_context
            )
            
            return Response({
                'refined_suggestions': formatted_suggestions,
                'count': len(formatted_suggestions),
                'refinement_applied': True
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to refine suggestions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_patterns(self, user_id: int) -> Dict[str, Any]:
        """Get user's task patterns for personalization"""
        patterns = TaskPatternsRepository.get_user_patterns(user_id)
        
        # Extract relevant patterns
        return {
            'common_durations': [p for p in patterns if p['pattern_type'] == 'duration_pattern'],
            'recurring_themes': [p for p in patterns if p['pattern_type'] == 'keyword_cluster'],
            'time_preferences': [p for p in patterns if p['pattern_type'] == 'recurring_time']
        }
    
    def _group_suggestions(
        self,
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group suggestions by category for better UI organization"""
        grouped = {
            'work': [],
            'personal': [],
            'health': [],
            'learning': [],
            'other': []
        }
        
        for suggestion in suggestions:
            category = suggestion.get('category', 'other')
            if category in grouped:
                grouped[category].append(suggestion)
            else:
                grouped['other'].append(suggestion)
        
        # Remove empty groups
        return {k: v for k, v in grouped.items() if v}
    
    def _generate_suggestion_insights(
        self,
        intention: str,
        suggestions: List[Dict[str, Any]],
        user_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights about the suggestions"""
        total_time = sum(s.get('estimated_minutes', 0) for s in suggestions)
        categories = set(s.get('category', 'other') for s in suggestions)
        
        insights = {
            'total_estimated_time': total_time,
            'time_breakdown': f"{total_time // 60}h {total_time % 60}m",
            'category_distribution': list(categories),
            'complexity_assessment': self._assess_complexity(suggestions),
            'personalization_applied': bool(user_patterns),
            'recommendations': []
        }
        
        # Add recommendations
        if total_time > 480:  # More than 8 hours
            insights['recommendations'].append({
                'type': 'time_warning',
                'message': 'Consider spreading these tasks across multiple days'
            })
        
        if len(categories) > 3:
            insights['recommendations'].append({
                'type': 'focus_suggestion',
                'message': 'Tasks span many categories. Consider focusing on 1-2 areas'
            })
        
        return insights
    
    def _assess_complexity(self, suggestions: List[Dict[str, Any]]) -> str:
        """Assess overall complexity of suggestions"""
        avg_duration = sum(s.get('estimated_minutes', 0) for s in suggestions) / len(suggestions)
        high_priority_count = sum(1 for s in suggestions if s.get('priority', 2) >= 4)
        
        if avg_duration > 120 or high_priority_count > len(suggestions) / 2:
            return 'high'
        elif avg_duration > 60:
            return 'medium'
        else:
            return 'low'
    
    def _store_suggestion_feedback(
        self,
        user_id: int,
        intention: str,
        feedback: Dict[str, Any]
    ) -> None:
        """Store user feedback for improving suggestions"""
        try:
            InsightsRepository.save_insight(
                user_id=user_id,
                insight_data={
                    'type': 'suggestion_feedback',
                    'intention': intention,
                    'feedback': feedback,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            # Log but don't fail the request
            print(f"Failed to store feedback: {e}")

class AIBatchProcessView(APIView):
    """
    Create multiple tasks from selected AI suggestions.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/ai/batch/
        Create tasks from selected suggestions.
        """
        try:
            user_id = request.user.id
            suggestions = request.data.get('suggestions', [])
            project_id = request.data.get('project_id')
            adjustments = request.data.get('adjustments', {})
            
            if not suggestions:
                return Response(
                    {'error': 'No suggestions provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            created_tasks = []
            
            # Get or create project
            if project_id:
                try:
                    project = Project.objects.get(id=project_id, user_id=user_id)
                except Project.DoesNotExist:
                    project = None
            else:
                project = None
            
            # Create tasks from suggestions
            for suggestion in suggestions:
                # Apply any adjustments
                if suggestion['id'] in adjustments:
                    suggestion.update(adjustments[suggestion['id']])
                
                # Create task
                task = Task.objects.create(
                    user_id=user_id,
                    title=suggestion['title'],
                    description=suggestion.get('description', ''),
                    project=project,
                    priority=suggestion.get('priority', 2),
                    estimated_duration=suggestion.get('estimated_minutes', 30),
                    labels=suggestion.get('tags', []),
                    ai_generated=True,
                    ai_confidence=suggestion.get('confidence', 0.85),
                    metadata={
                        'suggestion_id': suggestion['id'],
                        'category': suggestion.get('category', 'general'),
                        'created_from': 'ai_suggestions'
                    }
                )
                
                # Handle recurring tasks
                if suggestion.get('recurring'):
                    from .tasks import schedule_recurring_task
                    schedule_recurring_task.delay(
                        task_id=task.id,
                        pattern=suggestion['recurring']
                    )
                
                created_tasks.append(task)
            
            # Send notification
            NotificationService.notify_tasks_created(
                user_id=user_id,
                tasks=created_tasks
            )
            
            # Track analytics
            try:
                AnalyticsTracker.track_event(AnalyticsEvent(
                    event_type='batch_tasks_created',
                    user_id=user_id,
                    data={
                        'count': len(created_tasks),
                        'source': 'ai_suggestions',
                        'project_id': project_id
                    }
                ))
            except Exception:
                pass
            
            return Response({
                'tasks': TaskSerializer(created_tasks, many=True).data,
                'count': len(created_tasks),
                'message': f'Successfully created {len(created_tasks)} tasks'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create tasks: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AIPatternAnalysisView(APIView):
    """
    Analyze user patterns and provide insights.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/ai/patterns/
        Get user's task patterns and insights.
        """
        try:
            user_id = request.user.id
            days = int(request.query_params.get('days', 30))
            
            # Get patterns from MongoDB
            patterns = TaskPatternsRepository.get_user_patterns(user_id)
            
            # Get recent insights
            insights = InsightsRepository.get_user_insights(
                user_id=user_id,
                limit=10,
                insight_type='pattern_analysis'
            )
            
            # Generate pattern summary
            summary = self._generate_pattern_summary(patterns, days)
            
            return Response({
                'patterns': patterns,
                'insights': insights,
                'summary': summary,
                'period_days': days
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get patterns: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/ai/patterns/
        Trigger pattern analysis.
        """
        try:
            user_id = request.user.id
            analysis_type = request.data.get('type', 'full')  # full, quick, specific
            focus_area = request.data.get('focus_area')  # time, category, productivity
            
            # Queue pattern analysis
            task = analyze_user_patterns.delay(
                user_id=user_id,
                analysis_type=analysis_type,
                focus_area=focus_area
            )
            
            return Response({
                'task_id': str(task.id),
                'status': 'analyzing',
                'message': 'Pattern analysis started'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to start analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_pattern_summary(
        self,
        patterns: List[Dict[str, Any]],
        days: int
    ) -> Dict[str, Any]:
        """Generate summary of user patterns"""
        if not patterns:
            return {'status': 'no_patterns_found'}
        
        summary = {
            'total_patterns': len(patterns),
            'high_confidence_patterns': len([p for p in patterns if p['confidence'] > 0.8]),
            'pattern_types': {},
            'key_insights': [],
            'recommendations': []
        }
        
        # Count pattern types
        for pattern in patterns:
            ptype = pattern['pattern_type']
            if ptype not in summary['pattern_types']:
                summary['pattern_types'][ptype] = 0
            summary['pattern_types'][ptype] += 1
        
        # Generate insights
        if 'recurring_time' in summary['pattern_types']:
            summary['key_insights'].append(
                "You have consistent time-based patterns in your task creation"
            )
        
        if 'keyword_cluster' in summary['pattern_types']:
            summary['key_insights'].append(
                "Your tasks often cluster around specific themes"
            )
        
        # Add recommendations
        summary['recommendations'] = [
            "Use AI suggestions during your peak productivity hours",
            "Create task templates for recurring patterns"
        ]
        
        return summary

class AIInsightsView(APIView):
    """
    Get AI-generated insights and recommendations.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/ai/insights/
        Get personalized insights.
        """
        try:
            user_id = request.user.id
            insight_type = request.query_params.get('type', 'all')
            limit = int(request.query_params.get('limit', 5))
            
            # Get insights from MongoDB
            if insight_type == 'all':
                insights = InsightsRepository.get_user_insights(
                    user_id=user_id,
                    limit=limit
                )
            else:
                insights = InsightsRepository.get_user_insights(
                    user_id=user_id,
                    limit=limit,
                    insight_type=insight_type
                )
            
            # Format insights for display
            formatted_insights = []
            for insight in insights:
                formatted_insights.append({
                    'id': insight['_id'],
                    'type': insight.get('type', 'general'),
                    'title': self._generate_insight_title(insight),
                    'content': insight.get('insights', {}),
                    'confidence': insight.get('confidence_scores', {}).get('overall', 0.5),
                    'recommendations': insight.get('recommendations', []),
                    'created_at': insight.get('created_at'),
                    'actionable': self._is_actionable(insight)
                })
            
            # Get aggregated insights
            aggregated = InsightsRepository.get_aggregated_insights(
                user_id=user_id,
                days=30
            )
            
            return Response({
                'insights': formatted_insights,
                'aggregated': aggregated,
                'count': len(formatted_insights)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get insights: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/ai/insights/
        Generate new insights on demand.
        """
        try:
            user_id = request.user.id
            focus_area = request.data.get('focus_area', 'general')
            time_range = request.data.get('time_range', 'last_week')
            
            # Initialize agent
            agent = TaskAgent()
            
            # Get user data for analysis
            user_data = self._get_user_data_for_insights(user_id, time_range)
            
            # Generate insights
            insights = agent.generate_insights(
                user_data=user_data,
                focus_area=focus_area
            )
            
            # Store insights
            for insight in insights:
                InsightsRepository.save_insight(
                    user_id=user_id,
                    insight_data=insight
                )
            
            return Response({
                'insights': insights,
                'count': len(insights),
                'focus_area': focus_area
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate insights: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_insight_title(self, insight: Dict[str, Any]) -> str:
        """Generate a readable title for an insight"""
        insight_type = insight.get('type', 'general')
        
        titles = {
            'productivity': 'Productivity Analysis',
            'pattern_analysis': 'Task Pattern Discovery',
            'time_management': 'Time Management Insights',
            'goal_progress': 'Goal Progress Update',
            'workload_balance': 'Workload Balance Check',
            'general': 'General Insight'
        }
        
        return titles.get(insight_type, 'AI Insight')
    
    def _is_actionable(self, insight: Dict[str, Any]) -> bool:
        """Check if an insight has actionable recommendations"""
        return len(insight.get('recommendations', [])) > 0
    
    def _get_user_data_for_insights(
        self,
        user_id: int,
        time_range: str
    ) -> Dict[str, Any]:
        """Gather user data for insight generation"""
        # Map time ranges to days
        days_map = {
            'today': 1,
            'last_week': 7,
            'last_month': 30,
            'last_quarter': 90
        }
        days = days_map.get(time_range, 7)
        
        # Get tasks
        start_date = timezone.now() - timedelta(days=days)
        tasks = Task.objects.filter(
            user_id=user_id,
            created_at__gte=start_date
        )
        
        return {
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(is_completed=True).count(),
            'overdue_tasks': tasks.filter(
                is_completed=False,
                due_date__lt=timezone.now()
            ).count(),
            'task_categories': list(tasks.values_list('labels', flat=True)),
            'time_range': time_range,
            'days': days
        }

class AIStreamingView(APIView):
    """
    Handle streaming AI responses for real-time interaction.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/ai/stream/
        Initiate streaming AI response.
        """
        try:
            user_id = request.user.id
            intention = request.data.get('intention', '')
            stream_type = request.data.get('type', 'suggestions')  # suggestions, analysis, chat
            session_id = request.data.get('session_id', str(uuid.uuid4()))
            
            # Store streaming session
            cache_key = f"ai_stream:{session_id}"
            cache.set(cache_key, {
                'user_id': user_id,
                'intention': intention,
                'type': stream_type,
                'status': 'active',
                'started_at': timezone.now().isoformat()
            }, 300)  # 5 minute TTL
            
            # Return session info for WebSocket connection
            return Response({
                'session_id': session_id,
                'websocket_url': f'/ws/ai-stream/{session_id}/',
                'status': 'ready',
                'message': 'Connect to WebSocket for streaming response'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to initiate streaming: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# NEW: Intent-Based Chat API (More Efficient)
# =============================================================================

class AIIntentChatView(APIView):
    """
    Intent-based AI chat for task management.

    Extracts ALL tasks from user input and executes them.

    Features:
    - Multi-task extraction: "I want to learn coding, go to gym, and call mom" = 3 tasks
    - Intent-based: create, query, complete, update, delete, chat
    - Auto-execution: Creates tasks immediately
    - Token tracking: Reports token usage
    """
    permission_classes = [AllowAny]  # Uses X-Account-ID header

    _agent = None

    @classmethod
    def get_agent(cls):
        """Get or create IntentAgent singleton."""
        if cls._agent is None:
            cls._agent = IntentAgent()
        return cls._agent

    def post(self, request):
        """
        POST /ai/intent/
        Extract tasks from natural language and execute.

        Body:
        {
            "message": "I want to learn coding, go to gym, and call mom",
            "session_id": "optional-session-id"
        }

        Returns:
        {
            "success": true,
            "intent": "create",
            "message": "Created 3 tasks",
            "tasks": [
                {"title": "learn coding", "due_date": null, "priority": "medium"},
                {"title": "go to gym", "due_date": null, "priority": "medium"},
                {"title": "call mom", "due_date": null, "priority": "medium"}
            ],
            "execution": {
                "success": true,
                "created_tasks": [...]
            },
            "session_id": "session-id",
            "token_report": {...}
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')
        auto_execute = request.data.get('auto_execute', True)

        if not message:
            return Response(
                {'error': 'Message cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get user's tasks for context
            user_tasks = list(Task.objects.filter(
                user=account,
                totally_completed=False
            ).values('id', 'name', 'due_date', 'completed')[:20])

            # Extract tasks from input
            agent = self.get_agent()
            prediction = agent.predict_intent(
                user_input=message,
                session_id=session_id,
                user_tasks=user_tasks
            )

            # Build response
            response_data = {
                'success': prediction.success,
                'intent': prediction.intent,
                'message': prediction.message,
                'tasks': [t.model_dump() for t in prediction.tasks],
                'query_type': prediction.query_type,
                'needs_confirmation': prediction.needs_confirmation,
                'session_id': prediction.session_id,
                'token_report': prediction.token_report,
                # Legacy compatibility
                'intent_id': prediction.intent_id,
                'extracted_params': prediction.extracted_params
            }

            # Auto-execute based on intent type
            if auto_execute and prediction.success and not prediction.needs_confirmation:
                handlers = IntentHandlers(
                    account=account,
                    task_model=Task,
                    project_model=Project,
                    section_model=Section
                )

                if prediction.intent == 'create' and prediction.tasks:
                    # Create multiple tasks
                    execution_result = self._execute_create_tasks(handlers, prediction.tasks)
                    response_data['execution'] = execution_result
                    response_data['message'] = execution_result.get('message', prediction.message)

                elif prediction.intent == 'query':
                    # Execute query
                    result = handlers.execute(prediction.intent_id, prediction.extracted_params)
                    response_data['execution'] = {
                        'success': result.success,
                        'action_type': result.action_type.value,
                        'data': result.data,
                        'message': result.message,
                        'error': result.error
                    }
                    if result.message:
                        response_data['message'] = result.message

                elif prediction.intent in ['complete', 'delete', 'update'] and prediction.tasks:
                    # Execute on task names
                    result = handlers.execute(prediction.intent_id, {
                        'task_name': prediction.tasks[0].title if prediction.tasks else ''
                    })
                    response_data['execution'] = {
                        'success': result.success,
                        'action_type': result.action_type.value,
                        'data': result.data,
                        'message': result.message,
                        'error': result.error
                    }
                    if result.message:
                        response_data['message'] = result.message

            return Response(response_data)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to process: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _execute_create_tasks(self, handlers, tasks) -> Dict:
        """Create multiple tasks and return execution result."""
        created_tasks = []
        errors = []

        for task in tasks:
            try:
                # Build params for handler
                params = {
                    'title': task.title,
                    'due_date': task.due_date,
                    'due_time': task.due_time,
                    'priority': task.priority
                }

                # Determine which handler to use
                if task.due_date or task.due_time:
                    result = handlers.handle_task_create_with_date(params)
                else:
                    result = handlers.handle_task_create_simple(params)

                if result.success:
                    created_tasks.append({
                        'task_id': result.data.get('task_id'),
                        'task_name': result.data.get('task_name'),
                        'due_date': result.data.get('due_date')
                    })
                else:
                    errors.append(result.error)

            except Exception as e:
                errors.append(str(e))

        # Build result message
        if created_tasks:
            task_names = [t['task_name'] for t in created_tasks]
            if len(task_names) == 1:
                message = f"Created task: '{task_names[0]}'"
            else:
                message = f"Created {len(task_names)} tasks: {', '.join(task_names)}"
        else:
            message = "No tasks created"

        return {
            'success': len(created_tasks) > 0,
            'action_type': 'insert',
            'created_tasks': created_tasks,
            'count': len(created_tasks),
            'errors': errors,
            'message': message
        }


class AIIntentExecuteView(APIView):
    """
    Execute a specific intent with given params.

    Use this when:
    - User confirms a destructive action
    - Manually executing an intent
    - Replaying an intent with modified params
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        POST /ai/intent/execute/
        Execute a specific intent.

        Body:
        {
            "intent_id": "task-create-simple",
            "params": {"title": "My new task"}
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        intent_id = request.data.get('intent_id', '')
        params = request.data.get('params', {})

        if not intent_id:
            return Response(
                {'error': 'intent_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate intent exists
        intent = get_intent_by_id(intent_id)
        if not intent:
            return Response(
                {'error': f'Unknown intent: {intent_id}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            handlers = IntentHandlers(
                account=account,
                task_model=Task,
                project_model=Project,
                section_model=Section
            )
            result = handlers.execute(intent_id, params)

            return Response({
                'success': result.success,
                'intent_id': result.intent_id,
                'action_type': result.action_type.value,
                'data': result.data,
                'message': result.message,
                'error': result.error
            })

        except Exception as e:
            return Response(
                {'error': f'Execution failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIIntentListView(APIView):
    """
    List all available intents.

    Useful for:
    - Building UI with available commands
    - Debugging
    - API documentation
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET /ai/intent/list/
        List all available intents.
        """
        from .agents.intent_registry import INTENT_REGISTRY, IntentCategory

        category = request.query_params.get('category')

        intents = []
        for intent_id, intent in INTENT_REGISTRY.items():
            if category and intent.category.value != category:
                continue

            intents.append({
                'id': intent.id,
                'description': intent.description,
                'action_type': intent.action_type.value,
                'category': intent.category.value,
                'patterns': intent.patterns[:3],  # Sample patterns
                'requires_params': intent.requires_params,
                'optional_params': intent.optional_params,
                'safe': intent.safe
            })

        # Group by category
        grouped = {}
        for intent in intents:
            cat = intent['category']
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(intent)

        return Response({
            'intents': intents,
            'grouped': grouped,
            'total': len(intents),
            'categories': [c.value for c in IntentCategory]
        })


class AITaskExtractView(APIView):
    """
    Extract tasks from natural language WITHOUT auto-executing.

    Use this for:
    - Preview what tasks will be created
    - Let user modify before confirming
    - UI that shows extracted tasks for approval
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        POST /ai/extract/
        Extract tasks from text without creating them.

        Body:
        {
            "message": "I want to learn coding, go to gym, and call mom tomorrow"
        }

        Returns:
        {
            "success": true,
            "intent": "create",
            "tasks": [
                {"title": "learn coding", "due_date": null},
                {"title": "go to gym", "due_date": null},
                {"title": "call mom", "due_date": "tomorrow"}
            ],
            "token_report": {...}
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        message = request.data.get('message', '').strip()
        if not message:
            return Response(
                {'error': 'Message cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get user's tasks for context
            user_tasks = list(Task.objects.filter(
                user=account,
                totally_completed=False
            ).values('id', 'name', 'due_date', 'completed')[:20])

            # Extract tasks (no auto-execute)
            agent = AIIntentChatView.get_agent()
            prediction = agent.predict_intent(
                user_input=message,
                user_tasks=user_tasks
            )

            return Response({
                'success': prediction.success,
                'intent': prediction.intent,
                'message': prediction.message,
                'tasks': [t.model_dump() for t in prediction.tasks],
                'query_type': prediction.query_type,
                'token_report': prediction.token_report
            })

        except Exception as e:
            return Response(
                {'error': f'Extraction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIBatchCreateView(APIView):
    """
    Create multiple tasks from a pre-extracted list.

    Use after AITaskExtractView to create confirmed tasks.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        POST /ai/batch-create/
        Create multiple tasks from a list.

        Body:
        {
            "tasks": [
                {"title": "learn coding", "due_date": "tomorrow", "priority": "high"},
                {"title": "go to gym", "due_date": null, "priority": "medium"},
                {"title": "call mom", "due_time": "10pm"}
            ]
        }

        Returns:
        {
            "success": true,
            "created_tasks": [...],
            "count": 3,
            "message": "Created 3 tasks"
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tasks_data = request.data.get('tasks', [])
        if not tasks_data:
            return Response(
                {'error': 'No tasks provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            handlers = IntentHandlers(
                account=account,
                task_model=Task,
                project_model=Project,
                section_model=Section
            )

            created_tasks = []
            errors = []

            for task_data in tasks_data:
                title = task_data.get('title', '').strip()
                if not title:
                    errors.append("Empty task title skipped")
                    continue

                params = {
                    'title': title,
                    'due_date': task_data.get('due_date'),
                    'due_time': task_data.get('due_time'),
                    'priority': task_data.get('priority', 'medium')
                }

                # Use appropriate handler
                if params.get('due_date') or params.get('due_time'):
                    result = handlers.handle_task_create_with_date(params)
                else:
                    result = handlers.handle_task_create_simple(params)

                if result.success:
                    created_tasks.append({
                        'task_id': result.data.get('task_id'),
                        'task_name': result.data.get('task_name'),
                        'due_date': result.data.get('due_date')
                    })
                else:
                    errors.append(result.error)

            # Build response
            if created_tasks:
                task_names = [t['task_name'] for t in created_tasks]
                message = f"Created {len(task_names)} task(s): {', '.join(task_names)}"
            else:
                message = "No tasks created"

            return Response({
                'success': len(created_tasks) > 0,
                'created_tasks': created_tasks,
                'count': len(created_tasks),
                'errors': errors if errors else None,
                'message': message
            }, status=status.HTTP_201_CREATED if created_tasks else status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': f'Batch create failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIIntentSessionView(APIView):
    """
    Manage intent chat sessions.
    """
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        """
        GET /ai/intent/session/<session_id>/
        Get session history.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        agent = AIIntentChatView.get_agent()

        if session_id not in agent.conversations:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        context = agent.conversations[session_id]

        return Response({
            'session_id': session_id,
            'messages': [
                {
                    'role': m.role,
                    'content': m.content,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in context.messages
            ],
            'message_count': len(context.messages),
            'last_intent': context.last_intent_id
        })

    def delete(self, request, session_id):
        """
        DELETE /ai/intent/session/<session_id>/
        Clear session.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        agent = AIIntentChatView.get_agent()

        if session_id in agent.conversations:
            del agent.conversations[session_id]
            return Response({'message': 'Session cleared', 'session_id': session_id})

        return Response(
            {'error': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class AIQuickTaskView(APIView):
    """
    Quick single-task creation with smart defaults.
    Simpler than full intent chat for quick adds.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        POST /ai/quick-task/
        Quickly create a task with smart parsing.

        Body:
        {
            "text": "buy groceries tomorrow at 5pm"
        }

        Returns:
        {
            "success": true,
            "task": {
                "id": "...",
                "name": "buy groceries",
                "due_date": "2026-01-24",
                "due_time": "17:00"
            }
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        text = request.data.get('text', '').strip()
        if not text:
            return Response(
                {'error': 'Text cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Extract single task using LLM
            agent = AIIntentChatView.get_agent()
            prediction = agent.predict_intent(user_input=text)

            # Get first task or use text as title
            if prediction.tasks:
                task_data = prediction.tasks[0]
            else:
                from .agents.intent_agent import ExtractedTask
                task_data = ExtractedTask(title=text)

            # Create the task
            handlers = IntentHandlers(
                account=account,
                task_model=Task,
                project_model=Project,
                section_model=Section
            )

            params = {
                'title': task_data.title,
                'due_date': task_data.due_date,
                'due_time': task_data.due_time,
                'priority': task_data.priority
            }

            if params.get('due_date') or params.get('due_time'):
                result = handlers.handle_task_create_with_date(params)
            else:
                result = handlers.handle_task_create_simple(params)

            if result.success:
                return Response({
                    'success': True,
                    'task': result.data,
                    'message': result.message,
                    'token_report': prediction.token_report
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result.error
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': f'Quick task failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )