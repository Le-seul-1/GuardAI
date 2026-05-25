"""
File Selector Module for GuardAI

This module handles automatic selection of critical files for security analysis.
Uses IBM Bob AI's intelligent file selection algorithm.
"""

from typing import List, Dict


def select_critical_files(files: List[Dict], max_files: int = 3) -> List[Dict]:
    """
    Select the most critical files for security analysis.
    
    This function uses a local algorithm to identify
    the most security-critical files in a repository.
    
    Priority order:
    1. Backend files (Python, Java, Node.js, etc.)
    2. Configuration files (.env, .yml, .json)
    3. Authentication/Security files (auth, login, user)
    4. API routes and database models
    
    Args:
        files: List of file dictionaries from GitHub API
        max_files: Maximum number of files to select (default: 3)
        
    Returns:
        List[Dict]: Selected files with priority scores
        
    Example:
        >>> files = [{'path': 'app.py', 'size': 1024}, ...]
        >>> selected = select_critical_files(files, max_files=3)
        >>> len(selected)
        3
    """
    return _fallback_file_selection(files, max_files)


def _fallback_file_selection(files: List[Dict], max_files: int = 3) -> List[Dict]:
    """
    Fallback file selection algorithm (local, no API call).
    
    Used when IBM Bob AI is unavailable or fails.
    
    Args:
        files: List of file dictionaries
        max_files: Maximum number of files to select
        
    Returns:
        List[Dict]: Selected files with priority scores
    """
    # Critical extensions by priority
    CRITICAL_EXTENSIONS = {
        'high': ['.py', '.java', '.js', '.ts', '.php', '.rb', '.go'],
        'medium': ['.yml', '.yaml', '.json', '.xml', '.env', '.config'],
        'low': ['.sql', '.sh', '.bat', '.ps1']
    }
    
    # Critical keywords in file paths
    CRITICAL_KEYWORDS = [
        'auth', 'login', 'user', 'password', 'token', 'secret',
        'config', 'settings', 'database', 'db', 'model', 'models',
        'api', 'security', 'admin', 'route', 'controller'
    ]
    
    # Directories to deprioritize
    IGNORE_DIRS = ['test', 'tests', '__pycache__', 'node_modules', 'venv', 
                   'migrations', 'static', 'media', 'dist', 'build']
    
    scored_files = []
    
    for file in files:
        score = 0
        path_lower = file['path'].lower()
        
        # Skip if in ignored directory
        if any(ignored in path_lower for ignored in IGNORE_DIRS):
            continue
        
        # Score based on file extension
        for priority, extensions in CRITICAL_EXTENSIONS.items():
            if any(path_lower.endswith(ext) for ext in extensions):
                if priority == 'high':
                    score += 10
                elif priority == 'medium':
                    score += 5
                else:
                    score += 2
                break
        
        # Score based on critical keywords
        for keyword in CRITICAL_KEYWORDS:
            if keyword in path_lower:
                score += 3
        
        # Bonus for root-level files
        if '/' not in file['path'] or file['path'].count('/') == 1:
            score += 2
        
        # Penalty for test files
        if 'test' in path_lower or 'spec' in path_lower:
            score -= 10
        
        # Penalty for very large files (> 100KB)
        if file.get('size', 0) > 100000:
            score -= 3
        
        # Penalty for very small files (< 100 bytes)
        if file.get('size', 0) < 100:
            score -= 2
        
        if score > 0:
            scored_files.append({
                **file,
                'priority_score': score
            })
    
    # Sort by score (descending) and return top N
    scored_files.sort(key=lambda x: x['priority_score'], reverse=True)
    return scored_files[:max_files]


def filter_already_analyzed(files: List[Dict], analyzed_paths: List[str]) -> List[Dict]:
    """
    Filter out files that have already been analyzed.
    
    Args:
        files: List of all files
        analyzed_paths: List of file paths already analyzed
        
    Returns:
        List[Dict]: Files not yet analyzed
    """
    return [f for f in files if f['path'] not in analyzed_paths]


def get_file_extension(file_path: str) -> str:
    """
    Extract file extension from path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: File extension (e.g., '.py', '.js')
    """
    if '.' in file_path:
        return '.' + file_path.split('.')[-1]
    return ''


def get_file_name(file_path: str) -> str:
    """
    Extract file name from path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: File name (e.g., 'app.py')
    """
    return file_path.split('/')[-1]


# Made with Bob