from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, SectionViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'sections', SectionViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]