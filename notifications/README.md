# Notifications System

## Overview

The notifications system provides a comprehensive solution for managing user notifications in the Hybrid LMS platform. It supports multiple notification types, delivery methods, and user preferences.

## Features

1. **Multiple Notification Types**

   - Info, Warning, Success, Error
   - Enrollment, Review, Assignment
   - Course Updates, Payments, Certificates
   - Forum Activity, System Notifications

2. **Priority Levels**

   - Low (1)
   - Normal (2)
   - High (3)
   - Urgent (4)

3. **Delivery Methods**

   - In-app notifications
   - Email notifications
   - Push notifications (for mobile apps)

4. **User Preferences**

   - Granular control over notification types
   - Separate settings for each delivery method
   - Category-based preferences

5. **Email Templates**
   - Predefined templates for common notification types
   - Customizable subject and body
   - Template-based email formatting

## Models

### Notification

Main notification model storing all user notifications.

Fields:

- `user`: Foreign key to User
- `title`: Notification title
- `message`: Notification message
- `notification_type`: Type of notification
- `priority`: Priority level
- `is_read`: Read status
- `is_archived`: Archive status
- `created_at`: Creation timestamp
- `read_at`: Read timestamp
- `related_object_id`: Related object ID
- `related_content_type`: Related content type

### NotificationPreference

User-specific notification preferences.

Fields:

- `user`: One-to-one with User
- Email notification settings
- In-app notification settings
- Push notification settings

### EmailTemplate

Templates for email notifications.

Fields:

- `name`: Template name
- `template_type`: Template type
- `subject`: Email subject
- `body`: Email body
- `is_active`: Active status

## API Endpoints

### GET `/api/v1/notifications/`

Get user notifications with filtering options.

Parameters:

- `type`: Filter by notification type
- `read`: Filter by read status
- `priority`: Filter by priority level

### GET `/api/v1/notifications/<id>/`

Get notification detail and mark as read.

### POST `/api/v1/notifications/<id>/read/`

Mark notification as read.

### POST `/api/v1/notifications/<id>/unread/`

Mark notification as unread.

### DELETE `/api/v1/notifications/<id>/`

Delete notification.

### POST `/api/v1/notifications/<id>/archive/`

Archive notification.

### POST `/api/v1/notifications/mark-all-read/`

Mark all notifications as read.

### POST `/api/v1/notifications/bulk-read/`

Mark multiple notifications as read.

### GET/PUT `/api/v1/notifications/preferences/`

Get or update notification preferences.

### GET `/api/v1/notifications/stats/`

Get notification statistics.

## Services

### NotificationService

Main service class for notification management.

Methods:

- `create_notification()`: Create a single notification
- `create_bulk_notifications()`: Create notifications for multiple users
- `mark_as_read()`: Mark notification as read
- `mark_multiple_as_read()`: Mark multiple notifications as read
- `get_unread_count()`: Get count of unread notifications

## Usage Examples

### Creating a Notification

```python
from notifications.services import create_notification
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='testuser')

notification = create_notification(
    user=user,
    title='Welcome!',
    message='Welcome to our platform',
    notification_type='info',
    priority=2
)
```

### Creating Bulk Notifications

```python
from notifications.services import create_bulk_notifications
from django.contrib.auth import get_user_model

User = get_user_model()
users = User.objects.filter(is_active=True)

notifications = create_bulk_notifications(
    users=users,
    title='Platform Update',
    message='We have updated our platform',
    notification_type='system',
    priority=3
)
```

### Using in Signals

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.services import create_notification

@receiver(post_save, sender=Course)
def handle_course_creation(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.instructor,
            title='New Course Created',
            message=f'Your course "{instance.title}" has been created',
            notification_type='course_update'
        )
```

## Management Commands

### init_notifications

Initialize default email templates.

```bash
python manage.py init_notifications
```

## Admin Interface

All models are registered in the Django admin interface for easy management:

- Notifications
- Notification Preferences
- Email Templates

## Testing

Run tests with:

```bash
python manage.py test notifications
```
