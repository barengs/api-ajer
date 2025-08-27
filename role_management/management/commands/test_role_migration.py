from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
import sys


class Command(BaseCommand):
    help = 'Test role management migration status'

    def handle(self, *args, **options):
        try:
            # Force output to stderr to bypass any stdout issues
            sys.stderr.write("Testing role management migration status...\n")
            sys.stderr.flush()
            
            # Create a migration executor
            executor = MigrationExecutor(connection)
            
            # Get unapplied migrations
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            
            sys.stderr.write(f"Total migrations to apply: {len(plan)}\n")
            sys.stderr.flush()
            
            # Filter for role_management migrations
            role_migrations = [migration for migration, backwards in plan if migration.app_label == 'role_management']
            sys.stderr.write(f"Role management migrations to apply: {len(role_migrations)}\n")
            sys.stderr.flush()
            
            for migration in role_migrations:
                sys.stderr.write(f"  - {migration.app_label}.{migration.name}\n")
                sys.stderr.flush()
                
            # Check applied migrations
            applied_migrations = executor.loader.applied_migrations
            role_applied = [migration for migration in applied_migrations if migration[0] == 'role_management']
            sys.stderr.write(f"Applied role management migrations: {len(role_applied)}\n")
            sys.stderr.flush()
            
            for app_label, migration_name in role_applied:
                sys.stderr.write(f"  - {app_label}.{migration_name}\n")
                sys.stderr.flush()
                
            sys.stderr.write('Successfully checked migration status!\n')
            sys.stderr.flush()
            
        except Exception as e:
            sys.stderr.write(f'Error checking migration status: {e}\n')
            import traceback
            sys.stderr.write(traceback.format_exc())
            sys.stderr.flush()