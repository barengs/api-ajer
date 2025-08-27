from rest_framework import status
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from django.db.models import Q, QuerySet
from django.utils import timezone
from datetime import date, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from typing import Union, Any

from .models import PlatformMetrics, InstructorMetrics, CourseMetrics, StudentMetrics
from .serializers import (
    PlatformMetricsSerializer, InstructorMetricsSerializer, 
    CourseMetricsSerializer, StudentMetricsSerializer,
    PlatformAnalyticsSerializer, InstructorAnalyticsSerializer
)
from .services import AnalyticsService


class PlatformAnalyticsView(APIView):
    """Platform-wide analytics view (Admin only)"""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Analytics'],
        summary='Get Platform Analytics',
        description='''
        Mendapatkan analytics lengkap untuk platform (Admin only).
        
        **Metrics Platform:**
        - Total users, courses, instructors
        - Revenue metrics dan growth rate
        - User engagement dan activity metrics
        - Popular courses dan top instructors
        - Daily metrics untuk visualisasi chart
        
        **Parameters:**
        - days: Jumlah hari untuk analisis (default: 30)
        ''',
        parameters=[
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of days for analysis (default: 30)'
            )
        ],
        responses={
            200: PlatformAnalyticsSerializer,
            403: {'description': 'Forbidden - Admin access required'}
        }
    )
    def get(self, request):
        """Get comprehensive platform analytics"""
        # Check admin permission
        if not hasattr(request.user, 'role') or request.user.role != 'admin':  # type: ignore
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        
        try:
            analytics_data = AnalyticsService.get_platform_analytics(days=days)
            return Response(analytics_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Error generating analytics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InstructorAnalyticsView(APIView):
    """Instructor analytics view"""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Analytics'],
        summary='Get Instructor Analytics',
        description='''
        Mendapatkan analytics untuk instructor.
        
        **Metrics Instructor:**
        - Total students, courses, earnings
        - Performance metrics (rating, completion rate)
        - Course performance dan student insights
        - Growth metrics dan daily analytics
        
        **Access:**
        - Instructor: Hanya bisa akses analytics sendiri
        - Admin: Bisa akses analytics instructor manapun
        ''',
        parameters=[
            OpenApiParameter(
                name='instructor_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Instructor ID (Admin only, optional for instructor)'
            ),
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of days for analysis (default: 30)'
            )
        ],
        responses={
            200: InstructorAnalyticsSerializer,
            403: {'description': 'Forbidden - Instructor or Admin access required'}
        }
    )
    def get(self, request):
        """Get instructor analytics"""
        user = request.user
        
        # Determine instructor ID
        instructor_id = request.query_params.get('instructor_id')
        
        if hasattr(user, 'role') and user.role == 'admin':  # type: ignore
            # Admin can view any instructor's analytics
            if not instructor_id:
                return Response(
                    {'error': 'instructor_id parameter required for admin'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            instructor_id = int(instructor_id)
        elif hasattr(user, 'role') and user.role == 'instructor':  # type: ignore
            # Instructor can only view their own analytics
            instructor_id = user.id
        else:
            return Response(
                {'error': 'Instructor or Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        
        try:
            analytics_data = AnalyticsService.get_instructor_analytics(
                instructor_id=instructor_id, 
                days=days
            )
            
            if not analytics_data:
                return Response(
                    {'error': 'Instructor not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(analytics_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Error generating analytics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CourseAnalyticsView(APIView):
    """Course analytics view"""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Analytics'],
        summary='Get Course Analytics',
        description='''
        Mendapatkan analytics untuk course tertentu.
        
        **Metrics Course:**
        - Enrollment dan completion metrics
        - Student engagement dan progress
        - Revenue dan performance data
        
        **Access:**
        - Instructor: Hanya course milik sendiri
        - Admin: Semua course
        ''',
        parameters=[
            OpenApiParameter(
                name='course_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Course ID'
            ),
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of days for analysis (default: 30)'
            )
        ],
        responses={
            200: CourseMetricsSerializer,
            403: {'description': 'Forbidden - Access denied'},
            404: {'description': 'Course not found'}
        }
    )
    def get(self, request):
        """Get course analytics"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': 'course_id parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        days = int(request.query_params.get('days', 30))
        
        # Check permissions
        from courses.models import Course  # type: ignore
        
        try:
            course = Course.objects.get(id=course_id)
            
            user = request.user
            if hasattr(user, 'role'):  # type: ignore
                if user.role == 'instructor' and course.instructor != user:  # type: ignore
                    return Response(
                        {'error': 'Access denied - Not your course'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                elif user.role not in ['instructor', 'admin']:  # type: ignore
                    return Response(
                        {'error': 'Instructor or Admin access required'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            analytics_data = AnalyticsService.get_course_analytics(
                course_id=int(course_id), 
                days=days
            )
            return Response(analytics_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Error generating analytics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlatformMetricsListView(ListAPIView):
    """List platform metrics with filtering"""
    
    queryset = PlatformMetrics.objects.all()
    serializer_class = PlatformMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Analytics'],
        summary='List Platform Metrics',
        description='Get historical platform metrics with date filtering (Admin only)',
        parameters=[
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Start date (YYYY-MM-DD)'
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='End date (YYYY-MM-DD)'
            )
        ]
    )
    def get_queryset(self) -> Any:
        """Filter platform metrics by date range"""
        # Check admin permission
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'admin':  # type: ignore
            return PlatformMetrics.objects.none()
        
        queryset = PlatformMetrics.objects.all()
        
        request: Request = self.request  # type: ignore
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')


class InstructorMetricsListView(ListAPIView):
    """List instructor metrics with filtering"""
    
    queryset = InstructorMetrics.objects.all()
    serializer_class = InstructorMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Analytics'],
        summary='List Instructor Metrics',
        description='Get historical instructor metrics with filtering',
        parameters=[
            OpenApiParameter(
                name='instructor_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by instructor ID (Admin only)'
            ),
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Start date (YYYY-MM-DD)'
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='End date (YYYY-MM-DD)'
            )
        ]
    )
    def get_queryset(self) -> Any:
        """Filter instructor metrics"""
        request: Request = self.request  # type: ignore
        user = request.user
        
        if hasattr(user, 'role') and user.role == 'admin':  # type: ignore
            # Admin can view all instructor metrics
            queryset = InstructorMetrics.objects.all()
            
            instructor_id = request.query_params.get('instructor_id')
            if instructor_id:
                queryset = queryset.filter(instructor_id=instructor_id)
                
        elif hasattr(user, 'role') and user.role == 'instructor':  # type: ignore
            # Instructor can only view their own metrics
            queryset = InstructorMetrics.objects.filter(instructor=user)
        else:
            return InstructorMetrics.objects.none()
        
        # Date filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')


@extend_schema(
    tags=['Analytics'],
    summary='Update Platform Metrics',
    description='''
    Update atau generate platform metrics untuk tanggal tertentu (Admin only).
    
    **Process:**
    - Kalkulasi ulang semua metrics untuk tanggal yang ditentukan
    - Update database dengan data terbaru
    - Return metrics yang sudah diupdate
    ''',
    parameters=[
        OpenApiParameter(
            name='date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Target date (YYYY-MM-DD, default: today)'
        )
    ],
    responses={
        200: PlatformMetricsSerializer,
        403: {'description': 'Forbidden - Admin access required'}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_platform_metrics(request):
    """Update platform metrics for a specific date"""
    # Check admin permission
    if not hasattr(request.user, 'role') or request.user.role != 'admin':  # type: ignore
        return Response(
            {'error': 'Admin access required'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    target_date = request.query_params.get('date')
    if target_date:
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        target_date = date.today()
    
    try:
        metrics = AnalyticsService.update_platform_metrics(target_date)
        serializer = PlatformMetricsSerializer(metrics)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Error updating metrics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Analytics'],
    summary='Update Instructor Metrics',
    description='''
    Update instructor metrics untuk instructor dan tanggal tertentu.
    
    **Access:**
    - Instructor: Hanya bisa update metrics sendiri
    - Admin: Bisa update metrics instructor manapun
    ''',
    parameters=[
        OpenApiParameter(
            name='instructor_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Instructor ID (required for admin, optional for instructor)'
        ),
        OpenApiParameter(
            name='date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Target date (YYYY-MM-DD, default: today)'
        )
    ],
    responses={
        200: InstructorMetricsSerializer,
        403: {'description': 'Forbidden - Access denied'},
        404: {'description': 'Instructor not found'}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_instructor_metrics(request):
    """Update instructor metrics for a specific date"""
    user = request.user
    
    # Determine instructor ID
    instructor_id = request.query_params.get('instructor_id')
    
    if hasattr(user, 'role') and user.role == 'admin':  # type: ignore
        if not instructor_id:
            return Response(
                {'error': 'instructor_id parameter required for admin'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        instructor_id = int(instructor_id)
    elif hasattr(user, 'role') and user.role == 'instructor':  # type: ignore
        instructor_id = user.id
    else:
        return Response(
            {'error': 'Instructor or Admin access required'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    target_date = request.query_params.get('date')
    if target_date:
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        target_date = date.today()
    
    try:
        metrics = AnalyticsService.update_instructor_metrics(instructor_id, target_date)
        if not metrics:
            return Response(
                {'error': 'Instructor not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = InstructorMetricsSerializer(metrics)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Error updating metrics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )