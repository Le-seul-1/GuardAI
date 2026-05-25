from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.home, name='home'),
    path('repos/', views.repo_list, name='repo_list'),
    path('repos/<str:owner>/<str:repo>/select/', views.select_repository, name='select_repository'),
    path('repos/<str:owner>/<str:repo>/files/', views.file_selection, name='file_selection'),
    # Initial analysis (no session_id) - creates new session
    path('analyze/', views.analyze_files, name='analyze_files'),
    # Analysis with existing session (for adding files)
    path('session/<int:session_id>/analyze/', views.analyze_files, name='analyze_files_with_session'),
    path('session/<int:session_id>/report/', views.analysis_report, name='analysis_report'),
    path('session/<int:session_id>/add-file/', views.add_file, name='add_file'),
]

# Made with Bob
