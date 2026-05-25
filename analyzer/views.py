from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.exceptions import ValidationError
from .github_api import GitHubClient, GitHubAPIError, create_github_client
from .groq_ai import analyze_code, GroqAIError
from .file_selector import select_critical_files, filter_already_analyzed, get_file_extension, get_file_name
from .models import AnalysisSession, FileAnalysis, SecurityReport
from .validators import validate_github_token, validate_file_size, validate_file_count, validate_repository_name
from github_auth.models import UserGitHubToken
import logging

logger = logging.getLogger('analyzer')

def home(request):
    """Home page view"""
    return render(request, 'home.html')


def repo_list(request):
    """
    Affiche la liste des repositories GitHub de l'utilisateur.
    """
    # For MVP, get token from session (manual token entry)
    github_token = request.session.get('github_token')
    
    if not github_token:
        logger.warning(f"Accès sans token - IP: {request.META.get('REMOTE_ADDR')}")
        messages.warning(request, "Veuillez d'abord entrer votre token GitHub.")
        return redirect('github_auth:token_input')
    
    try:
        # Valider le token
        validate_github_token(github_token)
        
        # Créer le client GitHub
        client = create_github_client(github_token)
        
        logger.info("Récupération des repositories")
        
        # Récupérer les repos
        repos = client.get_user_repos(per_page=50)
        
        # Récupérer les infos utilisateur
        user_info = client.get_user_info()
        
        logger.info(f"Succès : {len(repos)} repositories pour {user_info['login']}")
        
        context = {
            'repos': repos,
            'user_info': user_info,
            'total_repos': len(repos)
        }
        
        return render(request, 'repo_list.html', context)
        
    except ValidationError as e:
        logger.error(f"Token invalide : {str(e)}")
        messages.error(request, f"Token invalide : {str(e)}")
        return redirect('github_auth:token_input')
        
    except GitHubAPIError as e:
        logger.error(f"Erreur GitHub API : {str(e)}")
        messages.error(request, f"Erreur GitHub API : {str(e)}")
        return redirect('github_auth:token_input')
        
    except Exception as e:
        logger.critical(f"Erreur inattendue dans repo_list : {str(e)}", exc_info=True)
        messages.error(request, "Une erreur inattendue s'est produite.")
        return redirect('analyzer:home')


def select_repository(request, owner, repo):
    """
    Sélectionne un repository et récupère sa liste de fichiers.
    """
    github_token = request.session.get('github_token')
    
    if not github_token:
        logger.warning(f"Accès select_repository sans token - IP: {request.META.get('REMOTE_ADDR')}")
        messages.warning(request, "Veuillez d'abord entrer votre token GitHub.")
        return redirect('github_auth:token_input')
    
    try:
        # Valider le nom du repository
        repo_name = f"{owner}/{repo}"
        validate_repository_name(repo_name)
        
        client = create_github_client(github_token)
        
        logger.info(f"Sélection du repository : {repo_name}")
        
        # Récupérer les infos du repo
        repos = client.get_user_repos()
        selected_repo = next((r for r in repos if r['owner'] == owner and r['name'] == repo), None)
        
        if not selected_repo:
            logger.warning(f"Repository introuvable : {repo_name}")
            messages.error(request, "Repository introuvable.")
            return redirect('analyzer:repo_list')
        
        # Récupérer l'arbre des fichiers
        files = client.get_repo_tree(
            owner=owner,
            repo=repo,
            branch=selected_repo['default_branch']
        )
        
        logger.info(f"Succès : {len(files)} fichiers récupérés pour {repo_name}")
        
        # Stocker dans la session pour utilisation ultérieure
        request.session['selected_repo'] = {
            'owner': owner,
            'name': repo,
            'branch': selected_repo['default_branch'],
            'url': selected_repo['url']
        }
        request.session['repo_files'] = files
        
        context = {
            'repo': selected_repo,
            'files': files,
            'total_files': len(files)
        }
        
        return render(request, 'file_selection.html', context)
        
    except ValidationError as e:
        logger.error(f"Nom de repository invalide : {owner}/{repo} - {str(e)}")
        messages.error(request, f"Nom de repository invalide : {str(e)}")
        return redirect('analyzer:repo_list')
        
    except GitHubAPIError as e:
        logger.error(f"Erreur GitHub API pour {owner}/{repo} : {str(e)}")
        messages.error(request, f"Erreur : {str(e)}")
        return redirect('analyzer:repo_list')
        
    except Exception as e:
        logger.critical(f"Erreur inattendue dans select_repository : {str(e)}", exc_info=True)
        messages.error(request, "Une erreur inattendue s'est produite.")
        return redirect('analyzer:repo_list')

