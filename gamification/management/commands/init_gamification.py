from django.core.management.base import BaseCommand
from gamification.utils import (
    create_default_badges, create_default_levels, create_default_leaderboards
)
from gamification.models import Achievement


class Command(BaseCommand):
    help = 'Initialize gamification system with default data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing data'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing gamification system...')
        
        # Create default levels
        self.stdout.write('Creating default user levels...')
        create_default_levels()
        self.stdout.write(self.style.SUCCESS('✓ User levels created'))
        
        # Create default badges
        self.stdout.write('Creating default badges...')
        create_default_badges()
        self.stdout.write(self.style.SUCCESS('✓ Badge types created'))
        
        # Create default leaderboards
        self.stdout.write('Creating default leaderboards...')
        create_default_leaderboards()
        self.stdout.write(self.style.SUCCESS('✓ Leaderboards created'))
        
        # Create default achievements
        self.stdout.write('Creating default achievements...')
        self._create_default_achievements()
        self.stdout.write(self.style.SUCCESS('✓ Achievements created'))
        
        self.stdout.write(
            self.style.SUCCESS('Gamification system initialized successfully!')
        )
    
    def _create_default_achievements(self):
        """Create default achievements"""
        default_achievements = [
            {
                'name': 'First Steps',
                'description': 'Complete your first lesson',
                'achievement_type': 'milestone',
                'requirements': {'lessons_completed': 1},
                'points_reward': 10,
                'is_hidden': False
            },
            {
                'name': 'Learning Machine',
                'description': 'Complete 50 lessons',
                'achievement_type': 'milestone',
                'requirements': {'lessons_completed': 50},
                'points_reward': 50,
                'is_hidden': False
            },
            {
                'name': 'Course Master',
                'description': 'Complete 5 courses',
                'achievement_type': 'milestone',
                'requirements': {'courses_completed': 5},
                'points_reward': 100,
                'is_hidden': False
            },
            {
                'name': 'Speed Learner',
                'description': 'Complete a course in under 7 days',
                'achievement_type': 'speed',
                'requirements': {'course_completion_days': 7},
                'points_reward': 75,
                'is_hidden': False
            },
            {
                'name': 'Perfectionist',
                'description': 'Get perfect scores on 10 quizzes',
                'achievement_type': 'excellence',
                'requirements': {'perfect_scores': 10},
                'points_reward': 100,
                'is_hidden': False
            },
            {
                'name': 'Social Butterfly',
                'description': 'Make 25 forum posts',
                'achievement_type': 'social',
                'requirements': {'forum_posts': 25},
                'points_reward': 50,
                'is_hidden': False
            },
            {
                'name': 'Helper',
                'description': 'Get 10 helpful votes on forum replies',
                'achievement_type': 'social',
                'requirements': {'helpful_replies': 10},
                'points_reward': 75,
                'is_hidden': False
            },
            {
                'name': 'Streak Master',
                'description': 'Maintain a 30-day login streak',
                'achievement_type': 'consistency',
                'requirements': {'login_streak': 30},
                'points_reward': 150,
                'is_hidden': False
            },
            {
                'name': 'Point Collector',
                'description': 'Earn 1000 total points',
                'achievement_type': 'milestone',
                'requirements': {'total_points': 1000},
                'points_reward': 100,
                'is_hidden': False
            },
            {
                'name': 'Legend',
                'description': 'Reach level 10',
                'achievement_type': 'milestone',
                'requirements': {'level': 10},
                'points_reward': 500,
                'is_hidden': True
            }
        ]
        
        for achievement_data in default_achievements:
            Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )