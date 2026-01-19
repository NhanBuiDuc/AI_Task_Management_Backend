# File: tasks_api/views_collaboration.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime, timedelta

from .models import Task, Project, Section, User
from .serializers import TaskSerializer, ProjectSerializer, UserSerializer
from .utils.notifications import NotificationService, Notification, NotificationType
from .utils.analytics import AnalyticsTracker

class CollaborationSessionView(APIView):
    """
    Manage real-time collaboration sessions for planning and brainstorming.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/collaboration/sessions/
        Get active collaboration sessions for the user.
        """
        try:
            user_id = request.user.id
            session_type = request.query_params.get('type')  # planning, brainstorming, review
            
            # Get sessions from cache
            cache_pattern = f"collab_session:*:{user_id}"
            sessions = []
            
            # Get user's active sessions
            user_sessions_key = f"user_collab_sessions:{user_id}"
            session_ids = cache.get(user_sessions_key, [])
            
            for session_id in session_ids:
                session_data = cache.get(f"collab_session:{session_id}")
                if session_data:
                    if not session_type or session_data.get('type') == session_type:
                        sessions.append(session_data)
            
            return Response({
                'sessions': sessions,
                'count': len(sessions)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get sessions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/collaboration/sessions/
        Create a new collaboration session.
        """
        try:
            user_id = request.user.id
            session_data = request.data
            
            # Validate session data
            session_type = session_data.get('type', 'planning')
            title = session_data.get('title', f'{session_type.title()} Session')
            description = session_data.get('description', '')
            project_id = session_data.get('project_id')
            
            # Create session
            session_id = str(uuid.uuid4())
            session = {
                'id': session_id,
                'type': session_type,
                'title': title,
                'description': description,
                'project_id': project_id,
                'created_by': user_id,
                'participants': [user_id],
                'created_at': timezone.now().isoformat(),
                'status': 'active',
                'data': {
                    'ideas': [],
                    'tasks': [],
                    'votes': {},
                    'notes': ''
                }
            }
            
            # Store in cache with 24 hour expiry
            cache.set(f"collab_session:{session_id}", session, 86400)
            
            # Add to user's sessions
            user_sessions_key = f"user_collab_sessions:{user_id}"
            user_sessions = cache.get(user_sessions_key, [])
            user_sessions.append(session_id)
            cache.set(user_sessions_key, user_sessions, 86400)
            
            # Send notification to participants
            NotificationService.send_notification(
                Notification(
                    type=NotificationType.COLLABORATION_STARTED,
                    user_id=user_id,
                    data={
                        'session_id': session_id,
                        'title': title,
                        'type': session_type
                    }
                )
            )
            
            # Track analytics
            AnalyticsTracker.track_event(
                event_type='collaboration_session_created',
                user_id=user_id,
                data={'session_type': session_type}
            )
            
            return Response(session, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """
        PUT /api/collaboration/sessions/
        Update collaboration session data.
        """
        try:
            user_id = request.user.id
            session_id = request.data.get('session_id')
            update_type = request.data.get('update_type')  # add_idea, vote, create_task
            update_data = request.data.get('data', {})
            
            # Get session
            session = cache.get(f"collab_session:{session_id}")
            if not session:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user is participant
            if user_id not in session['participants']:
                return Response(
                    {'error': 'Not a participant in this session'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Handle different update types
            if update_type == 'add_idea':
                idea = {
                    'id': str(uuid.uuid4()),
                    'text': update_data.get('text'),
                    'author': user_id,
                    'created_at': timezone.now().isoformat(),
                    'votes': 0,
                    'tags': update_data.get('tags', [])
                }
                session['data']['ideas'].append(idea)
                
            elif update_type == 'vote':
                idea_id = update_data.get('idea_id')
                vote_value = update_data.get('value', 1)  # 1 for upvote, -1 for downvote
                
                # Update vote count
                for idea in session['data']['ideas']:
                    if idea['id'] == idea_id:
                        idea['votes'] += vote_value
                        break
                
                # Track user's vote
                if 'votes' not in session['data']:
                    session['data']['votes'] = {}
                session['data']['votes'][f"{user_id}:{idea_id}"] = vote_value
                
            elif update_type == 'create_task':
                # Create task from idea
                idea_id = update_data.get('idea_id')
                idea_text = None
                
                for idea in session['data']['ideas']:
                    if idea['id'] == idea_id:
                        idea_text = idea['text']
                        break
                
                if idea_text:
                    task_data = {
                        'title': idea_text[:100],
                        'description': f"Created from collaboration session: {session['title']}",
                        'project_id': session.get('project_id'),
                        'created_from_session': session_id
                    }
                    session['data']['tasks'].append(task_data)
                
            elif update_type == 'update_notes':
                session['data']['notes'] = update_data.get('notes', '')
                
            elif update_type == 'add_participant':
                new_participant_id = update_data.get('user_id')
                if new_participant_id not in session['participants']:
                    session['participants'].append(new_participant_id)
            
            # Update session in cache
            cache.set(f"collab_session:{session_id}", session, 86400)
            
            # Broadcast update to participants via WebSocket
            self._broadcast_session_update(session, update_type, update_data)
            
            return Response({
                'message': 'Session updated successfully',
                'session': session
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request):
        """
        DELETE /api/collaboration/sessions/
        End a collaboration session.
        """
        try:
            user_id = request.user.id
            session_id = request.query_params.get('session_id')
            
            # Get session
            session = cache.get(f"collab_session:{session_id}")
            if not session:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user is creator
            if session['created_by'] != user_id:
                return Response(
                    {'error': 'Only session creator can end the session'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Create tasks from session if any
            if session['data'].get('tasks'):
                created_tasks = self._create_tasks_from_session(
                    session['data']['tasks'],
                    user_id,
                    session_id
                )
                
                # Store session summary in database for future reference
                self._store_session_summary(session, created_tasks)
            
            # Remove session from cache
            cache.delete(f"collab_session:{session_id}")
            
            # Remove from all participants' sessions
            for participant_id in session['participants']:
                user_sessions_key = f"user_collab_sessions:{participant_id}"
                user_sessions = cache.get(user_sessions_key, [])
                if session_id in user_sessions:
                    user_sessions.remove(session_id)
                    cache.set(user_sessions_key, user_sessions, 86400)
            
            # Notify participants
            for participant_id in session['participants']:
                NotificationService.send_notification(
                    Notification(
                        type=NotificationType.COLLABORATION_ENDED,
                        user_id=participant_id,
                        data={
                            'session_id': session_id,
                            'title': session['title'],
                            'ended_by': user_id
                        }
                    )
                )
            
            return Response({
                'message': 'Session ended successfully',
                'tasks_created': len(session['data'].get('tasks', []))
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to end session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _broadcast_session_update(
        self,
        session: Dict[str, Any],
        update_type: str,
        update_data: Dict[str, Any]
    ) -> None:
        """Broadcast session update to all participants"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f"collab_planning_{session['id']}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "collaboration.update",
                    "update_type": update_type,
                    "data": update_data,
                    "session": session
                }
            )
    
    def _create_tasks_from_session(
        self,
        tasks_data: List[Dict[str, Any]],
        user_id: int,
        session_id: str
    ) -> List[Task]:
        """Create actual tasks from session data"""
        created_tasks = []
        
        with transaction.atomic():
            for task_data in tasks_data:
                task = Task.objects.create(
                    user_id=user_id,
                    title=task_data['title'],
                    description=task_data.get('description', ''),
                    project_id=task_data.get('project_id'),
                    labels=['collaboration', 'planned'],
                    metadata={
                        'created_from_session': session_id,
                        'session_type': 'collaboration'
                    }
                )
                created_tasks.append(task)
        
        return created_tasks
    
    def _store_session_summary(
        self,
        session: Dict[str, Any],
        created_tasks: List[Task]
    ) -> None:
        """Store session summary for future reference"""
        # This could be stored in MongoDB for analytics
        from .utils.mongodb import get_insights_collection
        
        summary = {
            'session_id': session['id'],
            'type': 'collaboration_session',
            'title': session['title'],
            'participants': session['participants'],
            'duration': (
                timezone.now() - datetime.fromisoformat(session['created_at'])
            ).total_seconds(),
            'ideas_count': len(session['data']['ideas']),
            'tasks_created': len(created_tasks),
            'task_ids': [task.id for task in created_tasks],
            'ended_at': timezone.now().isoformat()
        }
        
        get_insights_collection().insert_one(summary)

