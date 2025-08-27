from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from role_management.models import RoleDefinition, RolePermissionGroup, RolePermissionAssignment


class Command(BaseCommand):
    help = 'Initialize default roles and permission groups for the LMS system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing roles',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Initializing default roles...'))
        
        # Create permission groups first
        self.create_permission_groups()
        
        # Create default roles
        self.create_default_roles(force)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized default roles and permissions!')
        )

    def create_permission_groups(self):
        """Create default permission groups"""
        permission_groups = [
            {
                'name': 'Course Management',
                'description': 'Permissions for managing courses and lessons',
                'permissions': [
                    'courses.add_course',
                    'courses.change_course', 
                    'courses.delete_course',
                    'courses.view_course',
                    'lessons.add_lesson',
                    'lessons.change_lesson',
                    'lessons.delete_lesson',
                    'lessons.view_lesson',
                ]
            },
            {
                'name': 'User Management',
                'description': 'Permissions for managing users and authentication',
                'permissions': [
                    'auth.add_user',
                    'auth.change_user',
                    'auth.delete_user',
                    'auth.view_user',
                    'users.change_userprofile',
                    'users.view_userprofile',
                ]
            },
            {
                'name': 'Content Moderation',
                'description': 'Permissions for moderating content and forums',
                'permissions': [
                    'forums.add_forum',
                    'forums.change_forum',
                    'forums.delete_forum',
                    'forums.view_forum',
                    'forums.add_forumpost',
                    'forums.change_forumpost',
                    'forums.delete_forumpost',
                    'forums.view_forumpost',
                ]
            },
            {
                'name': 'Payment Management',
                'description': 'Permissions for managing payments and transactions',
                'permissions': [
                    'payments.view_order',
                    'payments.change_order',
                    'payments.view_payment',
                    'payments.change_payment',
                    'payments.view_instructorrevenue',
                    'payments.change_instructorrevenue',
                ]
            },
            {
                'name': 'Analytics Access',
                'description': 'Permissions for viewing analytics and reports',
                'permissions': [
                    'analytics.view_platformmetrics',
                    'analytics.view_instructormetrics',
                    'analytics.view_coursemetrics',
                    'analytics.view_studentmetrics',
                ]
            },
        ]
        
        for group_data in permission_groups:
            group, created = RolePermissionGroup.objects.get_or_create(
                name=group_data['name'],
                defaults={
                    'description': group_data['description']
                }
            )
            
            if created or not group.permissions:
                # Add permissions to the group
                permission_codes = []
                for perm_code in group_data['permissions']:
                    try:
                        app_label, codename = perm_code.split('.')
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename
                        )
                        permission_codes.append(perm_code)
                    except (Permission.DoesNotExist, ValueError):
                        self.stdout.write(
                            self.style.WARNING(f'Permission {perm_code} not found, skipping...')
                        )
                
                group.permissions = permission_codes
                group.save()
                status = 'Created' if created else 'Updated'
                self.stdout.write(f'  {status} permission group: {group.name}')

    def create_default_roles(self, force=False):
        """Create default role definitions"""
        roles_data = [
            {
                'name': RoleDefinition.RoleType.ADMIN,
                'display_name': 'Administrator',
                'hierarchy_level': 1,
                'description': 'Full system access with all permissions',
                'permission_groups': ['User Management', 'Course Management', 'Content Moderation', 'Payment Management', 'Analytics Access']
            },
            {
                'name': RoleDefinition.RoleType.MODERATOR,
                'display_name': 'Content Moderator',
                'hierarchy_level': 2,
                'description': 'Content moderation and course approval',
                'permission_groups': ['Content Moderation', 'Course Management']
            },
            {
                'name': RoleDefinition.RoleType.INSTRUCTOR,
                'display_name': 'Instructor',
                'hierarchy_level': 3,
                'description': 'Course creation and management',
                'permission_groups': ['Course Management', 'Analytics Access']
            },
            {
                'name': RoleDefinition.RoleType.ASSISTANT,
                'display_name': 'Teaching Assistant',
                'hierarchy_level': 4,
                'description': 'Assistant for helping with course management',
                'permission_groups': []
            },
            {
                'name': RoleDefinition.RoleType.SUPPORT,
                'display_name': 'Support Staff',
                'hierarchy_level': 5,
                'description': 'Customer support and user assistance',
                'permission_groups': []
            },
            {
                'name': RoleDefinition.RoleType.STUDENT,
                'display_name': 'Student',
                'hierarchy_level': 6,
                'description': 'Standard student role for course enrollment',
                'permission_groups': []
            },
        ]
        
        for role_data in roles_data:
            name = role_data['name']
            
            if RoleDefinition.objects.filter(name=name).exists():
                if not force:
                    self.stdout.write(f'  Role "{role_data['display_name']}" already exists, skipping...')
                    continue
                else:
                    RoleDefinition.objects.filter(name=name).delete()
                    self.stdout.write(f'  Deleted existing role: {role_data['display_name']}')
            
            # Create the role
            role = RoleDefinition.objects.create(
                name=role_data['name'],
                display_name=role_data['display_name'],
                hierarchy_level=role_data['hierarchy_level'],
                description=role_data['description'],
            )
            
            # Add permission groups
            if role_data['permission_groups']:
                groups = RolePermissionGroup.objects.filter(
                    name__in=role_data['permission_groups']
                )
                for group in groups:
                    RolePermissionAssignment.objects.get_or_create(
                        role=role,
                        permission_group=group
                    )
            
            self.stdout.write(f'  Created role: {role.display_name} (Level {role.hierarchy_level})')
        
        self.stdout.write(f'Total roles in system: {RoleDefinition.objects.count()}')