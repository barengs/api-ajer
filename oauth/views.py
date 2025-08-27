"""
OAuth views for social authentication
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.utils import timezone
from social_core.exceptions import AuthCanceled, AuthForbidden
from social_django.utils import load_strategy, load_backend
from drf_spectacular.utils import extend_schema
from accounts.models import User, UserActivity
from accounts.serializers import UserSerializer
from typing import cast


@api_view(['POST'])
@permission_classes([AllowAny])
@extend_schema(
    tags=['Authentication'],
    summary='Google OAuth Login/Register',
    description='''
    Endpoint for Google OAuth login/registration.
    
    This endpoint accepts a Google OAuth token and either logs in an existing user
    or creates a new user if one doesn't exist with the Google email.
    
    The user will be authenticated and JWT tokens will be returned.
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'access_token': {
                    'type': 'string',
                    'description': 'Google OAuth2 access token'
                }
            },
            'required': ['access_token']
        }
    },
    responses={
        200: {
            'description': 'Authentication successful',
            'content': {
                'application/json': {
                    'example': {
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'user': {
                            'id': 1,
                            'email': 'user@gmail.com',
                            'full_name': 'John Doe',
                            'role': 'student',
                            'profile_image': '/media/profiles/image.jpg'
                        },
                        'is_new_user': False
                    }
                }
            }
        },
        400: {
            'description': 'Invalid token or authentication failed',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Authentication failed',
                        'details': 'Invalid token'
                    }
                }
            }
        }
    }
)
def google_oauth_login(request):
    """
    Handle Google OAuth login/registration via access token
    """
    try:
        # Get the access token from the request
        access_token = request.data.get('access_token')
        if not access_token:
            return Response(
                {'error': 'Access token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Use the social auth backend to authenticate
        strategy = load_strategy(request)
        backend = load_backend(strategy, 'google-oauth2', redirect_uri=None)
        
        # Authenticate with Google
        user = backend.do_auth(access_token)
        
        if user and user.is_active:
            # Log in the user
            login(request, user)
            
            # Generate JWT tokens
            refresh = cast(RefreshToken, RefreshToken.for_user(user))
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            # Check if this is a new user (first login)
            is_new_user = not hasattr(user, 'last_login') or user.last_login is None
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Track login activity
            UserActivity.objects.create(
                user=user,
                activity_type=UserActivity.ActivityType.LOGIN,
                description=f"User logged in via Google OAuth from {request.META.get('REMOTE_ADDR')}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_serializer.data,
                'is_new_user': is_new_user
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Authentication failed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except AuthCanceled:
        return Response(
            {'error': 'Authentication canceled by user'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except AuthForbidden:
        return Response(
            {'error': 'Authentication forbidden'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        return Response(
            {'error': 'Authentication failed', 'details': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )