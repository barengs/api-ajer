from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional

from .models import PlatformMetrics, InstructorMetrics, CourseMetrics, StudentMetrics

# Import models that are used in the service methods for proper mocking in tests
from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment
from payments.models import Order, Payment
from lessons.models import LessonProgress
from assignments.models import AssignmentSubmission

User = get_user_model()


def serialize_user(user):
    """Serialize User object for JSON response"""
    if user is None:
        return None
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': getattr(user, 'first_name', ''),
        'last_name': getattr(user, 'last_name', ''),
        'role': getattr(user, 'role', ''),
    }


def serialize_course(course):
    """Serialize Course object for JSON response"""
    if course is None:
        return None
    return {
        'id': course.id,
        'title': course.title,
        'slug': course.slug,
        'instructor_id': course.instructor_id if hasattr(course, 'instructor_id') else None,
        'enrollment_count': getattr(course, 'enrollment_count', 0) if hasattr(course, 'enrollment_count') else 0,
        'avg_rating': float(getattr(course, 'avg_rating', 0)) if hasattr(course, 'avg_rating') else 0,
    }


def serialize_platform_metrics(metrics):
    """Serialize PlatformMetrics object for JSON response"""
    if metrics is None:
        return None
    return {
        'id': metrics.id,
        'date': metrics.date.isoformat() if metrics.date else None,
        'total_users': metrics.total_users,
        'new_users': metrics.new_users,
        'total_courses': metrics.total_courses,
        'new_courses': metrics.new_courses,
        'published_courses': metrics.published_courses,
        'total_revenue': float(metrics.total_revenue),
        'daily_revenue': float(metrics.daily_revenue),
        'total_enrollments': metrics.total_enrollments,
        'new_enrollments': metrics.new_enrollments,
        'completed_courses': metrics.completed_courses,
        'forum_posts': metrics.forum_posts,
        'lesson_completions': metrics.lesson_completions,
        'assignment_submissions': metrics.assignment_submissions,
    }


def serialize_instructor_metrics(metrics):
    """Serialize InstructorMetrics object for JSON response"""
    if metrics is None:
        return None
    return {
        'id': metrics.id,
        'date': metrics.date.isoformat() if metrics.date else None,
        'total_courses': metrics.total_courses,
        'published_courses': metrics.published_courses,
        'draft_courses': metrics.draft_courses,
        'total_students': metrics.total_students,
        'new_students': metrics.new_students,
        'active_students': metrics.active_students,
        'total_earnings': float(metrics.total_earnings),
        'daily_earnings': float(metrics.daily_earnings),
        'average_rating': float(metrics.average_rating),
        'total_reviews': metrics.total_reviews,
        'completion_rate': float(metrics.completion_rate),
        'forum_interactions': metrics.forum_interactions,
        'student_questions': metrics.student_questions,
        'response_time_hours': float(metrics.response_time_hours),
    }


