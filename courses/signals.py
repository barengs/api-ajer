from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Course, Enrollment, CourseReview

# Optional imports for notifications and gamification
try:
    from notifications.models import Notification  # type: ignore
except ImportError:
    Notification = None

try:
    from gamification.models import UserPoints  # type: ignore
except ImportError:
    UserPoints = None

User = get_user_model()


@receiver(post_save, sender=Enrollment)
def handle_course_enrollment(sender, instance, created, **kwargs):
    """Handle actions when a student enrolls in a course"""
    if created:
        # Create notification for instructor
        if Notification is not None:
            Notification.objects.create(
                user=instance.course.instructor,
                title="New Student Enrollment",
                message=f"{instance.student.full_name} enrolled in your course: {instance.course.title}",
                notification_type="enrollment"
            )
        
        # Award points for enrollment (if gamification is enabled)
        if UserPoints is not None:
            try:
                UserPoints.objects.create(
                    user=instance.student,
                    points=10,
                    reason="Course enrollment",
                    related_course=instance.course
                )
            except:
                pass  # Gamification might not be set up yet


@receiver(post_save, sender=CourseReview)
def handle_course_review(sender, instance, created, **kwargs):
    """Handle actions when a course is reviewed"""
    if created:
        # Notify instructor about new review
        if Notification is not None:
            Notification.objects.create(
                user=instance.course.instructor,
                title="New Course Review",
                message=f"{instance.student.full_name} left a {instance.rating}-star review on {instance.course.title}",
                notification_type="review"
            )
        
        # Award points for reviewing
        if UserPoints is not None:
            try:
                UserPoints.objects.create(
                    user=instance.student,
                    points=5,
                    reason="Course review",
                    related_course=instance.course
                )
            except:
                pass


@receiver(post_save, sender=Course)
def handle_course_creation(sender, instance, created, **kwargs):
    """Handle actions when a new course is created"""
    if created:
        # Award points to instructor for creating course
        if UserPoints is not None:
            try:
                UserPoints.objects.create(
                    user=instance.instructor,
                    points=50,
                    reason="Course creation",
                    related_course=instance
                )
            except:
                pass