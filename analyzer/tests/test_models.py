"""
Tests unitaires pour les modèles de l'application analyzer.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from analyzer.models import AnalysisSession, FileAnalysis, SecurityReport


class AnalysisSessionModelTest(TestCase):
    """Tests pour le modèle AnalysisSession."""
    
    def setUp(self):
        """Prépare les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = AnalysisSession.objects.create(
            user=self.user,
            repository_name='test-repo',
            repository_owner='testowner',
            repository_url='https://github.com/testowner/test-repo',
            branch_name='main'
        )
    
    def test_session_creation(self):
        """Test la création d'une session."""
        self.assertEqual(self.session.file_count, 0)
        self.assertEqual(self.session.status, 'pending')
        self.assertIsNotNone(self.session.created_at)
        self.assertEqual(self.session.branch_name, 'main')
    
    def test_session_str_representation(self):
        """Test la représentation string d'une session."""
        expected = f"testowner/test-repo - {self.session.created_at.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.session), expected)
    
    def test_can_add_file(self):
        """Test la méthode can_add_file()."""
        self.assertTrue(self.session.can_add_file())
        
        # Ajouter 5 fichiers
        self.session.file_count = 5
        self.session.save()
        
        self.assertFalse(self.session.can_add_file())
    
    def test_increment_file_count(self):
        """Test l'incrémentation du compteur de fichiers."""
        initial_count = self.session.file_count
        
        result = self.session.increment_file_count()
        self.assertTrue(result)
        self.assertEqual(self.session.file_count, initial_count + 1)
        
        # Tester la limite
        self.session.file_count = 5
        self.session.save()
        
        result = self.session.increment_file_count()
        self.assertFalse(result)
        self.assertEqual(self.session.file_count, 5)
    
    def test_session_without_user(self):
        """Test la création d'une session sans utilisateur (MVP)."""
        session_no_user = AnalysisSession.objects.create(
            repository_name='test-repo-2',
            repository_owner='testowner2',
            repository_url='https://github.com/testowner2/test-repo-2',
            branch_name='develop'
        )
        
        self.assertIsNone(session_no_user.user)
        self.assertEqual(session_no_user.status, 'pending')
    
    def test_session_status_choices(self):
        """Test les différents statuts possibles."""
        statuses = ['pending', 'in_progress', 'completed', 'failed']
        
        for status in statuses:
            self.session.status = status
            self.session.save()
            self.assertEqual(self.session.status, status)


class FileAnalysisModelTest(TestCase):
    """Tests pour le modèle FileAnalysis."""
    
    def setUp(self):
        """Prépare les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = AnalysisSession.objects.create(
            user=self.user,
            repository_name='test-repo',
            repository_owner='testowner',
            repository_url='https://github.com/testowner/test-repo',
            branch_name='main'
        )
        
        self.file_analysis = FileAnalysis.objects.create(
            session=self.session,
            file_path='src/app.py',
            file_name='app.py',
            file_extension='.py',
            is_auto_selected=True,
            file_size=1024,
            analysis_result={
                'explanation': 'Test explanation',
                'vulnerabilities': [
                    {
                        'type': 'SQL Injection',
                        'severity': 'critical',
                        'description': 'Test vulnerability'
                    }
                ]
            },
            vulnerabilities_count=1,
            severity_level='critical',
            analysis_order=1
        )
    
    def test_file_analysis_creation(self):
        """Test la création d'une analyse de fichier."""
        self.assertEqual(self.file_analysis.file_name, 'app.py')
        self.assertEqual(self.file_analysis.vulnerabilities_count, 1)
        self.assertEqual(self.file_analysis.severity_level, 'critical')
        self.assertTrue(self.file_analysis.is_auto_selected)
    
    def test_file_analysis_str_representation(self):
        """Test la représentation string d'une analyse."""
        expected = "app.py - 1 vulnérabilités"
        self.assertEqual(str(self.file_analysis), expected)
    
    def test_file_analysis_ordering(self):
        """Test l'ordre des analyses de fichiers."""
        file2 = FileAnalysis.objects.create(
            session=self.session,
            file_path='src/utils.py',
            file_name='utils.py',
            file_extension='.py',
            is_auto_selected=True,
            file_size=512,
            analysis_result={},
            vulnerabilities_count=0,
            severity_level='info',
            analysis_order=2
        )
        
        analyses = FileAnalysis.objects.filter(session=self.session)
        self.assertEqual(analyses[0].analysis_order, 1)
        self.assertEqual(analyses[1].analysis_order, 2)
    
    def test_file_analysis_unique_constraint(self):
        """Test la contrainte d'unicité sur session + file_path."""
        with self.assertRaises(Exception):
            FileAnalysis.objects.create(
                session=self.session,
                file_path='src/app.py',  # Même chemin
                file_name='app.py',
                file_extension='.py',
                is_auto_selected=False,
                file_size=2048,
                analysis_result={},
                vulnerabilities_count=0,
                severity_level='info',
                analysis_order=2
            )
    
    def test_manual_file_addition(self):
        """Test l'ajout manuel d'un fichier."""
        manual_file = FileAnalysis.objects.create(
            session=self.session,
            file_path='src/config.py',
            file_name='config.py',
            file_extension='.py',
            is_auto_selected=False,  # Ajout manuel
            file_size=256,
            analysis_result={},
            vulnerabilities_count=0,
            severity_level='info',
            analysis_order=4
        )
        
        self.assertFalse(manual_file.is_auto_selected)
        self.assertEqual(manual_file.analysis_order, 4)


