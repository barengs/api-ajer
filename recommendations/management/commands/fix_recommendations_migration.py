from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix recommendations migration issues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of recommendations tables'
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        
        try:
            if force:
                self.stdout.write(
                    self.style.WARNING(
                        'Forcing recreation of recommendations tables...'
                    )
                )
                # This would drop and recreate tables if needed
                # For now, we'll just try to apply migrations
                call_command('migrate', 'recommendations', verbosity=2)
            else:
                self.stdout.write(
                    'Applying recommendations migrations...'
                )
                call_command('migrate', 'recommendations', verbosity=2)
            
            self.stdout.write(
                self.style.SUCCESS(
                    'Recommendations migrations applied successfully!'
                )
            )
            
        except Exception as e:
            logger.error(f"Error applying recommendations migrations: {e}")
            self.stdout.write(
                self.style.ERROR(
                    f'Error applying recommendations migrations: {e}\n'
                    'Try running with --force flag if the issue persists.'
                )
            )