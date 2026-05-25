from django.db import models
from django.contrib.auth.models import User


class UserGitHubToken(models.Model):
    """
    Store GitHub OAuth access tokens for authenticated users.
    
    This model maintains a one-to-one relationship with Django's User model,
    storing the GitHub OAuth token required for API access.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='github_token',
        help_text="User who owns this GitHub token"
    )
    access_token = models.CharField(
        max_length=255,
        help_text="GitHub OAuth access token"
    )
    token_type = models.CharField(
        max_length=50, 
        default='Bearer',
        help_text="Token type (usually 'Bearer')"
    )
    scope = models.CharField(
        max_length=255, 
        blank=True,
        help_text="OAuth scopes granted (e.g., 'user,repo')"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the token was created"
    )
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Token expiration date (if applicable)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this token is currently active"
    )
    
    class Meta:
        db_table = 'github_tokens'
        verbose_name = 'GitHub Token'
        verbose_name_plural = 'GitHub Tokens'
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"GitHub Token for {self.user.username}"
    
    def validate_token(self):
        """
        Check if the token is still valid.
        
        Returns:
            bool: True if token is active and not expired
        """
        if not self.is_active:
            return False
        
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() < self.expires_at
        
        return True

# Made with Bob
