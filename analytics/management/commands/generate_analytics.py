from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from analytics.services import AnalyticsService


class Command(BaseCommand):
    help = 'Generate analytics data for specified date range'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD), default: 30 days ago'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD), default: today'
        )
        parser.add_argument(
            '--instructor-id',
            type=int,
            help='Generate metrics for specific instructor only'
        )
        parser.add_argument(
            '--platform-only',
            action='store_true',
            help='Generate platform metrics only'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Parse dates
        end_date = date.today()
        if options['end_date']:
            try:
                end_date = date.fromisoformat(options['end_date'])
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid end date format. Use YYYY-MM-DD')
                )
                return
        
        start_date = end_date - timedelta(days=30)
        if options['start_date']:
            try:
                start_date = date.fromisoformat(options['start_date'])
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid start date format. Use YYYY-MM-DD')
                )
                return
        
        self.stdout.write(f'Generating analytics from {start_date} to {end_date}')
        
        # Generate platform metrics
        current_date = start_date
        platform_count = 0
        instructor_count = 0
        
        while current_date <= end_date:
            self.stdout.write(f'Processing {current_date}...')
            
            # Generate platform metrics
            try:
                AnalyticsService.update_platform_metrics(current_date)
                platform_count += 1
                self.stdout.write(f'  ✅ Platform metrics updated')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Platform metrics failed: {e}')
                )
            
            # Generate instructor metrics
            if not options['platform_only']:
                if options['instructor_id']:
                    # Specific instructor
                    try:
                        instructor = User.objects.get(
                            id=options['instructor_id'], 
                            role='instructor'  # type: ignore
                        )
                        AnalyticsService.update_instructor_metrics(
                            instructor.id, current_date
                        )
                        instructor_count += 1
                        self.stdout.write(
                            f'  ✅ Instructor metrics updated for {instructor.get_full_name()}'
                        )
                    except User.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR('  ❌ Instructor not found')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Instructor metrics failed: {e}')
                        )
                else:
                    # All instructors
                    instructors = User.objects.filter(role='instructor')  # type: ignore
                    for instructor in instructors:
                        try:
                            AnalyticsService.update_instructor_metrics(
                                instructor.id, current_date
                            )
                            instructor_count += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'  ❌ Failed for {instructor.get_full_name()}: {e}'
                                )
                            )
                    
                    if instructors.count() > 0:
                        self.stdout.write(
                            f'  ✅ Updated metrics for {instructors.count()} instructors'
                        )
            
            current_date += timedelta(days=1)
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Analytics generation completed!'
            )
        )
        self.stdout.write(f'Platform metrics: {platform_count} days')
        if not options['platform_only']:
            self.stdout.write(f'Instructor metrics: {instructor_count} records')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ All analytics data has been generated successfully!')
        )