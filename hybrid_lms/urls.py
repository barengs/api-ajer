"""hybrid_lms URL Configuration"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

def redirect_to_api(request):
    return redirect('api/docs/')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('', redirect_to_api),
    # Health Check
    path('api/v1/', include('health.urls')),
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Routes
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/oauth/', include('oauth.urls')),
    path('api/v1/auth/oauth/', include('social_django.urls', namespace='social')),
    path('api/v1/courses/', include('courses.urls')),
    path('api/v1/lessons/', include('lessons.urls')),
    path('api/v1/assignments/', include('assignments.urls')),
    path('api/v1/forums/', include('forums.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/gamification/', include('gamification.urls')),
    path('api/v1/live-sessions/', include('live_sessions.urls')),
    path('api/v1/role-management/', include('role_management.urls')),
    path('api/v1/navigation/', include('navigation.urls')),
    path('api/v1/recommendations/', include('recommendations.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)