# File: tasks_api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    TaskViewSet,
    ProjectViewSet,
    SectionViewSet,
)
from .views_agent import (
    AIIntentionView,
    AIInsightsView,
    AIPatternAnalysisView,
    AISuggestionsView,
    AIBatchProcessView,
    AIStreamingView,
    AIChatView,
    AISuggestionsManageView,
    AIChatHistoryView,
    # New intent-based views
    AIIntentChatView,
    AIIntentExecuteView,
    AIIntentListView,
    # Multi-task extraction views
    AITaskExtractView,
    AIBatchCreateView,
    AIIntentSessionView,
    AIQuickTaskView,
)
from .views_analytics import (
    UserAnalyticsView,
    ProductivityReportView,
    TaskPatternsView,
    SystemMetricsView,
    AnalyticsExportView,
    DashboardDataView
)
from .views_collaboration import (
    CollaborationSessionView,
    SharedProjectView,
    TeamWorkspaceView,
    CollaboratorsView,
    # Task collaboration views
    TaskInvitationView,
    TaskInvitationResponseView,
    TaskInvitationCancelView,
    TaskCollaboratorsView,
    TaskCollaborationUpdateView,
    SharedTasksView,
    UserSearchView,
    # Project collaboration views (role-based)
    JoinProjectView,
    ProjectCollaboratorsView,
    ProjectCollaboratorDetailView,
    ProjectAccessIdView,
    TransferOwnershipView,
    TaskAssignmentView,
    CollaborativeProjectsView
)
from .views_notifications import (
    NotificationPreferencesView,
    NotificationHistoryView,
    NotificationMarkReadView
)
from .views_scheduler import (
    generate_schedule,
    schedule_preview,
    score_task,
    workload_analysis
)
from .views_account import (
    register,
    login,
    profile,
    update_profile,
    change_password,
    list_accounts,
    delete_account
)

# Main router
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'sections', SectionViewSet, basename='section')

# Nested routers for related resources
projects_router = nested_routers.NestedDefaultRouter(
    router,
    r'projects',
    lookup='project'
)
projects_router.register(
    r'sections',
    SectionViewSet,
    basename='project-sections'
)

app_name = 'tasks_api'

