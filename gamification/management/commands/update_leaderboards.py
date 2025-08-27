from django.core.management.base import BaseCommand
from gamification.utils import update_leaderboards
from gamification.models import Leaderboard


class Command(BaseCommand):
    help = 'Update all leaderboards or specific leaderboard'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            help='Update specific leaderboard type'
        )
    
    def handle(self, *args, **options):
        leaderboard_type = options.get('type')
        
        if leaderboard_type:
            try:
                leaderboard = Leaderboard.objects.get(
                    leaderboard_type=leaderboard_type,
                    is_active=True
                )
                self.stdout.write(f'Updating {leaderboard.name}...')
                from gamification.utils import update_leaderboard
                update_leaderboard(leaderboard)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {leaderboard.name} updated successfully')
                )
            except Leaderboard.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Leaderboard type "{leaderboard_type}" not found')
                )
        else:
            self.stdout.write('Updating all leaderboards...')
            update_leaderboards()
            self.stdout.write(
                self.style.SUCCESS('✓ All leaderboards updated successfully')
            )