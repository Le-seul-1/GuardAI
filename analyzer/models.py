from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AnalysisSession(models.Model):
    """
    Represents a code analysis session for a GitHub repository.
    
    Each session can analyze up to 5 files maximum:
    - 3 files auto-selected by IBM Bob AI
    - 2 files manually added by the user
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('failed', 'Échouée'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analysis_sessions',
        null=True,
        blank=True,
        help_text="User who created this analysis session (optional for MVP)"
    )
    repository_name = models.CharField(
        max_length=255,
        help_text="Name of the GitHub repository"
    )
    repository_owner = models.CharField(
        max_length=255,
        help_text="Owner/organization of the repository"
    )
    repository_url = models.URLField(
        max_length=500,
        help_text="Full URL to the GitHub repository"
    )
    branch_name = models.CharField(
        max_length=100, 
        default='main',
        help_text="Branch being analyzed"
    )
    file_count = models.IntegerField(
        default=0,
        help_text="Number of files in this session (max 5)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the analysis"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the session was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the analysis was completed"
    )
    
    class Meta:
        db_table = 'analysis_sessions'
        ordering = ['-created_at']
        verbose_name = 'Session d\'Analyse'
        verbose_name_plural = 'Sessions d\'Analyse'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.repository_owner}/{self.repository_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def can_add_file(self):
        """
        Check if another file can be added to this session.
        
        Returns:
            bool: True if file_count < 5, False otherwise
        """
        return self.file_count < 5
    
    def increment_file_count(self):
        """
        Safely increment the file counter.
        
        Returns:
            bool: True if incremented successfully, False if limit reached
        """
        if self.can_add_file():
            self.file_count += 1
            self.save()
            return True
        return False


class FileAnalysis(models.Model):
    """
    Stores the analysis result for a single file in a session.
    
    Files are analyzed in order:
    - analysis_order 1-3: Auto-selected by IBM Bob AI (is_auto_selected=True)
    - analysis_order 4-5: Manually added by user (is_auto_selected=False)
    """
    SEVERITY_CHOICES = [
        ('critical', 'Critique'),
        ('high', 'Élevé'),
        ('medium', 'Moyen'),
        ('low', 'Faible'),
        ('info', 'Information'),
    ]
    
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='file_analyses',
        help_text="Analysis session this file belongs to"
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Relative path to the file in the repository"
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Name of the file (e.g., 'app.py')"
    )
    file_extension = models.CharField(
        max_length=50,
        help_text="File extension (e.g., '.py', '.js')"
    )
    is_auto_selected = models.BooleanField(
        default=False,
        help_text="True if auto-selected by IBM Bob AI, False if manually added"
    )
    file_size = models.IntegerField(
        help_text="File size in bytes"
    )
    file_content = models.TextField(
        blank=True,
        help_text="Content of the file (optional, for caching)"
    )
    analysis_result = models.JSONField(
        default=dict,
        help_text="IBM Bob AI analysis result (JSON format)"
    )
    vulnerabilities_count = models.IntegerField(
        default=0,
        help_text="Total number of vulnerabilities found"
    )
    severity_level = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='info',
        help_text="Highest severity level found in this file"
    )
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the analysis was performed"
    )
    analysis_order = models.IntegerField(
        default=0,
        help_text="Order in which this file was analyzed (1-5)"
    )
    
    class Meta:
        db_table = 'file_analyses'
        ordering = ['analysis_order', 'analyzed_at']
        verbose_name = 'Analyse de Fichier'
        verbose_name_plural = 'Analyses de Fichiers'
        unique_together = [['session', 'file_path']]
        indexes = [
            models.Index(fields=['session', 'analysis_order']),
            models.Index(fields=['is_auto_selected']),
        ]
    
    def __str__(self):
        return f"{self.file_name} - {self.vulnerabilities_count} vulnérabilités"


class SecurityReport(models.Model):
    """
    Aggregated security report for an analysis session.
    
    Generated after all files in a session have been analyzed.
    Contains overall statistics, security score, and recommendations.
    """
    session = models.OneToOneField(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='security_report',
        help_text="Analysis session this report belongs to"
    )
    summary = models.TextField(
        help_text="Executive summary of the security analysis"
    )
    total_vulnerabilities = models.IntegerField(
        default=0,
        help_text="Total number of vulnerabilities across all files"
    )
    critical_count = models.IntegerField(
        default=0,
        help_text="Number of critical severity vulnerabilities"
    )
    high_count = models.IntegerField(
        default=0,
        help_text="Number of high severity vulnerabilities"
    )
    medium_count = models.IntegerField(
        default=0,
        help_text="Number of medium severity vulnerabilities"
    )
    low_count = models.IntegerField(
        default=0,
        help_text="Number of low severity vulnerabilities"
    )
    recommendations = models.JSONField(
        default=list,
        help_text="List of security recommendations (JSON format)"
    )
    security_score = models.FloatField(
        default=0.0,
        help_text="Overall security score (0.0 to 10.0)"
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the report was generated"
    )
    
    class Meta:
        db_table = 'security_reports'
        verbose_name = 'Rapport de Sécurité'
        verbose_name_plural = 'Rapports de Sécurité'
    
    def __str__(self):
        return f"Rapport - {self.session.repository_name} ({self.security_score}/10)"
    
    def calculate_security_score(self):
        """
        Calculate the security score based on vulnerability counts.
        
        Scoring algorithm:
        - Start with 10.0 (perfect score)
        - Subtract penalties based on severity:
          * Critical: -2.0 per vulnerability
          * High: -1.5 per vulnerability
          * Medium: -1.0 per vulnerability
          * Low: -0.5 per vulnerability
        - Minimum score is 0.0
        
        Returns:
            float: Security score between 0.0 and 10.0
        """
        if self.total_vulnerabilities == 0:
            return 10.0
        
        penalty = (
            self.critical_count * 2.0 +
            self.high_count * 1.5 +
            self.medium_count * 1.0 +
            self.low_count * 0.5
        )
        score = max(0.0, 10.0 - penalty)
        return round(score, 2)
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically calculate security score.
        """
        self.security_score = self.calculate_security_score()
        super().save(*args, **kwargs)

# Made with Bob
