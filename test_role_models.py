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
    # Try to import the models
    from role_management.models import RoleDefinition, UserRoleAssignment, RoleChangeHistory, RolePermissionGroup, RolePermissionAssignment, UserRoleRequest
    
    print("✅ All role management models imported successfully!")
    
    # Try to create a simple role definition
    role, created = RoleDefinition.objects.get_or_create(
        name='student',
        defaults={
            'display_name': 'Student',
            'description': 'A student user',
            'hierarchy_level': 10
        }
    )
    
    if created:
        print(f"✅ Created role: {role.display_name}")
    else:
        print(f"✅ Found existing role: {role.display_name}")
        
    print("🎉 Role management system is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()