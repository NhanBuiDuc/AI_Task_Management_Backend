# tasks_api/models/user_achievement.py
"""User Achievement model for gamification features."""

from django.db import models
from django.conf import settings
from .base import BaseModel


class UserAchievement(BaseModel):
    """Track user achievements and badges."""

    user_id = models.IntegerField(help_text="User identifier")
    achievement_id = models.CharField(max_length=100, help_text="Unique achievement identifier")
    name = models.CharField(max_length=255, help_text="Achievement display name")
    description = models.TextField(null=True, blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user_id', 'achievement_id']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['achievement_id']),
        ]

    def __str__(self):
        return f"User {self.user_id} - {self.name}"
