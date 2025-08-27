"""
Management command to generate financial reports
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
import csv
import json
import os
from datetime import datetime, timedelta

from payments.models import Order, Payment, Refund, InstructorPayout, Revenue
from accounts.models import User
from courses.models import Course


class Command(BaseCommand):
    help = 'Generate financial reports for admin and instructors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='revenue',
            help='Type of report: revenue, payouts, refunds, courses'
        )
        parser.add_argument(
            '--period',
            type=str,
            default='monthly',
            help='Period: daily, weekly, monthly, quarterly, yearly'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            help='Output format: json, csv'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='financial_report',
            help='Output file name (without extension)'
        )

    def handle(self, *args, **options):
        report_type = options['type']
        period = options['period']
        start_date = options['start_date']
        end_date = options['end_date']
        output_format = options['format']
        output_name = options['output']

        try:
            # Generate report based on type
            if report_type == 'revenue':
                report_data = self.generate_revenue_report(period, start_date, end_date)
            elif report_type == 'payouts':
                report_data = self.generate_payout_report(period, start_date, end_date)
            elif report_type == 'refunds':
                report_data = self.generate_refund_report(period, start_date, end_date)
            elif report_type == 'courses':
                report_data = self.generate_course_performance_report(period, start_date, end_date)
            else:
                raise CommandError(f"Invalid report type: {report_type}")

            # Save report
            if output_format == 'json':
                self.save_json_report(report_data, output_name)
            elif output_format == 'csv':
                self.save_csv_report(report_data, output_name)
            else:
                raise CommandError(f"Invalid format: {output_format}")

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {report_type} report as {output_format} '
                    f'and saved to {output_name}.{output_format}'
                )
            )

        except Exception as e:
            raise CommandError(f'Error generating report: {str(e)}')

    def generate_revenue_report(self, period, start_date, end_date):
        """Generate revenue report data"""
        # Determine date range
        date_filters = self.get_date_filters(period, start_date, end_date)
        
        # Get orders with date filters
        orders = Order.objects.filter(**date_filters)
        
        # Calculate metrics
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_orders = orders.count()
        
        # Get daily revenue data
        daily_data = orders.extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(
            revenue=Sum('total_amount'),
            orders=Count('id')
        ).order_by('date')
        
        return {
            'report_type': 'revenue',
            'generated_at': timezone.now().isoformat(),
            'period': period,
            'summary': {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
                'average_order_value': float(total_revenue / total_orders) if total_orders > 0 else 0
            },
            'daily_data': [
                {
                    'date': entry['date'].isoformat(),
                    'revenue': float(entry['revenue']),
                    'orders': entry['orders']
                }
                for entry in daily_data
            ]
        }

    def generate_payout_report(self, period, start_date, end_date):
        """Generate payout report data"""
        # Determine date range
        date_filters = self.get_date_filters(period, start_date, end_date)
        date_filters['status'] = InstructorPayout.PayoutStatus.COMPLETED
        
        # Get payouts with date filters
        payouts = InstructorPayout.objects.filter(**date_filters)
        
        # Calculate metrics
        total_payouts = payouts.aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00')
        total_instructors = payouts.values('instructor').distinct().count()
        
        # Get payout data by instructor
        instructor_data = payouts.values(
            'instructor__id',
            'instructor__full_name',
            'instructor__email'
        ).annotate(
            total_payout=Sum('net_amount'),
            payout_count=Count('id')
        ).order_by('-total_payout')
        
        return {
            'report_type': 'payouts',
            'generated_at': timezone.now().isoformat(),
            'period': period,
            'summary': {
                'total_payouts': float(total_payouts),
                'total_instructors': total_instructors,
                'average_payout_per_instructor': float(total_payouts / total_instructors) if total_instructors > 0 else 0
            },
            'instructor_data': [
                {
                    'instructor_id': entry['instructor__id'],
                    'instructor_name': entry['instructor__full_name'] or entry['instructor__email'],
                    'total_payout': float(entry['total_payout']),
                    'payout_count': entry['payout_count']
                }
                for entry in instructor_data
            ]
        }

    def generate_refund_report(self, period, start_date, end_date):
        """Generate refund report data"""
        # Determine date range
        date_filters = self.get_date_filters(period, start_date, end_date)
        date_filters['status'] = Refund.RefundStatus.COMPLETED
        
        # Get refunds with date filters
        refunds = Refund.objects.filter(**date_filters)
        
        # Calculate metrics
        total_refunds = refunds.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_refund_count = refunds.count()
        
        # Get refund data by payment method
        payment_data = refunds.values(
            'payment__payment_method'
        ).annotate(
            total_refund=Sum('amount'),
            refund_count=Count('id')
        ).order_by('-total_refund')
        
        return {
            'report_type': 'refunds',
            'generated_at': timezone.now().isoformat(),
            'period': period,
            'summary': {
                'total_refunds': float(total_refunds),
                'total_refund_count': total_refund_count,
                'average_refund_amount': float(total_refunds / total_refund_count) if total_refund_count > 0 else 0
            },
            'payment_method_data': [
                {
                    'payment_method': entry['payment__payment_method'],
                    'total_refund': float(entry['total_refund']),
                    'refund_count': entry['refund_count']
                }
                for entry in payment_data
            ]
        }

    def generate_course_performance_report(self, period, start_date, end_date):
        """Generate course performance report data"""
        # Determine date range
        date_filters = self.get_date_filters(period, start_date, end_date)
        
        # Get revenues with date filters
        revenues = Revenue.objects.filter(**date_filters)
        
        # Calculate metrics
        total_revenue = revenues.aggregate(total=Sum('instructor_earnings'))['total'] or Decimal('0.00')
        total_courses = revenues.values('order_item__course').distinct().count()
        
        # Get course performance data
        course_data = revenues.values(
            'order_item__course__id',
            'order_item__course__title',
            'order_item__course__instructor__full_name'
        ).annotate(
            total_revenue=Sum('instructor_earnings'),
            sales_count=Count('order_item__order'),
            enrollment_count=Count('order_item__order__items__course')
        ).order_by('-total_revenue')
        
        return {
            'report_type': 'courses',
            'generated_at': timezone.now().isoformat(),
            'period': period,
            'summary': {
                'total_revenue': float(total_revenue),
                'total_courses': total_courses,
                'average_revenue_per_course': float(total_revenue / total_courses) if total_courses > 0 else 0
            },
            'course_data': [
                {
                    'course_id': entry['order_item__course__id'],
                    'course_title': entry['order_item__course__title'],
                    'instructor_name': entry['order_item__course__instructor__full_name'],
                    'total_revenue': float(entry['total_revenue']),
                    'sales_count': entry['sales_count'],
                    'enrollment_count': entry['enrollment_count']
                }
                for entry in course_data
            ]
        }

    def get_date_filters(self, period, start_date, end_date):
        """Helper function to generate date filters"""
        filters = {}
        now = timezone.now()
        
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                filters['created_at__gte'] = start_dt
                filters['created_at__lt'] = end_dt
            except ValueError:
                self.stdout.write(
                    self.style.WARNING('Invalid date format, using default period')
                )
                return self.get_default_date_filters(period, now)
        else:
            return self.get_default_date_filters(period, now)
        
        return filters

    def get_default_date_filters(self, period, now):
        """Get default date filters based on period"""
        filters = {}
        
        if period == 'daily':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            filters['created_at__gte'] = start
            filters['created_at__lt'] = end
        elif period == 'weekly':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            filters['created_at__gte'] = start
            filters['created_at__lt'] = end
        elif period == 'monthly':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = now.replace(year=now.year+1, month=1, day=1)
            else:
                end = now.replace(month=now.month+1, day=1)
            filters['created_at__gte'] = start
            filters['created_at__lt'] = end
        elif period == 'quarterly':
            quarter = (now.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month > 9:
                end = now.replace(year=now.year+1, month=1, day=1)
            else:
                end = now.replace(month=start.month+3, day=1)
            filters['created_at__gte'] = start
            filters['created_at__lt'] = end
        elif period == 'yearly':
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(year=now.year+1, month=1, day=1)
            filters['created_at__gte'] = start
            filters['created_at__lt'] = end
        
        return filters

    def save_json_report(self, report_data, output_name):
        """Save report as JSON file"""
        filename = f"{output_name}.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        self.stdout.write(f"Report saved to {filename}")

    def save_csv_report(self, report_data, output_name):
        """Save report as CSV file"""
        filename = f"{output_name}.csv"
        
        # Extract data based on report type
        if report_data['report_type'] == 'revenue':
            data = report_data['daily_data']
            headers = ['date', 'revenue', 'orders']
        elif report_data['report_type'] == 'payouts':
            data = report_data['instructor_data']
            headers = ['instructor_id', 'instructor_name', 'total_payout', 'payout_count']
        elif report_data['report_type'] == 'refunds':
            data = report_data['payment_method_data']
            headers = ['payment_method', 'total_refund', 'refund_count']
        elif report_data['report_type'] == 'courses':
            data = report_data['course_data']
            headers = ['course_id', 'course_title', 'instructor_name', 'total_revenue', 'sales_count', 'enrollment_count']
        else:
            data = []
            headers = []
        
        # Write CSV file
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        self.stdout.write(f"Report saved to {filename}")