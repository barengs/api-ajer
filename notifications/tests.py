from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification, NotificationPreference, EmailTemplate
from .services import NotificationService
from typing import Any

# Get the User model
User: Any = get_user_model()


class NotificationModelTest(TestCase):
    """Test cases for Notification model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type=Notification.NotificationType.INFO
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_archived)
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_mark_as_unread(self):
        """Test marking notification as unread"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification'
        )
        
        # Mark as read first
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        
        # Then mark as unread
        notification.mark_as_unread()
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)


class NotificationPreferenceModelTest(TestCase):
    """Test cases for NotificationPreference model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_notification_preference(self):
        """Test creating notification preferences"""
        preference = NotificationPreference.objects.create(
            user=self.user
        )
        
        self.assertEqual(preference.user, self.user)
        self.assertTrue(preference.email_notifications)
        self.assertTrue(preference.in_app_notifications)
        self.assertTrue(preference.push_notifications)


class EmailTemplateModelTest(TestCase):
    """Test cases for EmailTemplate model"""
    
    def test_create_email_template(self):
        """Test creating an email template"""
        template = EmailTemplate.objects.create(
            name='Welcome Email',
            template_type=EmailTemplate.TemplateType.WELCOME,
            subject='Welcome!',
            body='Welcome to our platform!'
        )
        
        self.assertEqual(template.name, 'Welcome Email')
        self.assertEqual(template.template_type, EmailTemplate.TemplateType.WELCOME)
        self.assertEqual(template.subject, 'Welcome!')
        self.assertEqual(template.body, 'Welcome to our platform!')
        self.assertTrue(template.is_active)


class NotificationServiceTest(TestCase):
    """Test cases for NotificationService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_notification(self):
        """Test creating notification through service"""
        notification = NotificationService.create_notification(
            user=self.user,
            title='Service Test',
            message='Test message from service'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Service Test')
        self.assertEqual(notification.message, 'Test message from service')
    
    def test_get_unread_count(self):
        """Test getting unread notification count"""
        # Create some notifications
        Notification.objects.create(
            user=self.user,
            title='Unread 1',
            message='Unread message 1'
        )
        Notification.objects.create(
            user=self.user,
            title='Unread 2',
            message='Unread message 2'
        )
        read_notification = Notification.objects.create(
            user=self.user,
            title='Read',
            message='Read message'
        )
        read_notification.mark_as_read()
        
        unread_count = NotificationService.get_unread_count(self.user)
        self.assertEqual(unread_count, 2)


class NotificationAPITest(TestCase):
    """Test cases for Notification API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_get_notification_list(self):
        """Test getting notification list"""
        # Create some notifications
        Notification.objects.create(
            user=self.user,
            title='Test 1',
            message='Test message 1'
        )
        Notification.objects.create(
            user=self.user,
            title='Test 2',
            message='Test message 2'
        )
        
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['notifications']), 2)
        self.assertEqual(response_data['unread_count'], 2)
    
    def test_mark_notification_read(self):
        """Test marking notification as read via API"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test message'
        )
        
        # Get the ID explicitly to satisfy type checker
        notification_id = notification.pk
        response = self.client.post(f'/api/v1/notifications/{notification_id}/read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
    
    def test_get_notification_preferences(self):
        """Test getting notification preferences"""
        response = self.client.get('/api/v1/notifications/preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that default preferences are returned
        response_data = response.json()
        self.assertTrue(response_data['email_notifications'])
        self.assertTrue(response_data['in_app_notifications'])