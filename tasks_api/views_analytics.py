# File: tasks_api/views_analytics.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from typing import Dict, Any, Optional
import json
import csv
import io
from datetime import datetime, timedelta

from .utils.analytics import AnalyticsTracker
from .utils.mongodb import InsightsRepository, TaskPatternsRepository, AILogsRepository
from .models import Task, Project
from .serializers import TaskSerializer, ProjectSerializer

class UserAnalyticsView(APIView):
    """
    Get comprehensive analytics for the authenticated user.
    Supports various time ranges and metric types.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/analytics/user/
        Query params:
            - days: Number of days to analyze (default: 30)
            - metrics: Comma-separated list of metrics to include
        """
        try:
            user_id = request.user.id
            days = int(request.query_params.get('days', 30))
            metrics = request.query_params.get('metrics', '').split(',')
            
            # Check cache first
            cache_key = f"user_analytics:{user_id}:{days}:{','.join(metrics)}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)
            
            # Get analytics data
            analytics_data = AnalyticsTracker.get_user_analytics(
                user_id=user_id,
                days=days
            )
            
            # Filter metrics if specified
            if metrics and metrics[0]:
                filtered_data = {}
                for metric in metrics:
                    if metric in analytics_data:
                        filtered_data[metric] = analytics_data[metric]
                analytics_data = filtered_data
            
            # Add additional insights from MongoDB
            insights = InsightsRepository.get_aggregated_insights(
                user_id=user_id,
                days=days
            )
            analytics_data['ai_insights'] = insights
            
            # Cache for 5 minutes
            cache.set(cache_key, analytics_data, 300)
            
            return Response(analytics_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProductivityReportView(APIView):
    """
    Generate detailed productivity reports with recommendations.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/analytics/productivity/
        Query params:
            - period: daily, weekly, monthly (default: daily)
            - date: Specific date for report (default: today)
        """
        try:
            user_id = request.user.id
            period = request.query_params.get('period', 'daily')
            date_str = request.query_params.get('date')
            
            if date_str:
                report_date = datetime.fromisoformat(date_str).date()
            else:
                report_date = timezone.now().date()
            
            # Generate report based on period
            if period == 'daily':
                report = AnalyticsTracker.generate_daily_report(user_id)
            elif period == 'weekly':
                report = self._generate_weekly_report(user_id, report_date)
            elif period == 'monthly':
                report = self._generate_monthly_report(user_id, report_date)
            else:
                return Response(
                    {'error': 'Invalid period. Use daily, weekly, or monthly'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add AI insights
            report['ai_insights'] = self._get_productivity_insights(
                user_id, period, report
            )
            
            return Response(report)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/analytics/productivity/
        Schedule productivity reports.
        """
        try:
            user_id = request.user.id
            schedule_data = request.data
            
            # Validate schedule data
            frequency = schedule_data.get('frequency')  # daily, weekly, monthly
            delivery_time = schedule_data.get('delivery_time', '09:00')
            delivery_method = schedule_data.get('method', 'email')
            
            if frequency not in ['daily', 'weekly', 'monthly']:
                return Response(
                    {'error': 'Invalid frequency'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Store schedule preference
            cache_key = f"report_schedule:{user_id}"
            schedule_config = {
                'frequency': frequency,
                'delivery_time': delivery_time,
                'delivery_method': delivery_method,
                'enabled': True,
                'created_at': timezone.now().isoformat()
            }
            
            cache.set(cache_key, schedule_config, None)  # No expiry
            
            # Schedule with Celery
            from .tasks import schedule_productivity_reports
            schedule_productivity_reports.delay(user_id, schedule_config)
            
            return Response({
                'message': 'Productivity reports scheduled successfully',
                'schedule': schedule_config
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to schedule reports: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_weekly_report(self, user_id: int, date: datetime.date) -> Dict[str, Any]:
        """Generate weekly productivity report"""
        start_date = date - timedelta(days=date.weekday())
        end_date = start_date + timedelta(days=6)
        
        # Get tasks for the week
        week_tasks = Task.objects.filter(
            user_id=user_id,
            created_at__date__range=[start_date, end_date]
        )
        
        completed_tasks = week_tasks.filter(is_completed=True)
        
        # Calculate daily breakdown
        daily_breakdown = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_tasks = week_tasks.filter(created_at__date=day)
            day_completed = completed_tasks.filter(completed_at__date=day)
            
            daily_breakdown.append({
                'date': day.isoformat(),
                'created': day_tasks.count(),
                'completed': day_completed.count(),
                'completion_rate': (
                    day_completed.count() / day_tasks.count() * 100
                    if day_tasks.count() > 0 else 0
                )
            })
        
        return {
            'period': 'weekly',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_created': week_tasks.count(),
            'total_completed': completed_tasks.count(),
            'completion_rate': (
                completed_tasks.count() / week_tasks.count() * 100
                if week_tasks.count() > 0 else 0
            ),
            'daily_breakdown': daily_breakdown,
            'most_productive_day': max(
                daily_breakdown,
                key=lambda x: x['completed']
            )['date'] if daily_breakdown else None
        }
    
    def _generate_monthly_report(self, user_id: int, date: datetime.date) -> Dict[str, Any]:
        """Generate monthly productivity report"""
        start_date = date.replace(day=1)
        if date.month == 12:
            end_date = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
        
        # Get analytics for the month
        days_in_month = (end_date - start_date).days + 1
        analytics = AnalyticsTracker.get_user_analytics(user_id, days_in_month)
        
        return {
            'period': 'monthly',
            'month': date.strftime('%B %Y'),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'analytics': analytics,
            'goal_progress': self._calculate_goal_progress(user_id, start_date, end_date)
        }
    
    def _get_productivity_insights(
        self,
        user_id: int,
        period: str,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI insights for productivity report"""
        # Get recent insights from MongoDB
        insights = InsightsRepository.get_user_insights(
            user_id=user_id,
            limit=5,
            insight_type='productivity'
        )
        
        return {
            'recent_insights': insights,
            'recommendations': self._generate_recommendations(report_data),
            'trends': self._analyze_trends(user_id, period)
        }
    
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> list:
        """Generate recommendations based on report data"""
        recommendations = []
        
        completion_rate = report_data.get('completion_rate', 0)
        if completion_rate < 50:
            recommendations.append({
                'type': 'task_management',
                'priority': 'high',
                'message': 'Your completion rate is below 50%. Consider breaking down large tasks into smaller, manageable pieces.',
                'action': 'review_task_size'
            })
        
        if report_data.get('most_productive_day'):
            recommendations.append({
                'type': 'scheduling',
                'priority': 'medium',
                'message': f"You're most productive on {report_data['most_productive_day']}. Schedule important tasks for this day.",
                'action': 'optimize_schedule'
            })
        
        return recommendations
    
    def _analyze_trends(self, user_id: int, period: str) -> Dict[str, Any]:
        """Analyze productivity trends"""
        # Implementation for trend analysis
        return {
            'completion_trend': 'improving',
            'consistency_trend': 'stable',
            'workload_trend': 'increasing'
        }
    
    def _calculate_goal_progress(
        self,
        user_id: int,
        start_date: datetime.date,
        end_date: datetime.date
    ) -> Dict[str, Any]:
        """Calculate progress toward goals"""
        # Implementation for goal tracking
        return {
            'monthly_task_goal': {
                'target': 100,
                'achieved': 85,
                'percentage': 85.0
            }
        }

class TaskPatternsView(APIView):
    """
    Analyze and retrieve task patterns using AI.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/analytics/patterns/
        Get discovered task patterns for the user.
        """
        try:
            user_id = request.user.id
            min_confidence = float(request.query_params.get('min_confidence', 0.7))
            
            # Get patterns from MongoDB
            patterns = TaskPatternsRepository.get_user_patterns(
                user_id=user_id,
                min_confidence=min_confidence
            )
            
            # Enhance with usage statistics
            enhanced_patterns = []
            for pattern in patterns:
                # Get tasks matching this pattern
                matching_tasks = self._find_matching_tasks(user_id, pattern)
                pattern['matching_tasks'] = len(matching_tasks)
                pattern['example_tasks'] = TaskSerializer(
                    matching_tasks[:3],
                    many=True
                ).data
                enhanced_patterns.append(pattern)
            
            return Response({
                'patterns': enhanced_patterns,
                'total_patterns': len(enhanced_patterns),
                'min_confidence': min_confidence
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get patterns: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/analytics/patterns/
        Trigger pattern analysis for the user.
        """
        try:
            user_id = request.user.id
            
            # Queue pattern analysis task
            from .tasks import analyze_user_patterns
            task = analyze_user_patterns.delay(user_id)
            
            return Response({
                'message': 'Pattern analysis started',
                'task_id': str(task.id),
                'status': 'processing'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to start pattern analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _find_matching_tasks(self, user_id: int, pattern: Dict[str, Any]) -> list:
        """Find tasks matching a pattern"""
        pattern_type = pattern.get('pattern_type')
        pattern_data = pattern.get('pattern_data', {})
        
        # Build query based on pattern type
        query = {'user_id': user_id}
        
        if pattern_type == 'recurring_time':
            # Tasks created at similar times
            time_range = pattern_data.get('time_range', {})
            query['created_at__hour__range'] = (
                time_range.get('start_hour', 0),
                time_range.get('end_hour', 23)
            )
        elif pattern_type == 'keyword_cluster':
            # Tasks with similar keywords
            keywords = pattern_data.get('keywords', [])
            query['title__icontains'] = keywords[0] if keywords else ''
        elif pattern_type == 'duration_pattern':
            # Tasks with similar durations
            duration_range = pattern_data.get('duration_range', {})
            query['estimated_duration__range'] = (
                duration_range.get('min', 0),
                duration_range.get('max', 480)
            )
        
        return list(Task.objects.filter(**query).order_by('-created_at')[:10])

class SystemMetricsView(APIView):
    """
    System-wide metrics for monitoring and admin dashboard.
    """
    permission_classes = [IsAuthenticated]  # Add admin check
    
    def get(self, request):
        """
        GET /api/analytics/system/
        Get system-wide metrics.
        """
        try:
            # Check if user is admin/staff
            if not request.user.is_staff:
                return Response(
                    {'error': 'Admin access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get system metrics
            metrics = AnalyticsTracker.get_system_metrics()
            
            # Add database statistics
            metrics['database'] = {
                'total_users': self._get_user_count(),
                'total_tasks': Task.objects.count(),
                'total_projects': Project.objects.count(),
                'active_users_today': self._get_active_users_count()
            }
            
            # Add AI processing statistics
            ai_stats = AILogsRepository.get_processing_stats(
                user_id=None,  # System-wide
                days=7
            )
            metrics['ai_processing'] = ai_stats
            
            # Add MongoDB health
            from .utils.mongodb import get_mongodb_manager
            mongo_health = get_mongodb_manager().health_check()
            metrics['mongodb'] = mongo_health
            
            return Response(metrics)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get system metrics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_count(self) -> int:
        """Get total user count"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.count()
    
    def _get_active_users_count(self) -> int:
        """Get count of active users today"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        today = timezone.now().date()
        return User.objects.filter(last_login__date=today).count()

class AnalyticsExportView(APIView):
    """
    Export analytics data in various formats.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/analytics/export/
        Query params:
            - format: csv, json, pdf (default: json)
            - period: daily, weekly, monthly, custom
            - start_date: Start date for custom period
            - end_date: End date for custom period
        """
        try:
            user_id = request.user.id
            export_format = request.query_params.get('format', 'json')
            period = request.query_params.get('period', 'monthly')
            
            # Get analytics data
            if period == 'custom':
                start_date = request.query_params.get('start_date')
                end_date = request.query_params.get('end_date')
                if not start_date or not end_date:
                    return Response(
                        {'error': 'start_date and end_date required for custom period'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                days = (
                    datetime.fromisoformat(end_date) -
                    datetime.fromisoformat(start_date)
                ).days
            else:
                days = {'daily': 1, 'weekly': 7, 'monthly': 30}.get(period, 30)
            
            analytics_data = AnalyticsTracker.get_user_analytics(user_id, days)
            
            # Export based on format
            if export_format == 'csv':
                return self._export_csv(analytics_data, period)
            elif export_format == 'json':
                return self._export_json(analytics_data, period)
            elif export_format == 'pdf':
                return self._export_pdf(analytics_data, period)
            else:
                return Response(
                    {'error': 'Invalid format. Use csv, json, or pdf'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Failed to export analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _export_csv(self, data: Dict[str, Any], period: str) -> HttpResponse:
        """Export analytics as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Metric', 'Value'])
        
        # Flatten nested data and write rows
        for key, value in self._flatten_dict(data).items():
            writer.writerow([key, value])
        
        response = HttpResponse(
            output.getvalue(),
            content_type='text/csv'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="analytics_{period}_{timezone.now().date()}.csv"'
        )
        
        return response
    
    def _export_json(self, data: Dict[str, Any], period: str) -> JsonResponse:
        """Export analytics as JSON"""
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = (
            f'attachment; filename="analytics_{period}_{timezone.now().date()}.json"'
        )
        return response
    
    def _export_pdf(self, data: Dict[str, Any], period: str) -> HttpResponse:
        """Export analytics as PDF"""
        # This would require a PDF generation library like ReportLab
        # For now, return a placeholder
        return Response(
            {'error': 'PDF export not yet implemented'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

class DashboardDataView(APIView):
    """
    Aggregate dashboard data for frontend display.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/analytics/dashboard/
        Get all dashboard data in one request.
        """
        try:
            user_id = request.user.id
            
            # Check cache for dashboard data
            cache_key = f"dashboard_data:{user_id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)
            
            # Aggregate all dashboard components
            dashboard_data = {
                'summary': self._get_summary_stats(user_id),
                'recent_tasks': self._get_recent_tasks(user_id),
                'upcoming_tasks': self._get_upcoming_tasks(user_id),
                'productivity_chart': self._get_productivity_chart_data(user_id),
                'project_progress': self._get_project_progress(user_id),
                'activity_feed': self._get_activity_feed(user_id),
                'ai_insights': self._get_latest_insights(user_id),
                'quick_stats': self._get_quick_stats(user_id),
                'timestamp': timezone.now().isoformat()
            }
            
            # Cache for 1 minute
            cache.set(cache_key, dashboard_data, 60)
            
            return Response(dashboard_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get dashboard data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_summary_stats(self, user_id: int) -> Dict[str, Any]:
        """Get summary statistics"""
        today = timezone.now().date()
        
        return {
            'tasks_today': Task.objects.filter(
                user_id=user_id,
                created_at__date=today
            ).count(),
            'completed_today': Task.objects.filter(
                user_id=user_id,
                is_completed=True,
                completed_at__date=today
            ).count(),
            'pending_tasks': Task.objects.filter(
                user_id=user_id,
                is_completed=False
            ).count(),
            'overdue_tasks': Task.objects.filter(
                user_id=user_id,
                is_completed=False,
                due_date__lt=timezone.now()
            ).count()
        }
    
    def _get_recent_tasks(self, user_id: int) -> list:
        """Get recent tasks"""
        recent_tasks = Task.objects.filter(
            user_id=user_id
        ).order_by('-created_at')[:5]
        
        return TaskSerializer(recent_tasks, many=True).data
    
    def _get_upcoming_tasks(self, user_id: int) -> list:
        """Get upcoming tasks"""
        upcoming = Task.objects.filter(
            user_id=user_id,
            is_completed=False,
            due_date__gte=timezone.now()
        ).order_by('due_date')[:5]
        
        return TaskSerializer(upcoming, many=True).data
    
    def _get_productivity_chart_data(self, user_id: int) -> Dict[str, Any]:
        """Get productivity chart data for last 7 days"""
        data_points = []
        today = timezone.now().date()
        
        for i in range(7):
            date = today - timedelta(days=i)
            created = Task.objects.filter(
                user_id=user_id,
                created_at__date=date
            ).count()
            completed = Task.objects.filter(
                user_id=user_id,
                is_completed=True,
                completed_at__date=date
            ).count()
            
            data_points.append({
                'date': date.isoformat(),
                'created': created,
                'completed': completed
            })
        
        return {
            'labels': [dp['date'] for dp in reversed(data_points)],
            'datasets': [
                {
                    'label': 'Created',
                    'data': [dp['created'] for dp in reversed(data_points)]
                },
                {
                    'label': 'Completed',
                    'data': [dp['completed'] for dp in reversed(data_points)]
                }
            ]
        }
    
    def _get_project_progress(self, user_id: int) -> list:
        """Get project progress data"""
        projects = Project.objects.filter(
            user_id=user_id,
            is_archived=False
        ).prefetch_related('tasks')[:5]
        
        project_data = []
        for project in projects:
            total_tasks = project.tasks.count()
            completed_tasks = project.tasks.filter(is_completed=True).count()
            
            project_data.append({
                'id': project.id,
                'name': project.name,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'progress': (
                    completed_tasks / total_tasks * 100
                    if total_tasks > 0 else 0
                )
            })
        
        return project_data
    
    def _get_activity_feed(self, user_id: int) -> list:
        """Get recent activity feed"""
        # This would pull from an activity log
        # For now, return placeholder data
        return [
            {
                'type': 'task_completed',
                'message': 'Completed task: Review project proposal',
                'timestamp': (timezone.now() - timedelta(hours=1)).isoformat()
            },
            {
                'type': 'ai_processed',
                'message': 'AI created 3 tasks from your input',
                'timestamp': (timezone.now() - timedelta(hours=2)).isoformat()
            }
        ]
    
    def _get_latest_insights(self, user_id: int) -> list:
        """Get latest AI insights"""
        insights = InsightsRepository.get_user_insights(
            user_id=user_id,
            limit=3
        )
        
        # Format for dashboard display
        formatted_insights = []
        for insight in insights:
            formatted_insights.append({
                'type': insight.get('type'),
                'message': insight.get('insights', {}).get('summary', ''),
                'confidence': insight.get('confidence_scores', {}).get('overall', 0),
                'created_at': insight.get('created_at')
            })
        
        return formatted_insights
    
    def _get_quick_stats(self, user_id: int) -> Dict[str, Any]:
        """Get quick stats for dashboard"""
        return {
            'productivity_score': cache.get(f"productivity_score:{user_id}", 0),
            'streak_days': self._calculate_streak(user_id),
            'focus_time_today': cache.get(f"focus_time:{user_id}:{timezone.now().date()}", 0),
            'ai_assists_today': cache.get(f"ai_assists:{user_id}:{timezone.now().date()}", 0)
        }
    
    def _calculate_streak(self, user_id: int) -> int:
        """Calculate task completion streak"""
        streak = 0
        date = timezone.now().date()
        
        while True:
            completed = Task.objects.filter(
                user_id=user_id,
                is_completed=True,
                completed_at__date=date
            ).exists()
            
            if completed:
                streak += 1
                date -= timedelta(days=1)
            else:
                break
        
        return streak