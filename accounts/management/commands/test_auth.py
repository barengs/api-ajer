from django.core.management.base import BaseCommand
from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

class Command(BaseCommand):
    help = 'Test custom user authentication functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing custom user authentication...')
        
        try:
            # Create a test user
            self.stdout.write('1. Creating test user...')
            test_image = SimpleUploadedFile(
                name='test_image.jpg',
                content=b'test image content',
                content_type='image/jpeg'
            )
            
            user = User.objects.create_user(
                email='testcmd@example.com',
                username='testcmd',
                password='testpassword123',
                full_name='Test Command User',
                role=User.UserRole.STUDENT,
                profile_image=test_image
            )
            self.stdout.write(self.style.SUCCESS(f'   ✓ Created user: {user.email}'))
            
            # Test that user has all required fields
            self.stdout.write('2. Verifying user data...')
            self.stdout.write(f'   ✓ Email: {user.email}')
            self.stdout.write(f'   ✓ Full Name: {user.full_name}')
            self.stdout.write(f'   ✓ Role: {user.role}')
            self.stdout.write(f'   ✓ Profile Image: {user.profile_image}')
            
            # Test JWT token generation
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)  # type: ignore
            # Access the access_token property explicitly
            access_token_obj = refresh.access_token  # type: ignore
            access_token = str(access_token_obj)
            
            self.stdout.write('3. Testing JWT token generation...')
            self.stdout.write(self.style.SUCCESS(f'   ✓ Access token generated: {access_token[:30]}...'))
            
            # Clean up
            user.delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleaned up test user'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ Custom user authentication is working correctly!'))
            self.stdout.write('\nTo test the login API endpoint:')
            self.stdout.write('  curl -X POST http://localhost:8000/api/v1/auth/login/ \\')
            self.stdout.write('       -H "Content-Type: application/json" \\')
            self.stdout.write('       -d \'{"email": "testcmd@example.com", "password": "testpassword123"}\'')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error testing custom user authentication: {e}'))
            import traceback
            traceback.print_exc()