"""
URL configuration for tasks_api including LangChain agent endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, SectionViewSet, TaskViewSet
from .views_agent import process_intentions, agent_health_check

# Existing router
router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'sections', SectionViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    # Existing API routes
    path('api/', include(router.urls)),
    
    # New Agent endpoints
    path('api/process-intentions/', process_intentions, name='process-intentions'),
    path('api/agent-health/', agent_health_check, name='agent-health'),
]