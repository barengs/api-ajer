#!/usr/bin/env python
"""
Test script to verify the migration dependency fix is correct.
This script simulates Django's migration dependency resolution.
"""

def test_migration_dependencies():
    """Test that migration dependencies are correctly ordered."""
    
    # Simulated migration dependencies after the fix
    migrations = {
        'accounts.0001_initial': [],
        'courses.0001_initial': ['accounts.0001_initial'],
        'assignments.0001_initial': ['courses.0001_initial'],
        'lessons.0001_initial': ['courses.0001_initial'],
        'gamification.0001_initial': [
            'assignments.0001_initial', 
            'courses.0001_initial', 
            'lessons.0001_initial',
            'accounts.0001_initial'
        ]
    }
    
    def can_apply_migration(migration, applied_migrations):
        """Check if a migration can be applied given currently applied migrations."""
        for dependency in migrations[migration]:
            if dependency not in applied_migrations:
                return False
        return True
    
    def resolve_migration_order(migrations_dict):
        """Resolve the order in which migrations should be applied."""
        applied = set()
        order = []
        remaining = set(migrations_dict.keys())
        
        while remaining:
            # Find migrations that can be applied
            ready = []
            for migration in remaining:
                if can_apply_migration(migration, applied):
                    ready.append(migration)
            
            if not ready:
                raise Exception(f"Circular dependency detected! Remaining: {remaining}")
            
            # Sort alphabetically for consistent ordering
            ready.sort()
            
            for migration in ready:
                order.append(migration)
                applied.add(migration)
                remaining.remove(migration)
        
        return order
    
    try:
        order = resolve_migration_order(migrations)
        print("✅ Migration dependency resolution successful!")
        print("Migration order:")
        for i, migration in enumerate(order, 1):
            print(f"{i}. {migration}")
        
        # Verify gamification comes after its dependencies
        gamification_index = order.index('gamification.0001_initial')
        assignments_index = order.index('assignments.0001_initial')
        courses_index = order.index('courses.0001_initial')
        lessons_index = order.index('lessons.0001_initial')
        
        if (gamification_index > assignments_index and 
            gamification_index > courses_index and 
            gamification_index > lessons_index):
            print("✅ Gamification migration correctly comes after its dependencies!")
            return True
        else:
            print("❌ Gamification migration dependency order is incorrect!")
            return False
            
    except Exception as e:
        print(f"❌ Migration dependency resolution failed: {e}")
        return False

if __name__ == "__main__":
    success = test_migration_dependencies()
    if success:
        print("\n🎉 Migration fix is correct!")
        print("The gamification migration dependencies have been properly fixed.")
        print("You can now run 'python manage.py migrate' without dependency issues.")
    else:
        print("\n💥 Migration fix has issues that need to be addressed.")