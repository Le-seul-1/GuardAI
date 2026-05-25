"""
Middleware personnalisé pour GuardAI.

Ce middleware gère :
- Les exceptions non capturées
- Les erreurs 404 et 500
- Le logging des erreurs
- Les messages utilisateur
"""

import logging
import traceback
from django.shortcuts import render
from django.contrib import messages

logger = logging.getLogger('analyzer')


class ErrorHandlingMiddleware:
    """
    Middleware pour gérer toutes les erreurs de l'application.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        Traite les exceptions non capturées.
        """
        # Logger l'erreur
        logger.error(
            f"Exception non gérée : {type(exception).__name__}",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': request.user.username if request.user.is_authenticated else 'Anonymous'
            }
        )
        
        # Message utilisateur
        messages.error(
            request,
            "Une erreur inattendue s'est produite. "
            "Nos équipes ont été notifiées."
        )
        
        return render(request, 'error.html', {
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'error_code': 'INTERNAL_ERROR',
            'traceback': traceback.format_exc() if request.user.is_staff else None
        }, status=500)


class RequestLoggingMiddleware:
    """
    Middleware pour logger toutes les requêtes.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django')
    
    def __call__(self, request):
        # Log avant la requête
        self.logger.info(
            f"{request.method} {request.path}",
            extra={
                'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                'ip': self.get_client_ip(request)
            }
        )
        
        response = self.get_response(request)
        
        # Log après la requête
        self.logger.info(
            f"{request.method} {request.path} - Status {response.status_code}"
        )
        
        return response
    
    def get_client_ip(self, request):
        """Récupère l'IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# Made with Bob
