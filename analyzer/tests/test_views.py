"""
Tests d'intégration pour les vues.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from analyzer.models import AnalysisSession, FileAnalysis, SecurityReport


class HomeViewTest(TestCase):
    """Tests pour la vue home."""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_page_loads(self):
        """Test que la page d'accueil se charge."""
        response = self.client.get(reverse('analyzer:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
    
    def test_home_page_content(self):
        """Test le contenu de la page d'accueil."""
        response = self.client.get(reverse('analyzer:home'))
        self.assertContains(response, 'GuardAI')


class RepoListViewTest(TestCase):
    """Tests pour la vue repo_list."""
    
    def setUp(self):
        self.client = Client()
    
    def test_redirect_without_token(self):
        """Test la redirection sans token."""
        response = self.client.get(reverse('analyzer:repo_list'))
        self.assertRedirects(
            response,
            reverse('github_auth:token_input')
        )
    
    @patch('analyzer.views.create_github_client')
    def test_repo_list_with_valid_token(self, mock_client):
        """Test l'affichage avec un token valide."""
        # Mock du client GitHub
        mock_instance = MagicMock()
        mock_instance.get_user_repos.return_value = [
            {
                'name': 'test-repo',
                'owner': 'testuser',
                'description': 'Test repository',
                'url': 'https://github.com/testuser/test-repo',
                'language': 'Python',
                'stars': 10,
                'default_branch': 'main'
            }
        ]
        mock_instance.get_user_info.return_value = {
            'login': 'testuser',
            'name': 'Test User',
            'avatar_url': 'https://example.com/avatar.png'
        }
        mock_client.return_value = mock_instance
        
        # Ajouter un token à la session
        session = self.client.session
        session['github_token'] = 'ghp_' + 'x' * 36
        session.save()
        
        response = self.client.get(reverse('analyzer:repo_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'repo_list.html')
        self.assertContains(response, 'test-repo')
        self.assertContains(response, 'testuser')
    
    def test_repo_list_with_invalid_token(self):
        """Test avec un token invalide."""
        session = self.client.session
        session['github_token'] = 'invalid_token'
        session.save()
        
        response = self.client.get(reverse('analyzer:repo_list'))
        self.assertRedirects(response, reverse('github_auth:token_input'))
    
    @patch('analyzer.views.create_github_client')
    def test_repo_list_github_api_error(self, mock_client):
        """Test la gestion d'erreur de l'API GitHub."""
        from analyzer.github_api import GitHubAPIError
        
        mock_instance = MagicMock()
        mock_instance.get_user_repos.side_effect = GitHubAPIError("API Error")
        mock_client.return_value = mock_instance
        
        session = self.client.session
        session['github_token'] = 'ghp_' + 'x' * 36
        session.save()
        
        response = self.client.get(reverse('analyzer:repo_list'))
        self.assertRedirects(response, reverse('github_auth:token_input'))


class SelectRepositoryViewTest(TestCase):
    """Tests pour la vue select_repository."""
    
    def setUp(self):
        self.client = Client()
    
    def test_redirect_without_token(self):
        """Test la redirection sans token."""
        response = self.client.get(
            reverse('analyzer:select_repository', args=['owner', 'repo'])
        )
        self.assertRedirects(response, reverse('github_auth:token_input'))
    
    @patch('analyzer.views.create_github_client')
    @patch('analyzer.views.select_critical_files')
    def test_select_repository_success(self, mock_select_files, mock_client):
        """Test la sélection réussie d'un repository."""
        # Mock du client GitHub
        mock_instance = MagicMock()
        mock_instance.get_user_repos.return_value = [
            {
                'name': 'test-repo',
                'owner': 'testowner',
                'description': 'Test',
                'url': 'https://github.com/testowner/test-repo',
                'default_branch': 'main'
            }
        ]
        mock_instance.get_file_tree.return_value = [
            {'path': 'src/app.py', 'type': 'blob', 'size': 1024},
            {'path': 'src/utils.py', 'type': 'blob', 'size': 512}
        ]
        mock_client.return_value = mock_instance
        
        # Mock de la sélection de fichiers
        mock_select_files.return_value = [
            {'path': 'src/app.py', 'type': 'blob', 'size': 1024}
        ]
        
        session = self.client.session
        session['github_token'] = 'ghp_' + 'x' * 36
        session.save()
        
        response = self.client.get(
            reverse('analyzer:select_repository', args=['testowner', 'test-repo'])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file_selection.html')


class FileSelectionViewTest(TestCase):
    """Tests pour la vue file_selection."""
    
    def setUp(self):
        self.client = Client()
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
    
    def test_file_selection_view_loads(self):
        """Test que la vue de sélection de fichiers se charge."""
        session = self.client.session
        session['github_token'] = 'ghp_' + 'x' * 36
        session['session_id'] = self.session.id
        session.save()
        
        response = self.client.get(
            reverse('analyzer:file_selection', args=[self.session.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'file_selection.html')


class AnalysisReportViewTest(TestCase):
    """Tests pour la vue analysis_report."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.session = AnalysisSession.objects.create(
            user=self.user,
            repository_name='test-repo',
            repository_owner='testowner',
            repository_url='https://github.com/testowner/test-repo',
            branch_name='main',
            status='completed'
        )
        
        # Créer une analyse de fichier
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
        
        # Créer un rapport de sécurité
        self.report = SecurityReport.objects.create(
            session=self.session,
            summary='Test summary',
            total_vulnerabilities=1,
            critical_count=1,
            high_count=0,
            medium_count=0,
            low_count=0,
            recommendations=['Fix SQL injection']
        )
    
    def test_analysis_report_view_loads(self):
        """Test que le rapport d'analyse se charge."""
        response = self.client.get(
            reverse('analyzer:analysis_report', args=[self.session.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analysis_report.html')
        self.assertContains(response, 'Test summary')
        self.assertContains(response, 'SQL Injection')
    
    def test_analysis_report_displays_score(self):
        """Test que le score de sécurité est affiché."""
        response = self.client.get(
            reverse('analyzer:analysis_report', args=[self.session.id])
        )
        
        # Le score devrait être 8.0 (10 - 2*1)
        self.assertContains(response, str(self.report.security_score))


class AddFileViewTest(TestCase):
    """Tests pour la vue add_file."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.session = AnalysisSession.objects.create(
            user=self.user,
            repository_name='test-repo',
            repository_owner='testowner',
            repository_url='https://github.com/testowner/test-repo',
            branch_name='main',
            file_count=3  # 3 fichiers auto-sélectionnés
        )
    
    def test_add_file_view_loads(self):
        """Test que la vue d'ajout de fichier se charge."""
        session = self.client.session
        session['github_token'] = 'ghp_' + 'x' * 36
        session.save()
        
        response = self.client.get(
            reverse('analyzer:add_file', args=[self.session.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_file.html')
    
    def test_add_file_limit_reached(self):
        """Test quand la limite de 5 fichiers est atteinte."""
        self.session.file_count = 5
        self.session.save()
        
        session = self.client.session
        session['github_token'] = 'ghp_' + 'x' * 36
        session.save()
        
        response = self.client.get(
            reverse('analyzer:add_file', args=[self.session.id])
        )
        
        # Devrait rediriger vers le rapport
        self.assertRedirects(
            response,
            reverse('analyzer:analysis_report', args=[self.session.id])
        )


class SessionManagementTest(TestCase):
    """Tests pour la gestion des sessions."""
    
    def setUp(self):
        self.client = Client()
    
    def test_session_token_storage(self):
        """Test le stockage du token en session."""
        session = self.client.session
        test_token = 'ghp_' + 'x' * 36
        session['github_token'] = test_token
        session.save()
        
        # Vérifier que le token est stocké
        self.assertEqual(self.client.session['github_token'], test_token)
    
    def test_session_cleanup(self):
        """Test le nettoyage de la session."""
        session = self.client.session
        session['github_token'] = 'ghp_' + 'x' * 36
        session['session_id'] = 123
        session.save()
        
        # Supprimer les données de session
        del session['github_token']
        del session['session_id']
        session.save()
        
        self.assertNotIn('github_token', self.client.session)
        self.assertNotIn('session_id', self.client.session)


class ErrorHandlingTest(TestCase):
    """Tests pour la gestion des erreurs."""
    
    def setUp(self):
        self.client = Client()
    
    def test_404_page(self):
        """Test la page 404."""
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_session_id(self):
        """Test avec un ID de session invalide."""
        response = self.client.get(
            reverse('analyzer:analysis_report', args=[99999])
        )
        self.assertEqual(response.status_code, 404)

# Made with Bob