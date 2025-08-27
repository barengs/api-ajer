from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from navigation.models import MenuGroup, MenuItem
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize default navigation menus for the LMS system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing menus (will delete existing data)',
        )
        parser.add_argument(
            '--admin-user',
            type=str,
            help='Email of admin user to set as creator (defaults to first superuser)',
        )
        parser.add_argument(
            '--config-file',
            type=str,
            help='Path to JSON configuration file for menu structure',
        )

    def handle(self, *args, **options):
        """Initialize default navigation menus"""
        try:
            # Get admin user
            admin_user = self.get_admin_user(options.get('admin_user'))
            
            # Load configuration
            if options.get('config_file'):
                menu_config = self.load_config_file(options['config_file'])
            else:
                menu_config = self.get_default_menu_config()
            
            # Check if menus already exist
            if MenuGroup.objects.exists() and not options.get('force'):
                self.stdout.write(
                    self.style.WARNING(
                        'Navigation menus already exist. Use --force to recreate them.'
                    )
                )
                return
            
            # Clear existing menus if force flag is used
            if options.get('force'):
                self.stdout.write('Clearing existing navigation data...')
                MenuGroup.objects.all().delete()
            
            # Create menus
            with transaction.atomic():
                self.create_menu_structure(menu_config, admin_user)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully initialized navigation menus!')
            )
            
        except Exception as e:
            raise CommandError(f'Failed to initialize navigation: {str(e)}')

    def get_admin_user(self, admin_email=None):
        """Get admin user for setting as creator"""
        if admin_email:
            try:
                return User.objects.get(email=admin_email, is_superuser=True)
            except User.DoesNotExist:
                raise CommandError(f'Admin user with email {admin_email} not found')
        
        # Get first superuser
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            raise CommandError('No superuser found. Please create a superuser first.')
        
        return admin_user

    def load_config_file(self, config_path):
        """Load menu configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise CommandError(f'Configuration file not found: {config_path}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON in configuration file: {str(e)}')

    def get_default_menu_config(self):
        """Get default menu configuration"""
        return {
            "menu_groups": [
                {
                    "name": "Main Navigation",
                    "slug": "main-navigation",
                    "description": "Primary navigation menu for all users",
                    "group_type": "main",
                    "min_role_level": 10,
                    "sort_order": 0,
                    "items": [
                        {
                            "title": "Dashboard",
                            "description": "User dashboard",
                            "icon": "fas fa-tachometer-alt",
                            "target_type": "internal",
                            "url_name": "dashboard",
                            "sort_order": 0,
                            "min_role_level": 10,
                            "requires_authentication": True
                        },
                        {
                            "title": "Courses",
                            "description": "Browse and manage courses",
                            "icon": "fas fa-graduation-cap",
                            "target_type": "internal",
                            "url_name": "courses:course_list",
                            "sort_order": 1,
                            "min_role_level": 10,
                            "requires_authentication": False
                        },
                        {
                            "title": "My Learning",
                            "description": "Your enrolled courses and progress",
                            "icon": "fas fa-book-reader",
                            "target_type": "internal",
                            "url_name": "courses:my_courses",
                            "sort_order": 2,
                            "min_role_level": 10,
                            "requires_authentication": True
                        },
                        {
                            "title": "Forums",
                            "description": "Discussion forums",
                            "icon": "fas fa-comments",
                            "target_type": "internal",
                            "url_name": "forums:forum_list",
                            "sort_order": 3,
                            "min_role_level": 10,
                            "requires_authentication": False
                        }
                    ]
                },
                {
                    "name": "Instructor Panel",
                    "slug": "instructor-panel",
                    "description": "Navigation for instructors",
                    "group_type": "instructor",
                    "min_role_level": 30,
                    "sort_order": 1,
                    "items": [
                        {
                            "title": "My Courses",
                            "description": "Manage your courses",
                            "icon": "fas fa-chalkboard-teacher",
                            "target_type": "internal",
                            "url_name": "courses:instructor_courses",
                            "sort_order": 0,
                            "min_role_level": 30,
                            "requires_authentication": True
                        },
                        {
                            "title": "Create Course",
                            "description": "Create a new course",
                            "icon": "fas fa-plus-circle",
                            "target_type": "internal",
                            "url_name": "courses:course_create",
                            "sort_order": 1,
                            "min_role_level": 30,
                            "requires_authentication": True,
                            "badge_text": "New",
                            "badge_color": "success"
                        },
                        {
                            "title": "Analytics",
                            "description": "Course analytics and reports",
                            "icon": "fas fa-chart-bar",
                            "target_type": "internal",
                            "url_name": "analytics:instructor_dashboard",
                            "sort_order": 2,
                            "min_role_level": 30,
                            "requires_authentication": True
                        }
                    ]
                },
                {
                    "name": "Admin Panel",
                    "slug": "admin-panel", 
                    "description": "Administrative navigation",
                    "group_type": "admin",
                    "min_role_level": 70,
                    "sort_order": 2,
                    "items": [
                        {
                            "title": "User Management",
                            "description": "Manage system users",
                            "icon": "fas fa-users",
                            "target_type": "internal",
                            "url_name": "admin:accounts_user_changelist",
                            "sort_order": 0,
                            "min_role_level": 70,
                            "requires_authentication": True
                        },
                        {
                            "title": "Course Management",
                            "description": "Manage all courses",
                            "icon": "fas fa-university",
                            "target_type": "internal",
                            "url_name": "admin:courses_course_changelist",
                            "sort_order": 1,
                            "min_role_level": 70,
                            "requires_authentication": True
                        },
                        {
                            "title": "Navigation Settings",
                            "description": "Manage navigation menus",
                            "icon": "fas fa-sitemap",
                            "target_type": "internal",
                            "url_name": "admin:navigation_menugroup_changelist",
                            "sort_order": 2,
                            "min_role_level": 70,
                            "requires_authentication": True
                        },
                        {
                            "title": "System Analytics",
                            "description": "Platform analytics",
                            "icon": "fas fa-analytics",
                            "target_type": "internal",
                            "url_name": "analytics:admin_dashboard",
                            "sort_order": 3,
                            "min_role_level": 70,
                            "requires_authentication": True
                        }
                    ]
                }
            ]
        }

    def create_menu_structure(self, config, admin_user):
        """Create menu structure from configuration"""
        created_groups = 0
        created_items = 0
        
        for group_data in config.get('menu_groups', []):
            # Create menu group
            group_items = group_data.pop('items', [])
            group = MenuGroup.objects.create(
                created_by=admin_user,
                **group_data
            )
            created_groups += 1
            
            self.stdout.write(f'Created menu group: {group.name}')
            
            # Create menu items
            for item_data in group_items:
                # Handle nested items (children)
                children_data = item_data.pop('children', [])
                
                item = MenuItem.objects.create(
                    menu_group=group,
                    created_by=admin_user,
                    **item_data
                )
                created_items += 1
                
                self.stdout.write(f'  Created menu item: {item.title}')
                
                # Create child items
                for child_data in children_data:
                    child = MenuItem.objects.create(
                        menu_group=group,
                        parent=item,
                        created_by=admin_user,
                        **child_data
                    )
                    created_items += 1
                    
                    self.stdout.write(f'    Created child item: {child.title}')
        
        self.stdout.write(f'Created {created_groups} menu groups and {created_items} menu items')