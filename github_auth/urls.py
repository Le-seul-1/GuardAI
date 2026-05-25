from django.urls import path
from . import views

app_name = 'github_auth'

urlpatterns = [
    path('token/', views.token_input, name='token_input'),
    path('token/save/', views.save_token, name='save_token'),
    path('logout/', views.logout_view, name='logout'),
]

# Made with Bob
