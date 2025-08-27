from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.logout_view, name='logout'),
    
    # Registration and verification
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify_email'),
    
    # Password management
    path('password/change/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/detail/', views.UserProfileDetailView.as_view(), name='user_profile_detail'),
    
    # Instructor application
    path('instructor/apply/', views.InstructorApplicationView.as_view(), name='instructor_apply'),
    
    # Dashboard
    path('dashboard/', views.user_dashboard_data, name='user_dashboard'),
]