class SharedProjectView(APIView):
    """
    Manage shared projects and team collaboration.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/collaboration/shared-projects/
        Get projects shared with or by the user.
        """
        try:
            user_id = request.user.id
            filter_type = request.query_params.get('filter', 'all')  # all, owned, shared
            
            if filter_type == 'owned':
                # Projects owned by user that are shared
                projects = Project.objects.filter(
                    user_id=user_id,
                    is_shared=True
                ).annotate(
                    collaborator_count=Count('collaborators')
                )
            elif filter_type == 'shared':
                # Projects shared with user
                projects = Project.objects.filter(
                    collaborators__id=user_id
                ).annotate(
                    collaborator_count=Count('collaborators')
                )
            else:
                # All shared projects (owned or shared with)
                projects = Project.objects.filter(
                    Q(user_id=user_id, is_shared=True) |
                    Q(collaborators__id=user_id)
                ).distinct().annotate(
                    collaborator_count=Count('collaborators')
                )
            
            # Serialize with additional collaboration info
            serialized_projects = []
            for project in projects:
                project_data = ProjectSerializer(project).data
                project_data['is_owner'] = project.user_id == user_id
                project_data['collaborator_count'] = project.collaborator_count
                project_data['permissions'] = self._get_user_permissions(
                    project,
                    user_id
                )
                serialized_projects.append(project_data)
            
            return Response({
                'projects': serialized_projects,
                'count': len(serialized_projects)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get shared projects: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/collaboration/shared-projects/
        Share a project with other users.
        """
        try:
            user_id = request.user.id
            project_id = request.data.get('project_id')
            collaborator_emails = request.data.get('emails', [])
            permissions = request.data.get('permissions', 'edit')  # view, edit, admin
            message = request.data.get('message', '')
            
            # Get project
            try:
                project = Project.objects.get(id=project_id, user_id=user_id)
            except Project.DoesNotExist:
                return Response(
                    {'error': 'Project not found or not owned by user'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Find users by email
            collaborators = User.objects.filter(email__in=collaborator_emails)
            
            if not collaborators.exists():
                return Response(
                    {'error': 'No valid users found with provided emails'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Share project
            project.is_shared = True
            project.save()
            
            # Add collaborators
            added_collaborators = []
            for collaborator in collaborators:
                if collaborator.id != user_id:  # Don't add owner as collaborator
                    project.collaborators.add(collaborator)
                    added_collaborators.append(collaborator)
                    
                    # Store permissions in cache
                    perm_key = f"project_perms:{project_id}:{collaborator.id}"
                    cache.set(perm_key, permissions, None)
                    
                    # Send notification
                    NotificationService.send_notification(
                        Notification(
                            type=NotificationType.PROJECT_SHARED,
                            user_id=collaborator.id,
                            data={
                                'project_id': project_id,
                                'project_name': project.name,
                                'shared_by': request.user.get_full_name() or request.user.username,
                                'permissions': permissions,
                                'message': message
                            }
                        )
                    )
            
            # Track analytics
            AnalyticsTracker.track_event(
                event_type='project_shared',
                user_id=user_id,
                data={
                    'project_id': project_id,
                    'collaborator_count': len(added_collaborators)
                }
            )
            
            return Response({
                'message': 'Project shared successfully',
                'project_id': project_id,
                'collaborators_added': [
                    {'id': c.id, 'email': c.email}
                    for c in added_collaborators
                ]
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to share project: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """
        PUT /api/collaboration/shared-projects/
        Update sharing settings or permissions.
        """
        try:
            user_id = request.user.id
            project_id = request.data.get('project_id')
            collaborator_id = request.data.get('collaborator_id')
            new_permissions = request.data.get('permissions')
            action = request.data.get('action')  # update_permissions, remove_collaborator
            
            # Get project
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {'error': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user has admin permissions
            if not self._user_has_admin_permission(project, user_id):
                return Response(
                    {'error': 'Admin permission required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if action == 'update_permissions':
                # Update collaborator permissions
                perm_key = f"project_perms:{project_id}:{collaborator_id}"
                cache.set(perm_key, new_permissions, None)
                
                # Notify collaborator
                NotificationService.send_notification(
                    Notification(
                        type=NotificationType.PERMISSIONS_UPDATED,
                        user_id=collaborator_id,
                        data={
                            'project_id': project_id,
                            'project_name': project.name,
                            'new_permissions': new_permissions
                        }
                    )
                )
                
            elif action == 'remove_collaborator':
                # Remove collaborator
                project.collaborators.remove(collaborator_id)
                
                # Remove permissions
                perm_key = f"project_perms:{project_id}:{collaborator_id}"
                cache.delete(perm_key)
                
                # Notify removed collaborator
                NotificationService.send_notification(
                    Notification(
                        type=NotificationType.REMOVED_FROM_PROJECT,
                        user_id=collaborator_id,
                        data={
                            'project_id': project_id,
                            'project_name': project.name
                        }
                    )
                )
                
                # Check if project still has collaborators
                if project.collaborators.count() == 0:
                    project.is_shared = False
                    project.save()
            
            return Response({
                'message': 'Project sharing updated successfully'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update sharing: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_permissions(self, project: Project, user_id: int) -> str:
        """Get user's permissions for a project"""
        if project.user_id == user_id:
            return 'owner'
        
        perm_key = f"project_perms:{project.id}:{user_id}"
        return cache.get(perm_key, 'view')
    
    def _user_has_admin_permission(self, project: Project, user_id: int) -> bool:
        """Check if user has admin permission on project"""
        if project.user_id == user_id:
            return True
        
        permissions = self._get_user_permissions(project, user_id)
        return permissions in ['admin', 'owner']

class TeamWorkspaceView(APIView):
    """
    Manage team workspaces for larger collaboration.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/collaboration/workspaces/
        Get user's team workspaces.
        """
        try:
            user_id = request.user.id
            
            # Get workspaces from cache (in production, this would be from database)
            workspace_keys = cache.keys(f"workspace:*:members")
            workspaces = []
            
            for key in workspace_keys:
                members = cache.get(key, [])
                if user_id in members:
                    workspace_id = key.split(':')[1]
                    workspace_data = cache.get(f"workspace:{workspace_id}")
                    if workspace_data:
                        workspaces.append(workspace_data)
            
            return Response({
                'workspaces': workspaces,
                'count': len(workspaces)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get workspaces: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /api/collaboration/workspaces/
        Create a new team workspace.
        """
        try:
            user_id = request.user.id
            workspace_data = request.data
            
            # Create workspace
            workspace_id = str(uuid.uuid4())
            workspace = {
                'id': workspace_id,
                'name': workspace_data.get('name', 'Team Workspace'),
                'description': workspace_data.get('description', ''),
                'created_by': user_id,
                'created_at': timezone.now().isoformat(),
                'settings': {
                    'default_project_sharing': True,
                    'allow_guest_access': False,
                    'require_task_approval': False
                },
                'stats': {
                    'member_count': 1,
                    'project_count': 0,
                    'active_tasks': 0
                }
            }
            
            # Store workspace
            cache.set(f"workspace:{workspace_id}", workspace, None)
            cache.set(f"workspace:{workspace_id}:members", [user_id], None)
            
            # Add to user's workspaces
            user_workspaces_key = f"user_workspaces:{user_id}"
            user_workspaces = cache.get(user_workspaces_key, [])
            user_workspaces.append(workspace_id)
            cache.set(user_workspaces_key, user_workspaces, None)
            
            return Response(workspace, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create workspace: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CollaboratorsView(APIView):
    """
    Manage and search for collaborators.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET /api/collaboration/collaborators/
        Get user's collaborators or search for new ones.
        """
        try:
            user_id = request.user.id
            search_query = request.query_params.get('q')
            project_id = request.query_params.get('project_id')
            
            if search_query:
                # Search for users
                users = User.objects.filter(
                    Q(email__icontains=search_query) |
                    Q(username__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query)
                ).exclude(id=user_id)[:10]
                
                serialized_users = UserSerializer(users, many=True).data
                
            elif project_id:
                # Get project collaborators
                try:
                    project = Project.objects.get(id=project_id)
                    collaborators = project.collaborators.all()
                    
                    serialized_users = []
                    for collaborator in collaborators:
                        user_data = UserSerializer(collaborator).data
                        user_data['permissions'] = self._get_user_permissions(
                            project,
                            collaborator.id
                        )
                        serialized_users.append(user_data)
                        
                except Project.DoesNotExist:
                    return Response(
                        {'error': 'Project not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Get all user's collaborators across projects
                collaborated_projects = Project.objects.filter(
                    Q(user_id=user_id) | Q(collaborators__id=user_id)
                ).distinct()
                
                collaborator_ids = set()
                for project in collaborated_projects:
                    collaborator_ids.update(
                        project.collaborators.values_list('id', flat=True)
                    )
                    if project.user_id != user_id:
                        collaborator_ids.add(project.user_id)
                
                collaborator_ids.discard(user_id)  # Remove self
                
                collaborators = User.objects.filter(id__in=collaborator_ids)
                serialized_users = UserSerializer(collaborators, many=True).data
            
            return Response({
                'collaborators': serialized_users,
                'count': len(serialized_users)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get collaborators: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_permissions(self, project: Project, user_id: int) -> str:
        """Get user's permissions for a project"""
        if project.user_id == user_id:
            return 'owner'
        
        perm_key = f"project_perms:{project.id}:{user_id}"
        return cache.get(perm_key, 'view')