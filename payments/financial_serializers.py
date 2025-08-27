"""
Serializers for Financial Management Module
"""

from rest_framework import serializers
from decimal import Decimal
from .models import (
    Order, Payment, Refund, InstructorPayout, Revenue, Coupon
)
from accounts.models import User
from courses.models import Course


class FinancialSummarySerializer(serializers.Serializer):
    """Serializer for financial summary data"""
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = serializers.DecimalField(max_digits=10, decimal_places=2)
    instructor_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    net_platform_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderMetricsSerializer(serializers.Serializer):
    """Serializer for order metrics"""
    total_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    conversion_rate = serializers.CharField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)


class PaymentMetricsSerializer(serializers.Serializer):
    """Serializer for payment metrics"""
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    success_rate = serializers.CharField()


class RefundMetricsSerializer(serializers.Serializer):
    """Serializer for refund metrics"""
    total_refunds = serializers.IntegerField()
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    refund_rate = serializers.CharField()


class TopCourseSerializer(serializers.Serializer):
    """Serializer for top performing courses"""
    course_id = serializers.IntegerField()
    title = serializers.CharField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders = serializers.IntegerField()


class TopInstructorSerializer(serializers.Serializer):
    """Serializer for top performing instructors"""
    instructor_id = serializers.IntegerField()
    name = serializers.CharField()
    earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    courses_sold = serializers.IntegerField()


class AdminFinancialDashboardSerializer(serializers.Serializer):
    """Serializer for admin financial dashboard"""
    period = serializers.CharField()
    revenue_summary = FinancialSummarySerializer()
    order_metrics = OrderMetricsSerializer()
    payment_metrics = PaymentMetricsSerializer()
    refund_metrics = RefundMetricsSerializer()
    top_courses = TopCourseSerializer(many=True)
    top_instructors = TopInstructorSerializer(many=True)


class EarningsSummarySerializer(serializers.Serializer):
    """Serializer for instructor earnings summary"""
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_payout = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_out = serializers.DecimalField(max_digits=10, decimal_places=2)
    courses_sold = serializers.IntegerField()


class CoursePerformanceSerializer(serializers.Serializer):
    """Serializer for course performance data"""
    course_id = serializers.IntegerField()
    title = serializers.CharField()
    earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    sales = serializers.IntegerField()
    enrollments = serializers.IntegerField()


class PayoutHistorySerializer(serializers.Serializer):
    """Serializer for payout history"""
    payout_id = serializers.CharField()
    period = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    processed_at = serializers.DateTimeField(allow_null=True)


class EnrollmentTrendSerializer(serializers.Serializer):
    """Serializer for enrollment trends"""
    date = serializers.DateField()
    count = serializers.IntegerField()


class InstructorFinancialDashboardSerializer(serializers.Serializer):
    """Serializer for instructor financial dashboard"""
    period = serializers.CharField()
    earnings_summary = EarningsSummarySerializer()
    course_performance = CoursePerformanceSerializer(many=True)
    payout_history = PayoutHistorySerializer(many=True)
    enrollment_trends = EnrollmentTrendSerializer(many=True)


class PayoutRequestSerializer(serializers.Serializer):
    """Serializer for instructor payout requests"""
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    payout_method = serializers.CharField(max_length=50)
    payout_details = serializers.JSONField()


class PayoutRequestResponseSerializer(serializers.Serializer):
    """Serializer for payout request response"""
    payout_id = serializers.CharField()
    message = serializers.CharField()


class FinancialReportRequestSerializer(serializers.Serializer):
    """Serializer for financial report requests"""
    report_type = serializers.ChoiceField(choices=[
        ('revenue', 'Revenue Report'),
        ('payouts', 'Payout Report'),
        ('refunds', 'Refund Report'),
        ('courses', 'Course Performance Report'),
    ])
    period = serializers.ChoiceField(choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ])
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    format = serializers.ChoiceField(choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
    ], default='json')


class FinancialReportResponseSerializer(serializers.Serializer):
    """Serializer for financial report response"""
    report_id = serializers.CharField()
    message = serializers.CharField()
    download_url = serializers.URLField(allow_null=True)