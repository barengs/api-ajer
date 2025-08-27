from django.urls import path
from .views import (
    PlatformAnalyticsView, InstructorAnalyticsView, CourseAnalyticsView,
    PlatformMetricsListView, InstructorMetricsListView,
    update_platform_metrics, update_instructor_metrics
)

urlpatterns = [
    # Analytics overview endpoints
    path('platform/', PlatformAnalyticsView.as_view(), name='platform_analytics'),
    path('instructor/', InstructorAnalyticsView.as_view(), name='instructor_analytics'),
    path('course/', CourseAnalyticsView.as_view(), name='course_analytics'),
    
    # Historical metrics endpoints
    path('platform/metrics/', PlatformMetricsListView.as_view(), name='platform_metrics_list'),
    path('instructor/metrics/', InstructorMetricsListView.as_view(), name='instructor_metrics_list'),
    
    # Metrics update endpoints
    path('platform/update/', update_platform_metrics, name='update_platform_metrics'),
    path('instructor/update/', update_instructor_metrics, name='update_instructor_metrics'),
]