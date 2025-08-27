#!/usr/bin/env python
"""
Script to fix migration dependency issues for gamification module.
This script resets migration states and reapplies them in the correct order.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection
from django.core.management.color import no_style

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
    django.setup()

def check_database_connection():
    """Check if database connection is working"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_migration_table():
    """Check if django_migrations table exists"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='django_migrations'
            """)
            result = cursor.fetchone()
            if result:
                print("✅ Django migrations table found")
                return True
            else:
                print("❌ Django migrations table not found")
                return False
    except Exception as e:
        print(f"❌ Error checking migrations table: {e}")
        return False

def show_current_migration_state():
    """Show current migration state for relevant apps"""
    print("\n📋 Current migration state:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app IN ('accounts', 'courses', 'lessons', 'assignments', 'gamification', 'payments', 'live_sessions')
                ORDER BY app, name
            """)
            results = cursor.fetchall()
            
            if not results:
                print("   No migrations found for relevant apps")
                return
                
            current_app = None
            for app, name, applied in results:
                if app != current_app:
                    print(f"\n{app}:")
                    current_app = app
                status = "✅" if applied else "❌"
                print(f"  {status} {name}")
                
    except Exception as e:
        print(f"❌ Error showing migration state: {e}")

def fix_migration_dependencies():
    """Fix migration dependency issues"""
    print("\n🔧 Fixing migration dependencies...")
    
    # Step 1: Reset problematic migrations
    print("\n1️⃣ Resetting migration states...")
    
    # Apps to reset in dependency order (reverse)
    apps_to_reset = ['gamification', 'payments', 'live_sessions', 'assignments', 'lessons']
    
    for app in apps_to_reset:
        try:
            print(f"   Resetting {app} migrations...")
            execute_from_command_line(['manage.py', 'migrate', '--fake', app, 'zero'])
            print(f"   ✅ {app} migrations reset")
        except Exception as e:
            print(f"   ❌ Error resetting {app}: {e}")
    
    # Step 2: Reapply migrations in correct order
    print("\n2️⃣ Reapplying migrations in correct order...")
    
    # Apps to apply in dependency order
    apps_to_apply = ['accounts', 'courses', 'lessons', 'assignments', 'gamification', 'payments', 'live_sessions']
    
    for app in apps_to_apply:
        try:
            print(f"   Applying {app} migrations...")
            execute_from_command_line(['manage.py', 'migrate', app])
            print(f"   ✅ {app} migrations applied")
        except Exception as e:
            print(f"   ❌ Error applying {app} migrations: {e}")
            # Continue with other apps even if one fails
    
    print("\n✅ Migration dependency fix completed!")

def main():
    """Main function to fix migration issues"""
    print("🔄 Django Migration Dependency Fixer")
    print("=" * 50)
    
    # Setup Django
    setup_django()
    
    # Check database connection
    if not check_database_connection():
        return 1
    
    # Check migration table
    if not check_migration_table():
        print("Creating initial migration state...")
        try:
            execute_from_command_line(['manage.py', 'migrate'])
            return 0
        except Exception as e:
            print(f"❌ Error creating migrations: {e}")
            return 1
    
    # Show current state
    show_current_migration_state()
    
    # Ask for confirmation
    print("\n⚠️  This will reset and reapply migrations. Continue? (y/N): ", end="")
    if input().lower() != 'y':
        print("Operation cancelled")
        return 0
    
    # Fix dependencies
    fix_migration_dependencies()
    
    # Show final state
    print("\n📋 Final migration state:")
    show_current_migration_state()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())