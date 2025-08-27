"""
URLs for Financial Management Module
"""

from django.urls import path
from . import financial_views

urlpatterns = [
    # Admin Financial Management
    path('admin/dashboard/', financial_views.admin_financial_dashboard, name='admin_financial_dashboard'),
    
    # Instructor Financial Management
    path('instructor/dashboard/', financial_views.instructor_financial_dashboard, name='instructor_financial_dashboard'),
]