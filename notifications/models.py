from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Any

User = get_user_model()


class Notification(models.Model):
    """Model to store user notifications"""
    
    # Explicitly declare the id field for type checkers
    id: Any
    
    class NotificationType(models.TextChoices):
        INFO = 'info', 'Information'
        WARNING = 'warning', 'Warning'
        SUCCESS = 'success', 'Success'
        ERROR = 'error', 'Error'
        ENROLLMENT = 'enrollment', 'Enrollment'
        REVIEW = 'review', 'Review'
        ASSIGNMENT = 'assignment', 'Assignment'
        COURSE_UPDATE = 'course_update', 'Course Update'
        PAYMENT = 'payment', 'Payment'
        CERTIFICATE = 'certificate', 'Certificate'
        FORUM = 'forum', 'Forum'
        SYSTEM = 'system', 'System'
    
    class Priority(models.IntegerChoices):
        LOW = 1, 'Low'
        NORMAL = 2, 'Normal'
        HIGH = 3, 'High'
        URGENT = 4, 'Urgent'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    priority = models.IntegerField(
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_content_type = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save()


class NotificationPreference(models.Model):
    """Model to store user notification preferences"""
    
    # Explicitly declare the id field for type checkers
    id: Any
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notification preferences
    email_notifications = models.BooleanField(default=True)
    email_course_updates = models.BooleanField(default=True)
    email_assignments = models.BooleanField(default=True)
    email_forum_activity = models.BooleanField(default=True)
    email_payments = models.BooleanField(default=True)
    
    # In-app notification preferences
    in_app_notifications = models.BooleanField(default=True)
    in_app_course_updates = models.BooleanField(default=True)
    in_app_assignments = models.BooleanField(default=True)
    in_app_forum_activity = models.BooleanField(default=True)
    in_app_payments = models.BooleanField(default=True)
    
    # Push notification preferences (for mobile apps)
    push_notifications = models.BooleanField(default=True)
    push_course_updates = models.BooleanField(default=True)
    push_assignments = models.BooleanField(default=True)
    push_forum_activity = models.BooleanField(default=True)
    push_payments = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class EmailTemplate(models.Model):
    """Model to store email templates for notifications"""
    
    # Explicitly declare the id field for type checkers
    id: Any
    
    class TemplateType(models.TextChoices):
        WELCOME = 'welcome', 'Welcome Email'
        COURSE_ENROLLMENT = 'course_enrollment', 'Course Enrollment'
        COURSE_REVIEW = 'course_review', 'Course Review'
        ASSIGNMENT_DUE = 'assignment_due', 'Assignment Due'
        PAYMENT_CONFIRMATION = 'payment_confirmation', 'Payment Confirmation'
        CERTIFICATE_AWARDED = 'certificate_awarded', 'Certificate Awarded'
        FORUM_REPLY = 'forum_reply', 'Forum Reply'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        ACCOUNT_ACTIVATION = 'account_activation', 'Account Activation'
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(
        max_length=50,
        choices=TemplateType.choices,
        unique=True
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name