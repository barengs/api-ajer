"""
URLs for OAuth app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('google/', views.google_oauth_login, name='google_oauth_login'),
]