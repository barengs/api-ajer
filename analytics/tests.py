from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock
from typing import Any

from .models import PlatformMetrics, InstructorMetrics, CourseMetrics, StudentMetrics
from .services import AnalyticsService
from courses.models import Course  # Import Course model properly

User = get_user_model()


class AnalyticsModelsTest(TestCase):
    """Test analytics models"""
    
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.instructor = User.objects.create_user(  # type: ignore[attr-defined]
            username='instructor',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'  # type: ignore
        )
        
        self.admin = User.objects.create_user(  # type: ignore[attr-defined]
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'  # type: ignore
        )
    
    def test_platform_metrics_creation(self):
        """Test platform metrics model creation"""
        # Use get_or_create to avoid UNIQUE constraint issues in tests
        metrics, created = PlatformMetrics.objects.get_or_create(
            date=date.today(),
            defaults={
                'total_users': 100,
                'total_courses': 50,
                'total_revenue': Decimal('1000.00')
            }
        )
        
        self.assertEqual(metrics.total_users, 100)
        self.assertEqual(metrics.total_courses, 50)
        self.assertEqual(metrics.total_revenue, Decimal('1000.00'))
        self.assertEqual(str(metrics), f"Platform metrics for {date.today()}")
    
    def test_instructor_metrics_creation(self):
        """Test instructor metrics model creation"""
        metrics = InstructorMetrics.objects.create(
            instructor=self.instructor,
            date=date.today(),
            total_courses=5,
            total_students=25,
            total_earnings=Decimal('500.00')
        )
        
        self.assertEqual(metrics.instructor, self.instructor)
        self.assertEqual(metrics.total_courses, 5)
        self.assertEqual(metrics.total_students, 25)
        self.assertEqual(metrics.total_earnings, Decimal('500.00'))
    
    def test_student_metrics_creation(self):
        """Test student metrics model creation"""
        metrics = StudentMetrics.objects.create(
            student=self.user,
            date=date.today(),
            courses_enrolled=3,
            courses_completed=1,
            total_points=150
        )
        
        self.assertEqual(metrics.student, self.user)
        self.assertEqual(metrics.courses_enrolled, 3)
        self.assertEqual(metrics.courses_completed, 1)
        self.assertEqual(metrics.total_points, 150)