def file_selection(request, owner, repo):
    """
    Phase 5: Auto-select 3 critical files and create analysis session.
    """
    github_token = request.session.get('github_token')
    
    if not github_token:
        messages.warning(request, "Veuillez d'abord entrer votre token GitHub.")
        return redirect('github_auth:token_input')
    
    try:
        # Get repository files from session
        repo_files = request.session.get('repo_files', [])
        selected_repo = request.session.get('selected_repo')
        
        if not repo_files or not selected_repo:
            messages.error(request, "Veuillez d'abord sélectionner un repository.")
            return redirect('analyzer:repo_list')
        
        # Auto-select 3 critical files using IBM Bob AI
        selected_files = select_critical_files(repo_files, max_files=3)
        
        if len(selected_files) < 3:
            messages.warning(request, f"Seulement {len(selected_files)} fichiers critiques trouvés.")
        
        # Store selected files in session for confirmation
        request.session['selected_files'] = selected_files
        
        context = {
            'repo': selected_repo,
            'selected_files': selected_files,
            'total_files': len(repo_files)
        }
        
        return render(request, 'file_selection.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la sélection des fichiers : {str(e)}")
        return redirect('analyzer:repo_list')


def analyze_files(request, session_id=None):
    """
    Phase 5: Analyze the selected files and create/update session.
    """
    github_token = request.session.get('github_token')
    
    if not github_token:
        messages.warning(request, "Veuillez d'abord entrer votre token GitHub.")
        return redirect('github_auth:token_input')
    
    # Get data from session
    selected_repo = request.session.get('selected_repo')
    selected_files = request.session.get('selected_files', [])
    
    if not selected_repo or not selected_files:
        messages.error(request, "Aucun fichier sélectionné pour l'analyse.")
        return redirect('analyzer:repo_list')
    
    try:
        # Create GitHub client
        github_client = create_github_client(github_token)
        
        # Create or get analysis session
        if session_id:
            session = get_object_or_404(AnalysisSession, id=session_id)
        else:
            # Create new session (for initial 3 files)
            session = AnalysisSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                repository_name=selected_repo['name'],
                repository_owner=selected_repo['owner'],
                repository_url=selected_repo['url'],
                branch_name=selected_repo['branch'],
                status='in_progress'
            )
        
        # Analyze each selected file
        for idx, file_info in enumerate(selected_files, start=1):
            # Check if file already analyzed
            if FileAnalysis.objects.filter(session=session, file_path=file_info['path']).exists():
                continue
            
            # Get file content from GitHub
            file_data = github_client.get_file_content(
                owner=selected_repo['owner'],
                repo=selected_repo['name'],
                file_path=file_info['path']
            )
            
            # Analyze with Groq AI
            analysis_result = analyze_code(file_data['content'])
            
            # Count vulnerabilities by severity
            vulnerabilities = analysis_result.get('vulnerabilities', [])
            severity_level = 'info'
            if vulnerabilities:
                severities = [v.get('severity', 'low') for v in vulnerabilities]
                if 'critical' in severities:
                    severity_level = 'critical'
                elif 'high' in severities:
                    severity_level = 'high'
                elif 'medium' in severities:
                    severity_level = 'medium'
                else:
                    severity_level = 'low'
            
            # Create FileAnalysis record
            FileAnalysis.objects.create(
                session=session,
                file_path=file_info['path'],
                file_name=get_file_name(file_info['path']),
                file_extension=get_file_extension(file_info['path']),
                is_auto_selected=(session.file_count < 3),  # First 3 are auto-selected
                file_size=file_info.get('size', 0),
                file_content=file_data['content'][:10000],  # Store first 10KB only
                analysis_result=analysis_result,
                vulnerabilities_count=len(vulnerabilities),
                severity_level=severity_level,
                analysis_order=session.file_count + 1
            )
            
            # Increment file count
            session.increment_file_count()
        
        # Update session status
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        # Generate security report
        generate_security_report(session)
        
        messages.success(request, f"✅ Analyse terminée ! {session.file_count} fichier(s) analysé(s).")
        return redirect('analyzer:analysis_report', session_id=session.id)
        
    except GitHubAPIError as e:
        messages.error(request, f"Erreur GitHub : {str(e)}")
        return redirect('analyzer:repo_list')
    except GroqAIError as e:
        messages.error(request, f"Erreur Groq AI : {str(e)}")
        return redirect('analyzer:repo_list')
    except Exception as e:
        messages.error(request, f"Erreur inattendue : {str(e)}")
        return redirect('analyzer:repo_list')


def generate_security_report(session):
    """
    Phase 7: Generate comprehensive security report for a session.
    """
    # Get all file analyses for this session
    file_analyses = FileAnalysis.objects.filter(session=session)
    
    # Aggregate vulnerabilities
    total_vulnerabilities = 0
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    all_vulnerabilities = []
    
    for fa in file_analyses:
        vulnerabilities = fa.analysis_result.get('vulnerabilities', [])
        total_vulnerabilities += len(vulnerabilities)
        all_vulnerabilities.extend(vulnerabilities)
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'low')
            if severity == 'critical':
                critical_count += 1
            elif severity == 'high':
                high_count += 1
            elif severity == 'medium':
                medium_count += 1
            elif severity == 'low':
                low_count += 1
    
    # Generate summary
    if total_vulnerabilities == 0:
        summary = "✅ Aucune vulnérabilité détectée. Le code semble sécurisé."
    elif critical_count > 0:
        summary = f"🚨 {critical_count} vulnérabilité(s) CRITIQUE(S) détectée(s) ! Action immédiate requise."
    elif high_count > 0:
        summary = f"⚠️ {high_count} vulnérabilité(s) ÉLEVÉE(S) détectée(s). Correction recommandée rapidement."
    else:
        summary = f"ℹ️ {total_vulnerabilities} vulnérabilité(s) mineure(s) détectée(s)."
    
    # Generate recommendations
    recommendations = []
    
    if critical_count > 0:
        recommendations.append({
            'priority': 'critical',
            'category': 'Sécurité',
            'title': 'Corriger immédiatement les vulnérabilités critiques',
            'description': f'{critical_count} faille(s) de sécurité critique(s) détectée(s). Ces vulnérabilités peuvent être exploitées pour compromettre le système.'
        })
    
    if high_count > 0:
        recommendations.append({
            'priority': 'high',
            'category': 'Sécurité',
            'title': 'Corriger les vulnérabilités élevées',
            'description': f'{high_count} vulnérabilité(s) de niveau élevé nécessitent une attention rapide.'
        })
    
    if medium_count > 0:
        recommendations.append({
            'priority': 'medium',
            'category': 'Qualité',
            'title': 'Améliorer la qualité du code',
            'description': f'{medium_count} problème(s) de niveau moyen à corriger pour améliorer la sécurité.'
        })
    
    # Create or update SecurityReport
    report, created = SecurityReport.objects.update_or_create(
        session=session,
        defaults={
            'summary': summary,
            'total_vulnerabilities': total_vulnerabilities,
            'critical_count': critical_count,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count,
            'recommendations': recommendations
        }
    )
    
    return report


def analysis_report(request, session_id):
    """
    Phase 7: Display comprehensive analysis report.
    """
    session = get_object_or_404(AnalysisSession, id=session_id)
    
    # Get all file analyses
    file_analyses = FileAnalysis.objects.filter(session=session).order_by('analysis_order')
    
    # Get security report
    try:
        security_report = SecurityReport.objects.get(session=session)
    except SecurityReport.DoesNotExist:
        # Generate if doesn't exist
        security_report = generate_security_report(session)
    
    context = {
        'session': session,
        'file_analyses': file_analyses,
        'security_report': security_report,
        'can_add_file': session.can_add_file()
    }
    
    return render(request, 'analysis_report.html', context)


def add_file(request, session_id):
    """
    Phase 6: Add additional file to existing analysis session.
    """
    session = get_object_or_404(AnalysisSession, id=session_id)
    
    try:
        # Valider le nombre de fichiers
        validate_file_count(session.file_count)
    except ValidationError as e:
        logger.warning(f"Tentative d'ajout au-delà de la limite - Session {session_id}: {str(e)}")
        messages.warning(request, f"⚠️ {str(e)}")
        return redirect('analyzer:analysis_report', session_id=session.id)
    
    # Check if can add more files
    if not session.can_add_file():
        logger.warning(f"Limite de fichiers atteinte - Session {session_id}")
        messages.warning(request, "⚠️ Limite atteinte : 5 fichiers maximum par analyse.")
        return redirect('analyzer:analysis_report', session_id=session.id)
    
    github_token = request.session.get('github_token')
    
    if not github_token:
        logger.warning(f"Accès add_file sans token - Session {session_id}")
        messages.warning(request, "Veuillez d'abord entrer votre token GitHub.")
        return redirect('github_auth:token_input')
    
    # GET: Display file selection form
    if request.method == 'GET':
        try:
            # Get all repository files
            repo_files = request.session.get('repo_files', [])
            
            if not repo_files:
                # Fetch files again if not in session
                github_client = create_github_client(github_token)
                repo_files = github_client.get_repo_tree(
                    owner=session.repository_owner,
                    repo=session.repository_name,
                    branch=session.branch_name
                )
                request.session['repo_files'] = repo_files
            
            # Get already analyzed file paths
            analyzed_paths = list(
                FileAnalysis.objects.filter(session=session).values_list('file_path', flat=True)
            )
            
            # Filter out already analyzed files
            available_files = filter_already_analyzed(repo_files, analyzed_paths)
            
            context = {
                'session': session,
                'available_files': available_files,
                'analyzed_count': len(analyzed_paths),
                'remaining_slots': 5 - session.file_count
            }
            
            return render(request, 'add_file.html', context)
            
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
            return redirect('analyzer:analysis_report', session_id=session.id)
    
    # POST: Analyze selected file
    else:
        file_path = request.POST.get('file_path')
        
        if not file_path:
            messages.error(request, "Veuillez sélectionner un fichier.")
            return redirect('analyzer:add_file', session_id=session.id)
        
        try:
            # Check if file already analyzed
            if FileAnalysis.objects.filter(session=session, file_path=file_path).exists():
                messages.warning(request, "Ce fichier a déjà été analysé.")
                return redirect('analyzer:analysis_report', session_id=session.id)
            
            # Get file info from session
            repo_files = request.session.get('repo_files', [])
            file_info = next((f for f in repo_files if f['path'] == file_path), None)
            
            if not file_info:
                messages.error(request, "Fichier introuvable.")
                return redirect('analyzer:add_file', session_id=session.id)
            
            # Store selected file in session and analyze
            request.session['selected_files'] = [file_info]
            
            # Redirect to analyze_files with session_id
            return analyze_files(request, session_id=session.id)
            
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
            return redirect('analyzer:add_file', session_id=session.id)


def custom_404(request, exception):
    """Vue personnalisée pour les erreurs 404."""
    logger.warning(f"404 - Page introuvable : {request.path}")
    return render(request, '404.html', status=404)


def custom_500(request):
    """Vue personnalisée pour les erreurs 500."""
    logger.critical(f"500 - Erreur serveur sur : {request.path}")
    return render(request, '500.html', status=500)


# Made with Bob
