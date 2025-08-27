from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.templatetags.static import static
from datetime import timedelta
import uuid

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import User, UserProfile, EmailVerification, PasswordResetToken, UserActivity
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    UserProfileSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer
)

# Import for Google OAuth
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from social_django.utils import psa
from social_core.exceptions import AuthCanceled, AuthForbidden
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@extend_schema(
    tags=['Authentication'],
    summary='Login Pengguna',
    description='''
    Endpoint untuk login pengguna dan mendapatkan JWT access token.
    
    Setelah login berhasil, aktivitas user akan dicatat untuk keperluan audit.
    Token yang diberikan berlaku selama 60 menit dan refresh token berlaku 7 hari.
    ''',
    examples=[
        OpenApiExample(
            'Login Request',
            value={
                'email': 'user@example.com',
                'password': 'password123'
            },
            request_only=True
        ),
        OpenApiExample(
            'Login Response',
            value={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'user': {
                    'id': 1,
                    'email': 'user@example.com',
                    'full_name': 'John Doe',
                    'role': 'student',
                    'profile_image': '/media/profiles/image.jpg'
                }
            },
            response_only=True
        )
    ],
    responses={
        200: {
            'description': 'Login berhasil',
            'content': {
                'application/json': {
                    'example': {
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'user': {
                            'id': 1,
                            'email': 'user@example.com',
                            'full_name': 'John Doe',
                            'role': 'student',
                            'profile_image': '/media/profiles/image.jpg'
                        }
                    }
                }
            }
        },
        401: {
            'description': 'Kredensial tidak valid',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'No active account found with the given credentials'
                    }
                }
            }
        }
    }
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view with user activity tracking and detailed user data"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Track login activity
            email = request.data.get('email')  # type: ignore
            user = User.objects.filter(email=email).first()
            if user:
                UserActivity.objects.create(  # type: ignore
                    user=user,
                    activity_type=UserActivity.ActivityType.LOGIN,
                    description=f"User logged in from {request.META.get('REMOTE_ADDR')}",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Add user data to response
                user_data = {
                    'id': user.pk,
                    'email': user.email,
                    'full_name': user.full_name or user.username,
                    'role': user.role,
                }
                
                # Add profile image URL if available
                if user.profile_image:
                    user_data['profile_image'] = user.profile_image.url
                else:
                    # Provide a default profile image
                    user_data['profile_image'] = static('images/default-profile.png')
                
                # Ensure response.data is not None before assignment
                if response.data is not None:
                    response.data['user'] = user_data
                else:
                    # Create a new dict if response.data is None
                    response.data = {'user': user_data}
        
        return response


@extend_schema(
    tags=['Authentication'],
    summary='Registrasi Pengguna Baru',
    description='''
    Endpoint untuk registrasi pengguna baru dengan role Student sebagai default.
    
    Setelah registrasi berhasil:
    - Profil pengguna akan dibuat otomatis
    - Token verifikasi email akan dikirim
    - JWT tokens akan diberikan untuk akses langsung
    - Aktivitas registrasi akan dicatat
    
    **Catatan**: Email perlu diverifikasi untuk mengaktifkan semua fitur akun.
    ''',
    examples=[
        OpenApiExample(
            'Registration Request',
            value={
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password': 'SecurePassword123!',
                'password_confirm': 'SecurePassword123!',
                'full_name': 'John Doe',
                'role': 'student'
            },
            request_only=True
        ),
        OpenApiExample(
            'Registration Response',
            value={
                'user': {
                    'id': 1,
                    'email': 'newuser@example.com',
                    'full_name': 'John Doe',
                    'role': 'student',
                    'profile_image': '/static/images/default-profile.png'
                },
                'tokens': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                },
                'verification_token': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                'message': 'Registration successful. Please check your email to verify your account.'
            },
            response_only=True
        )
    ],
    responses={
        201: {
            'description': 'Registrasi berhasil',
        },
        400: {
            'description': 'Data tidak valid',
            'content': {
                'application/json': {
                    'examples': {
                        'email_exists': {
                            'summary': 'Email sudah terdaftar',
                            'value': {
                                'email': ['User with this email already exists.']
                            }
                        },
                        'weak_password': {
                            'summary': 'Password terlalu lemah',
                            'value': {
                                'password': ['This password is too common.']
                            }
                        },
                        'username_taken': {
                            'summary': 'Username sudah digunakan',
                            'value': {
                                'username': ['A user with that username already exists.']
                            }
                        },
                        'password_mismatch': {
                            'summary': 'Password tidak cocok',
                            'value': {
                                'password_confirm': ["Passwords don't match"]
                            }
                        }
                    }
                }
            }
        }
    }
)
class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user
        user = serializer.save()
        
        # Create email verification token
        verification_token = str(uuid.uuid4())
        EmailVerification.objects.create(
            user=user,
            token=verification_token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Track registration activity
        UserActivity.objects.create(  # type: ignore
            user=user,
            activity_type=UserActivity.ActivityType.LOGIN,  # Consider as first login
            description="User registered",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Prepare user data for response
        user_data = {
            'id': user.pk,
            'email': user.email,
            'full_name': user.full_name or user.username,
            'role': user.role,
        }
        
        # Add profile image URL if available
        if user.profile_image:
            user_data['profile_image'] = user.profile_image.url
        else:
            # Provide a default profile image
            user_data['profile_image'] = static('images/default-profile.png')
        
        return Response({
            'user': user_data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'verification_token': verification_token,
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Authentication'],
    summary='Verifikasi Email',
    description='''
    Endpoint untuk memverifikasi email pengguna menggunakan token yang dikirim via email.
    
    Token verifikasi berlaku selama 24 jam setelah registrasi.
    Setelah verifikasi berhasil, status `is_email_verified` akan diubah menjadi `true`.
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'token': {
                    'type': 'string',
                    'description': 'Token verifikasi yang dikirim via email',
                    'example': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
                }
            },
            'required': ['token']
        }
    },
    examples=[
        OpenApiExample(
            'Verification Request',
            value={
                'token': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
            },
            request_only=True
        )
    ],
    responses={
        200: {
            'description': 'Email berhasil diverifikasi',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Email verified successfully'
                    }
                }
            }
        },
        400: {
            'description': 'Token tidak valid atau sudah expired',
            'content': {
                'application/json': {
                    'examples': {
                        'missing_token': {
                            'summary': 'Token tidak disediakan',
                            'value': {
                                'error': 'Verification token is required'
                            }
                        },
                        'invalid_token': {
                            'summary': 'Token tidak valid',
                            'value': {
                                'error': 'Invalid verification token'
                            }
                        },
                        'expired_token': {
                            'summary': 'Token sudah expired',
                            'value': {
                                'error': 'Verification token is invalid or expired'
                            }
                        }
                    }
                }
            }
        }
    }
)
class EmailVerificationView(generics.GenericAPIView):
    """Email verification endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Verification token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            verification = EmailVerification.objects.get(token=token)  # type: ignore
            
            if not verification.is_valid():
                return Response(
                    {'error': 'Verification token is invalid or expired'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark email as verified
            verification.user.is_email_verified = True
            verification.user.save()
            
            # Mark verification as used
            verification.is_used = True
            verification.save()
            
            return Response(
                {'message': 'Email verified successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except EmailVerification.DoesNotExist:  # type: ignore
            return Response(
                {'error': 'Invalid verification token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=['Profile'],
    summary='Get or Update User Profile',
    description='''
    Endpoint untuk mendapatkan atau memperbarui profil pengguna.
    
    GET: Mendapatkan informasi profil pengguna
    PUT: Memperbarui informasi profil pengguna
    
    Hanya pengguna yang terautentikasi yang dapat mengakses endpoint ini.
    ''',
    examples=[
        OpenApiExample(
            'Profile Response',
            value={
                'id': 1,
                'email': 'user@example.com',
                'username': 'johndoe',
                'full_name': 'John Doe',
                'role': 'student',
                'bio': 'Software developer passionate about learning',
                'profile_image': 'http://example.com/media/profiles/image.jpg',
                'birth_date': '1990-01-01',
                'phone': '+1234567890',
                'country': 'United States',
                'city': 'New York',
                'is_email_verified': True,
                'verification_status': 'verified',
                'date_joined': '2023-01-01T00:00:00Z',
                'last_login': '2023-01-15T10:30:00Z'
            },
            response_only=True
        )
    ]
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):  # type: ignore
        return self.request.user


@extend_schema(
    tags=['Profile'],
    summary='Get or Update Detailed User Profile',
    description='''
    Endpoint untuk mendapatkan atau memperbarui profil pengguna yang lebih detail.
    
    GET: Mendapatkan informasi profil detail pengguna
    PUT: Memperbarui informasi profil detail pengguna
    
    Informasi detail mencakup media sosial, pendidikan, pengalaman kerja, 
    keterampilan, dan minat pengguna.
    
    Hanya pengguna yang terautentikasi yang dapat mengakses endpoint ini.
    ''',
    examples=[
        OpenApiExample(
            'Profile Detail Response',
            value={
                'user_email': 'user@example.com',
                'user_full_name': 'John Doe',
                'website': 'https://johndoe.com',
                'linkedin': 'https://linkedin.com/in/johndoe',
                'twitter': 'https://twitter.com/johndoe',
                'github': 'https://github.com/johndoe',
                'education': [
                    {
                        'institution': 'University of Example',
                        'degree': 'Bachelor of Science',
                        'field_of_study': 'Computer Science',
                        'start_date': '2010-09-01',
                        'end_date': '2014-06-01'
                    }
                ],
                'experience': [
                    {
                        'company': 'Tech Company',
                        'position': 'Software Developer',
                        'description': 'Developed web applications',
                        'start_date': '2015-01-01',
                        'end_date': '2020-12-31'
                    }
                ],
                'skills': ['Python', 'JavaScript', 'Django'],
                'interests': ['Web Development', 'Machine Learning'],
                'profile_visibility': 'public'
            },
            response_only=True
        )
    ]
)
class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """Get and update detailed user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):  # type: ignore
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)  # type: ignore
        return profile


class ChangePasswordView(generics.UpdateAPIView):
    """Change user password"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):  # type: ignore
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Invalid old password'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {'message': 'Password changed successfully'}, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    """Request password reset"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            
            # Create password reset token
            reset_token = str(uuid.uuid4())
            PasswordResetToken.objects.create(  # type: ignore
                user=user,
                token=reset_token,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            
            # In a real application, send email here
            # send_password_reset_email(user, reset_token)
            
            return Response(
                {
                    'message': 'Password reset instructions sent to your email',
                    'reset_token': reset_token  # Remove this in production
                }, 
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:  # type: ignore
            # Don't reveal if email exists
            return Response(
                {'message': 'If the email exists, password reset instructions have been sent'}, 
                status=status.HTTP_200_OK
            )


class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset with token"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not token or not new_password:
            return Response(
                {'error': 'Token and new password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate password
            validate_password(new_password)
        except ValidationError as e:
            return Response(
                {'error': e.messages}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)  # type: ignore
            
            if not reset_token.is_valid():
                return Response(
                    {'error': 'Reset token is invalid or expired'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password
            reset_token.user.set_password(new_password)
            reset_token.user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return Response(
                {'message': 'Password reset successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except PasswordResetToken.DoesNotExist:  # type: ignore
            return Response(
                {'error': 'Invalid reset token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class InstructorApplicationView(generics.UpdateAPIView):
    """Apply to become an instructor"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        
        if user.role == User.UserRole.INSTRUCTOR:
            return Response(
                {'error': 'You are already an instructor'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user to apply for instructor role
        user.instructor_application_date = timezone.now()
        user.instructor_bio = request.data.get('instructor_bio', '')
        user.expertise_areas = request.data.get('expertise_areas', [])
        user.verification_status = User.VerificationStatus.PENDING
        user.save()
        
        return Response(
            {'message': 'Instructor application submitted successfully'}, 
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_data(request):
    """Get dashboard data for current user"""
    user = request.user
    
    if user.role == User.UserRole.STUDENT:
        # Student dashboard data
        enrollments = user.enrollments.filter(is_active=True)
        data = {
            'user_type': 'student',
            'total_courses': enrollments.count(),
            'completed_courses': enrollments.filter(status='completed').count(),
            'in_progress_courses': enrollments.filter(status='active').count(),
            'recent_activities': []  # Add recent activities
        }
    
    elif user.role == User.UserRole.INSTRUCTOR:
        # Instructor dashboard data
        courses = user.created_courses.filter(is_published=True)
        data = {
            'user_type': 'instructor',
            'total_courses': courses.count(),
            'total_students': sum(course.total_enrollments for course in courses),
            'pending_courses': user.created_courses.filter(status='pending_review').count(),
            'recent_activities': []  # Add recent activities
        }
    
    else:
        # Admin dashboard data
        data = {
            'user_type': 'admin',
            'total_users': User.objects.count(),
            'total_instructors': User.objects.filter(role='instructor').count(),
            'pending_instructor_applications': User.objects.filter(
                verification_status='pending'
            ).count(),
        }
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout user and track activity"""
    try:
        # Track logout activity
        UserActivity.objects.create(  # type: ignore
            user=request.user,
            activity_type=UserActivity.ActivityType.LOGOUT,
            description="User logged out",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(
            {'message': 'Logged out successfully'}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': 'Logout failed'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

