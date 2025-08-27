from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from navigation.models import MenuGroup, MenuItem, MenuClickTracking, MenuConfiguration
from navigation.utils import get_menu_statistics
import json


class Command(BaseCommand):
    help = 'Generate navigation analytics and reports'

    def add_arguments(self, parser):
        parser.add_argument(
            'report_type',
            choices=[
                'usage', 'popular', 'performance', 'accessibility', 
                'structure', 'health', 'export'
            ],
            help='Type of report to generate'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        parser.add_argument(
            '--group',
            type=str,
            help='Menu group slug to analyze (optional)'
        )
        parser.add_argument(
            '--format',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)'
        )
        parser.add_argument(
            '--include-inactive',
            action='store_true',
            help='Include inactive menu items in analysis'
        )

    def handle(self, *args, **options):
        """Generate navigation reports"""
        report_type = options['report_type']
        
        try:
            if report_type == 'usage':
                self.usage_report(options)
            elif report_type == 'popular':
                self.popular_items_report(options)
            elif report_type == 'performance':
                self.performance_report(options)
            elif report_type == 'accessibility':
                self.accessibility_report(options)
            elif report_type == 'structure':
                self.structure_report(options)
            elif report_type == 'health':
                self.health_report(options)
            elif report_type == 'export':
                self.export_analytics(options)
                
        except Exception as e:
            raise CommandError(f'Report generation failed: {str(e)}')

    def usage_report(self, options):
        """Generate usage analytics report"""
        days = options['days']
        group_slug = options.get('group')
        
        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Navigation Usage Report ({days} days)')
        )
        self.stdout.write('=' * 50)
        
        # Filter clicks by date
        clicks_qs = MenuClickTracking.objects.filter(
            clicked_at__gte=start_date
        )
        
        if group_slug:
            clicks_qs = clicks_qs.filter(
                menu_item__menu_group__slug=group_slug
            )
        
        # Overall statistics
        total_clicks = clicks_qs.count()
        unique_users = clicks_qs.values('user').distinct().count()
        unique_items = clicks_qs.values('menu_item').distinct().count()
        
        self.stdout.write(f'Total Clicks: {total_clicks:,}')
        self.stdout.write(f'Unique Users: {unique_users:,}')
        self.stdout.write(f'Menu Items Used: {unique_items:,}')
        
        if total_clicks > 0:
            avg_clicks_per_user = total_clicks / unique_users if unique_users > 0 else 0
            self.stdout.write(f'Avg Clicks per User: {avg_clicks_per_user:.1f}')
        
        # Daily breakdown
        self.stdout.write('\nDaily Usage:')
        daily_stats = self.get_daily_usage_stats(clicks_qs, days)
        
        for day_data in daily_stats:
            self.stdout.write(
                f"  {day_data['date']}: {day_data['clicks']:,} clicks "
                f"({day_data['unique_users']} users)"
            )

    def popular_items_report(self, options):
        """Generate popular menu items report"""
        days = options['days']
        group_slug = options.get('group')
        include_inactive = options.get('include_inactive', False)
        
        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Popular Menu Items Report ({days} days)')
        )
        self.stdout.write('=' * 50)
        
        # Get menu items with click counts
        items_qs = MenuItem.objects.all()
        
        if not include_inactive:
            items_qs = items_qs.filter(is_active=True)
        
        if group_slug:
            items_qs = items_qs.filter(menu_group__slug=group_slug)
        
        # Annotate with click counts
        items_with_clicks = items_qs.annotate(
            click_count=Count(
                'click_tracking',
                filter=Q(click_tracking__clicked_at__gte=start_date)
            ),
            unique_users=Count(
                'click_tracking__user',
                filter=Q(click_tracking__clicked_at__gte=start_date),
                distinct=True
            )
        ).order_by('-click_count')
        
        # Top 20 items
        top_items = items_with_clicks[:20]
        
        self.stdout.write('\nTop 20 Most Clicked Items:')
        self.stdout.write(f'{"Rank":<4} {"Title":<30} {"Group":<20} {"Clicks":<8} {"Users":<6}')
        self.stdout.write('-' * 70)
        
        for i, item in enumerate(top_items, 1):
            # Access annotated fields using getattr to satisfy type checker
            click_count = getattr(item, 'click_count', 0)
            unique_users = getattr(item, 'unique_users', 0)
            
            title = item.title[:28] + '...' if len(item.title) > 30 else item.title
            group_name = item.menu_group.name[:18] + '...' if len(item.menu_group.name) > 20 else item.menu_group.name
            
            self.stdout.write(
                f'{i:<4} {title:<30} {group_name:<20} '
                f'{click_count:<8} {unique_users:<6}'
            )
        
        # Items with no clicks
        no_clicks = items_qs.filter(
            click_tracking__isnull=True
        ).count()
        
        if no_clicks > 0:
            self.stdout.write(f'\nItems with no clicks: {no_clicks}')

    def performance_report(self, options):
        """Generate performance analysis report"""
        days = options['days']
        
        self.stdout.write(
            self.style.SUCCESS(f'Navigation Performance Report ({days} days)')
        )
        self.stdout.write('=' * 50)
        
        # Menu groups performance
        groups = MenuGroup.objects.filter(is_active=True).annotate(
            total_items=Count('items'),
            active_items=Count('items', filter=Q(items__is_active=True)),
            total_clicks=Count(
                'items__click_tracking',
                filter=Q(
                    items__click_tracking__clicked_at__gte=timezone.now() - timedelta(days=days)
                )
            )
        ).order_by('-total_clicks')
        
        self.stdout.write('\nMenu Group Performance:')
        self.stdout.write(f'{"Group":<25} {"Items":<8} {"Active":<8} {"Clicks":<8} {"Efficiency":<10}')
        self.stdout.write('-' * 60)
        
        for group in groups:
            # Access annotated fields using getattr to satisfy type checker
            total_items = getattr(group, 'total_items', 0)
            active_items = getattr(group, 'active_items', 0)
            total_clicks = getattr(group, 'total_clicks', 0)
            
            efficiency = (total_clicks / active_items) if active_items > 0 else 0
            group_name = group.name[:23] + '...' if len(group.name) > 25 else group.name
            
            self.stdout.write(
                f'{group_name:<25} {total_items:<8} {active_items:<8} '
                f'{total_clicks:<8} {efficiency:<10.2f}'
            )
        
        # URL resolution issues
        broken_items = []
        for item in MenuItem.objects.filter(is_active=True):
            try:
                url = item.get_url()
                if url == '#' or not url:
                    broken_items.append(item)
            except Exception:
                broken_items.append(item)
        
        if broken_items:
            self.stdout.write(f'\nItems with URL issues: {len(broken_items)}')
            for item in broken_items[:10]:  # Show first 10
                self.stdout.write(f'  - {item.menu_group.name} > {item.title}')

    def accessibility_report(self, options):
        """Generate accessibility compliance report"""
        self.stdout.write(
            self.style.SUCCESS('Navigation Accessibility Report')
        )
        self.stdout.write('=' * 40)
        
        # Check various accessibility criteria
        total_items = MenuItem.objects.filter(is_active=True).count()
        
        # Items without icons
        no_icon = MenuItem.objects.filter(
            is_active=True,
            icon__in=['', None]
        ).count()
        
        # Items without descriptions
        no_description = MenuItem.objects.filter(
            is_active=True,
            description__in=['', None]
        ).count()
        
        # Items with very long titles
        long_titles = MenuItem.objects.filter(
            is_active=True,
            title__regex=r'.{50,}'
        ).count()
        
        # External links without new window indication
        external_no_new_window = MenuItem.objects.filter(
            is_active=True,
            target_type=MenuItem.TargetType.EXTERNAL,
            opens_in_new_window=False
        ).count()
        
        # Role level distribution
        role_levels = MenuItem.objects.filter(is_active=True).values(
            'min_role_level'
        ).annotate(
            count=Count('id')
        ).order_by('min_role_level')
        
        self.stdout.write(f'Total Active Items: {total_items}')
        self.stdout.write(f'Items without icons: {no_icon} ({(no_icon/total_items*100):.1f}%)')
        self.stdout.write(f'Items without descriptions: {no_description} ({(no_description/total_items*100):.1f}%)')
        self.stdout.write(f'Items with long titles (>50 chars): {long_titles}')
        self.stdout.write(f'External links not opening in new window: {external_no_new_window}')
        
        self.stdout.write('\nRole Level Distribution:')
        for level_data in role_levels:
            level = level_data['min_role_level']
            count = level_data['count']
            percentage = (count / total_items * 100) if total_items > 0 else 0
            self.stdout.write(f'  Level {level}: {count} items ({percentage:.1f}%)')

    def structure_report(self, options):
        """Generate menu structure analysis report"""
        include_inactive = options.get('include_inactive', False)
        
        self.stdout.write(
            self.style.SUCCESS('Navigation Structure Report')
        )
        self.stdout.write('=' * 40)
        
        # Menu groups overview
        groups_qs = MenuGroup.objects.all()
        if not include_inactive:
            groups_qs = groups_qs.filter(is_active=True)
        
        self.stdout.write(f'Total Menu Groups: {groups_qs.count()}')
        
        for group in groups_qs:
            items_qs = group.items.all()
            if not include_inactive:
                items_qs = items_qs.filter(is_active=True)
            
            root_items = items_qs.filter(parent=None)
            child_items = items_qs.exclude(parent=None)
            
            max_depth = 0
            for item in items_qs:
                depth = 0
                current = item
                while current.parent:
                    depth += 1
                    current = current.parent
                    if depth > 10:  # Prevent infinite loops
                        break
                max_depth = max(max_depth, depth)
            
            self.stdout.write(f'\n{group.name} ({group.group_type}):')
            self.stdout.write(f'  Total items: {items_qs.count()}')
            self.stdout.write(f'  Root items: {root_items.count()}')
            self.stdout.write(f'  Child items: {child_items.count()}')
            self.stdout.write(f'  Max depth: {max_depth}')
            
            # Show structure
            self.show_menu_structure(root_items, include_inactive)

    def show_menu_structure(self, items, include_inactive, level=0):
        """Display menu structure hierarchically"""
        if level > 3:  # Limit depth for readability
            return
            
        for item in items.order_by('sort_order', 'title'):
            if not include_inactive and not item.is_active:
                continue
                
            indent = '  ' * (level + 2)
            status = '✓' if item.is_active else '✗'
            self.stdout.write(f'{indent}{status} {item.title}')
            
            # Show children
            children = item.children.all()
            if children.exists():
                self.show_menu_structure(children, include_inactive, level + 1)

    def health_report(self, options):
        """Generate navigation health check report"""
        self.stdout.write(
            self.style.SUCCESS('Navigation Health Report')
        )
        self.stdout.write('=' * 40)
        
        issues = []
        warnings = []
        
        # Check for circular references
        for item in MenuItem.objects.all():
            visited = set()
            current = item.parent
            path_length = 0
            
            while current and path_length < 10:
                if current.id in visited:
                    issues.append(f'Circular reference detected: {item.title}')
                    break
                visited.add(current.id)
                current = current.parent
                path_length += 1
        
        # Check for orphaned items
        orphaned = MenuItem.objects.filter(menu_group__isnull=True).count()
        if orphaned > 0:
            issues.append(f'{orphaned} orphaned menu items found')
        
        # Check for items without URLs
        no_url = MenuItem.objects.filter(
            is_active=True,
            url_name='',
            url_path=''
        ).count()
        if no_url > 0:
            warnings.append(f'{no_url} active items without URLs')
        
        # Check for duplicate titles in same group
        from django.db.models import Count
        duplicates = MenuItem.objects.values(
            'menu_group', 'title'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            warnings.append(f'{duplicates.count()} duplicate titles found in same groups')
        
        # Check role level consistency
        inconsistent_roles = MenuItem.objects.filter(
            parent__isnull=False,
            min_role_level__lt=models.F('parent__min_role_level')
        ).count()
        
        if inconsistent_roles > 0:
            warnings.append(f'{inconsistent_roles} items with lower role level than parent')
        
        # Display results
        if not issues and not warnings:
            self.stdout.write(
                self.style.SUCCESS('✓ All health checks passed!')
            )
        else:
            if issues:
                self.stdout.write(
                    self.style.ERROR(f'Issues found: {len(issues)}')
                )
                for issue in issues:
                    self.stdout.write(f'  ✗ {issue}')
            
            if warnings:
                self.stdout.write(
                    self.style.WARNING(f'Warnings: {len(warnings)}')
                )
                for warning in warnings:
                    self.stdout.write(f'  ⚠ {warning}')

    def export_analytics(self, options):
        """Export analytics data to file"""
        days = options['days']
        output_format = options.get('format', 'json')
        output_file = options.get('output')
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'navigation_analytics_{timestamp}.{output_format}'
        
        # Gather analytics data
        analytics_data = {
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'summary': get_menu_statistics(),
            'groups': [],
            'popular_items': [],
            'daily_usage': []
        }
        
        # Group data
        for group in MenuGroup.objects.filter(is_active=True):
            group_data = {
                'name': group.name,
                'slug': group.slug,
                'type': group.group_type,
                'total_items': group.items.count(),
                'active_items': group.items.filter(is_active=True).count(),
                'total_clicks': group.items.aggregate(
                    total=Count('click_tracking')
                )['total'] or 0
            }
            analytics_data['groups'].append(group_data)
        
        # Popular items
        start_date = timezone.now() - timedelta(days=days)
        popular_items = MenuItem.objects.filter(
            is_active=True
        ).annotate(
            click_count=Count(
                'click_tracking',
                filter=Q(click_tracking__clicked_at__gte=start_date)
            )
        ).order_by('-click_count')[:20]
        
        for item in popular_items:
            # Access annotated field using getattr to satisfy type checker
            click_count = getattr(item, 'click_count', 0)
            
            analytics_data['popular_items'].append({
                'title': item.title,
                'group': item.menu_group.name,
                'clicks': click_count,
                'url': item.get_url()
            })
        
        # Daily usage
        clicks_qs = MenuClickTracking.objects.filter(
            clicked_at__gte=start_date
        )
        daily_stats = self.get_daily_usage_stats(clicks_qs, days)
        analytics_data['daily_usage'] = daily_stats
        
        # Export data
        if output_format == 'json':
            with open(output_file, 'w') as f:
                json.dump(analytics_data, f, indent=2, default=str)
        elif output_format == 'csv':
            self.export_csv(analytics_data, output_file)
        
        self.stdout.write(
            self.style.SUCCESS(f'Analytics exported to {output_file}')
        )

    def get_daily_usage_stats(self, clicks_qs, days):
        """Get daily usage statistics"""
        daily_stats = []
        
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            day_clicks = clicks_qs.filter(clicked_at__date=date)
            
            daily_stats.append({
                'date': date.isoformat(),
                'clicks': day_clicks.count(),
                'unique_users': day_clicks.values('user').distinct().count(),
                'unique_items': day_clicks.values('menu_item').distinct().count()
            })
        
        return list(reversed(daily_stats))

    def export_csv(self, data, output_file):
        """Export analytics data to CSV format"""
        import csv
        
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Popular items section
            writer.writerow(['Popular Items'])
            writer.writerow(['Title', 'Group', 'Clicks', 'URL'])
            
            for item in data['popular_items']:
                writer.writerow([
                    item['title'],
                    item['group'],
                    item['clicks'],
                    item['url']
                ])
            
            writer.writerow([])  # Empty row
            
            # Daily usage section
            writer.writerow(['Daily Usage'])
            writer.writerow(['Date', 'Clicks', 'Unique Users', 'Unique Items'])
            
            for day in data['daily_usage']:
                writer.writerow([
                    day['date'],
                    day['clicks'],
                    day['unique_users'],
                    day['unique_items']
                ])