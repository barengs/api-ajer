from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from datetime import date
from .services import AnalyticsService

User = get_user_model()


@receiver(post_save, sender=User)
def update_platform_metrics_on_user_creation(sender, instance, created, **kwargs):
    """Update platform metrics when a new user is created"""
    if created:
        try:
            # Update platform metrics for today
            AnalyticsService.update_platform_metrics(date.today())
        except Exception:
            # Silently fail to avoid breaking user creation
            pass


@receiver(post_save, sender='courses.Course')  # type: ignore
def update_metrics_on_course_creation(sender, instance, created, **kwargs):
    """Update metrics when a course is created or updated"""
    try:
        # Update platform metrics
        AnalyticsService.update_platform_metrics(date.today())
        
        # Update instructor metrics if instructor exists
        if hasattr(instance, 'instructor') and instance.instructor:
            AnalyticsService.update_instructor_metrics(
                instance.instructor.id, date.today()
            )
    except Exception:
        # Silently fail to avoid breaking course operations
        pass


@receiver(post_save, sender='courses.Enrollment')  # type: ignore
def update_metrics_on_enrollment(sender, instance, created, **kwargs):
    """Update metrics when enrollment occurs"""
    try:
        # Update platform metrics
        AnalyticsService.update_platform_metrics(date.today())
        
        # Update instructor metrics
        if hasattr(instance, 'course') and instance.course and instance.course.instructor:
            AnalyticsService.update_instructor_metrics(
                instance.course.instructor.id, date.today()
            )
        
        # Update student metrics
        if hasattr(instance, 'student') and instance.student:
            # This would be implemented when StudentMetrics service methods are added
            pass
            
    except Exception:
        # Silently fail
        pass


@receiver(post_save, sender='payments.Order')  # type: ignore
def update_metrics_on_order_completion(sender, instance, **kwargs):
    """Update financial metrics when order is completed"""
    if hasattr(instance, 'status') and instance.status == 'completed':
        try:
            # Update platform metrics
            AnalyticsService.update_platform_metrics(date.today())
            
            # Update instructor metrics for all course instructors in the order
            order_items = getattr(instance, 'items', None)
            if order_items:
                for item in order_items.all():
                    if hasattr(item, 'course') and item.course and item.course.instructor:
                        AnalyticsService.update_instructor_metrics(
                            item.course.instructor.id, date.today()
                        )
                        
        except Exception:
            # Silently fail
            pass


@receiver(post_save, sender='lessons.LessonProgress')  # type: ignore
def update_metrics_on_lesson_completion(sender, instance, **kwargs):
    """Update metrics when lesson is completed"""
    if hasattr(instance, 'is_completed') and instance.is_completed:
        try:
            # Update platform metrics
            AnalyticsService.update_platform_metrics(date.today())
            
            # Update instructor metrics
            if (hasattr(instance, 'lesson') and instance.lesson and 
                hasattr(instance.lesson, 'section') and instance.lesson.section and
                hasattr(instance.lesson.section, 'course') and instance.lesson.section.course and
                instance.lesson.section.course.instructor):
                
                AnalyticsService.update_instructor_metrics(
                    instance.lesson.section.course.instructor.id, date.today()
                )
                
        except Exception:
            # Silently fail
            pass


@receiver(post_save, sender='assignments.AssignmentSubmission')  # type: ignore
def update_metrics_on_assignment_submission(sender, instance, created, **kwargs):
    """Update metrics when assignment is submitted"""
    if created:
        try:
            # Update platform metrics
            AnalyticsService.update_platform_metrics(date.today())
            
            # Update instructor metrics
            if (hasattr(instance, 'assignment') and instance.assignment and
                hasattr(instance.assignment, 'course') and instance.assignment.course and
                instance.assignment.course.instructor):
                
                AnalyticsService.update_instructor_metrics(
                    instance.assignment.course.instructor.id, date.today()
                )
                
        except Exception:
            # Silently fail
            pass


@receiver(post_save, sender='forums.ForumPost')  # type: ignore
def update_metrics_on_forum_activity(sender, instance, created, **kwargs):
    """Update metrics when forum post is created"""
    if created:
        try:
            # Update platform metrics
            AnalyticsService.update_platform_metrics(date.today())
                
        except Exception:
            # Silently fail
            pass