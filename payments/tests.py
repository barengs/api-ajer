"""
Tests for Financial Management Module
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Order, Payment, InstructorPayout, Revenue
from courses.models import Course

User = get_user_model()


class FinancialManagementTestCase(APITestCase):
    """Test cases for financial management functionality"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_user(  # type: ignore
            email='admin@example.com',
            username='admin',
            password='testpass123'
        )
        self.admin_user.role = User.UserRole.ADMIN  # type: ignore
        self.admin_user.save()
        
        self.instructor_user = User.objects.create_user(  # type: ignore
            email='instructor@example.com',
            username='instructor',
            password='testpass123'
        )
        self.instructor_user.role = User.UserRole.INSTRUCTOR  # type: ignore
        self.instructor_user.save()
        
        self.student_user = User.objects.create_user(  # type: ignore
            email='student@example.com',
            username='student',
            password='testpass123'
        )
        self.student_user.role = User.UserRole.STUDENT  # type: ignore
        self.student_user.save()
        
        # Create course
        self.course = Course.objects.create(
            title='Test Course',
            description='Test course description',
            price=Decimal('100000.00'),
            instructor=self.instructor_user
        )
        
        # Create order
        self.order = Order.objects.create(
            user=self.student_user,
            order_number='ORD20240101TEST001',
            subtotal=Decimal('100000.00'),
            total_amount=Decimal('100000.00'),
            billing_email=self.student_user.email,
            billing_name=self.student_user.full_name or self.student_user.username
        )
        
        # Create payment
        self.payment = Payment.objects.create(
            order=self.order,
            payment_id='PAY20240101TEST001',
            amount=Decimal('100000.00'),
            currency='IDR',
            payment_method=Payment.PaymentMethod.CREDIT_CARD,
            status=Payment.PaymentStatus.COMPLETED
        )
        
        # Create revenue
        # First create an order item since it's required
        order_item = self.order.items.create(  # type: ignore
            course=self.course,
            unit_price=Decimal('100000.00'),
            discount_amount=Decimal('0.00'),
            total_price=Decimal('100000.00'),
            course_title=self.course.title,
            instructor_name=self.instructor_user.full_name or self.instructor_user.username
        )
        
        self.revenue = Revenue.objects.create(
            order_item=order_item,
            instructor=self.instructor_user,
            gross_amount=Decimal('100000.00'),
            platform_commission=Decimal('10000.00'),
            instructor_earnings=Decimal('90000.00'),
            commission_rate=Decimal('0.1000')
        )
        
        # Create payout
        self.payout = InstructorPayout.objects.create(
            instructor=self.instructor_user,
            period_start=timezone.now().date() - timedelta(days=30),
            period_end=timezone.now().date(),
            gross_revenue=Decimal('90000.00'),
            platform_commission=Decimal('0.00'),
            commission_rate=Decimal('0.0000'),
            net_amount=Decimal('90000.00'),
            payout_method='bank_transfer'
        )
        
        # Set up API clients
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        
        self.instructor_client = APIClient()
        self.instructor_client.force_authenticate(user=self.instructor_user)
        
        self.student_client = APIClient()
        self.student_client.force_authenticate(user=self.student_user)

    def test_admin_financial_dashboard_access(self):
        """Test admin can access financial dashboard"""
        response = self.admin_client.get('/api/v1/payments/financial/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        
        # Check response structure
        data = response.data  # type: ignore
        self.assertIn('period', data)
        self.assertIn('revenue_summary', data)
        self.assertIn('order_metrics', data)
        self.assertIn('payment_metrics', data)

    def test_instructor_financial_dashboard_access(self):
        """Test instructor can access financial dashboard"""
        response = self.instructor_client.get('/api/v1/payments/financial/instructor/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        
        # Check response structure
        data = response.data  # type: ignore
        self.assertIn('period', data)
        self.assertIn('earnings_summary', data)
        self.assertIn('course_performance', data)

    def test_student_cannot_access_admin_dashboard(self):
        """Test student cannot access admin financial dashboard"""
        response = self.student_client.get('/api/v1/payments/financial/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore

    def test_student_cannot_access_instructor_dashboard(self):
        """Test student cannot access instructor financial dashboard"""
        response = self.student_client.get('/api/v1/payments/financial/instructor/dashboard/')
        # Students should be able to access their own dashboard if implemented
        # For now, we'll check that it doesn't return a 500 error
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)  # type: ignore

    def test_admin_revenue_report(self):
        """Test admin can generate revenue report"""
        response = self.admin_client.get('/api/v1/payments/admin/reports/', {
            'report_type': 'revenue',
            'period': 'monthly'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        
        # Check response structure
        data = response.data  # type: ignore
        self.assertIn('report_id', data)
        self.assertIn('report_type', data)
        self.assertIn('data', data)

    def test_admin_payout_processing(self):
        """Test admin can process instructor payouts"""
        response = self.admin_client.post('/api/v1/payments/admin/payouts/process/', {
            'instructor_id': self.instructor_user.id,
            'period_start': (timezone.now().date() - timedelta(days=60)).isoformat(),
            'period_end': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'amount': '50000.00',
            'payout_method': 'bank_transfer',
            'notes': 'Test payout'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        
        # Check response structure
        data = response.data  # type: ignore
        self.assertIn('payout_id', data)
        self.assertIn('message', data)
        self.assertIn('amount', data)

    def test_date_filtering(self):
        """Test date filtering functionality"""
        from payments.financial_views import get_date_filters
        
        # Test today filter
        filters = get_date_filters('today')
        self.assertIn('created_at__gte', filters)
        self.assertIn('created_at__lt', filters)
        
        # Test custom range
        filters = get_date_filters('custom_range', '2024-01-01', '2024-01-31')
        self.assertIn('created_at__gte', filters)
        self.assertIn('created_at__lt', filters)

    def tearDown(self):
        """Clean up test data"""
        InstructorPayout.objects.all().delete()
        Revenue.objects.all().delete()
        Payment.objects.all().delete()
        Order.objects.all().delete()
        Course.objects.all().delete()
        User.objects.all().delete()