class AnalyticsService:
    """Service class for analytics calculations and data aggregation"""
    
    @staticmethod
    def get_platform_analytics(days: int = 30) -> Dict[str, Any]:
        """Get comprehensive platform analytics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Basic counts
        total_users = User.objects.count()
        total_courses = Course.objects.count()
        total_instructors = User.objects.filter(role='instructor').count()  # type: ignore
        
        # Revenue calculations
        completed_orders = Order.objects.filter(status='completed')
        total_revenue = completed_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Growth calculations
        previous_period_start = start_date - timedelta(days=days)
        previous_users = User.objects.filter(
            date_joined__lt=start_date
        ).count()
        
        user_growth_rate = 0.0
        if previous_users > 0:
            user_growth_rate = ((total_users - previous_users) / previous_users) * 100
        
        # Engagement metrics
        recent_enrollments = Enrollment.objects.filter(
            enrolled_at__gte=start_date
        )
        active_users = recent_enrollments.values('student').distinct().count()
        active_users_percentage = (active_users / total_users * 100) if total_users > 0 else 0
        
        # Course completion rate
        completed_enrollments = recent_enrollments.filter(status='completed').count()
        total_enrollments = recent_enrollments.count()
        completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
        
        # Popular courses
        popular_courses = Course.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:5]
        
        # Top instructors
        top_instructors = User.objects.filter(
            role='instructor'
        ).annotate(
            total_students=Count('created_courses__enrollments'),
            avg_rating=Avg('created_courses__reviews__rating')
        ).order_by('-total_students')[:5]
        
        # Daily metrics for charts
        daily_metrics = PlatformMetrics.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        return {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_instructors': total_instructors,
            'total_revenue': float(total_revenue),
            'user_growth_rate': round(user_growth_rate, 2),
            'course_growth_rate': 0.0,  # To be calculated
            'revenue_growth_rate': 0.0,  # To be calculated
            'active_users_percentage': round(active_users_percentage, 2),
            'course_completion_rate': round(completion_rate, 2),
            'average_session_duration': 0.0,  # To be implemented with session tracking
            'popular_courses': [serialize_course(course) for course in popular_courses],
            'top_instructors': [serialize_user(instructor) for instructor in top_instructors],
            'daily_metrics': [serialize_platform_metrics(metric) for metric in daily_metrics],
            'revenue_breakdown': {
                'course_sales': float(total_revenue),
                'refunds': 0.0,  # To be calculated
                'net_revenue': float(total_revenue)
            },
            'refund_rate': 0.0
        }
    
    @staticmethod
    def get_instructor_analytics(instructor_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive instructor analytics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        try:
            instructor = User.objects.get(id=instructor_id, role='instructor')  # type: ignore
        except User.DoesNotExist:
            return {}
        
        # Instructor's courses
        instructor_courses = Course.objects.filter(instructor=instructor)
        
        # Student metrics
        enrollments = Enrollment.objects.filter(course__in=instructor_courses)
        total_students = enrollments.values('student').distinct().count()
        recent_enrollments = enrollments.filter(enrolled_at__gte=start_date)
        
        # Earnings - check if InstructorRevenue model exists
        total_earnings = Decimal('0.00')
        try:
            # Try to import and use InstructorRevenue if it exists
            from payments.models import InstructorRevenue  # type: ignore
            revenues = InstructorRevenue.objects.filter(instructor=instructor)
            total_earnings = revenues.aggregate(
                total=Sum('instructor_amount')
            )['total'] or Decimal('0.00')
        except (ImportError, AttributeError):
            # Handle case where InstructorRevenue model doesn't exist
            # Fall back to calculating from completed orders
            from payments.models import Order  # type: ignore
            completed_orders = Order.objects.filter(
                items__course__in=instructor_courses,
                status='completed'
            ).distinct()
            # This is a simplified calculation - in reality, you'd need to calculate
            # the instructor's share based on your revenue sharing model
            total_earnings = completed_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
        
        # Performance metrics
        avg_rating = instructor_courses.aggregate(
            avg=Avg('reviews__rating')
        )['avg'] or Decimal('0.00')
        
        completed_enrollments = enrollments.filter(status='completed').count()
        completion_rate = (completed_enrollments / enrollments.count() * 100) if enrollments.count() > 0 else 0
        
        # Best performing courses
        best_courses = instructor_courses.annotate(
            enrollment_count=Count('enrollments'),
            avg_rating=Avg('reviews__rating')
        ).order_by('-enrollment_count')[:5]
        
        # Growth calculations
        previous_period_start = start_date - timedelta(days=days)
        previous_students = enrollments.filter(
            enrolled_at__lt=start_date
        ).values('student').distinct().count()
        
        student_growth_rate = 0.0
        if previous_students > 0:
            student_growth_rate = ((total_students - previous_students) / previous_students) * 100
        
        # Daily metrics
        daily_metrics = InstructorMetrics.objects.filter(
            instructor=instructor,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        return {
            'instructor': serialize_user(instructor),
            'total_students': total_students,
            'total_courses': instructor_courses.count(),
            'total_earnings': float(total_earnings),
            'average_rating': float(avg_rating),
            'student_growth_rate': round(student_growth_rate, 2),
            'earnings_growth_rate': 0.0,  # To be calculated
            'completion_rate': round(completion_rate, 2),
            'engagement_score': 0.0,  # To be calculated
            'response_time': 0.0,  # To be implemented
            'best_performing_courses': [serialize_course(course) for course in best_courses],
            'recent_enrollments': {
                'this_week': recent_enrollments.filter(
                    enrolled_at__gte=end_date - timedelta(days=7)
                ).count(),
                'this_month': recent_enrollments.count()
            },
            'student_demographics': {},  # To be implemented
            'student_feedback': {},  # To be implemented
            'daily_metrics': [serialize_instructor_metrics(metric) for metric in daily_metrics]
        }
    
    @staticmethod
    def get_course_analytics(course_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive course analytics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return {}
        
        # Enrollment metrics
        enrollments = Enrollment.objects.filter(course=course)
        recent_enrollments = enrollments.filter(enrolled_at__gte=start_date)
        
        # Progress metrics
        lesson_progress = LessonProgress.objects.filter(
            lesson__section__course=course
        )
        avg_progress = lesson_progress.aggregate(
            avg=Avg('completion_percentage')
        )['avg'] or Decimal('0.00')
        
        # Completion metrics
        completed_enrollments = enrollments.filter(status='completed').count()
        completion_rate = (completed_enrollments / enrollments.count() * 100) if enrollments.count() > 0 else 0
        
        # Assignment metrics
        assignments = course.assignments.all()  # type: ignore
        assignment_submissions = AssignmentSubmission.objects.filter(
            assignment__in=assignments
        )
        
        return {
            'course': serialize_course(course),
            'total_enrollments': enrollments.count(),
            'new_enrollments': recent_enrollments.count(),
            'completion_rate': round(completion_rate, 2),
            'average_progress': float(avg_progress),
            'assignment_submissions': assignment_submissions.count(),
            'active_students': recent_enrollments.values('student').distinct().count()
        }
    
    @staticmethod
    def update_platform_metrics(target_date: Optional[date] = None) -> PlatformMetrics:
        """Update or create platform metrics for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        from django.contrib.auth import get_user_model
        from courses.models import Course, Enrollment  # type: ignore
        from payments.models import Order  # type: ignore
        from forums.models import ForumPost  # type: ignore
        from lessons.models import LessonProgress  # type: ignore
        from assignments.models import AssignmentSubmission  # type: ignore
        
        User = get_user_model()
        
        # Get or create metrics for the date
        metrics, created = PlatformMetrics.objects.get_or_create(
            date=target_date,
            defaults={}
        )
        
        # User metrics
        metrics.total_users = User.objects.filter(
            date_joined__lte=target_date
        ).count()
        
        metrics.new_users = User.objects.filter(
            date_joined__date=target_date
        ).count()
        
        # Course metrics
        metrics.total_courses = Course.objects.filter(
            created_at__lte=target_date
        ).count()
        
        metrics.new_courses = Course.objects.filter(
            created_at__date=target_date
        ).count()
        
        metrics.published_courses = Course.objects.filter(
            is_published=True,
            published_at__lte=target_date
        ).count()
        
        # Financial metrics
        completed_orders = Order.objects.filter(  # type: ignore
            status='completed',
            completed_at__lte=target_date
        )
        
        metrics.total_revenue = completed_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        daily_orders = completed_orders.filter(completed_at__date=target_date)
        metrics.daily_revenue = daily_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Enrollment metrics
        metrics.total_enrollments = Enrollment.objects.filter(  # type: ignore
            enrolled_at__lte=target_date
        ).count()
        
        metrics.new_enrollments = Enrollment.objects.filter(  # type: ignore
            enrolled_at__date=target_date
        ).count()
        
        metrics.completed_courses = Enrollment.objects.filter(  # type: ignore
            status='completed',
            completed_at__date=target_date
        ).count()
        
        # Engagement metrics
        metrics.forum_posts = ForumPost.objects.filter(  # type: ignore
            created_at__date=target_date
        ).count()
        
        metrics.lesson_completions = LessonProgress.objects.filter(  # type: ignore
            completed_at__date=target_date,
            is_completed=True
        ).count()
        
        metrics.assignment_submissions = AssignmentSubmission.objects.filter(  # type: ignore
            submitted_at__date=target_date
        ).count()
        
        metrics.save()
        return metrics
    
    @staticmethod
    def update_instructor_metrics(instructor_id: int, target_date: Optional[date] = None) -> Optional[InstructorMetrics]:
        """Update or create instructor metrics for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        from django.contrib.auth import get_user_model
        from courses.models import Course, Enrollment  # type: ignore
        from payments.models import Revenue  # type: ignore
        
        User = get_user_model()
        
        try:
            instructor = User.objects.get(id=instructor_id, role='instructor')  # type: ignore
        except User.DoesNotExist:
            return None
        
        # Get or create metrics for the instructor and date
        metrics, created = InstructorMetrics.objects.get_or_create(
            instructor=instructor,
            date=target_date,
            defaults={}
        )
        
        # Course metrics
        instructor_courses = Course.objects.filter(instructor=instructor)
        metrics.total_courses = instructor_courses.filter(
            created_at__lte=target_date
        ).count()
        
        metrics.published_courses = instructor_courses.filter(
            is_published=True,
            published_at__lte=target_date
        ).count()
        
        metrics.draft_courses = instructor_courses.filter(
            status='draft'
        ).count()
        
        # Student metrics
        enrollments = Enrollment.objects.filter(  # type: ignore
            course__in=instructor_courses,
            enrolled_at__lte=target_date
        )
        
        metrics.total_students = enrollments.values('student').distinct().count()
        metrics.new_students = enrollments.filter(
            enrolled_at__date=target_date
        ).values('student').distinct().count()
        
        # Earnings
        revenues = Revenue.objects.filter(  # type: ignore
            instructor=instructor,
            created_at__lte=target_date
        )
        
        metrics.total_earnings = revenues.aggregate(
            total=Sum('instructor_earnings')
        )['total'] or Decimal('0.00')
        
        daily_revenues = revenues.filter(created_at__date=target_date)
        metrics.daily_earnings = daily_revenues.aggregate(
            total=Sum('instructor_earnings')
        )['total'] or Decimal('0.00')
        
        # Performance metrics
        metrics.average_rating = instructor_courses.aggregate(
            avg=Avg('reviews__rating')
        )['avg'] or Decimal('0.00')
        
        metrics.total_reviews = instructor_courses.aggregate(
            count=Count('reviews')
        )['count'] or 0
        
        completed_enrollments = enrollments.filter(status='completed').count()
        total_enrollments = enrollments.count()
        metrics.completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else Decimal('0.00')
        
        metrics.save()
        return metrics