import requests
from typing import List, Dict, Optional
import base64


class GitHubAPIError(Exception):
    """Exception personnalisée pour les erreurs GitHub API"""
    pass


class GitHubClient:
    """
    Client pour interagir avec l'API GitHub.
    
    Ce client gère toutes les communications avec GitHub :
    - Authentification
    - Récupération des repositories
    - Lecture des fichiers
    - Gestion des erreurs
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, access_token: str):
        """
        Initialise le client avec un token d'accès.
        
        Args:
            access_token: Token GitHub (commence par 'ghp_')
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Méthode privée pour faire des requêtes HTTP.
        
        Args:
            method: 'GET', 'POST', etc.
            endpoint: URL relative (ex: '/user/repos')
            **kwargs: Paramètres supplémentaires pour requests
            
        Returns:
            Dict: Réponse JSON de l'API
            
        Raises:
            GitHubAPIError: Si la requête échoue
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = None
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=30,
                **kwargs
            )
            
            # Vérifier le rate limit
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining and int(remaining) < 10:
                print(f"⚠️ Attention : Il ne reste que {remaining} requêtes")
            
            # Lever une exception si erreur HTTP
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response and response.status_code == 401:
                raise GitHubAPIError("Token invalide ou expiré")
            elif response and response.status_code == 403:
                raise GitHubAPIError("Rate limit dépassé ou accès refusé")
            elif response and response.status_code == 404:
                raise GitHubAPIError("Repository ou fichier introuvable")
            else:
                status = response.status_code if response else "Unknown"
                raise GitHubAPIError(f"Erreur HTTP {status}: {str(e)}")
                
        except requests.exceptions.Timeout:
            raise GitHubAPIError("Timeout : GitHub ne répond pas")
            
        except requests.exceptions.RequestException as e:
            raise GitHubAPIError(f"Erreur de connexion : {str(e)}")
    
    def get_user_info(self) -> Dict:
        """
        Récupère les informations de l'utilisateur authentifié.
        
        Returns:
            Dict: {
                'login': 'username',
                'name': 'Full Name',
                'email': 'user@example.com',
                'avatar_url': 'https://...',
                'public_repos': 42
            }
        """
        return self._make_request('GET', '/user')
    
    def get_user_repos(self, sort: str = 'updated', per_page: int = 100) -> List[Dict]:
        """
        Récupère la liste des repositories de l'utilisateur.
        
        Args:
            sort: Tri ('updated', 'created', 'pushed', 'full_name')
            per_page: Nombre de repos par page (max 100)
            
        Returns:
            List[Dict]: Liste des repositories avec leurs infos
        """
        params = {
            'sort': sort,
            'per_page': per_page,
            'type': 'all'  # 'all', 'owner', 'member'
        }
        
        repos = self._make_request('GET', '/user/repos', params=params)
        
        # Simplifier les données retournées
        simplified_repos = []
        for repo in repos:
            simplified_repos.append({
                'name': repo['name'],
                'full_name': repo['full_name'],
                'owner': repo['owner']['login'],
                'description': repo.get('description', ''),
                'url': repo['html_url'],
                'default_branch': repo['default_branch'],
                'language': repo.get('language', 'Unknown'),
                'stars': repo['stargazers_count'],
                'updated_at': repo['updated_at'],
                'private': repo['private']
            })
        
        return simplified_repos
    
    def get_repo_tree(self, owner: str, repo: str, branch: str = 'main') -> List[Dict]:
        """
        Récupère l'arbre complet des fichiers d'un repository.
        
        Args:
            owner: Propriétaire du repo (ex: 'facebook')
            repo: Nom du repo (ex: 'react')
            branch: Branche à analyser (défaut: 'main')
            
        Returns:
            List[Dict]: Liste de tous les fichiers avec leurs chemins
        """
        endpoint = f'/repos/{owner}/{repo}/git/trees/{branch}'
        params = {'recursive': '1'}  # Récursif = tous les fichiers
        
        try:
            data = self._make_request('GET', endpoint, params=params)
            
            # Filtrer uniquement les fichiers (pas les dossiers)
            files = []
            for item in data.get('tree', []):
                if item['type'] == 'blob':  # 'blob' = fichier, 'tree' = dossier
                    files.append({
                        'path': item['path'],
                        'size': item['size'],
                        'sha': item['sha'],  # Hash unique du fichier
                        'url': item['url']
                    })
            
            return files
            
        except GitHubAPIError as e:
            # Si 'main' n'existe pas, essayer 'master'
            if branch == 'main' and '404' in str(e):
                return self.get_repo_tree(owner, repo, branch='master')
            raise
    
    def get_file_content(self, owner: str, repo: str, file_path: str) -> Dict:
        """
        Récupère le contenu d'un fichier spécifique.
        
        Args:
            owner: Propriétaire du repo
            repo: Nom du repo
            file_path: Chemin du fichier (ex: 'src/app.py')
            
        Returns:
            Dict: {
                'content': 'contenu décodé du fichier',
                'encoding': 'utf-8',
                'size': 1234,
                'name': 'app.py',
                'path': 'src/app.py'
            }
        """
        endpoint = f'/repos/{owner}/{repo}/contents/{file_path}'
        
        data = self._make_request('GET', endpoint)
        
        # Le contenu est encodé en base64, il faut le décoder
        if data.get('encoding') == 'base64':
            content_bytes = base64.b64decode(data['content'])
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Si c'est un fichier binaire
                content = "[Fichier binaire - contenu non affichable]"
        else:
            content = data.get('content', '')
        
        return {
            'content': content,
            'encoding': data.get('encoding', 'utf-8'),
            'size': data.get('size', 0),
            'name': data.get('name', ''),
            'path': data.get('path', file_path),
            'sha': data.get('sha', '')
        }
    
    def validate_token(self) -> bool:
        """
        Vérifie si le token est valide.
        
        Returns:
            bool: True si le token fonctionne, False sinon
        """
        try:
            self.get_user_info()
            return True
        except GitHubAPIError:
            return False


# Fonction utilitaire pour créer un client
def create_github_client(token: str) -> GitHubClient:
    """
    Crée et retourne un client GitHub configuré.
    
    Args:
        token: Token d'accès GitHub
        
    Returns:
        GitHubClient: Client prêt à l'emploi
        
    Raises:
        GitHubAPIError: Si le token est invalide
    """
    client = GitHubClient(token)
    
    if not client.validate_token():
        raise GitHubAPIError("Token GitHub invalide")
    
    return client


# Made with Bob