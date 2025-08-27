from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from role_management.models import RoleDefinition, UserRoleAssignment
from role_management.services import RoleManagementService
import csv
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type hint for better IDE support without runtime impact
    from django.contrib.auth.models import AbstractUser
    User = AbstractUser
else:
    User = get_user_model()


class Command(BaseCommand):
    help = 'Bulk role management operations'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')
        
        # Assign roles
        assign_parser = subparsers.add_parser('assign', help='Assign roles to users')
        assign_parser.add_argument('--file', required=True, help='CSV file with user assignments')
        assign_parser.add_argument('--admin-user', required=True, help='Admin user performing the assignment')
        
        # Revoke roles
        revoke_parser = subparsers.add_parser('revoke', help='Revoke roles from users')
        revoke_parser.add_argument('--file', required=True, help='CSV file with user revocations')
        revoke_parser.add_argument('--admin-user', required=True, help='Admin user performing the revocation')
        
        # List users with roles
        list_parser = subparsers.add_parser('list', help='List users with their roles')
        list_parser.add_argument('--role-type', help='Filter by role type')
        list_parser.add_argument('--output', help='Output file (JSON format)')
        
        # Export roles
        export_parser = subparsers.add_parser('export', help='Export role assignments')
        export_parser.add_argument('--output', required=True, help='Output CSV file')
        export_parser.add_argument('--role-type', help='Filter by role type')
        
        # Clean expired
        clean_parser = subparsers.add_parser('clean-expired', help='Clean expired role assignments')
        clean_parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without actually doing it')

    def handle(self, *args, **options):
        operation = options['operation']
        
        if operation == 'assign':
            self.handle_assign(options)
        elif operation == 'revoke':
            self.handle_revoke(options)
        elif operation == 'list':
            self.handle_list(options)
        elif operation == 'export':
            self.handle_export(options)
        elif operation == 'clean-expired':
            self.handle_clean_expired(options)
        else:
            raise CommandError('Please specify an operation: assign, revoke, list, export, or clean-expired')

    def handle_assign(self, options):
        """Handle bulk role assignment from CSV file"""
        file_path = options['file']
        admin_username = options['admin_user']
        
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            raise CommandError(f'Admin user "{admin_username}" not found')
        
        service = RoleManagementService()
        success_count = 0
        error_count = 0
        
        self.stdout.write(f'Processing role assignments from: {file_path}')
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate headers
                required_headers = ['username', 'role_name']
                if reader.fieldnames is None or not all(header in reader.fieldnames for header in required_headers):
                    raise CommandError(f'CSV must contain columns: {", ".join(required_headers)}')
                
                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        username = None
                        role_name = None
                        try:
                            username = row['username'].strip()
                            role_name = row['role_name'].strip()
                            reason = row.get('reason', '').strip() or 'Bulk assignment'
                            expires_at = row.get('expires_at', '').strip() or None
                            
                            # Get user and role
                            user = User.objects.get(username=username)
                            role = RoleDefinition.objects.get(name=role_name)
                            
                            # Parse expires_at if provided
                            effective_until = None
                            if expires_at:
                                from django.utils.dateparse import parse_datetime
                                effective_until = parse_datetime(expires_at)
                                if not effective_until:
                                    # Try parsing as date
                                    from django.utils.dateparse import parse_date
                                    from datetime import datetime, time
                                    expires_date = parse_date(expires_at)
                                    if expires_date:
                                        from django.utils import timezone
                                        effective_until = timezone.make_aware(
                                            datetime.combine(expires_date, time.min)
                                        )
                            
                            # Assign role
                            assignment = service.assign_role(
                                user_id=user.pk,
                                role_id=role.pk,
                                assigned_by=admin_user,
                                reason=reason,
                                effective_until=effective_until
                            )
                            
                            # Assign role returns UserRoleAssignment on success
                            if assignment:
                                success_count += 1
                                self.stdout.write(f'  ✓ Row {row_num}: Assigned {role_name} to {username}')
                            else:
                                error_count += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ✗ Row {row_num}: Failed to assign role')
                                )
                        
                        except User.DoesNotExist:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Row {row_num}: User "{username}" not found')
                            )
                        except RoleDefinition.DoesNotExist:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Row {row_num}: Role "{role_name}" not found')
                            )
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Row {row_num}: {str(e)}')
                            )
        
        except FileNotFoundError:
            raise CommandError(f'File "{file_path}" not found')
        except Exception as e:
            raise CommandError(f'Error processing file: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Completed: {success_count} successful, {error_count} errors')
        )

    def handle_revoke(self, options):
        """Handle bulk role revocation from CSV file"""
        file_path = options['file']
        admin_username = options['admin_user']
        
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            raise CommandError(f'Admin user "{admin_username}" not found')
        
        service = RoleManagementService()
        success_count = 0
        error_count = 0
        
        self.stdout.write(f'Processing role revocations from: {file_path}')
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate headers
                required_headers = ['username', 'role_name']
                if reader.fieldnames is None or not all(header in reader.fieldnames for header in required_headers):
                    raise CommandError(f'CSV must contain columns: {", ".join(required_headers)}')
                
                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        username = None
                        role_name = None
                        try:
                            username = row['username'].strip()
                            role_name = row['role_name'].strip()
                            reason = row.get('reason', '').strip() or 'Bulk revocation'
                            
                            # Get user and role
                            user = User.objects.get(username=username)
                            role = RoleDefinition.objects.get(name=role_name)
                            
                            # Find the active assignment
                            assignment = UserRoleAssignment.objects.filter(
                                user=user,
                                role=role,
                                status=UserRoleAssignment.AssignmentStatus.ACTIVE
                            ).first()
                            
                            if not assignment:
                                error_count += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ✗ Row {row_num}: No active assignment found for {role_name} on {username}')
                                )
                                continue
                            
                            # Revoke role
                            revoked_assignment = service.revoke_role(
                                assignment_id=assignment.pk,
                                revoked_by=admin_user,
                                reason=reason
                            )
                            
                            # Revoke role returns UserRoleAssignment on success
                            if revoked_assignment:
                                success_count += 1
                                self.stdout.write(f'  ✓ Row {row_num}: Revoked {role_name} from {username}')
                            else:
                                error_count += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ✗ Row {row_num}: Failed to revoke role')
                                )
                        
                        except User.DoesNotExist:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Row {row_num}: User "{username}" not found')
                            )
                        except RoleDefinition.DoesNotExist:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Row {row_num}: Role "{role_name}" not found')
                            )
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Row {row_num}: {str(e)}')
                            )
        
        except FileNotFoundError:
            raise CommandError(f'File "{file_path}" not found')
        except Exception as e:
            raise CommandError(f'Error processing file: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Completed: {success_count} successful, {error_count} errors')
        )

    def handle_list(self, options):
        """List users with their roles"""
        role_type = options.get('role_type')
        output_file = options.get('output')
        
        queryset = User.objects.prefetch_related('role_assignments__role_definition')
        
        if role_type:
            queryset = queryset.filter(
                role_assignments__role__role_type=role_type,
                role_assignments__status=UserRoleAssignment.AssignmentStatus.ACTIVE
            ).distinct()
        
        users_data = []
        
        for user in queryset:
            active_roles = user.role_assignments.filter(status=UserRoleAssignment.AssignmentStatus.ACTIVE)  # type: ignore[attr-defined]
            roles_info = []
            
            for assignment in active_roles:
                roles_info.append({
                    'role_name': assignment.role.name,
                    'role_type': assignment.role.role_type,
                    'level': assignment.role.hierarchy_level,
                    'assigned_at': assignment.assigned_at.isoformat(),
                    'expires_at': assignment.effective_until.isoformat() if assignment.effective_until else None,
                })
            
            user_data = {
                'username': user.username,  # type: ignore[attr-defined]
                'email': user.email,  # type: ignore[attr-defined]
                'full_name': user.get_full_name(),  # type: ignore[attr-defined]
                'is_active': user.is_active,  # type: ignore[attr-defined]
                'roles': roles_info
            }
            users_data.append(user_data)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)
            self.stdout.write(f'User data exported to: {output_file}')
        else:
            for user_data in users_data:
                self.stdout.write(f'\nUser: {user_data["username"]} ({user_data["email"]})')
                if user_data['roles']:
                    for role in user_data['roles']:
                        expires = f' (expires: {role["expires_at"]})' if role['expires_at'] else ''
                        self.stdout.write(f'  - {role["role_name"]} (Level {role["level"]}){expires}')
                else:
                    self.stdout.write('  - No active roles')
        
        self.stdout.write(f'\nTotal users: {len(users_data)}')

    def handle_export(self, options):
        """Export role assignments to CSV"""
        output_file = options['output']
        role_type = options.get('role_type')
        
        queryset = UserRoleAssignment.objects.select_related(
            'user', 'role', 'assigned_by'
        ).filter(status=UserRoleAssignment.AssignmentStatus.ACTIVE)
        
        if role_type:
            queryset = queryset.filter(role__role_type=role_type)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'username', 'email', 'full_name', 'role_name', 'role_type', 
                'role_level', 'assigned_by', 'assigned_at', 'expires_at', 'reason'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for assignment in queryset:
                writer.writerow({
                    'username': assignment.user.username,
                    'email': assignment.user.email,
                    'full_name': assignment.user.get_full_name(),
                    'role_name': assignment.role.name,
                    'role_type': assignment.role.role_type,
                    'role_level': assignment.role.hierarchy_level,
                    'assigned_by': assignment.assigned_by.username if assignment.assigned_by else '',
                    'assigned_at': assignment.assigned_at.isoformat(),
                    'expires_at': assignment.effective_until.isoformat() if assignment.effective_until else '',
                    'reason': assignment.assignment_reason or '',
                })
        
        self.stdout.write(f'Role assignments exported to: {output_file}')
        self.stdout.write(f'Total assignments exported: {queryset.count()}')

    def handle_clean_expired(self, options):
        """Clean expired role assignments"""
        dry_run = options['dry_run']
        
        from django.utils import timezone
        now = timezone.now()
        
        expired_assignments = UserRoleAssignment.objects.filter(
            status=UserRoleAssignment.AssignmentStatus.ACTIVE,
            effective_until__lt=now
        )
        
        count = expired_assignments.count()
        
        if dry_run:
            self.stdout.write(f'Would deactivate {count} expired role assignments:')
            for assignment in expired_assignments:
                self.stdout.write(
                    f'  - {assignment.user.username}: {assignment.role.name} '
                    f'(expired: {assignment.effective_until})'
                )
        else:
            updated = expired_assignments.update(status=UserRoleAssignment.AssignmentStatus.EXPIRED)
            self.stdout.write(f'Deactivated {updated} expired role assignments')
        
        if count == 0:
            self.stdout.write('No expired role assignments found')