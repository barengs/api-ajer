"""
Health check views for monitoring application status
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
import logging
from typing import Any

logger = logging.getLogger(__name__)

@extend_schema(
    tags=['Health'],
    summary='Basic Health Check',
    description='Returns the health status of the application',
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'healthy'},
                    'timestamp': {'type': 'string', 'format': 'date-time'},
                    'database': {'type': 'string', 'example': 'connected'},
                    'cache': {'type': 'string', 'example': 'connected'}
                }
            },
            description='Application is healthy'
        ),
        503: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'unhealthy'},
                    'error': {'type': 'string'},
                    'timestamp': {'type': 'string', 'format': 'date-time'}
                }
            },
            description='Application is unhealthy'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if the application is healthy, 503 otherwise
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        # Check cache connectivity
        cache.set('health_check', 'ok', 30)
        cache_status = cache.get('health_check') == 'ok'
        
        if not cache_status:
            raise Exception("Cache health check failed")
            
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'cache': 'connected'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@extend_schema(
    tags=['Health'],
    summary='Deep Health Check',
    description='Performs comprehensive health checks including external services',
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'healthy'},
                    'timestamp': {'type': 'string', 'format': 'date-time'},
                    'checks': {
                        'type': 'object',
                        'properties': {
                            'database': {'type': 'string', 'example': 'connected'},
                            'cache': {'type': 'string', 'example': 'connected'},
                            'redis': {'type': 'string', 'example': 'connected'}
                        }
                    }
                }
            },
            description='Application is healthy'
        ),
        503: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'unhealthy'},
                    'error': {'type': 'string'},
                    'timestamp': {'type': 'string', 'format': 'date-time'}
                }
            },
            description='Application is unhealthy'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def deep_health_check(request):
    """
    Deep health check endpoint
    Performs more comprehensive checks including external services
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        # Check cache connectivity
        cache.set('health_check', 'ok', 30)
        cache_status = cache.get('health_check') == 'ok'
        
        # Check Redis connectivity (used by Celery)
        redis_status = False
        try:
            import redis
            from django.conf import settings
            redis_client: Any = redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
            redis_status = True
        except Exception as e:
            logger.warning(f"Redis health check failed: {str(e)}")
            redis_status = False
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': 'connected',
                'cache': 'connected' if cache_status else 'disconnected',
                'redis': 'connected' if redis_status else 'disconnected',
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Deep health check failed: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)