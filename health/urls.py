"""
URL configuration for health check endpoints
"""

from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('health/deep/', views.deep_health_check, name='deep_health_check'),
]