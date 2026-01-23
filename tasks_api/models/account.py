# tasks_api/models/account.py
"""Account model for basic user management."""

from django.db import models
from django.utils import timezone
import hashlib
import secrets
from .base import BaseModel


class Account(BaseModel):
    """
    Basic account model for user management.
    Uses simple SHA-256 hashing for passwords (not for production use).
    """

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=64)  # SHA-256 hex digest
    salt = models.CharField(max_length=32)  # Random salt for password

    # Profile fields
    display_name = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)

    # Status fields
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)

    # Preferences (stored as JSON-like text for simplicity)
    timezone = models.CharField(max_length=50, default='UTC')
    theme = models.CharField(max_length=20, default='light')

    class Meta:
        ordering = ['username']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """Override save to generate salt if not present."""
        if not self.salt:
            self.salt = secrets.token_hex(16)
        super().save(*args, **kwargs)

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """
        Hash a password with the given salt using SHA-256.

        Args:
            password: Plain text password
            salt: Random salt string

        Returns:
            Hexadecimal hash string
        """
        salted_password = f"{salt}{password}{salt}"
        return hashlib.sha256(salted_password.encode('utf-8')).hexdigest()

    def set_password(self, password: str) -> None:
        """
        Set the account password.

        Args:
            password: Plain text password to hash and store
        """
        if not self.salt:
            self.salt = secrets.token_hex(16)
        self.password_hash = self.hash_password(password, self.salt)

    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.

        Args:
            password: Plain text password to check

        Returns:
            True if password matches, False otherwise
        """
        return self.password_hash == self.hash_password(password, self.salt)

    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])

    @classmethod
    def create_account(cls, username: str, email: str, password: str, **kwargs) -> 'Account':
        """
        Create a new account with hashed password.

        Args:
            username: Unique username
            email: Email address
            password: Plain text password
            **kwargs: Additional fields (display_name, etc.)

        Returns:
            Created Account instance
        """
        account = cls(
            username=username,
            email=email,
            **kwargs
        )
        account.set_password(password)
        account.save()
        return account

    @classmethod
    def authenticate(cls, username_or_email: str, password: str) -> 'Account | None':
        """
        Authenticate a user by username/email and password.

        Args:
            username_or_email: Username or email to look up
            password: Plain text password to verify

        Returns:
            Account instance if authenticated, None otherwise
        """
        try:
            # Try to find by username first, then email
            try:
                account = cls.objects.get(username=username_or_email, is_active=True)
            except cls.DoesNotExist:
                account = cls.objects.get(email=username_or_email, is_active=True)

            if account.check_password(password):
                account.update_last_login()
                return account
            return None

        except cls.DoesNotExist:
            return None

    def to_dict(self) -> dict:
        """Return account data as dictionary (excluding sensitive fields)."""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'display_name': self.display_name or self.username,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'timezone': self.timezone,
            'theme': self.theme,
            'created_at': self.created_at.isoformat(),
        }
