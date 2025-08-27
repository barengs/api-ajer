from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Apply navigation migrations'

    def handle(self, *args, **options):
        self.stdout.write('Applying role_management migrations...')
        try:
            call_command('migrate', 'role_management')
            self.stdout.write(
                self.style.SUCCESS('Successfully applied role_management migrations')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error applying role_management migrations: {e}')
            )
        
        self.stdout.write('Applying navigation migrations...')
        try:
            call_command('migrate', 'navigation')
            self.stdout.write(
                self.style.SUCCESS('Successfully applied navigation migrations')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error applying navigation migrations: {e}')
            )