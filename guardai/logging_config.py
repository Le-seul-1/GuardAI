"""
Configuration du système de logging pour GuardAI.

Ce module configure les loggers pour différents niveaux :
- DEBUG : Informations détaillées pour le développement
- INFO : Événements généraux de l'application
- WARNING : Situations inhabituelles mais gérables
- ERROR : Erreurs qui nécessitent une attention
- CRITICAL : Erreurs graves qui peuvent arrêter l'application
"""

import logging
import os
from pathlib import Path

# Créer le dossier logs s'il n'existe pas
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Configuration du format des logs
LOG_FORMAT = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configuration des handlers
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': LOG_FORMAT,
            'datefmt': DATE_FORMAT,
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'guardai.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'analyzer': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'github_auth': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}


def setup_logging():
    """
    Configure le système de logging.
    À appeler dans settings.py
    """
    from logging.config import dictConfig
    dictConfig(LOGGING_CONFIG)

# Made with Bob
