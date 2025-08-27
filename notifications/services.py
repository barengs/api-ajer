from typing import Optional, List, Dict, Any
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification, NotificationPreference, EmailTemplate

User = get_user_model()


class NotificationService:
    """Service class for handling notifications"""
    
    @staticmethod
    def create_notification(
        user,
        title: str,
        message: str,
        notification_type: str = Notification.NotificationType.INFO,
        priority: int = Notification.Priority.NORMAL,
        related_object_id: Optional[int] = None,
        related_content_type: Optional[str] = None
    ) -> Notification:
        """
        Create a new notification for a user
        
        Args:
            user: User object to send notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            related_object_id: ID of related object
            related_content_type: Content type of related object
            
        Returns:
            Notification: Created notification object
        """
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            related_object_id=related_object_id,
            related_content_type=related_content_type
        )
        
        # Send email notification if enabled
        NotificationService._send_email_notification(notification)
        
        return notification
    
    @staticmethod
    def create_bulk_notifications(
        users: List[User],
        title: str,
        message: str,
        notification_type: str = Notification.NotificationType.INFO,
        priority: int = Notification.Priority.NORMAL
    ) -> List[Notification]:
        """
        Create notifications for multiple users
        
        Args:
            users: List of User objects
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            
        Returns:
            List[Notification]: List of created notification objects
        """
        notifications = []
        for user in users:
            notification = NotificationService.create_notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id: int, user) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: ID of notification to mark as read
            user: User who owns the notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def mark_multiple_as_read(notification_ids: List[int], user) -> int:
        """
        Mark multiple notifications as read
        
        Args:
            notification_ids: List of notification IDs
            user: User who owns the notifications
            
        Returns:
            int: Number of notifications marked as read
        """
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            user=user,
            is_read=False
        )
        
        count = notifications.count()
        notifications.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return count
    
    @staticmethod
    def get_unread_count(user) -> int:
        """
        Get count of unread notifications for a user
        
        Args:
            user: User object
            
        Returns:
            int: Count of unread notifications
        """
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
    
    @staticmethod
    def _send_email_notification(notification: Notification) -> bool:
        """
        Send email notification if user has email notifications enabled
        
        Args:
            notification: Notification object
            
        Returns:
            bool: True if email sent, False otherwise
        """
        try:
            # Get user preferences
            preferences, created = NotificationPreference.objects.get_or_create(
                user=notification.user
            )
            
            # Check if email notifications are enabled
            if not preferences.email_notifications:
                return False
            
            # Check specific notification type preference
            type_preference_map = {
                Notification.NotificationType.ENROLLMENT: preferences.email_course_updates,
                Notification.NotificationType.REVIEW: preferences.email_course_updates,
                Notification.NotificationType.ASSIGNMENT: preferences.email_assignments,
                Notification.NotificationType.COURSE_UPDATE: preferences.email_course_updates,
                Notification.NotificationType.PAYMENT: preferences.email_payments,
                Notification.NotificationType.CERTIFICATE: preferences.email_course_updates,
                Notification.NotificationType.FORUM: preferences.email_forum_activity,
            }
            
            # Check if specific notification type is enabled
            if notification.notification_type in type_preference_map:
                if not type_preference_map[notification.notification_type]:
                    return False
            
            # Get email template
            try:
                template = EmailTemplate.objects.get(
                    template_type=notification.notification_type,
                    is_active=True
                )
                subject = template.subject.format(
                    title=notification.title
                )
                body = template.body.format(
                    message=notification.message,
                    user_name=notification.user.get_full_name() or notification.user.username
                )
            except EmailTemplate.DoesNotExist:
                # Use default email format
                subject = f"Notification: {notification.title}"
                body = f"Hello {notification.user.get_full_name() or notification.user.username},\n\n{notification.message}"
            
            # Send email
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=True
            )
            
            return True
        except Exception as e:
            # Log error but don't fail the notification creation
            print(f"Error sending email notification: {e}")
            return False


# Convenience functions
def create_notification(*args, **kwargs) -> Notification:
    """Convenience function to create a notification"""
    return NotificationService.create_notification(*args, **kwargs)


def create_bulk_notifications(*args, **kwargs) -> List[Notification]:
    """Convenience function to create bulk notifications"""
    return NotificationService.create_bulk_notifications(*args, **kwargs)


def mark_as_read(*args, **kwargs) -> bool:
    """Convenience function to mark notification as read"""
    return NotificationService.mark_as_read(*args, **kwargs)


def mark_multiple_as_read(*args, **kwargs) -> int:
    """Convenience function to mark multiple notifications as read"""
    return NotificationService.mark_multiple_as_read(*args, **kwargs)


def get_unread_count(*args, **kwargs) -> int:
    """Convenience function to get unread notification count"""
    return NotificationService.get_unread_count(*args, **kwargs)