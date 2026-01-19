# File: tasks_api/views_agent.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime, timedelta

from .models import Task, Project, Section
from .serializers import TaskSerializer
from .agents.task_agent import TaskAgent
from .tasks import process_ai_intention, analyze_user_patterns
from .utils.analytics import AnalyticsTracker
from .utils.mongodb import InsightsRepository, TaskPatternsRepository
from .utils.notifications import NotificationService, Notification, NotificationType

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
            AnalyticsTracker.track_event(
                event_type='ai_suggestions_generated',
                user_id=user_id,
                data={
                    'intention_length': len(intention),
                    'suggestions_count': len(enhanced_suggestions),
                    'context_type': context_type
                }
            )
            
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
            AnalyticsTracker.track_event(
                event_type='batch_tasks_created',
                user_id=user_id,
                data={
                    'count': len(created_tasks),
                    'source': 'ai_suggestions',
                    'project_id': project_id
                }
            )
            
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