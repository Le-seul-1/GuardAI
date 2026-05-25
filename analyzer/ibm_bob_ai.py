import requests
from typing import List, Dict, Optional
from decouple import config


class IBMBobAIError(Exception):
    """Exception pour les erreurs IBM Bob AI"""
    pass


class IBMBobClient:
    """
    Client pour interagir avec IBM Bob AI.
    
    Ce client gère :
    - La sélection automatique de fichiers critiques
    - L'analyse de code
    - La détection de vulnérabilités
    - La génération de code amélioré
    """
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialise le client IBM Bob AI.
        
        Args:
            api_key: Clé API IBM Bob (ou depuis .env)
            api_url: URL de l'API (ou depuis .env)
        """
        self.api_key = api_key or config('IBM_BOB_API_KEY')
        self.api_url = api_url or config('IBM_BOB_API_URL')
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """
        Fait une requête à l'API IBM Bob.
        
        Args:
            endpoint: Endpoint de l'API (ex: '/analyze')
            data: Données à envoyer
            
        Returns:
            Dict: Réponse de l'API
            
        Raises:
            IBMBobAIError: Si la requête échoue
        """
        url = f"{self.api_url}{endpoint}"
        response = None
        
        try:
            response = requests.post(
                url=url,
                headers=self.headers,
                json=data,
                timeout=60  # 60 secondes pour l'analyse
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response and response.status_code == 401:
                raise IBMBobAIError("Clé API invalide")
            elif response and response.status_code == 429:
                raise IBMBobAIError("Quota dépassé")
            else:
                status = response.status_code if response else 'unknown'
                error_detail = response.text if response else str(e)
                raise IBMBobAIError(f"Erreur HTTP {status}: {error_detail[:200]}")
                
        except requests.exceptions.Timeout:
            raise IBMBobAIError("Timeout : L'analyse prend trop de temps")
            
        except requests.exceptions.RequestException as e:
            raise IBMBobAIError(f"Erreur de connexion : {str(e)}")
    
    def select_critical_files(self, files: List[Dict], max_files: int = 3) -> List[Dict]:
        """
        Sélectionne automatiquement les fichiers les plus critiques.
        
        Critères de sélection :
        1. Fichiers backend (Python, Java, Node.js)
        2. Fichiers de configuration (config, env, yml)
        3. Fichiers d'authentification (auth, login, user)
        4. Fichiers de base de données (db, models, queries)
        
        Args:
            files: Liste de tous les fichiers du repository
            max_files: Nombre maximum de fichiers à sélectionner (défaut: 3)
            
        Returns:
            List[Dict]: Liste des fichiers sélectionnés
        """
        # Extensions critiques par priorité
        CRITICAL_EXTENSIONS = {
            'high': ['.py', '.java', '.js', '.ts', '.php', '.rb'],
            'medium': ['.yml', '.yaml', '.json', '.xml', '.env'],
            'low': ['.sql', '.sh', '.bat']
        }
        
        # Mots-clés critiques dans les noms de fichiers
        CRITICAL_KEYWORDS = [
            'auth', 'login', 'user', 'password', 'token',
            'config', 'settings', 'database', 'db', 'model',
            'api', 'security', 'admin', 'secret'
        ]
        
        # Scorer chaque fichier
        scored_files = []
        for file in files:
            score = 0
            path_lower = file['path'].lower()
            
            # Score basé sur l'extension
            for priority, extensions in CRITICAL_EXTENSIONS.items():
                if any(path_lower.endswith(ext) for ext in extensions):
                    if priority == 'high':
                        score += 10
                    elif priority == 'medium':
                        score += 5
                    else:
                        score += 2
            
            # Score basé sur les mots-clés
            for keyword in CRITICAL_KEYWORDS:
                if keyword in path_lower:
                    score += 3
            
            # Pénalité pour les fichiers de test
            if 'test' in path_lower or 'spec' in path_lower:
                score -= 5
            
            # Pénalité pour les fichiers trop gros (> 100KB)
            if file['size'] > 100000:
                score -= 2
            
            scored_files.append({
                **file,
                'priority_score': score
            })
        
        # Trier par score décroissant
        scored_files.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Retourner les N premiers
        return scored_files[:max_files]
    
    def analyze_code(self, file_path: str, file_content: str, language: Optional[str] = None) -> Dict:
        """
        Analyse un fichier de code avec IBM Bob AI.
        
        Args:
            file_path: Chemin du fichier
            file_content: Contenu du fichier
            language: Langage de programmation (auto-détecté si None)
            
        Returns:
            Dict: {
                'explanation': 'Description du code',
                'vulnerabilities': [
                    {
                        'type': 'SQL Injection',
                        'severity': 'critical',
                        'line': 42,
                        'description': '...',
                        'recommendation': '...'
                    }
                ],
                'improved_code': 'Code amélioré',
                'code_quality_score': 7.5,
                'maintainability_index': 65,
                'complexity': 'medium'
            }
        """
        # Auto-détecter le langage si non fourni
        if not language:
            extension = file_path.split('.')[-1]
            language_map = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'typescript',
                'java': 'java',
                'php': 'php',
                'rb': 'ruby',
                'go': 'go'
            }
            language = language_map.get(extension, 'unknown')
        
        # Préparer les données pour l'API
        data = {
            'file_path': file_path,
            'content': file_content,
            'language': language,
            'analysis_type': 'security',
            'options': {
                'detect_vulnerabilities': True,
                'generate_improvements': True,
                'calculate_metrics': True
            }
        }
        
        # Faire la requête
        try:
            result = self._make_request('/analyze', data)
            
            # Formater la réponse
            return {
                'explanation': result.get('explanation', ''),
                'vulnerabilities': result.get('vulnerabilities', []),
                'improved_code': result.get('improved_code', ''),
                'code_quality_score': result.get('quality_score', 0.0),
                'maintainability_index': result.get('maintainability', 0),
                'complexity': result.get('complexity', 'unknown')
            }
            
        except IBMBobAIError as e:
            # En cas d'erreur, retourner une analyse vide
            return {
                'explanation': f"Erreur d'analyse : {str(e)}",
                'vulnerabilities': [],
                'improved_code': file_content,
                'code_quality_score': 0.0,
                'maintainability_index': 0,
                'complexity': 'unknown'
            }
    
    def generate_report(self, analyses: List[Dict]) -> Dict:
        """
        Génère un rapport de sécurité global.
        
        Args:
            analyses: Liste des analyses de fichiers
            
        Returns:
            Dict: {
                'summary': 'Résumé exécutif',
                'total_vulnerabilities': 10,
                'critical_count': 2,
                'high_count': 3,
                'medium_count': 4,
                'low_count': 1,
                'recommendations': [...]
            }
        """
        # Agréger les vulnérabilités
        all_vulnerabilities = []
        for analysis in analyses:
            all_vulnerabilities.extend(analysis.get('vulnerabilities', []))
        
        # Compter par sévérité
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for vuln in all_vulnerabilities:
            severity = vuln.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Générer le résumé
        total = len(all_vulnerabilities)
        if total == 0:
            summary = "✅ Aucune vulnérabilité détectée. Le code semble sécurisé."
        elif severity_counts['critical'] > 0:
            summary = f"🚨 {severity_counts['critical']} vulnérabilités CRITIQUES détectées ! Action immédiate requise."
        elif severity_counts['high'] > 0:
            summary = f"⚠️ {severity_counts['high']} vulnérabilités ÉLEVÉES détectées. Correction recommandée."
        else:
            summary = f"ℹ️ {total} vulnérabilités mineures détectées."
        
        # Générer les recommandations
        recommendations = []
        if severity_counts['critical'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'Security',
                'title': 'Corriger les vulnérabilités critiques',
                'description': 'Des failles de sécurité critiques ont été détectées et doivent être corrigées immédiatement.'
            })
        
        return {
            'summary': summary,
            'total_vulnerabilities': total,
            'critical_count': severity_counts['critical'],
            'high_count': severity_counts['high'],
            'medium_count': severity_counts['medium'],
            'low_count': severity_counts['low'],
            'recommendations': recommendations
        }


# Fonction utilitaire
def create_ibm_bob_client() -> IBMBobClient:
    """
    Crée et retourne un client IBM Bob AI configuré.
    
    Returns:
        IBMBobClient: Client prêt à l'emploi
    """
    return IBMBobClient()

# Made with Bob
