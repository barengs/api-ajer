from django.core.management.base import BaseCommand
from django.urls import reverse
from django.conf import settings

class Command(BaseCommand):
    help = 'Test profile endpoints'

    def handle(self, *args, **options):
        self.stdout.write('Testing profile endpoints...')
        
        try:
            # Test URL resolution
            profile_url = reverse('user_profile')
            self.stdout.write(self.style.SUCCESS(f'Profile URL: {profile_url}'))
            
            profile_detail_url = reverse('user_profile_detail')
            self.stdout.write(self.style.SUCCESS(f'Profile detail URL: {profile_detail_url}'))
            
            self.stdout.write(self.style.SUCCESS('All profile endpoints are properly configured!'))
            
            # Show available endpoints
            self.stdout.write('\nAvailable profile endpoints:')
            self.stdout.write('  GET/PUT /api/v1/auth/profile/ - Basic user profile')
            self.stdout.write('  GET/PUT /api/v1/auth/profile/detail/ - Detailed user profile')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing profile endpoints: {e}'))
            import traceback
            traceback.print_exc()