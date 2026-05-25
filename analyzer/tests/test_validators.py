"""
Tests pour les validateurs personnalisés.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from analyzer.validators import (
    validate_github_token,
    validate_file_size,
    validate_file_count,
    validate_repository_name,
    GitHubTokenValidator,
    FileSizeValidator,
    RepositoryNameValidator,
    FileCountValidator
)


class GitHubTokenValidatorTest(TestCase):
    """Tests pour le validateur de token GitHub."""
    
    def test_valid_token_ghp_prefix(self):
        """Test avec un token valide (préfixe ghp_)."""
        valid_token = 'ghp_' + 'x' * 36
        result = validate_github_token(valid_token)
        self.assertEqual(result, valid_token)
    
    def test_valid_token_github_pat_prefix(self):
        """Test avec un token valide (préfixe github_pat_)."""
        valid_token = 'github_pat_' + 'x' * 36
        result = validate_github_token(valid_token)
        self.assertEqual(result, valid_token)
    
    def test_invalid_token_too_short(self):
        """Test avec un token trop court."""
        with self.assertRaises(ValidationError) as context:
            validate_github_token('ghp_short')
        
        self.assertIn('trop court', str(context.exception))
    
    def test_invalid_token_wrong_prefix(self):
        """Test avec un mauvais préfixe."""
        with self.assertRaises(ValidationError) as context:
            validate_github_token('invalid_' + 'x' * 36)
        
        self.assertIn('doit commencer par', str(context.exception))
    
    def test_invalid_token_empty(self):
        """Test avec un token vide."""
        with self.assertRaises(ValidationError) as context:
            validate_github_token('')
        
        self.assertIn('ne peut pas être vide', str(context.exception))
    
    def test_invalid_token_none(self):
        """Test avec None."""
        with self.assertRaises(ValidationError):
            validate_github_token(None)
    
    def test_invalid_token_not_string(self):
        """Test avec un type invalide."""
        with self.assertRaises(ValidationError) as context:
            validate_github_token(12345)
        
        self.assertIn('chaîne de caractères', str(context.exception))


class FileSizeValidatorTest(TestCase):
    """Tests pour le validateur de taille de fichier."""
    
    def test_valid_file_size(self):
        """Test avec une taille valide."""
        valid_size = 500 * 1024  # 500 KB
        result = validate_file_size(valid_size)
        self.assertEqual(result, valid_size)
    
    def test_valid_file_size_at_limit(self):
        """Test avec une taille exactement à la limite."""
        limit_size = 1 * 1024 * 1024  # 1 MB
        result = validate_file_size(limit_size)
        self.assertEqual(result, limit_size)
    
    def test_invalid_file_size_too_large(self):
        """Test avec une taille trop grande."""
        with self.assertRaises(ValidationError) as context:
            validate_file_size(2 * 1024 * 1024)  # 2 MB
        
        self.assertIn('trop volumineux', str(context.exception))
    
    def test_custom_max_size(self):
        """Test avec une limite personnalisée."""
        validator = FileSizeValidator(max_size_mb=5)
        
        # 3 MB devrait passer avec limite de 5 MB
        result = validator(3 * 1024 * 1024)
        self.assertEqual(result, 3 * 1024 * 1024)
        
        # 6 MB devrait échouer
        with self.assertRaises(ValidationError):
            validator(6 * 1024 * 1024)
    
    def test_zero_size(self):
        """Test avec une taille de 0."""
        result = validate_file_size(0)
        self.assertEqual(result, 0)


class RepositoryNameValidatorTest(TestCase):
    """Tests pour le validateur de nom de repository."""
    
    def test_valid_repository_name(self):
        """Test avec un nom de repo valide."""
        valid_name = 'owner/repo-name'
        result = validate_repository_name(valid_name)
        self.assertEqual(result, valid_name)
    
    def test_valid_repository_name_with_underscores(self):
        """Test avec des underscores."""
        valid_name = 'test_owner/test_repo'
        result = validate_repository_name(valid_name)
        self.assertEqual(result, valid_name)
    
    def test_valid_repository_name_with_dots(self):
        """Test avec des points dans le nom du repo."""
        valid_name = 'owner/repo.name'
        result = validate_repository_name(valid_name)
        self.assertEqual(result, valid_name)
    
    def test_valid_repository_name_with_numbers(self):
        """Test avec des chiffres."""
        valid_name = 'owner123/repo456'
        result = validate_repository_name(valid_name)
        self.assertEqual(result, valid_name)
    
    def test_invalid_repository_name_no_slash(self):
        """Test sans slash (format invalide)."""
        with self.assertRaises(ValidationError) as context:
            validate_repository_name('invalid-format')
        
        self.assertIn('owner/repo', str(context.exception))
    
    def test_invalid_repository_name_empty(self):
        """Test avec un nom vide."""
        with self.assertRaises(ValidationError) as context:
            validate_repository_name('')
        
        self.assertIn('ne peut pas être vide', str(context.exception))
    
    def test_invalid_repository_name_special_chars(self):
        """Test avec des caractères spéciaux invalides."""
        with self.assertRaises(ValidationError) as context:
            validate_repository_name('owner/repo@name')
        
        self.assertIn('caractères invalides', str(context.exception))
    
    def test_invalid_repository_name_spaces(self):
        """Test avec des espaces."""
        with self.assertRaises(ValidationError):
            validate_repository_name('owner/repo name')


class FileCountValidatorTest(TestCase):
    """Tests pour le validateur de nombre de fichiers."""
    
    def test_valid_file_count_zero(self):
        """Test avec 0 fichier."""
        result = validate_file_count(0)
        self.assertEqual(result, 0)
    
    def test_valid_file_count_one(self):
        """Test avec 1 fichier."""
        result = validate_file_count(1)
        self.assertEqual(result, 1)
    
    def test_valid_file_count_three(self):
        """Test avec 3 fichiers (auto-sélection)."""
        result = validate_file_count(3)
        self.assertEqual(result, 3)
    
    def test_valid_file_count_five(self):
        """Test avec 5 fichiers (limite maximale)."""
        result = validate_file_count(5)
        self.assertEqual(result, 5)
    
    def test_invalid_file_count_too_high(self):
        """Test avec un nombre trop élevé."""
        with self.assertRaises(ValidationError) as context:
            validate_file_count(6)
        
        self.assertIn('Limite de 5 fichiers', str(context.exception))
    
    def test_invalid_file_count_negative(self):
        """Test avec un nombre négatif."""
        with self.assertRaises(ValidationError) as context:
            validate_file_count(-1)
        
        self.assertIn('ne peut pas être négatif', str(context.exception))
    
    def test_invalid_file_count_large_number(self):
        """Test avec un très grand nombre."""
        with self.assertRaises(ValidationError):
            validate_file_count(100)


class ValidatorClassesTest(TestCase):
    """Tests pour les classes de validateurs."""
    
    def test_github_token_validator_class(self):
        """Test de la classe GitHubTokenValidator."""
        validator = GitHubTokenValidator()
        
        valid_token = 'ghp_' + 'x' * 36
        result = validator(valid_token)
        self.assertEqual(result, valid_token)
    
    def test_file_size_validator_class(self):
        """Test de la classe FileSizeValidator."""
        validator = FileSizeValidator(max_size_mb=2)
        
        valid_size = 1.5 * 1024 * 1024  # 1.5 MB
        result = validator(valid_size)
        self.assertEqual(result, valid_size)
    
    def test_repository_name_validator_class(self):
        """Test de la classe RepositoryNameValidator."""
        validator = RepositoryNameValidator()
        
        valid_name = 'owner/repo'
        result = validator(valid_name)
        self.assertEqual(result, valid_name)
    
    def test_file_count_validator_class(self):
        """Test de la classe FileCountValidator."""
        validator = FileCountValidator()
        
        self.assertEqual(validator.MAX_FILES, 5)
        
        result = validator(3)
        self.assertEqual(result, 3)


class EdgeCasesTest(TestCase):
    """Tests pour les cas limites."""
    
    def test_github_token_exactly_40_chars(self):
        """Test avec un token de exactement 40 caractères."""
        token = 'ghp_' + 'x' * 36  # 4 + 36 = 40
        result = validate_github_token(token)
        self.assertEqual(result, token)
    
    def test_file_size_exactly_1mb(self):
        """Test avec exactement 1 MB."""
        size = 1024 * 1024
        result = validate_file_size(size)
        self.assertEqual(result, size)
    
    def test_file_size_one_byte_over_limit(self):
        """Test avec 1 byte au-dessus de la limite."""
        with self.assertRaises(ValidationError):
            validate_file_size(1024 * 1024 + 1)
    
    def test_repository_name_minimum_valid(self):
        """Test avec le nom le plus court valide."""
        result = validate_repository_name('a/b')
        self.assertEqual(result, 'a/b')
    
    def test_file_count_boundary_values(self):
        """Test des valeurs limites pour le compteur."""
        # Valeurs valides
        for count in [0, 1, 2, 3, 4, 5]:
            result = validate_file_count(count)
            self.assertEqual(result, count)
        
        # Valeurs invalides
        for count in [-1, 6, 10]:
            with self.assertRaises(ValidationError):
                validate_file_count(count)

# Made with Bob