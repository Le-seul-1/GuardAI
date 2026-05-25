from django.contrib import admin
from .models import AnalysisSession, FileAnalysis, SecurityReport


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for analysis sessions.
    """
    list_display = ['id', 'user', 'repository_name', 'repository_owner', 'file_count', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'branch_name']
    search_fields = ['repository_name', 'repository_owner', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('User & Repository', {
            'fields': ('user', 'repository_name', 'repository_owner', 'repository_url', 'branch_name')
        }),
        ('Analysis Status', {
            'fields': ('status', 'file_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make file_count readonly after creation to prevent manual manipulation.
        """
        if obj:  # Editing existing object
            return self.readonly_fields + ('file_count',)
        return self.readonly_fields


@admin.register(FileAnalysis)
class FileAnalysisAdmin(admin.ModelAdmin):
    """
    Admin interface for file analyses.
    """
    list_display = ['id', 'session', 'file_name', 'is_auto_selected', 'vulnerabilities_count', 'severity_level', 'analysis_order']
    list_filter = ['is_auto_selected', 'severity_level', 'analyzed_at']
    search_fields = ['file_name', 'file_path', 'session__repository_name']
    readonly_fields = ['analyzed_at']
    
    fieldsets = (
        ('Session & File Info', {
            'fields': ('session', 'file_path', 'file_name', 'file_extension', 'file_size')
        }),
        ('Analysis Details', {
            'fields': ('is_auto_selected', 'analysis_order', 'vulnerabilities_count', 'severity_level')
        }),
        ('Results', {
            'fields': ('analysis_result', 'file_content'),
            'classes': ('collapse',)  # Collapsed by default
        }),
        ('Timestamp', {
            'fields': ('analyzed_at',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queries by selecting related session data.
        """
        qs = super().get_queryset(request)
        return qs.select_related('session', 'session__user')


@admin.register(SecurityReport)
class SecurityReportAdmin(admin.ModelAdmin):
    """
    Admin interface for security reports.
    """
    list_display = ['id', 'session', 'total_vulnerabilities', 'security_score', 'critical_count', 'high_count', 'generated_at']
    list_filter = ['generated_at']
    search_fields = ['session__repository_name', 'session__repository_owner']
    readonly_fields = ['generated_at', 'security_score']
    
    fieldsets = (
        ('Session', {
            'fields': ('session',)
        }),
        ('Vulnerability Counts', {
            'fields': ('total_vulnerabilities', 'critical_count', 'high_count', 'medium_count', 'low_count')
        }),
        ('Score & Summary', {
            'fields': ('security_score', 'summary')
        }),
        ('Recommendations', {
            'fields': ('recommendations',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('generated_at',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queries by selecting related session data.
        """
        qs = super().get_queryset(request)
        return qs.select_related('session', 'session__user')
    
    def save_model(self, request, obj, form, change):
        """
        Automatically calculate security score before saving.
        """
        obj.security_score = obj.calculate_security_score()
        super().save_model(request, obj, form, change)

# Made with Bob
