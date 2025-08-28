#!/usr/bin/env python
"""
Test script to verify the migration fix for the status field issue
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

print("Django setup completed successfully!")

# Try to import the migration module using importlib
try:
    import importlib
    migration_module = importlib.import_module('role_management.migrations.0002_rolepermissionassignment_and_more')
    Migration = getattr(migration_module, 'Migration')
    print("Migration module imported successfully!")
    
    # Check if the operations are in the correct order
    operations = Migration.operations
    
    # Find the index of the AddField operation for 'status' field
    status_field_index = None
    user_status_index_index = None
    role_status_index_index = None
    
    for i, operation in enumerate(operations):
        if hasattr(operation, 'name') and operation.name == 'status' and hasattr(operation, 'model_name') and operation.model_name == 'userroleassignment':
            status_field_index = i
        elif hasattr(operation, 'model_name') and operation.model_name == 'userroleassignment' and hasattr(operation, 'index'):
            # Check if this is an index on user and status or role and status
            fields = getattr(operation.index, 'fields', [])
            if 'status' in fields and 'user' in fields:
                user_status_index_index = i
            elif 'status' in fields and 'role' in fields:
                role_status_index_index = i
    
    print(f"Status field add operation index: {status_field_index}")
    print(f"User-status index operation index: {user_status_index_index}")
    print(f"Role-status index operation index: {role_status_index_index}")
    
    # Verify that the status field is added before the indexes
    if status_field_index is not None and user_status_index_index is not None and role_status_index_index is not None:
        if status_field_index < user_status_index_index and status_field_index < role_status_index_index:
            print("✅ Status field is correctly added before the indexes that reference it!")
        else:
            print("❌ Status field is NOT added before the indexes that reference it!")
    else:
        print("⚠️  Could not find all required operations to verify order")
        
except Exception as e:
    print(f"Error importing migration module: {e}")
    import traceback
    traceback.print_exc()