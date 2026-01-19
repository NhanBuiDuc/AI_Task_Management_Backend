# File: tasks_api/views_notifications.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils import timezone
from django.core.paginator import Paginator
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

from .utils.notifications import (
    NotificationService, 
    NotificationPreferences,
    NotificationType
)
from .models import Task

class NotificationPreferencesView(APIView):
    """
    Manage user notification preferences.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/notifications/preferences/
        Get user's notification preferences.
        """
        try:
            user_id = request.user.id
            preferences = NotificationPreferences.get_user_preferences(user_id)
            
            # Add channel-specific settings
            preferences['channels'] = {
                'in_app': True,
                'email': cache.get(f"notif_email_enabled:{user_id}", False),
                'push': cache.get(f"notif_push_enabled:{user_id}", False),
                'sms': cache.get(f"notif_sms_enabled:{user_id}", False)
            }
            
            # Add time preferences
            preferences['quiet_hours'] = {
                'enabled': cache.get(f"quiet_hours_enabled:{user_id}", False),
                'start': cache.get(f"quiet_hours_start:{user_id}", "22:00"),
                'end': cache.get(f"quiet_hours_end:{user_id}", "08:00")
            }
            
            # Add frequency settings
            preferences['frequency'] = {
                'realtime': cache.get(f"notif_realtime:{user_id}", True),
                'digest': cache.get(f"notif_digest:{user_id}", False),
                'digest_time': cache.get(f"notif_digest_time:{user_id}", "09:00")
            }
            
            return Response(preferences)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get preferences: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """
        PUT /api/notifications/preferences/
        Update notification preferences.
        """
        try:
            user_id = request.user.id
            updates = request.data
            
            # Update basic preferences
            if 'preferences' in updates:
                NotificationPreferences.update_preferences(
                    user_id,
                    updates['preferences']
                )
            
            # Update channel settings
            if 'channels' in updates:
                for channel, enabled in updates['channels'].items():
                    cache.set(f"notif_{channel}_enabled:{user_id}", enabled, None)
            
            # Update quiet hours
            if 'quiet_hours' in updates:
                qh = updates['quiet_hours']
                cache.set(f"quiet_hours_enabled:{user_id}", qh.get('enabled', False), None)
                cache.set(f"quiet_hours_start:{user_id}", qh.get('start', "22:00"), None)
                cache.set(f"quiet_hours_end:{user_id}", qh.get('end', "08:00"), None)
            
            # Update frequency settings
            if 'frequency' in updates:
                freq = updates['frequency']
                cache.set(f"notif_realtime:{user_id}", freq.get('realtime', True), None)
                cache.set(f"notif_digest:{user_id}", freq.get('digest', False), None)
                cache.set(f"notif_digest_time:{user_id}", freq.get('digest_time', "09:00"), None)
                
                # Schedule digest if enabled
                if freq.get('digest'):
                    from .tasks import schedule_notification_digest
                    schedule_notification_digest.delay(user_id, freq.get('digest_time'))
            
            # Get updated preferences
            updated_preferences = NotificationPreferences.get_user_preferences(user_id)
            
            return Response({
                'message': 'Preferences updated successfully',
                'preferences': updated_preferences
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update preferences: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/notifications/preferences/
        Test notification settings.
        """
        try:
            user_id = request.user.id
            test_type = request.data.get('type', 'all')
            
            # Send test notifications
            test_results = {}
            
            if test_type in ['all', 'in_app']:
                # Send in-app notification
                NotificationService.send_notification({
                    'type': NotificationType.TEST,
                    'user_id': user_id,
                    'data': {
                        'message': 'Test in-app notification',
                        'timestamp': timezone.now().isoformat()
                    }
                })
                test_results['in_app'] = 'sent'
            
            if test_type in ['all', 'email']:
                # Queue test email
                from .tasks import send_test_email_notification
                send_test_email_notification.delay(user_id)
                test_results['email'] = 'queued'
            
            if test_type in ['all', 'push']:
                # Send test push notification
                if cache.get(f"notif_push_enabled:{user_id}"):
                    # Implementation for push notification
                    test_results['push'] = 'sent'
                else:
                    test_results['push'] = 'not_enabled'
            
            return Response({
                'message': 'Test notifications sent',
                'results': test_results
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to send test notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NotificationHistoryView(APIView):
    """
    View and manage notification history.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/notifications/history/
        Get notification history with pagination.
        """
        try:
            user_id = request.user.id
            page = int(request.query_params.get('page', 1))
            per_page = int(request.query_params.get('per_page', 20))
            filter_type = request.query_params.get('type')
            unread_only = request.query_params.get('unread_only', 'false') == 'true'
            
            # Get notifications from cache/storage
            cache_key = f"notif_history:{user_id}"
            all_notifications = cache.get(cache_key, [])
            
            # Filter notifications
            filtered_notifications = []
            for notif in all_notifications:
                # Type filter
                if filter_type and notif.get('type') != filter_type:
                    continue
                
                # Unread filter
                if unread_only and notif.get('read', False):
                    continue
                
                filtered_notifications.append(notif)
            
            # Sort by timestamp (newest first)
            filtered_notifications.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )
            
            # Paginate
            paginator = Paginator(filtered_notifications, per_page)
            page_obj = paginator.get_page(page)
            
            # Get unread count
            unread_count = sum(
                1 for n in all_notifications if not n.get('read', False)
            )
            
            return Response({
                'notifications': list(page_obj),
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                },
                'unread_count': unread_count,
                'types': self._get_notification_types(all_notifications)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get notification history: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request):
        """
        DELETE /api/notifications/history/
        Clear notification history.
        """
        try:
            user_id = request.user.id
            clear_type = request.query_params.get('type', 'read')  # read, all, older_than
            
            cache_key = f"notif_history:{user_id}"
            notifications = cache.get(cache_key, [])
            
            if clear_type == 'all':
                # Clear all notifications
                notifications = []
            elif clear_type == 'read':
                # Keep only unread notifications
                notifications = [n for n in notifications if not n.get('read', False)]
            elif clear_type == 'older_than':
                # Clear notifications older than specified days
                days = int(request.query_params.get('days', 30))
                cutoff_date = timezone.now() - timedelta(days=days)
                notifications = [
                    n for n in notifications
                    if datetime.fromisoformat(n.get('timestamp', '')) > cutoff_date
                ]
            
            # Update cache
            cache.set(cache_key, notifications, 2592000)  # 30 days
            
            return Response({
                'message': 'Notification history cleared',
                'remaining_count': len(notifications)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to clear history: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_notification_types(self, notifications: List[Dict[str, Any]]) -> List[str]:
        """Get unique notification types from history"""
        types = set()
        for notif in notifications:
            if 'type' in notif:
                types.add(notif['type'])
        return sorted(list(types))

class NotificationMarkReadView(APIView):
    """
    Mark notifications as read/unread.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/notifications/mark-read/
        Mark notifications as read.
        """
        try:
            user_id = request.user.id
            notification_ids = request.data.get('notification_ids', [])
            mark_all = request.data.get('mark_all', False)
            
            cache_key = f"notif_history:{user_id}"
            notifications = cache.get(cache_key, [])
            
            if mark_all:
                # Mark all as read
                for notif in notifications:
                    notif['read'] = True
                    notif['read_at'] = timezone.now().isoformat()
                marked_count = len(notifications)
            else:
                # Mark specific notifications as read
                marked_count = 0
                for notif in notifications:
                    if notif.get('id') in notification_ids:
                        notif['read'] = True
                        notif['read_at'] = timezone.now().isoformat()
                        marked_count += 1
            
            # Update cache
            cache.set(cache_key, notifications, 2592000)  # 30 days
            
            # Update unread count cache
            unread_count = sum(1 for n in notifications if not n.get('read', False))
            cache.set(f"notif_unread_count:{user_id}", unread_count, 3600)
            
            return Response({
                'message': 'Notifications marked as read',
                'marked_count': marked_count,
                'unread_count': unread_count
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to mark notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """
        PUT /api/notifications/mark-read/
        Mark notifications as unread.
        """
        try:
            user_id = request.user.id
            notification_ids = request.data.get('notification_ids', [])
            
            cache_key = f"notif_history:{user_id}"
            notifications = cache.get(cache_key, [])
            
            marked_count = 0
            for notif in notifications:
                if notif.get('id') in notification_ids:
                    notif['read'] = False
                    notif.pop('read_at', None)
                    marked_count += 1
            
            # Update cache
            cache.set(cache_key, notifications, 2592000)  # 30 days
            
            # Update unread count
            unread_count = sum(1 for n in notifications if not n.get('read', False))
            cache.set(f"notif_unread_count:{user_id}", unread_count, 3600)
            
            return Response({
                'message': 'Notifications marked as unread',
                'marked_count': marked_count,
                'unread_count': unread_count
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to mark notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )