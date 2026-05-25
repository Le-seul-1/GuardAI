from django.contrib import admin
from .models import UserGitHubToken


@admin.register(UserGitHubToken)
class UserGitHubTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for GitHub tokens.
    """
    list_display = ['user', 'token_type', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'token_type', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Token Details', {
            'fields': ('access_token', 'token_type', 'scope', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    def has_add_permission(self, request):
        """
        Restrict manual token creation - should be done via OAuth flow.
        """
        return request.user.is_superuser

# Made with Bob
