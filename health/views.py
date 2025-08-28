"""
Health check views for monitoring application status
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def health_check(request):
    """
    Simple health check endpoint for deployment verification
    """
    try:
        # Check database connection
        db_status = "ok"
        try:
            connection.ensure_connection()
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error(f"Database connection error: {e}")

        # Check cache (if configured)
        cache_status = "ok"
        try:
            cache.set("health_check", "ok", 30)
            if cache.get("health_check") != "ok":
                cache_status = "error: cache not working"
        except Exception as e:
            cache_status = f"error: {str(e)}"
            logger.error(f"Cache error: {e}")

        # Prepare response
        status = "ok" if db_status == "ok" and cache_status == "ok" else "degraded"
        
        response_data = {
            "status": status,
            "timestamp": timezone.now().isoformat(),
            "services": {
                "database": db_status,
                "cache": cache_status,
            }
        }

        # Return appropriate status code
        status_code = 200 if status == "ok" else 503
        
        return JsonResponse(response_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)

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