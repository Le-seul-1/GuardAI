from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

# Temporary placeholder views - will be implemented in Phase 3

def token_input(request):
    """Display GitHub token input form"""
    return render(request, 'token_input.html')

def save_token(request):
    """Save GitHub token to session"""
    if request.method == 'POST':
        token = request.POST.get('token')
        if token:
            request.session['github_token'] = token
            messages.success(request, 'GitHub token saved successfully!')
            return redirect('analyzer:repo_list')
        else:
            messages.error(request, 'Please provide a valid token.')
    return redirect('github_auth:token_input')

def logout_view(request):
    """Clear GitHub token from session"""
    if 'github_token' in request.session:
        del request.session['github_token']
    messages.info(request, 'Logged out successfully.')
    return redirect('github_auth:token_input')

# Made with Bob
