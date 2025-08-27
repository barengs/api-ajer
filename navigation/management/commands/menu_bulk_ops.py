from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.serializers import serialize, deserialize
from navigation.models import MenuGroup, MenuItem, MenuItemPermission, MenuConfiguration
from navigation.utils import validate_menu_structure, export_menu_structure
import json
import os
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Bulk operations for navigation menus: import, export, validate, and cleanup'

    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            choices=['export', 'import', 'validate', 'cleanup', 'backup', 'restore'],
            help='Operation to perform'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='File path for import/export operations'
        )
        parser.add_argument(
            '--group',
            type=str,
            help='Menu group slug to operate on (optional)'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'django'],
            default='json',
            help='Export format (json or django serialization)'
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Automatically fix validation issues where possible'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force operation without confirmation prompts'
        )

    def handle(self, *args, **options):
        """Handle bulk navigation operations"""
        operation = options['operation']
        
        try:
            if operation == 'export':
                self.export_menus(options)
            elif operation == 'import':
                self.import_menus(options)
            elif operation == 'validate':
                self.validate_menus(options)
            elif operation == 'cleanup':
                self.cleanup_menus(options)
            elif operation == 'backup':
                self.backup_menus(options)
            elif operation == 'restore':
                self.restore_menus(options)
                
        except Exception as e:
            raise CommandError(f'Operation failed: {str(e)}')

    def export_menus(self, options):
        """Export menu structure to file"""
        file_path = options.get('file')
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f'navigation_export_{timestamp}.json'
        
        group_slug = options.get('group')
        export_format = options.get('format', 'json')
        
        if group_slug:
            try:
                menu_group = MenuGroup.objects.get(slug=group_slug)
                groups = [menu_group]
            except MenuGroup.DoesNotExist:
                raise CommandError(f'Menu group "{group_slug}" not found')
        else:
            groups = MenuGroup.objects.all()
        
        if export_format == 'json':
            self.export_json_format(groups, file_path)
        else:
            self.export_django_format(groups, file_path)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported to {file_path}')
        )

    def export_json_format(self, groups, file_path):
        """Export in custom JSON format"""
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'version': '1.0',
            'menu_groups': []
        }
        
        for group in groups:
            group_data = export_menu_structure(group)
            export_data['menu_groups'].append(group_data)
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

    def export_django_format(self, groups, file_path):
        """Export using Django serialization"""
        all_objects = []
        
        for group in groups:
            all_objects.append(group)
            all_objects.extend(group.items.all())
            
            # Include permissions
            for item in group.items.all():
                all_objects.extend(item.permissions.all())
        
        serialized_data = serialize('json', all_objects, indent=2)
        
        with open(file_path, 'w') as f:
            f.write(serialized_data)

    def import_menus(self, options):
        """Import menu structure from file"""
        file_path = options.get('file')
        if not file_path:
            raise CommandError('File path is required for import operation')
        
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')
        
        force = options.get('force', False)
        
        if not force:
            confirm = input('This will modify existing navigation data. Continue? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Import cancelled.')
                return
        
        with open(file_path, 'r') as f:
            try:
                import_data = json.load(f)
            except json.JSONDecodeError as e:
                raise CommandError(f'Invalid JSON file: {str(e)}')
        
        with transaction.atomic():
            self.process_import_data(import_data)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully imported navigation data')
        )

    def process_import_data(self, import_data):
        """Process imported navigation data"""
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            raise CommandError('No superuser found')
        
        if 'menu_groups' in import_data:
            # Custom JSON format
            for group_data in import_data['menu_groups']:
                self.import_menu_group(group_data, admin_user)
        else:
            # Django serialization format
            for obj in deserialize('json', json.dumps(import_data)):
                obj.save()

    def import_menu_group(self, group_data, admin_user):
        """Import a single menu group"""
        items_data = group_data['menu_group'].pop('items', [])
        
        # Create or update group
        group, created = MenuGroup.objects.get_or_create(
            slug=group_data['menu_group']['slug'],
            defaults={
                **group_data['menu_group'],
                'created_by': admin_user
            }
        )
        
        if created:
            self.stdout.write(f'Created group: {group.name}')
        else:
            self.stdout.write(f'Updated group: {group.name}')
        
        # Import items
        for item_data in items_data:
            self.import_menu_item(item_data, group, admin_user)

    def import_menu_item(self, item_data, group, admin_user, parent=None):
        """Import a single menu item"""
        children_data = item_data.pop('children', [])
        
        item, created = MenuItem.objects.get_or_create(
            menu_group=group,
            title=item_data['title'],
            parent=parent,
            defaults={
                **item_data,
                'created_by': admin_user
            }
        )
        
        action = 'Created' if created else 'Updated'
        indent = '  ' * (item.level if hasattr(item, 'level') else 0)
        self.stdout.write(f'{indent}{action} item: {item.title}')
        
        # Import children
        for child_data in children_data:
            self.import_menu_item(child_data, group, admin_user, parent=item)

    def validate_menus(self, options):
        """Validate menu structure and report issues"""
        group_slug = options.get('group')
        fix_issues = options.get('fix_issues', False)
        
        if group_slug:
            try:
                groups = [MenuGroup.objects.get(slug=group_slug)]
            except MenuGroup.DoesNotExist:
                raise CommandError(f'Menu group "{group_slug}" not found')
        else:
            groups = MenuGroup.objects.all()
        
        total_issues = 0
        total_warnings = 0
        
        for group in groups:
            self.stdout.write(f'Validating group: {group.name}')
            
            validation = validate_menu_structure(group)
            
            if validation['issues']:
                total_issues += len(validation['issues'])
                self.stdout.write(
                    self.style.ERROR(f'  Issues found: {len(validation["issues"])}')
                )
                for issue in validation['issues']:
                    self.stdout.write(f'    - {issue}')
            
            if validation['warnings']:
                total_warnings += len(validation['warnings'])
                self.stdout.write(
                    self.style.WARNING(f'  Warnings: {len(validation["warnings"])}')
                )
                for warning in validation['warnings']:
                    self.stdout.write(f'    - {warning}')
            
            if not validation['issues'] and not validation['warnings']:
                self.stdout.write(
                    self.style.SUCCESS('  ✓ No issues found')
                )
        
        # Summary
        if total_issues > 0:
            self.stdout.write(
                self.style.ERROR(f'Total issues: {total_issues}')
            )
        if total_warnings > 0:
            self.stdout.write(
                self.style.WARNING(f'Total warnings: {total_warnings}')
            )
        
        if total_issues == 0 and total_warnings == 0:
            self.stdout.write(
                self.style.SUCCESS('All menu structures are valid!')
            )

    def cleanup_menus(self, options):
        """Clean up unused or problematic menu data"""
        force = options.get('force', False)
        
        # Find items to clean up
        items_without_groups = MenuItem.objects.filter(menu_group__isnull=True)
        inactive_groups = MenuGroup.objects.filter(is_active=False)
        unused_permissions = MenuItemPermission.objects.filter(
            menu_item__isnull=True
        )
        
        total_to_delete = (
            items_without_groups.count() + 
            inactive_groups.count() + 
            unused_permissions.count()
        )
        
        if total_to_delete == 0:
            self.stdout.write(
                self.style.SUCCESS('No cleanup needed!')
            )
            return
        
        self.stdout.write(f'Found {total_to_delete} items to clean up:')
        self.stdout.write(f'  - Items without groups: {items_without_groups.count()}')
        self.stdout.write(f'  - Inactive groups: {inactive_groups.count()}')
        self.stdout.write(f'  - Unused permissions: {unused_permissions.count()}')
        
        if not force:
            confirm = input('Proceed with cleanup? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Cleanup cancelled.')
                return
        
        with transaction.atomic():
            deleted_count = 0
            
            # Clean up orphaned items
            deleted_count += items_without_groups.count()
            items_without_groups.delete()
            
            # Clean up unused permissions
            deleted_count += unused_permissions.count()
            unused_permissions.delete()
            
            # Optionally clean up inactive groups
            if force:
                deleted_count += inactive_groups.count()
                inactive_groups.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Cleaned up {deleted_count} items')
        )

    def backup_menus(self, options):
        """Create a backup of all navigation data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'navigation_backup_{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup groups
        groups_file = os.path.join(backup_dir, 'menu_groups.json')
        self.export_json_format(MenuGroup.objects.all(), groups_file)
        
        # Backup configurations
        configs = MenuConfiguration.objects.all()
        if configs.exists():
            config_data = []
            for config in configs:
                config_data.append({
                    'key': config.key,
                    'config_type': config.config_type,
                    'description': config.description,
                    'value': config.value,
                    'is_active': config.is_active
                })
            
            config_file = os.path.join(backup_dir, 'configurations.json')
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'Backup created in {backup_dir}')
        )

    def restore_menus(self, options):
        """Restore navigation data from backup"""
        backup_dir = options.get('file')
        if not backup_dir:
            raise CommandError('Backup directory path is required for restore')
        
        if not os.path.exists(backup_dir):
            raise CommandError(f'Backup directory not found: {backup_dir}')
        
        force = options.get('force', False)
        
        if not force:
            confirm = input('This will replace all navigation data. Continue? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Restore cancelled.')
                return
        
        with transaction.atomic():
            # Clear existing data
            MenuGroup.objects.all().delete()
            MenuConfiguration.objects.all().delete()
            
            # Restore groups
            groups_file = os.path.join(backup_dir, 'menu_groups.json')
            if os.path.exists(groups_file):
                with open(groups_file, 'r') as f:
                    import_data = json.load(f)
                self.process_import_data(import_data)
            
            # Restore configurations
            config_file = os.path.join(backup_dir, 'configurations.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                for config in config_data:
                    MenuConfiguration.objects.create(**config)
        
        self.stdout.write(
            self.style.SUCCESS('Navigation data restored successfully')
        )