class SecurityReportModelTest(TestCase):
    """Tests pour le modèle SecurityReport."""
    
    def setUp(self):
        """Prépare les données de test."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.session = AnalysisSession.objects.create(
            user=self.user,
            repository_name='test-repo',
            repository_owner='testowner',
            repository_url='https://github.com/testowner/test-repo',
            branch_name='main'
        )
        
        self.report = SecurityReport.objects.create(
            session=self.session,
            summary='Test summary',
            total_vulnerabilities=10,
            critical_count=2,
            high_count=3,
            medium_count=4,
            low_count=1,
            recommendations=[]
        )
    
    def test_security_score_calculation(self):
        """Test le calcul du score de sécurité."""
        # Score = 10 - (2*2 + 3*1.5 + 4*1 + 1*0.5)
        # Score = 10 - (4 + 4.5 + 4 + 0.5) = 10 - 13 = -3 -> 0
        expected_score = 0.0
        self.assertEqual(self.report.security_score, expected_score)
    
    def test_security_score_perfect(self):
        """Test le score avec aucune vulnérabilité."""
        perfect_report = SecurityReport.objects.create(
            session=self.session,
            summary='Perfect code',
            total_vulnerabilities=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            recommendations=[]
        )
        
        self.assertEqual(perfect_report.security_score, 10.0)
    
    def test_security_score_medium_severity(self):
        """Test le score avec des vulnérabilités moyennes."""
        medium_report = SecurityReport.objects.create(
            session=self.session,
            summary='Medium severity issues',
            total_vulnerabilities=5,
            critical_count=0,
            high_count=1,
            medium_count=3,
            low_count=1,
            recommendations=[]
        )
        
        # Score = 10 - (0 + 1.5 + 3 + 0.5) = 10 - 5 = 5.0
        self.assertEqual(medium_report.security_score, 5.0)
    
    def test_security_report_str_representation(self):
        """Test la représentation string d'un rapport."""
        expected = f"Rapport - test-repo ({self.report.security_score}/10)"
        self.assertEqual(str(self.report), expected)
    
    def test_security_report_auto_calculation_on_save(self):
        """Test que le score est calculé automatiquement lors de la sauvegarde."""
        new_report = SecurityReport(
            session=self.session,
            summary='Auto calculation test',
            total_vulnerabilities=2,
            critical_count=1,
            high_count=0,
            medium_count=1,
            low_count=0,
            recommendations=[]
        )
        
        # Avant save, le score n'est pas calculé
        self.assertEqual(new_report.security_score, 0.0)
        
        # Après save, le score est calculé automatiquement
        new_report.save()
        # Score = 10 - (1*2 + 0 + 1*1 + 0) = 10 - 3 = 7.0
        self.assertEqual(new_report.security_score, 7.0)
    
    def test_security_report_recommendations(self):
        """Test le stockage des recommandations."""
        recommendations = [
            "Fix SQL injection in login.py",
            "Update dependencies",
            "Enable HTTPS"
        ]
        
        report_with_recs = SecurityReport.objects.create(
            session=self.session,
            summary='Report with recommendations',
            total_vulnerabilities=3,
            critical_count=1,
            high_count=1,
            medium_count=1,
            low_count=0,
            recommendations=recommendations
        )
        
        self.assertEqual(len(report_with_recs.recommendations), 3)
        self.assertIn("Fix SQL injection in login.py", report_with_recs.recommendations)
    
    def test_one_to_one_relationship(self):
        """Test la relation OneToOne avec AnalysisSession."""
        # Tenter de créer un second rapport pour la même session devrait échouer
        with self.assertRaises(Exception):
            SecurityReport.objects.create(
                session=self.session,  # Même session
                summary='Duplicate report',
                total_vulnerabilities=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                recommendations=[]
            )

# Made with Bob