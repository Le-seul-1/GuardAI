"""
Validateurs personnalisés pour GuardAI.

Ce module contient tous les validateurs pour :
- Tokens GitHub
- Tailles de fichiers
- Formats de données
- Limites de l'application
"""

import re
from django.core.exceptions import ValidationError


class GitHubTokenValidator:
    """
    Valide les tokens GitHub.
    
    Format attendu : ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    """
    
    def __call__(self, value):
        if not value:
            raise ValidationError("Le token GitHub ne peut pas être vide.")
        
        if not isinstance(value, str):
            raise ValidationError("Le token doit être une chaîne de caractères.")
        
        if len(value) < 40:
            raise ValidationError("Le token GitHub est trop court (minimum 40 caractères).")
        
        if not value.startswith('ghp_') and not value.startswith('github_pat_'):
            raise ValidationError(
                "Le token doit commencer par 'ghp_' ou 'github_pat_'. "
                "Vérifiez que vous avez copié le bon token."
            )
        
        return value


class FileSizeValidator:
    """
    Valide la taille des fichiers.
    
    Limite : 1 MB par défaut
    """
    
    def __init__(self, max_size_mb=1):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_size_mb = max_size_mb
    
    def __call__(self, size_bytes):
        if size_bytes > self.max_size_bytes:
            raise ValidationError(
                f"Le fichier est trop volumineux ({size_bytes / 1024 / 1024:.2f} MB). "
                f"Taille maximale : {self.max_size_mb} MB."
            )
        
        return size_bytes


class RepositoryNameValidator:
    """
    Valide les noms de repository GitHub.
    
    Format : owner/repo
    """
    
    REPO_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$')
    
    def __call__(self, value):
        if not value:
            raise ValidationError("Le nom du repository ne peut pas être vide.")
        
        if '/' not in value:
            raise ValidationError(
                "Le nom du repository doit être au format 'owner/repo'."
            )
        
        if not self.REPO_PATTERN.match(value):
            raise ValidationError(
                "Le nom du repository contient des caractères invalides. "
                "Utilisez uniquement des lettres, chiffres, tirets et underscores."
            )
        
        return value


class FileCountValidator:
    """
    Valide le nombre de fichiers dans une session.
    
    Maximum : 5 fichiers
    """
    
    MAX_FILES = 5
    
    def __call__(self, count):
        if count < 0:
            raise ValidationError("Le nombre de fichiers ne peut pas être négatif.")
        
        if count > self.MAX_FILES:
            raise ValidationError(
                f"Limite de {self.MAX_FILES} fichiers atteinte. "
                f"Vous ne pouvez pas ajouter plus de fichiers."
            )
        
        return count


def validate_github_token(token):
    """Valide un token GitHub."""
    validator = GitHubTokenValidator()
    return validator(token)


def validate_file_size(size_bytes, max_size_mb=1):
    """Valide la taille d'un fichier."""
    validator = FileSizeValidator(max_size_mb)
    return validator(size_bytes)


def validate_repository_name(repo_name):
    """Valide un nom de repository."""
    validator = RepositoryNameValidator()
    return validator(repo_name)


def validate_file_count(count):
    """Valide le nombre de fichiers."""
    validator = FileCountValidator()
    return validator(count)

# Made with Bob
