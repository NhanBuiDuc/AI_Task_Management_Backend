# File: tasks_api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    TaskViewSet,
    ProjectViewSet,
    SectionViewSet,
    UserTaskViewViewSet,
    CommentViewSet,
    AttachmentViewSet,
    TaskActivityViewSet,
    LabelViewSet
)
from .views_agent import (
    AIIntentionView,
    AIInsightsView,
    AIPatternAnalysisView,
    AISuggestionsView,
    AIBatchProcessView,
    AIStreamingView
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
    CollaboratorsView
)
from .views_notifications import (
    NotificationPreferencesView,
    NotificationHistoryView,
    NotificationMarkReadView
)

# Main router
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'labels', LabelViewSet, basename='label')
router.register(r'task-views', UserTaskViewViewSet, basename='task-view')

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

tasks_router = nested_routers.NestedDefaultRouter(
    router,
    r'tasks',
    lookup='task'
)
tasks_router.register(
    r'comments',
    CommentViewSet,
    basename='task-comments'
)
tasks_router.register(
    r'attachments',
    AttachmentViewSet,
    basename='task-attachments'
)
tasks_router.register(
    r'activities',
    TaskActivityViewSet,
    basename='task-activities'
)

app_name = 'tasks_api'

urlpatterns = [
    # Include routers
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    path('', include(tasks_router.urls)),
    
    # AI Agent endpoints
    path('ai/', include([
        path('process/', AIIntentionView.as_view(), name='ai-process'),
        path('insights/', AIInsightsView.as_view(), name='ai-insights'),
        path('patterns/', AIPatternAnalysisView.as_view(), name='ai-patterns'),
        path('suggestions/', AISuggestionsView.as_view(), name='ai-suggestions'),
        path('batch/', AIBatchProcessView.as_view(), name='ai-batch'),
        path('stream/', AIStreamingView.as_view(), name='ai-stream'),
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
        path('sessions/', CollaborationSessionView.as_view(), name='collab-sessions'),
        path('shared-projects/', SharedProjectView.as_view(), name='collab-shared-projects'),
        path('workspaces/', TeamWorkspaceView.as_view(), name='collab-workspaces'),
        path('collaborators/', CollaboratorsView.as_view(), name='collab-collaborators'),
    ])),
    
    # Notification endpoints
    path('notifications/', include([
        path('preferences/', NotificationPreferencesView.as_view(), name='notif-preferences'),
        path('history/', NotificationHistoryView.as_view(), name='notif-history'),
        path('mark-read/', NotificationMarkReadView.as_view(), name='notif-mark-read'),
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

# WebSocket routing
websocket_urlpatterns = [
    path('ws/tasks/', 'tasks_api.consumers.TaskManagementConsumer.as_asgi()'),
    path('ws/collaboration/', 'tasks_api.consumers.CollaborativePlanningConsumer.as_asgi()'),
    path('ws/dashboard/', 'tasks_api.consumers.DashboardConsumer.as_asgi()'),
]