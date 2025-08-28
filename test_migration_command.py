#!/usr/bin/env python
"""
Test command to verify the migration fix
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS

def test_migration():
    """Test if the migration can be loaded and planned successfully"""
    try:
        # Create migration executor
        connection = connections[DEFAULT_DB_ALIAS]
        executor = MigrationExecutor(connection)
        
        # Get the migration loader
        loader = executor.loader
        
        # Check if our migration exists
        migration_name = ('role_management', '0002_rolepermissionassignment_and_more')
        if migration_name in loader.graph.nodes:
            print("✅ Migration found in migration graph")
            
            # Get the migration
            migration = loader.graph.nodes[migration_name]
            print(f"✅ Migration loaded successfully: {migration}")
            
            # Check operations
            print(f"Number of operations: {len(migration.operations)}")
            
            # Look for the status field operation
            status_field_op = None
            user_status_index_op = None
            role_status_index_op = None
            
            for i, op in enumerate(migration.operations):
                # Check for AddField operation for status field
                if (hasattr(op, 'name') and op.name == 'status' and 
                    hasattr(op, 'model_name') and op.model_name == 'userroleassignment'):
                    status_field_op = (i, op)
                
                # Check for AddIndex operations on status field
                elif (hasattr(op, 'model_name') and op.model_name == 'userroleassignment' and
                      hasattr(op, 'index')):
                    fields = getattr(op.index, 'fields', [])
                    if 'status' in fields and 'user' in fields:
                        user_status_index_op = (i, op)
                    elif 'status' in fields and 'role' in fields:
                        role_status_index_op = (i, op)
            
            print(f"Status field operation: {status_field_op[0] if status_field_op else 'Not found'}")
            print(f"User-status index operation: {user_status_index_op[0] if user_status_index_op else 'Not found'}")
            print(f"Role-status index operation: {role_status_index_op[0] if role_status_index_op else 'Not found'}")
            
            # Verify order
            if (status_field_op and user_status_index_op and role_status_index_op):
                if (status_field_op[0] < user_status_index_op[0] and 
                    status_field_op[0] < role_status_index_op[0]):
                    print("✅ Status field is correctly ordered before the indexes!")
                    return True
                else:
                    print("❌ Status field is NOT correctly ordered before the indexes!")
                    return False
            else:
                print("⚠️  Could not find all required operations to verify order")
                return False
        else:
            print("❌ Migration not found in migration graph")
            return False
            
    except Exception as e:
        print(f"Error testing migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_migration()
    if success:
        print("\n🎉 Migration fix verification successful!")
    else:
        print("\n💥 Migration fix verification failed!")