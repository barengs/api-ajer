from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Fix migration dependency issues for gamification module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('🔄 Fixing Migration Dependencies')
        )
        self.stdout.write('=' * 50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Step 1: Show current migration state
        self.show_migration_state()
        
        if not dry_run:
            # Step 2: Reset problematic migrations
            self.reset_migrations()
            
            # Step 3: Reapply migrations in correct order
            self.apply_migrations()
            
            # Step 4: Show final state
            self.stdout.write('\n📋 Final migration state:')
            self.show_migration_state()
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Migration fix completed!')
            )
        else:
            self.stdout.write('\nTo apply the fix, run: python manage.py fix_migration_deps')

    def show_migration_state(self):
        """Show current migration state"""
        self.stdout.write('\n📋 Current migration state:')
        
        apps = ['accounts', 'courses', 'lessons', 'assignments', 'gamification', 'payments', 'live_sessions']
        
        try:
            with connection.cursor() as cursor:
                for app in apps:
                    cursor.execute(
                        "SELECT name FROM django_migrations WHERE app = %s ORDER BY name",
                        [app]
                    )
                    migrations = cursor.fetchall()
                    
                    self.stdout.write(f"\n{app}:")
                    if migrations:
                        for (name,) in migrations:
                            self.stdout.write(f"  ✅ {name}")
                    else:
                        self.stdout.write(f"  ❌ No migrations applied")
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error checking migration state: {e}")
            )

    def reset_migrations(self):
        """Reset problematic migrations"""
        self.stdout.write('\n1️⃣ Resetting migration states...')
        
        # Apps to reset in reverse dependency order
        apps_to_reset = ['live_sessions', 'payments', 'gamification', 'assignments', 'lessons']
        
        for app in apps_to_reset:
            try:
                self.stdout.write(f"   Resetting {app}...")
                call_command('migrate', app, 'zero', '--fake', verbosity=0)
                self.stdout.write(f"   ✅ {app} reset")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error resetting {app}: {e}")
                )

    def apply_migrations(self):
        """Apply migrations in correct order"""
        self.stdout.write('\n2️⃣ Applying migrations in correct order...')
        
        # Apps to apply in dependency order
        apps_to_apply = ['accounts', 'courses', 'lessons', 'assignments', 'gamification', 'payments', 'live_sessions']
        
        for app in apps_to_apply:
            try:
                self.stdout.write(f"   Applying {app}...")
                call_command('migrate', app, verbosity=0)
                self.stdout.write(f"   ✅ {app} applied")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error applying {app}: {e}")
                )
                # Continue with other apps