urlpatterns = [
    # Include routers
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    
    # AI Agent endpoints
    path('ai/', include([
        # Legacy endpoints
        path('process/', AIIntentionView.as_view(), name='ai-process'),
        path('insights/', AIInsightsView.as_view(), name='ai-insights'),
        path('patterns/', AIPatternAnalysisView.as_view(), name='ai-patterns'),
        path('suggestions/', AISuggestionsView.as_view(), name='ai-suggestions'),
        path('batch/', AIBatchProcessView.as_view(), name='ai-batch'),
        path('stream/', AIStreamingView.as_view(), name='ai-stream'),
        # New chat-based endpoints
        path('chat/', AIChatView.as_view(), name='ai-chat'),
        path('chat/<str:session_id>/history/', AIChatHistoryView.as_view(), name='ai-chat-history'),
        path('suggestions/<str:session_id>/', AISuggestionsManageView.as_view(), name='ai-suggestions-manage'),
        # Intent-based endpoints (more efficient)
        path('intent/', AIIntentChatView.as_view(), name='ai-intent'),
        path('intent/execute/', AIIntentExecuteView.as_view(), name='ai-intent-execute'),
        path('intent/list/', AIIntentListView.as_view(), name='ai-intent-list'),
        path('intent/session/<str:session_id>/', AIIntentSessionView.as_view(), name='ai-intent-session'),
        # Multi-task extraction endpoints
        path('extract/', AITaskExtractView.as_view(), name='ai-extract'),
        path('batch-create/', AIBatchCreateView.as_view(), name='ai-batch-create'),
        path('quick-task/', AIQuickTaskView.as_view(), name='ai-quick-task'),
    ])),
    
    # Analytics endpoints
    path('analytics/', include([
        path('user/', UserAnalyticsView.as_view(), name='analytics-user'),
        path('productivity/', ProductivityReportView.as_view(), name='analytics-productivity'),
        path('patterns/', TaskPatternsView.as_view(), name='analytics-patterns'),
        path('system/', SystemMetricsView.as_view(), name='analytics-system'),
        path('export/', AnalyticsExportView.as_view(), name='analytics-export'),
        path('dashboard/', DashboardDataView.as_view(), name='analytics-dashboard'),
    ])),
    
    # Collaboration endpoints
    path('collaboration/', include([
        # Legacy collaboration endpoints
        path('sessions/', CollaborationSessionView.as_view(), name='collab-sessions'),
        path('shared-projects/', SharedProjectView.as_view(), name='collab-shared-projects'),
        path('workspaces/', TeamWorkspaceView.as_view(), name='collab-workspaces'),
        path('collaborators/', CollaboratorsView.as_view(), name='collab-collaborators'),

        # Task invitation endpoints
        path('invitations/', TaskInvitationView.as_view(), name='collab-invitations'),
        path('invitations/<uuid:invitation_id>/respond/', TaskInvitationResponseView.as_view(), name='collab-invitation-respond'),
        path('invitations/<uuid:invitation_id>/', TaskInvitationCancelView.as_view(), name='collab-invitation-cancel'),

        # Task collaboration endpoints
        path('tasks/<uuid:task_id>/collaborators/', TaskCollaboratorsView.as_view(), name='collab-task-collaborators'),
        path('collaborations/<uuid:collaboration_id>/', TaskCollaborationUpdateView.as_view(), name='collab-update'),

        # Shared tasks endpoint
        path('shared-tasks/', SharedTasksView.as_view(), name='collab-shared-tasks'),

        # User search for inviting
        path('users/search/', UserSearchView.as_view(), name='collab-user-search'),

        # Project collaboration endpoints (role-based access)
        path('projects/', CollaborativeProjectsView.as_view(), name='collab-projects'),
        path('projects/join/', JoinProjectView.as_view(), name='collab-join-project'),
        path('projects/<uuid:project_id>/collaborators/', ProjectCollaboratorsView.as_view(), name='collab-project-collaborators'),
        path('projects/<uuid:project_id>/collaborators/<uuid:collaborator_id>/', ProjectCollaboratorDetailView.as_view(), name='collab-project-collaborator-detail'),
        path('projects/<uuid:project_id>/access-id/', ProjectAccessIdView.as_view(), name='collab-project-access-id'),
        path('projects/<uuid:project_id>/transfer/', TransferOwnershipView.as_view(), name='collab-transfer-ownership'),

        # Task assignment endpoint
        path('tasks/<uuid:task_id>/assign/', TaskAssignmentView.as_view(), name='collab-task-assign'),
    ])),
    
    # Notification endpoints
    path('notifications/', include([
        path('preferences/', NotificationPreferencesView.as_view(), name='notif-preferences'),
        path('history/', NotificationHistoryView.as_view(), name='notif-history'),
        path('mark-read/', NotificationMarkReadView.as_view(), name='notif-mark-read'),
    ])),

    # Scheduler endpoints
    path('scheduler/', include([
        path('generate/', generate_schedule, name='scheduler-generate'),
        path('preview/', schedule_preview, name='scheduler-preview'),
        path('score/', score_task, name='scheduler-score'),
        path('workload/', workload_analysis, name='scheduler-workload'),
    ])),

    # Account endpoints
    path('account/', include([
        path('register/', register, name='account-register'),
        path('login/', login, name='account-login'),
        path('profile/', profile, name='account-profile'),
        path('update/', update_profile, name='account-update'),
        path('change-password/', change_password, name='account-change-password'),
        path('list/', list_accounts, name='account-list'),
        path('delete/', delete_account, name='account-delete'),
    ])),

    # Quick actions
    path('quick-actions/', include([
        path('complete-task/<int:task_id>/', 
             TaskViewSet.as_view({'post': 'complete'}), 
             name='quick-complete-task'),
        path('star-task/<int:task_id>/', 
             TaskViewSet.as_view({'post': 'star'}), 
             name='quick-star-task'),
        path('archive-project/<int:project_id>/', 
             ProjectViewSet.as_view({'post': 'archive'}), 
             name='quick-archive-project'),
    ])),
    
    # Bulk operations
    path('bulk/', include([
        path('tasks/update/', 
             TaskViewSet.as_view({'post': 'bulk_update'}), 
             name='bulk-update-tasks'),
        path('tasks/delete/', 
             TaskViewSet.as_view({'post': 'bulk_delete'}), 
             name='bulk-delete-tasks'),
        path('tasks/move/', 
             TaskViewSet.as_view({'post': 'bulk_move'}), 
             name='bulk-move-tasks'),
    ])),
    
    # Search and filters
    path('search/', include([
        path('tasks/', TaskViewSet.as_view({'get': 'search'}), name='search-tasks'),
        path('projects/', ProjectViewSet.as_view({'get': 'search'}), name='search-projects'),
        path('global/', TaskViewSet.as_view({'get': 'global_search'}), name='search-global'),
    ])),
    
    # Templates and presets
    path('templates/', include([
        path('task/', TaskViewSet.as_view({'get': 'templates'}), name='task-templates'),
        path('project/', ProjectViewSet.as_view({'get': 'templates'}), name='project-templates'),
        path('save/', TaskViewSet.as_view({'post': 'save_as_template'}), name='save-template'),
    ])),
    
    # Import/Export
    path('import/', include([
        path('csv/', TaskViewSet.as_view({'post': 'import_csv'}), name='import-csv'),
        path('json/', TaskViewSet.as_view({'post': 'import_json'}), name='import-json'),
        path('todoist/', TaskViewSet.as_view({'post': 'import_todoist'}), name='import-todoist'),
    ])),
    
    path('export/', include([
        path('csv/', TaskViewSet.as_view({'get': 'export_csv'}), name='export-csv'),
        path('json/', TaskViewSet.as_view({'get': 'export_json'}), name='export-json'),
        path('pdf/', TaskViewSet.as_view({'get': 'export_pdf'}), name='export-pdf'),
    ])),
    
    # Recurring tasks
    path('recurring/', include([
        path('create/', TaskViewSet.as_view({'post': 'create_recurring'}), name='create-recurring'),
        path('patterns/', TaskViewSet.as_view({'get': 'recurring_patterns'}), name='recurring-patterns'),
        path('pause/<int:task_id>/', TaskViewSet.as_view({'post': 'pause_recurring'}), name='pause-recurring'),
    ])),
    
    # Time tracking
    path('time/', include([
        path('start/<int:task_id>/', TaskViewSet.as_view({'post': 'start_timer'}), name='start-timer'),
        path('stop/<int:task_id>/', TaskViewSet.as_view({'post': 'stop_timer'}), name='stop-timer'),
        path('log/', TaskViewSet.as_view({'post': 'log_time'}), name='log-time'),
        path('report/', TaskViewSet.as_view({'get': 'time_report'}), name='time-report'),
    ])),
    
    # Webhooks
    path('webhooks/', include([
        path('register/', TaskViewSet.as_view({'post': 'register_webhook'}), name='register-webhook'),
        path('list/', TaskViewSet.as_view({'get': 'list_webhooks'}), name='list-webhooks'),
        path('delete/<str:webhook_id>/', TaskViewSet.as_view({'delete': 'delete_webhook'}), name='delete-webhook'),
    ])),
]

# WebSocket routing - defined in routing.py for Django Channels
# To use WebSockets, configure ASGI and routing separately
# websocket_urlpatterns = [
#     path('ws/tasks/', consumers.TaskManagementConsumer.as_asgi()),
#     path('ws/collaboration/', consumers.CollaborativePlanningConsumer.as_asgi()),
#     path('ws/dashboard/', consumers.DashboardConsumer.as_asgi()),
# ]