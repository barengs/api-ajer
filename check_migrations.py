#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')

# Setup Django
django.setup()

try:
    # Import migration modules
    from django.db.migrations.executor import MigrationExecutor
    from django.db import connections, DEFAULT_DB_ALIAS
    
    # Get the default database connection
    connection = connections[DEFAULT_DB_ALIAS]
    
    # Create a migration executor
    executor = MigrationExecutor(connection)
    
    # Get the migration plan
    targets = executor.loader.graph.leaf_nodes()
    plan = executor.migration_plan(targets)
    
    print(f"Migration plan has {len(plan)} migrations to apply")
    
    # Check if role_management migrations are in the plan
    role_migrations = [migration for migration in plan if migration[0].app_label == 'role_management']
    print(f"Role management migrations to apply: {len(role_migrations)}")
    
    for migration, backwards in role_migrations:
        print(f"  - {migration.app_label}.{migration.name}")
        
    # Check which migrations have been applied
    applied_migrations = executor.loader.applied_migrations
    role_applied = [migration for migration in applied_migrations if migration[0] == 'role_management']
    print(f"\nApplied role management migrations: {len(role_applied)}")
    
    for app_label, migration_name in role_applied:
        print(f"  - {app_label}.{migration_name}")
        
    print("\n🎉 Migration check completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()