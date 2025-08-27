"""
Financial Management Module for Admins and Instructors
This module provides comprehensive financial dashboards and management tools.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    Order, Payment, Refund, InstructorPayout, Revenue, Coupon
)
from accounts.models import User
from courses.models import Course, Enrollment


@extend_schema(
    tags=['Financial Management'],
    summary='Admin Financial Dashboard',
    description='''
    Comprehensive financial dashboard for administrators with:
    - Platform revenue analytics
    - Order and payment statistics
    - Refund tracking
    - Instructor payout summaries
    - Coupon performance metrics
    
    **Time Filters:**
    - today, yesterday, this_week, last_week
    - this_month, last_month, this_quarter
    - this_year, last_year, custom_range
    
    **Data Provided:**
    - Revenue breakdown (gross, net, commissions)
    - Order metrics (count, conversion rates)
    - Payment success/failure statistics
    - Top performing courses and instructors
    ''',
    parameters=[
        OpenApiParameter(
            name='period',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Time period filter',
            enum=[
                'today', 'yesterday', 'this_week', 'last_week',
                'this_month', 'last_month', 'this_quarter',
                'this_year', 'last_year', 'custom_range'
            ],
            default='this_month'
        ),
        OpenApiParameter(
            name='start_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Start date for custom range (YYYY-MM-DD)',
            required=False
        ),
        OpenApiParameter(
            name='end_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='End date for custom range (YYYY-MM-DD)',
            required=False
        ),
    ],
    responses={
        200: {
            'description': 'Admin financial dashboard data',
            'content': {
                'application/json': {
                    'example': {
                        'period': 'this_month',
                        'revenue_summary': {
                            'total_revenue': '15000000.00',
                            'platform_commission': '1500000.00',
                            'instructor_earnings': '13500000.00',
                            'net_platform_revenue': '1500000.00'
                        },
                        'order_metrics': {
                            'total_orders': 150,
                            'completed_orders': 142,
                            'conversion_rate': '94.67%',
                            'average_order_value': '100000.00'
                        },
                        'payment_metrics': {
                            'total_payments': 150,
                            'successful_payments': 148,
                            'failed_payments': 2,
                            'success_rate': '98.67%'
                        },
                        'refund_metrics': {
                            'total_refunds': 8,
                            'refund_amount': '800000.00',
                            'refund_rate': '5.33%'
                        },
                        'top_courses': [
                            {
                                'course_id': 1,
                                'title': 'Python untuk Pemula',
                                'revenue': '2500000.00',
                                'orders': 25
                            }
                        ],
                        'top_instructors': [
                            {
                                'instructor_id': 1,
                                'name': 'Dr. Jane Smith',
                                'earnings': '2250000.00',
                                'courses_sold': 25
                            }
                        ]
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_financial_dashboard(request):
    """Admin financial dashboard with comprehensive analytics"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get period parameters
    period = request.query_params.get('period', 'this_month')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Determine date range
    date_filters = get_date_filters(period, start_date, end_date)
    
    # Get base querysets with date filters
    orders = Order.objects.filter(**date_filters)
    payments = Payment.objects.filter(**date_filters)
    refunds = Refund.objects.filter(**date_filters)
    revenues = Revenue.objects.filter(**date_filters)
    
    # Revenue Summary
    revenue_summary = {
        'total_revenue': orders.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00'),
        'platform_commission': revenues.aggregate(
            total=Sum('platform_commission')
        )['total'] or Decimal('0.00'),
        'instructor_earnings': revenues.aggregate(
            total=Sum('instructor_earnings')
        )['total'] or Decimal('0.00'),
    }
    revenue_summary['net_platform_revenue'] = (
        revenue_summary['total_revenue'] - 
        revenue_summary['instructor_earnings']
    )
    
    # Order Metrics
    total_orders = orders.count()
    completed_orders = orders.filter(
        status=Order.OrderStatus.COMPLETED
    ).count()
    conversion_rate = (
        f"{(completed_orders/total_orders*100):.2f}%" 
        if total_orders > 0 else "0.00%"
    )
    avg_order_value = (
        orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
    )
    
    order_metrics = {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'conversion_rate': conversion_rate,
        'average_order_value': avg_order_value
    }
    
    # Payment Metrics
    total_payments = payments.count()
    successful_payments = payments.filter(
        status=Payment.PaymentStatus.COMPLETED
    ).count()
    failed_payments = payments.filter(
        status__in=[
            Payment.PaymentStatus.FAILED,
            Payment.PaymentStatus.CANCELLED
        ]
    ).count()
    success_rate = (
        f"{(successful_payments/total_payments*100):.2f}%" 
        if total_payments > 0 else "0.00%"
    )
    
    payment_metrics = {
        'total_payments': total_payments,
        'successful_payments': successful_payments,
        'failed_payments': failed_payments,
        'success_rate': success_rate
    }
    
    # Refund Metrics
    total_refunds = refunds.filter(
        status=Refund.RefundStatus.COMPLETED
    ).count()
    refund_amount = refunds.filter(
        status=Refund.RefundStatus.COMPLETED
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    refund_rate = (
        f"{(total_refunds/total_orders*100):.2f}%" 
        if total_orders > 0 else "0.00%"
    )
    
    refund_metrics = {
        'total_refunds': total_refunds,
        'refund_amount': refund_amount,
        'refund_rate': refund_rate
    }
    
    # Top Courses
    top_courses = Order.objects.filter(**date_filters).values(
        'items__course__id',
        'items__course__title'
    ).annotate(
        revenue=Sum('items__total_price'),
        order_count=Count('id')
    ).order_by('-revenue')[:5]
    
    # Top Instructors
    top_instructors = Revenue.objects.filter(**date_filters).values(
        'instructor__id',
        'instructor__full_name'
    ).annotate(
        earnings=Sum('instructor_earnings'),
        course_count=Count('order_item__course')
    ).order_by('-earnings')[:5]
    
    return Response({
        'period': period,
        'revenue_summary': revenue_summary,
        'order_metrics': order_metrics,
        'payment_metrics': payment_metrics,
        'refund_metrics': refund_metrics,
        'top_courses': [
            {
                'course_id': course['items__course__id'],
                'title': course['items__course__title'],
                'revenue': course['revenue'],
                'orders': course['order_count']
            }
            for course in top_courses
        ],
        'top_instructors': [
            {
                'instructor_id': instructor['instructor__id'],
                'name': instructor['instructor__full_name'],
                'earnings': instructor['earnings'],
                'courses_sold': instructor['course_count']
            }
            for instructor in top_instructors
        ]
    })


@extend_schema(
    tags=['Financial Management'],
    summary='Instructor Financial Dashboard',
    description='''
    Financial dashboard for instructors with:
    - Personal earnings analytics
    - Course sales performance
    - Payout history and status
    - Revenue trends over time
    
    **Time Filters:**
    - today, yesterday, this_week, last_week
    - this_month, last_month, this_quarter
    - this_year, last_year, custom_range
    
    **Data Provided:**
    - Earnings breakdown (gross, net)
    - Course-specific sales data
    - Payout history and pending amounts
    - Enrollment trends
    ''',
    parameters=[
        OpenApiParameter(
            name='period',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Time period filter',
            enum=[
                'today', 'yesterday', 'this_week', 'last_week',
                'this_month', 'last_month', 'this_quarter',
                'this_year', 'last_year', 'custom_range'
            ],
            default='this_month'
        ),
        OpenApiParameter(
            name='start_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Start date for custom range (YYYY-MM-DD)',
            required=False
        ),
        OpenApiParameter(
            name='end_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='End date for custom range (YYYY-MM-DD)',
            required=False
        ),
    ],
    responses={
        200: {
            'description': 'Instructor financial dashboard data',
            'content': {
                'application/json': {
                    'example': {
                        'period': 'this_month',
                        'earnings_summary': {
                            'total_earnings': '2250000.00',
                            'pending_payout': '2250000.00',
                            'paid_out': '0.00',
                            'courses_sold': 25
                        },
                        'course_performance': [
                            {
                                'course_id': 1,
                                'title': 'Python untuk Pemula',
                                'earnings': '1500000.00',
                                'sales': 15,
                                'enrollments': 15
                            }
                        ],
                        'payout_history': [
                            {
                                'payout_id': 'PO20240115ABC123',
                                'period': '2023-12-01 to 2023-12-31',
                                'amount': '5000000.00',
                                'status': 'completed',
                                'processed_at': '2024-01-10T10:00:00Z'
                            }
                        ],
                        'enrollment_trends': [
                            {
                                'date': '2024-01-01',
                                'count': 5
                            }
                        ]
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def instructor_financial_dashboard(request):
    """Instructor financial dashboard with earnings analytics"""
    # Get period parameters
    period = request.query_params.get('period', 'this_month')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Determine date range
    date_filters = get_date_filters(period, start_date, end_date)
    date_filters['instructor'] = request.user
    
    # Get base querysets with date filters
    revenues = Revenue.objects.filter(**date_filters)
    payouts = InstructorPayout.objects.filter(
        instructor=request.user
    ).order_by('-created_at')
    
    # Earnings Summary
    total_earnings = revenues.aggregate(
        total=Sum('instructor_earnings')
    )['total'] or Decimal('0.00')
    
    paid_out = payouts.filter(
        status=InstructorPayout.PayoutStatus.COMPLETED
    ).aggregate(
        total=Sum('net_amount')
    )['total'] or Decimal('0.00')
    
    pending_payout = payouts.filter(
        status__in=[
            InstructorPayout.PayoutStatus.PENDING,
            InstructorPayout.PayoutStatus.PROCESSING
        ]
    ).aggregate(
        total=Sum('net_amount')
    )['total'] or Decimal('0.00')
    
    courses_sold = revenues.values(
        'order_item__course'
    ).distinct().count()
    
    earnings_summary = {
        'total_earnings': total_earnings,
        'pending_payout': pending_payout,
        'paid_out': paid_out,
        'courses_sold': courses_sold
    }
    
    # Course Performance
    course_performance = revenues.values(
        'order_item__course__id',
        'order_item__course__title'
    ).annotate(
        earnings=Sum('instructor_earnings'),
        sales=Count('order_item__order'),
        enrollments=Count('order_item__order__items__course')
    ).order_by('-earnings')
    
    # Payout History
    payout_history = payouts[:10]  # Last 10 payouts
    
    # Enrollment Trends (last 30 days)
    enrollment_trends = []
    if period == 'this_month' or period == 'last_month':
        # Get daily enrollment counts
        enrollments = Enrollment.objects.filter(
            course__instructor=request.user,
            enrolled_at__gte=timezone.now() - timedelta(days=30)
        ).extra(
            select={'date': 'date(enrolled_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        enrollment_trends = [
            {
                'date': entry['date'],
                'count': entry['count']
            }
            for entry in enrollments
        ]
    
    return Response({
        'period': period,
        'earnings_summary': earnings_summary,
        'course_performance': [
            {
                'course_id': perf['order_item__course__id'],
                'title': perf['order_item__course__title'],
                'earnings': perf['earnings'],
                'sales': perf['sales'],
                'enrollments': perf['enrollments']
            }
            for perf in course_performance
        ],
        'payout_history': [
            {
                'payout_id': payout.payout_id,
                'period': f"{payout.period_start} to {payout.period_end}",
                'amount': payout.net_amount,
                'status': payout.status,
                'processed_at': payout.processed_at
            }
            for payout in payout_history
        ],
        'enrollment_trends': enrollment_trends
    })


def get_date_filters(period: str, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
    """Helper function to generate date filters for querysets"""
    filters = {}
    now = timezone.now()
    
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'yesterday':
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=1)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'this_week':
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'last_week':
        end = now - timedelta(days=now.weekday())
        end = end.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=7)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'this_month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = now.replace(year=now.year+1, month=1, day=1)
        else:
            end = now.replace(month=now.month+1, day=1)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'last_month':
        end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if end.month == 1:
            start = end.replace(year=end.year-1, month=12)
        else:
            start = end.replace(month=end.month-1)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'this_quarter':
        quarter = (now.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        start = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month > 9:
            end = now.replace(year=now.year+1, month=1, day=1)
        else:
            end = now.replace(month=start.month+3, day=1)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'this_year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(year=now.year+1, month=1, day=1)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'last_year':
        start = now.replace(year=now.year-1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        filters['created_at__gte'] = start
        filters['created_at__lt'] = end
    elif period == 'custom_range' and start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            filters['created_at__gte'] = start_dt
            filters['created_at__lt'] = end_dt
        except ValueError:
            # Invalid date format, use this month as default
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = now.replace(year=now.year+1, month=1, day=1)
            else:
                end = now.replace(month=now.month+1, day=1)
            filters['created_at__gte'] = start
            filters['created_at__lt'] = end
    
    return filters