class AnalyticsServiceTest(TestCase):
    """Test analytics service functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.instructor = User.objects.create_user(  # type: ignore[attr-defined]
            username='instructor',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'  # type: ignore
        )
    
    @patch('analytics.services.Course')
    @patch('analytics.services.Order')
    def test_get_platform_analytics(self, mock_order, mock_course):
        """Test platform analytics retrieval"""
        # Mock course count
        mock_course.objects.count.return_value = 10
        
        # Mock order aggregation
        mock_order.objects.filter.return_value.aggregate.return_value = {
            'total': Decimal('1000.00')
        }
        
        analytics = AnalyticsService.get_platform_analytics(days=30)
        
        self.assertIn('total_users', analytics)
        self.assertIn('total_courses', analytics)
        self.assertIn('total_revenue', analytics)
        self.assertEqual(analytics['total_courses'], 10)
    
    def test_update_platform_metrics(self):
        """Test platform metrics update"""
        target_date = date.today()
        
        # Create metrics
        metrics = AnalyticsService.update_platform_metrics(target_date)
        
        self.assertIsInstance(metrics, PlatformMetrics)
        self.assertEqual(metrics.date, target_date)
        
        # Test update existing metrics
        metrics2 = AnalyticsService.update_platform_metrics(target_date)
        self.assertEqual(metrics.id, metrics2.id)  # Should update same record  # type: ignore[attr-defined]
    
    def test_update_instructor_metrics(self):
        """Test instructor metrics update"""
        target_date = date.today()
        
        # Test with valid instructor
        metrics = AnalyticsService.update_instructor_metrics(
            self.instructor.id, target_date
        )
        
        self.assertIsInstance(metrics, InstructorMetrics)
        self.assertEqual(metrics.instructor, self.instructor)  # type: ignore[attr-defined]
        self.assertEqual(metrics.date, target_date)  # type: ignore[attr-defined]
        
        # Test with invalid instructor
        result = AnalyticsService.update_instructor_metrics(9999, target_date)
        self.assertIsNone(result)


class AnalyticsAPITest(APITestCase):
    """Test analytics API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.student = User.objects.create_user(  # type: ignore[attr-defined]
            username='student',
            email='student@example.com',
            password='testpass123',
            role='student'  # type: ignore
        )
        
        self.instructor = User.objects.create_user(  # type: ignore[attr-defined]
            username='instructor',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'  # type: ignore
        )
        
        self.admin = User.objects.create_user(  # type: ignore[attr-defined]
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'  # type: ignore
        )
    
    def test_platform_analytics_admin_required(self):
        """Test platform analytics requires admin access"""
        url = reverse('platform_analytics')
        
        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test student access
        self.client.force_authenticate(user=self.student)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test instructor access
        self.client.force_authenticate(user=self.instructor)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test admin access
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_instructor_analytics_access_control(self):
        """Test instructor analytics access control"""
        url = reverse('instructor_analytics')
        
        # Test instructor can access their own analytics
        self.client.force_authenticate(user=self.instructor)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test admin can access with instructor_id parameter
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]
        response = self.client.get(url, {'instructor_id': self.instructor.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test admin needs instructor_id parameter
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test student cannot access
        self.client.force_authenticate(user=self.student)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('courses.models.Course')
    def test_course_analytics_access_control(self, mock_course):
        """Test course analytics access control"""
        # Mock course
        mock_course_instance = Mock()
        mock_course_instance.instructor = self.instructor
        mock_course.objects.get.return_value = mock_course_instance
        
        url = reverse('course_analytics')
        
        # Test requires course_id parameter
        self.client.force_authenticate(user=self.instructor)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test instructor can access their own course
        response = self.client.get(url, {'course_id': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test admin can access any course
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]
        response = self.client.get(url, {'course_id': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_platform_metrics_list_admin_only(self):
        """Test platform metrics list endpoint"""
        url = reverse('platform_metrics_list')
        
        # Create test metrics using get_or_create to avoid UNIQUE constraint issues
        metrics, created = PlatformMetrics.objects.get_or_create(
            date=date.today(),
            defaults={
                'total_users': 100,
                'total_courses': 50
            }
        )
        
        # Test admin access
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # type: ignore[attr-defined]
        
        # Test non-admin access returns empty
        self.client.force_authenticate(user=self.instructor)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # type: ignore[attr-defined]
    
    def test_instructor_metrics_list_filtering(self):
        """Test instructor metrics list with filtering"""
        url = reverse('instructor_metrics_list')
        
        # Create test metrics
        InstructorMetrics.objects.create(
            instructor=self.instructor,
            date=date.today(),
            total_courses=5
        )
        
        # Test instructor can see their own metrics
        self.client.force_authenticate(user=self.instructor)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # type: ignore[attr-defined]
        
        # Test admin can see all metrics
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test admin can filter by instructor
        response = self.client.get(url, {'instructor_id': self.instructor.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # type: ignore[attr-defined]
    
    def test_update_platform_metrics_admin_only(self):
        """Test update platform metrics endpoint"""
        url = reverse('update_platform_metrics')
        
        # Test admin access
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('date', response.data)  # type: ignore[attr-defined]
        
        # Test with specific date
        response = self.client.post(url, {'date': '2024-01-01'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test invalid date format
        response = self.client.post(url, {'date': 'invalid-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test non-admin access
        self.client.force_authenticate(user=self.instructor)  # type: ignore[attr-defined]
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_instructor_metrics_access_control(self):
        """Test update instructor metrics access control"""
        url = reverse('update_instructor_metrics')
        
        # Test instructor can update their own metrics
        self.client.force_authenticate(user=self.instructor)  # type: ignore[attr-defined]
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test admin can update any instructor's metrics
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]
        response = self.client.post(url, {'instructor_id': self.instructor.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test admin needs instructor_id parameter
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test student cannot access
        self.client.force_authenticate(user=self.student)  # type: ignore[attr-defined]
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AnalyticsIntegrationTest(TestCase):
    """Integration tests for analytics functionality"""
    
    def setUp(self):
        self.instructor = User.objects.create_user(  # type: ignore[attr-defined]
            username='instructor',
            email='instructor@example.com',
            password='testpass123',
            role='instructor'  # type: ignore
        )
    
    def test_complete_analytics_workflow(self):
        """Test complete analytics generation workflow"""
        target_date = date.today()
        
        # Generate platform metrics
        platform_metrics = AnalyticsService.update_platform_metrics(target_date)
        self.assertIsInstance(platform_metrics, PlatformMetrics)
        
        # Generate instructor metrics
        instructor_metrics = AnalyticsService.update_instructor_metrics(
            self.instructor.id, target_date
        )
        self.assertIsInstance(instructor_metrics, InstructorMetrics)
        
        # Verify metrics are linked properly
        self.assertEqual(instructor_metrics.instructor, self.instructor)  # type: ignore[attr-defined]
        self.assertEqual(instructor_metrics.date, target_date)  # type: ignore[attr-defined]
        
        # Test metrics retrieval
        analytics_data = AnalyticsService.get_platform_analytics(days=30)
        self.assertIsInstance(analytics_data, dict)
        self.assertIn('total_users', analytics_data)
        
        instructor_analytics = AnalyticsService.get_instructor_analytics(
            self.instructor.id, days=30
        )
        self.assertIsInstance(instructor_analytics, dict)
        self.assertIn('total_students', instructor_analytics)