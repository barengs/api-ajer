#!/usr/bin/env python
"""
Simple script to verify that role management models can be imported and used
"""
import os
import sys
import django
from django.conf import settings

def setup_django():
    """Setup Django environment"""
    # Add the project directory to the Python path
    sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')
    
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
    
    # Setup Django
    django.setup()

def test_models():
    """Test that role management models can be imported"""
    try:
        print("Testing role management models...")
        
        # Import models
        from role_management.models import (
            RoleDefinition, 
            UserRoleAssignment, 
            RoleChangeHistory, 
            RolePermissionGroup, 
            RolePermissionAssignment, 
            UserRoleRequest
        )
        
        print("✅ All models imported successfully!")
        
        # Test creating a role definition
        role_def = RoleDefinition(
            name='student',
            display_name='Student',
            description='A student user',
            hierarchy_level=10
        )
        print(f"✅ RoleDefinition instance created: {role_def.name}")
        
        # Test creating other model instances
        perm_group = RolePermissionGroup(
            name='basic_permissions',
            description='Basic permissions for all users'
        )
        print(f"✅ RolePermissionGroup instance created: {perm_group.name}")
        
        print("🎉 All tests passed! Role management models are working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("Setting up Django environment...")
    setup_django()
    
    print("Running model tests...")
    success = test_models()
    
    if success:
        print("\n✅ Verification completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Verification failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()