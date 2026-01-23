# File: tasks_api/views_collaboration.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from .models import (
    Task, Project, Section, Account,
    TaskCollaboration, TaskInvitation, ProjectCollaboration
)
from .serializers import (
    TaskSerializer, ProjectSerializer,
    TaskCollaborationSerializer, TaskInvitationSerializer,
    CreateTaskInvitationSerializer, InvitationResponseSerializer,
    UpdateCollaborationPermissionSerializer, SharedTaskSerializer,
    CollaboratorSerializer
)

User = get_user_model()
from .utils.notifications import NotificationService, Notification, NotificationType
from .utils.analytics import AnalyticsTracker


# ============================================
# Helper function to get account from request
# ============================================

def get_account_from_request(request):
    """
    Get account from request. Uses X-Account-ID header for simple auth.
    In production, this should use proper JWT/session authentication.
    """
    account_id = request.headers.get('X-Account-ID')
    if not account_id:
        return None
    try:
        return Account.objects.get(id=account_id, is_active=True)
    except (Account.DoesNotExist, ValueError):
        return None


# ============================================
# Task Invitation Views
# ============================================

class TaskInvitationView(APIView):
    """
    Manage task collaboration invitations.

    POST - Send a new invitation
    GET - List invitations (sent or received)
    """
    permission_classes = [AllowAny]  # Using custom auth via header

    def get(self, request):
        """
        GET /api/collaboration/invitations/
        List invitations sent by or received by the user.

        Query params:
        - type: 'sent' or 'received' (default: 'received')
        - status: 'pending', 'accepted', 'declined', 'all' (default: 'pending')
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        invitation_type = request.query_params.get('type', 'received')
        status_filter = request.query_params.get('status', 'pending')

        if invitation_type == 'sent':
            invitations = TaskInvitation.objects.filter(invited_by=account)
        else:
            invitations = TaskInvitation.objects.filter(invitee=account)

        if status_filter != 'all':
            invitations = invitations.filter(status=status_filter)

        invitations = invitations.select_related(
            'task', 'invited_by', 'invitee'
        ).order_by('-created_at')

        serializer = TaskInvitationSerializer(invitations, many=True)
        return Response({
            'invitations': serializer.data,
            'count': invitations.count()
        })

    def post(self, request):
        """
        POST /api/collaboration/invitations/
        Send a new task collaboration invitation.

        Body:
        {
            "task_id": "uuid",
            "invitee_id": "uuid" (optional),
            "invitee_email": "email@example.com" (optional),
            "permission": "view" | "edit" | "admin",
            "message": "Optional invitation message"
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = CreateTaskInvitationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        task_id = data['task_id']

        # Verify task exists and user has permission to share it
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user owns the task or has admin permission
        if task.user != account:
            collaboration = TaskCollaboration.objects.filter(
                task=task, collaborator=account, is_active=True
            ).first()
            if not collaboration or not collaboration.can_admin():
                return Response(
                    {'error': 'You do not have permission to share this task'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Find or validate invitee
        invitee = None
        invitee_email = data.get('invitee_email')

        if data.get('invitee_id'):
            try:
                invitee = Account.objects.get(id=data['invitee_id'], is_active=True)
            except Account.DoesNotExist:
                return Response(
                    {'error': 'Invitee not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif invitee_email:
            # Try to find user by email
            invitee = Account.objects.filter(email=invitee_email, is_active=True).first()

        # Cannot invite yourself
        if invitee and invitee == account:
            return Response(
                {'error': 'You cannot invite yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing pending invitation
        existing = TaskInvitation.objects.filter(
            task=task,
            status='pending'
        )
        if invitee:
            existing = existing.filter(invitee=invitee)
        elif invitee_email:
            existing = existing.filter(invitee_email=invitee_email)

        if existing.exists():
            return Response(
                {'error': 'An invitation is already pending for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already a collaborator
        if invitee:
            existing_collab = TaskCollaboration.objects.filter(
                task=task, collaborator=invitee, is_active=True
            ).exists()
            if existing_collab:
                return Response(
                    {'error': 'User is already a collaborator on this task'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create invitation
        invitation = TaskInvitation.objects.create(
            task=task,
            invited_by=account,
            invitee=invitee,
            invitee_email=invitee_email if not invitee else None,
            permission=data['permission'],
            message=data.get('message', ''),
            expires_at=timezone.now() + timedelta(days=7)  # 7 day expiry
        )

        # Send notification if invitee exists
        if invitee:
            try:
                NotificationService.send_notification(
                    Notification(
                        type=NotificationType.TASK_SHARED,
                        user_id=invitee.id,
                        data={
                            'invitation_id': str(invitation.id),
                            'task_id': str(task.id),
                            'task_name': task.name,
                            'invited_by': account.display_name or account.username,
                            'permission': data['permission']
                        }
                    )
                )
            except Exception:
                pass  # Don't fail if notification fails

        serializer = TaskInvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskInvitationResponseView(APIView):
    """
    Respond to a task invitation (accept/decline).

    POST /api/collaboration/invitations/<invitation_id>/respond/
    """
    permission_classes = [AllowAny]

    def post(self, request, invitation_id):
        """
        Accept or decline an invitation.

        Body:
        {
            "action": "accept" | "decline"
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            invitation = TaskInvitation.objects.get(id=invitation_id)
        except TaskInvitation.DoesNotExist:
            return Response(
                {'error': 'Invitation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify the user is the invitee
        if invitation.invitee != account:
            return Response(
                {'error': 'You are not the invitee for this invitation'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InvitationResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']

        if action == 'accept':
            collaboration = invitation.accept()
            if not collaboration:
                return Response(
                    {'error': 'Invitation is no longer valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Notify the inviter
            try:
                NotificationService.send_notification(
                    Notification(
                        type=NotificationType.INVITATION_ACCEPTED,
                        user_id=invitation.invited_by.id,
                        data={
                            'task_id': str(invitation.task.id),
                            'task_name': invitation.task.name,
                            'accepted_by': account.display_name or account.username
                        }
                    )
                )
            except Exception:
                pass

            return Response({
                'message': 'Invitation accepted',
                'collaboration': TaskCollaborationSerializer(collaboration).data
            })

        else:  # decline
            if not invitation.decline():
                return Response(
                    {'error': 'Invitation is no longer valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({'message': 'Invitation declined'})


class TaskInvitationCancelView(APIView):
    """
    Cancel a sent invitation.

    DELETE /api/collaboration/invitations/<invitation_id>/
    """
    permission_classes = [AllowAny]

    def delete(self, request, invitation_id):
        """Cancel a pending invitation."""
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            invitation = TaskInvitation.objects.get(id=invitation_id)
        except TaskInvitation.DoesNotExist:
            return Response(
                {'error': 'Invitation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify the user is the inviter
        if invitation.invited_by != account:
            return Response(
                {'error': 'You can only cancel invitations you sent'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not invitation.cancel():
            return Response(
                {'error': 'Invitation cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'message': 'Invitation cancelled'})


# ============================================
# Task Collaboration Views
# ============================================

class TaskCollaboratorsView(APIView):
    """
    Manage collaborators for a task.

    GET - List collaborators for a task
    """
    permission_classes = [AllowAny]

    def get(self, request, task_id):
        """
        GET /api/collaboration/tasks/<task_id>/collaborators/
        List all collaborators for a task.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has access to the task
        if task.user != account:
            collaboration = TaskCollaboration.objects.filter(
                task=task, collaborator=account, is_active=True
            ).first()
            if not collaboration:
                return Response(
                    {'error': 'You do not have access to this task'},
                    status=status.HTTP_403_FORBIDDEN
                )

        collaborations = TaskCollaboration.objects.filter(
            task=task, is_active=True
        ).select_related('collaborator', 'owner')

        serializer = TaskCollaborationSerializer(collaborations, many=True)

        # Also include the owner
        owner_data = CollaboratorSerializer(task.user).data
        owner_data['permission'] = 'owner'

        return Response({
            'owner': owner_data,
            'collaborators': serializer.data,
            'count': collaborations.count()
        })


class TaskCollaborationUpdateView(APIView):
    """
    Update or remove a collaboration.

    PATCH - Update collaboration permission
    DELETE - Remove collaboration
    """
    permission_classes = [AllowAny]

    def patch(self, request, collaboration_id):
        """
        PATCH /api/collaboration/collaborations/<collaboration_id>/
        Update collaboration permission.

        Body:
        {
            "permission": "view" | "edit" | "admin"
        }
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            collaboration = TaskCollaboration.objects.select_related('task').get(
                id=collaboration_id
            )
        except TaskCollaboration.DoesNotExist:
            return Response(
                {'error': 'Collaboration not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has admin permission
        task = collaboration.task
        if task.user != account:
            user_collab = TaskCollaboration.objects.filter(
                task=task, collaborator=account, is_active=True
            ).first()
            if not user_collab or not user_collab.can_admin():
                return Response(
                    {'error': 'You do not have permission to modify collaborators'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = UpdateCollaborationPermissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        collaboration.permission = serializer.validated_data['permission']
        collaboration.save(update_fields=['permission', 'updated_at'])

        return Response({
            'message': 'Permission updated',
            'collaboration': TaskCollaborationSerializer(collaboration).data
        })

    def delete(self, request, collaboration_id):
        """
        DELETE /api/collaboration/collaborations/<collaboration_id>/
        Remove a collaboration.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            collaboration = TaskCollaboration.objects.select_related('task').get(
                id=collaboration_id
            )
        except TaskCollaboration.DoesNotExist:
            return Response(
                {'error': 'Collaboration not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        task = collaboration.task

        # Allow removal if:
        # 1. User is the task owner
        # 2. User has admin permission
        # 3. User is removing themselves
        can_remove = False
        if task.user == account:
            can_remove = True
        elif collaboration.collaborator == account:
            can_remove = True  # User can leave a collaboration
        else:
            user_collab = TaskCollaboration.objects.filter(
                task=task, collaborator=account, is_active=True
            ).first()
            if user_collab and user_collab.can_admin():
                can_remove = True

        if not can_remove:
            return Response(
                {'error': 'You do not have permission to remove this collaborator'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Soft delete by marking inactive
        collaboration.is_active = False
        collaboration.save(update_fields=['is_active', 'updated_at'])

        # Notify the removed collaborator
        try:
            NotificationService.send_notification(
                Notification(
                    type=NotificationType.REMOVED_FROM_PROJECT,  # Reusing type
                    user_id=collaboration.collaborator.id,
                    data={
                        'task_id': str(task.id),
                        'task_name': task.name,
                        'removed_by': account.display_name or account.username
                    }
                )
            )
        except Exception:
            pass

        return Response({'message': 'Collaborator removed'})


# ============================================
# Shared Tasks View
# ============================================

class SharedTasksView(APIView):
    """
    List tasks shared with the user.

    GET /api/collaboration/shared-tasks/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Get all tasks that have been shared with the user.

        Query params:
        - permission: Filter by permission level ('view', 'edit', 'admin')
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_filter = request.query_params.get('permission')

        collaborations = TaskCollaboration.objects.filter(
            collaborator=account,
            is_active=True
        ).select_related('task', 'task__user', 'task__project', 'task__section')

        if permission_filter:
            collaborations = collaborations.filter(permission=permission_filter)

        # Get task IDs from collaborations
        task_ids = collaborations.values_list('task_id', flat=True)
        tasks = Task.objects.filter(
            id__in=task_ids,
            totally_completed=False
        ).prefetch_related('task_views', 'collaborations')

        # Add request to context for permission lookup
        request.account = account
        serializer = SharedTaskSerializer(
            tasks, many=True, context={'request': request}
        )

        return Response({
            'tasks': serializer.data,
            'count': tasks.count()
        })


# ============================================
# User Search for Collaboration
# ============================================

class UserSearchView(APIView):
    """
    Search for users to invite for collaboration.

    GET /api/collaboration/users/search/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Search for users by username or email.

        Query params:
        - q: Search query (required, min 2 characters)
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        users = Account.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(display_name__icontains=query),
            is_active=True
        ).exclude(id=account.id)[:10]

        serializer = CollaboratorSerializer(users, many=True)
        return Response({
            'users': serializer.data,
            'count': len(serializer.data)
        })


# ============================================
# Project Collaboration Views (Role-based)
# ============================================

class JoinProjectView(APIView):
    """
    Join a project using access_id.

    POST /api/collaboration/projects/join/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Join a project using its access_id.

        Body:
        {
            "access_id": "ABC12345"
        }
        """
        from .serializers import JoinProjectSerializer, ProjectCollaborationSerializer

        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = JoinProjectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        access_id = serializer.validated_data['access_id'].upper()

        # Find project by access_id
        try:
            project = Project.objects.get(access_id=access_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Invalid access code'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is already the owner
        if project.user == account:
            return Response(
                {'error': 'You are the owner of this project'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already a collaborator
        existing = ProjectCollaboration.objects.filter(
            project=project, collaborator=account
        ).first()

        if existing:
            if existing.is_active:
                return Response(
                    {'error': 'You are already a collaborator on this project'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Reactivate
                existing.is_active = True
                existing.joined_at = timezone.now()
                existing.save()
                collaboration = existing
        else:
            # Create new collaboration as collaborator (lowest role)
            collaboration = ProjectCollaboration.objects.create(
                project=project,
                collaborator=account,
                role='collaborator',
                is_active=True,
                joined_at=timezone.now()
            )

        # Enable collaborative mode
        if not project.is_collaborative:
            project.is_collaborative = True
            project.save(update_fields=['is_collaborative', 'updated_at'])

        # Notify project owner
        try:
            NotificationService.send_notification(
                Notification(
                    type=NotificationType.PROJECT_SHARED,
                    user_id=project.user.id,
                    data={
                        'project_id': str(project.id),
                        'project_name': project.name,
                        'joined_by': account.display_name or account.username
                    }
                )
            )
        except Exception:
            pass

        return Response({
            'message': 'Successfully joined project',
            'collaboration': ProjectCollaborationSerializer(collaboration).data,
            'project': {
                'id': str(project.id),
                'name': project.name,
                'owner': {
                    'id': str(project.user.id),
                    'username': project.user.username,
                    'display_name': project.user.display_name
                }
            }
        }, status=status.HTTP_201_CREATED)


class ProjectCollaboratorsView(APIView):
    """
    Manage collaborators for a project.

    GET - List all collaborators
    POST - Invite a new collaborator
    """
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        """
        GET /api/collaboration/projects/<project_id>/collaborators/
        List all collaborators for a project including the owner.
        """
        from .serializers import ProjectCollaborationSerializer

        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has access
        is_owner = project.user == account
        is_collaborator = ProjectCollaboration.objects.filter(
            project=project, collaborator=account, is_active=True
        ).exists()

        if not is_owner and not is_collaborator:
            return Response(
                {'error': 'You do not have access to this project'},
                status=status.HTTP_403_FORBIDDEN
            )

        collaborations = ProjectCollaboration.objects.filter(
            project=project, is_active=True
        ).select_related('collaborator')

        # Build response with owner info
        owner_data = CollaboratorSerializer(project.user).data
        owner_data['role'] = 'owner'

        return Response({
            'owner': owner_data,
            'collaborators': ProjectCollaborationSerializer(collaborations, many=True).data,
            'access_id': project.access_id if is_owner else None,
            'count': collaborations.count()
        })


class ProjectCollaboratorDetailView(APIView):
    """
    Update or remove a project collaborator.

    PATCH - Update collaborator role
    DELETE - Remove collaborator
    """
    permission_classes = [AllowAny]

    def patch(self, request, project_id, collaborator_id):
        """
        PATCH /api/collaboration/projects/<project_id>/collaborators/<collaborator_id>/
        Update collaborator role (only owner can do this).

        Body:
        {
            "role": "moderator" | "collaborator"
        }
        """
        from .serializers import UpdateProjectRoleSerializer, ProjectCollaborationSerializer

        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only owner can change roles
        if project.user != account:
            return Response(
                {'error': 'Only the project owner can change roles'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            collaboration = ProjectCollaboration.objects.get(
                project=project, collaborator_id=collaborator_id, is_active=True
            )
        except ProjectCollaboration.DoesNotExist:
            return Response(
                {'error': 'Collaborator not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateProjectRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        collaboration.role = serializer.validated_data['role']
        collaboration.save(update_fields=['role', 'updated_at'])

        # Notify the collaborator
        try:
            NotificationService.send_notification(
                Notification(
                    type=NotificationType.PERMISSIONS_UPDATED,
                    user_id=collaboration.collaborator.id,
                    data={
                        'project_id': str(project.id),
                        'project_name': project.name,
                        'new_role': collaboration.role
                    }
                )
            )
        except Exception:
            pass

        return Response({
            'message': 'Role updated',
            'collaboration': ProjectCollaborationSerializer(collaboration).data
        })

    def delete(self, request, project_id, collaborator_id):
        """
        DELETE /api/collaboration/projects/<project_id>/collaborators/<collaborator_id>/
        Remove a collaborator from the project.
        """
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required. Provide X-Account-ID header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            collaboration = ProjectCollaboration.objects.get(
                project=project, collaborator_id=collaborator_id
            )
        except ProjectCollaboration.DoesNotExist:
            return Response(
                {'error': 'Collaborator not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Allow removal if:
        # 1. User is the project owner
        # 2. User is removing themselves (leaving the project)
        is_owner = project.user == account
        is_self = str(collaborator_id) == str(account.id)

        if not is_owner and not is_self:
            return Response(
                {'error': 'You can only remove yourself or be the owner to remove others'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Soft delete
        collaboration.is_active = False
        collaboration.save(update_fields=['is_active', 'updated_at'])

        # Notify if owner removed someone
        if is_owner and not is_self:
            try:
                NotificationService.send_notification(
                    Notification(
                        type=NotificationType.REMOVED_FROM_PROJECT,
                        user_id=collaboration.collaborator.id,
                        data={
                            'project_id': str(project.id),
                            'project_name': project.name
                        }
                    )
                )
            except Exception:
                pass

        return Response({'message': 'Collaborator removed'})


class ProjectAccessIdView(APIView):
    """
    Manage project access_id.

    GET - Get current access_id
    POST - Regenerate access_id
    """
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        """Get project access_id (owner only)."""
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if project.user != account:
            return Response(
                {'error': 'Only the owner can view the access code'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            'access_id': project.access_id,
            'is_collaborative': project.is_collaborative
        })

    def post(self, request, project_id):
        """Regenerate project access_id (owner only)."""
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if project.user != account:
            return Response(
                {'error': 'Only the owner can regenerate the access code'},
                status=status.HTTP_403_FORBIDDEN
            )

        new_access_id = project.regenerate_access_id()

        return Response({
            'message': 'Access code regenerated',
            'access_id': new_access_id
        })


class TransferOwnershipView(APIView):
    """
    Transfer project ownership to another collaborator.

    POST /api/collaboration/projects/<project_id>/transfer/
    """
    permission_classes = [AllowAny]

    def post(self, request, project_id):
        """
        Transfer ownership to another user.

        Body:
        {
            "new_owner_id": "uuid"
        }
        """
        from .serializers import TransferOwnershipSerializer

        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if project.user != account:
            return Response(
                {'error': 'Only the owner can transfer ownership'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TransferOwnershipSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_owner_id = serializer.validated_data['new_owner_id']

        # Find new owner (must be a collaborator)
        try:
            new_owner = Account.objects.get(id=new_owner_id, is_active=True)
        except Account.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify new owner is a collaborator
        is_collaborator = ProjectCollaboration.objects.filter(
            project=project, collaborator=new_owner, is_active=True
        ).exists()

        if not is_collaborator:
            return Response(
                {'error': 'New owner must be a collaborator on the project'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Transfer ownership
        project.transfer_ownership(new_owner)

        # Notify new owner
        try:
            NotificationService.send_notification(
                Notification(
                    type=NotificationType.PERMISSIONS_UPDATED,
                    user_id=new_owner.id,
                    data={
                        'project_id': str(project.id),
                        'project_name': project.name,
                        'message': 'You are now the owner of this project'
                    }
                )
            )
        except Exception:
            pass

        return Response({
            'message': 'Ownership transferred successfully',
            'new_owner': {
                'id': str(new_owner.id),
                'username': new_owner.username,
                'display_name': new_owner.display_name
            }
        })


class TaskAssignmentView(APIView):
    """
    Assign users to a task.

    GET - Get assigned users
    POST - Assign users to task
    """
    permission_classes = [AllowAny]

    def get(self, request, task_id):
        """Get users assigned to a task."""
        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check access
        if not self._has_task_access(task, account):
            return Response(
                {'error': 'You do not have access to this task'},
                status=status.HTTP_403_FORBIDDEN
            )

        assigned_users = task.assigned_to.all()
        return Response({
            'assigned_to': CollaboratorSerializer(assigned_users, many=True).data,
            'count': assigned_users.count()
        })

    def post(self, request, task_id):
        """
        Assign users to a task.

        Body:
        {
            "user_ids": ["uuid1", "uuid2"]
        }
        """
        from .serializers import AssignTaskSerializer

        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user can assign (owner or moderator)
        if not self._can_assign_task(task, account):
            return Response(
                {'error': 'You do not have permission to assign users to this task'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AssignTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_ids = serializer.validated_data['user_ids']

        # Validate that all users are collaborators on the project
        if task.project:
            valid_collaborator_ids = set(
                ProjectCollaboration.objects.filter(
                    project=task.project, is_active=True
                ).values_list('collaborator_id', flat=True)
            )
            # Also include project owner
            valid_collaborator_ids.add(task.project.user.id)

            invalid_ids = [uid for uid in user_ids if uid not in valid_collaborator_ids]
            if invalid_ids:
                return Response(
                    {'error': 'Some users are not collaborators on this project'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Update assignments
        task.assigned_to.clear()
        if user_ids:
            users_to_assign = Account.objects.filter(id__in=user_ids, is_active=True)
            task.assigned_to.add(*users_to_assign)

            # Notify assigned users
            for user in users_to_assign:
                if user != account:
                    try:
                        NotificationService.send_notification(
                            Notification(
                                type=NotificationType.TASK_SHARED,
                                user_id=user.id,
                                data={
                                    'task_id': str(task.id),
                                    'task_name': task.name,
                                    'assigned_by': account.display_name or account.username
                                }
                            )
                        )
                    except Exception:
                        pass

        return Response({
            'message': 'Task assignments updated',
            'assigned_to': CollaboratorSerializer(task.assigned_to.all(), many=True).data
        })

    def _has_task_access(self, task, account):
        """Check if user has read access to the task."""
        # Owner of the task
        if task.user == account:
            return True

        # Project owner or collaborator
        if task.project:
            if task.project.user == account:
                return True
            return ProjectCollaboration.objects.filter(
                project=task.project, collaborator=account, is_active=True
            ).exists()

        return False

    def _can_assign_task(self, task, account):
        """Check if user can assign people to the task."""
        # Task owner
        if task.user == account:
            return True

        # Project owner
        if task.project and task.project.user == account:
            return True

        # Moderator
        if task.project:
            collab = ProjectCollaboration.objects.filter(
                project=task.project, collaborator=account, is_active=True
            ).first()
            return collab and collab.role == 'moderator'

        return False


class CollaborativeProjectsView(APIView):
    """
    Get all collaborative projects for the current user.

    GET /api/collaboration/projects/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Get all projects the user owns or collaborates on."""
        from .serializers import ProjectSerializer

        account = get_account_from_request(request)
        if not account:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        filter_type = request.query_params.get('filter', 'all')

        if filter_type == 'owned':
            # Projects owned by user that have collaborators
            projects = Project.objects.filter(
                user=account, is_collaborative=True
            )
        elif filter_type == 'shared':
            # Projects shared with user
            project_ids = ProjectCollaboration.objects.filter(
                collaborator=account, is_active=True
            ).values_list('project_id', flat=True)
            projects = Project.objects.filter(id__in=project_ids)
        else:
            # All collaborative projects (owned or shared)
            owned_ids = Project.objects.filter(
                user=account, is_collaborative=True
            ).values_list('id', flat=True)
            collab_ids = ProjectCollaboration.objects.filter(
                collaborator=account, is_active=True
            ).values_list('project_id', flat=True)
            all_ids = set(owned_ids) | set(collab_ids)
            projects = Project.objects.filter(id__in=all_ids)

        # Add role info to each project
        results = []
        for project in projects:
            project_data = ProjectSerializer(project).data
            if project.user == account:
                project_data['my_role'] = 'owner'
            else:
                collab = ProjectCollaboration.objects.filter(
                    project=project, collaborator=account, is_active=True
                ).first()
                project_data['my_role'] = collab.role if collab else None
            results.append(project_data)

        return Response({
            'projects': results,
            'count': len(results)
        })


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