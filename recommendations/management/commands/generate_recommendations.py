from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from ...services import recommendation_service
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Generate AI-powered recommendations for all users or specific users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate recommendations for a specific user ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate recommendations for all users'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if recommendations are not expired'
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        all_users = options.get('all')
        force_refresh = options.get('force')
        
        if not user_id and not all_users:
            self.stdout.write(
                self.style.ERROR(
                    'Please specify either --user-id or --all flag'
                )
            )
            return
        
        users = []
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                users.append(user)
                self.stdout.write(
                    f'Generating recommendations for user: {user.email}'
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'User with ID {user_id} does not exist'
                    )
                )
                return
        elif all_users:
            users = User.objects.all()
            self.stdout.write(
                f'Generating recommendations for all {users.count()} users'
            )
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                recommendations = recommendation_service.generate_recommendations(
                    user, force_refresh=force_refresh
                )
                self.stdout.write(
                    f'Generated {len(recommendations)} recommendations for {user.email}'
                )
                success_count += 1
            except Exception as e:
                logger.error(f'Error generating recommendations for {user.email}: {e}')
                self.stdout.write(
                    self.style.ERROR(
                        f'Error generating recommendations for {user.email}: {e}'
                    )
                )
                error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated recommendations for {success_count} users. '
                f'Errors: {error_count}'
            )
        )