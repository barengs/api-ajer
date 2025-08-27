from typing import Dict, Any, List
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta

from .models import (
    BadgeType, UserBadge, PointsTransaction, UserStats, 
    Achievement, UserAchievement, LeaderboardEntry, Leaderboard
)

User = get_user_model()


# Points configuration
POINTS_CONFIG = {
    'lesson_complete': 10,
    'assignment_submit': 20,
    'quiz_pass': 15,
    'quiz_perfect': 25,
    'forum_post': 5,
    'forum_reply': 3,
    'helpful_reply': 10,
    'course_complete': 100,
    'first_course': 50,
    'daily_login': 2,
    'referral': 100,
}


def get_or_create_user_stats(user) -> UserStats:
    """Get or create user stats"""
    stats, created = UserStats.objects.get_or_create(user=user)
    if created:
        # Initialize with current level
        from .models import UserLevel
        initial_level = UserLevel.objects.filter(min_points=0).first()
        if initial_level:
            stats.current_level = initial_level
            stats.save()
    return stats


def award_points(user, points: int, transaction_type: str, description: str, **kwargs):
    """Award points to user and update stats"""
    stats = get_or_create_user_stats(user)
    stats.add_points(points, transaction_type, description, **kwargs)
    return stats


def check_user_badges(user):
    """Check and award badges for user based on their stats"""
    stats = get_or_create_user_stats(user)
    awarded_badges = []
    
    # Define badge criteria
    badge_criteria = {
        # Learning badges
        'First Steps': lambda s: s.lessons_completed >= 1,
        'Learning Enthusiast': lambda s: s.lessons_completed >= 10,
        'Knowledge Seeker': lambda s: s.lessons_completed >= 50,
        'Master Learner': lambda s: s.lessons_completed >= 100,
        
        'Assignment Starter': lambda s: s.assignments_submitted >= 1,
        'Assignment Pro': lambda s: s.assignments_submitted >= 10,
        'Assignment Master': lambda s: s.assignments_submitted >= 25,
        
        'Quiz Rookie': lambda s: s.quizzes_passed >= 1,
        'Quiz Expert': lambda s: s.quizzes_passed >= 20,
        'Quiz Champion': lambda s: s.quizzes_passed >= 50,
        
        'Course Finisher': lambda s: s.courses_completed >= 1,
        'Course Collector': lambda s: s.courses_completed >= 5,
        'Course Master': lambda s: s.courses_completed >= 10,
        
        # Social badges
        'Conversation Starter': lambda s: s.forum_posts >= 1,
        'Community Member': lambda s: s.forum_posts >= 10,
        'Community Leader': lambda s: s.forum_posts >= 50,
        
        'Helpful Member': lambda s: s.helpful_replies >= 5,
        'Super Helper': lambda s: s.helpful_replies >= 20,
        
        # Achievement badges
        'Perfectionist': lambda s: s.perfect_scores >= 5,
        'Overachiever': lambda s: s.perfect_scores >= 15,
        
        'Streak Starter': lambda s: s.current_login_streak >= 7,
        'Dedication': lambda s: s.longest_login_streak >= 30,
        'Commitment': lambda s: s.longest_login_streak >= 100,
        
        # Points badges
        'Point Collector': lambda s: s.total_points >= 100,
        'Point Hunter': lambda s: s.total_points >= 500,
        'Point Master': lambda s: s.total_points >= 1000,
        'Point Legend': lambda s: s.total_points >= 5000,
    }
    
    for badge_name, criteria in badge_criteria.items():
        try:
            badge_type = BadgeType.objects.get(name=badge_name, is_active=True)
            
            # Check if user already has this badge
            if not UserBadge.objects.filter(user=user, badge_type=badge_type).exists():
                # Check if criteria is met
                if criteria(stats):
                    UserBadge.objects.create(
                        user=user,
                        badge_type=badge_type,
                        metadata={'auto_awarded': True, 'stats_snapshot': {
                            'total_points': stats.total_points,
                            'courses_completed': stats.courses_completed,
                            'lessons_completed': stats.lessons_completed,
                        }}
                    )
                    awarded_badges.append(badge_type)
        except BadgeType.DoesNotExist:
            # Badge type doesn't exist, skip
            continue
    
    return awarded_badges


def calculate_achievement_progress(user, achievement) -> Dict[str, Any]:
    """Calculate user's progress toward an achievement"""
    stats = get_or_create_user_stats(user)
    requirements = achievement.requirements
    progress = {}
    
    if not requirements:
        return progress
    
    # Common progress calculations
    if 'total_points' in requirements:
        progress['points'] = {
            'current': stats.total_points,
            'required': requirements['total_points'],
            'percentage': min(100, (stats.total_points / requirements['total_points']) * 100)
        }
    
    if 'courses_completed' in requirements:
        progress['courses'] = {
            'current': stats.courses_completed,
            'required': requirements['courses_completed'],
            'percentage': min(100, (stats.courses_completed / requirements['courses_completed']) * 100)
        }
    
    if 'login_streak' in requirements:
        progress['streak'] = {
            'current': stats.current_login_streak,
            'required': requirements['login_streak'],
            'percentage': min(100, (stats.current_login_streak / requirements['login_streak']) * 100)
        }
    
    if 'perfect_scores' in requirements:
        progress['perfect_scores'] = {
            'current': stats.perfect_scores,
            'required': requirements['perfect_scores'],
            'percentage': min(100, (stats.perfect_scores / requirements['perfect_scores']) * 100)
        }
    
    # Calculate overall progress
    if progress:
        total_percentage = sum(item['percentage'] for item in progress.values())
        progress['overall'] = total_percentage / len(progress)
    
    return progress


def check_user_achievements(user):
    """Check and award achievements for user"""
    awarded_achievements = []
    
    for achievement in Achievement.objects.filter(is_active=True):
        # Skip if user already has this achievement
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            continue
        
        progress = calculate_achievement_progress(user, achievement)
        
        # Check if all requirements are met (100% progress)
        if progress and progress.get('overall', 0) >= 100:
            user_achievement = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                progress_data=progress
            )
            
            # Award points and badge if specified
            if achievement.points_reward:
                award_points(
                    user,
                    achievement.points_reward,
                    PointsTransaction.TransactionType.BONUS,
                    f"Achievement: {achievement.name}",
                    metadata={'achievement_id': achievement.pk}  # type: ignore[attr-defined]
                )
            
            if achievement.badge_reward:
                UserBadge.objects.get_or_create(
                    user=user,
                    badge_type=achievement.badge_reward,
                    defaults={'metadata': {'achievement_reward': achievement.pk}}  # type: ignore[attr-defined]
                )
            
            awarded_achievements.append(achievement)
    
    return awarded_achievements


def update_leaderboards():
    """Update all active leaderboards"""
    for leaderboard in Leaderboard.objects.filter(is_active=True):
        update_leaderboard(leaderboard)


def update_leaderboard(leaderboard: Leaderboard):
    """Update a specific leaderboard"""
    # Clear existing entries
    LeaderboardEntry.objects.filter(leaderboard=leaderboard).delete()
    
    # Get data based on leaderboard type
    if leaderboard.leaderboard_type == Leaderboard.LeaderboardType.OVERALL_POINTS:
        users_data = UserStats.objects.select_related('user').order_by('-total_points')[:100]
        
        for rank, stats in enumerate(users_data, 1):
            LeaderboardEntry.objects.create(
                leaderboard=leaderboard,
                user=stats.user,
                rank=rank,
                score=stats.total_points,
                metadata={
                    'level': stats.current_level.name if stats.current_level else 'Beginner',
                    'courses_completed': stats.courses_completed,
                }
            )
    
    elif leaderboard.leaderboard_type == Leaderboard.LeaderboardType.MONTHLY_POINTS:
        # Points earned this month
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_points = PointsTransaction.objects.filter(
            created_at__gte=current_month,
            points__gt=0
        ).values('user').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')[:100]
        
        for rank, data in enumerate(monthly_points, 1):
            user = User.objects.get(id=data['user'])
            LeaderboardEntry.objects.create(
                leaderboard=leaderboard,
                user=user,
                rank=rank,
                score=data['total_points'],
                metadata={
                    'period': 'monthly',
                    'month': timezone.now().strftime('%Y-%m'),
                }
            )
    
    elif leaderboard.leaderboard_type == Leaderboard.LeaderboardType.COURSE_COMPLETION:
        users_data = UserStats.objects.select_related('user').order_by('-courses_completed')[:100]
        
        for rank, stats in enumerate(users_data, 1):
            LeaderboardEntry.objects.create(
                leaderboard=leaderboard,
                user=stats.user,
                rank=rank,
                score=stats.courses_completed,
                metadata={
                    'lessons_completed': stats.lessons_completed,
                    'completion_rate': calculate_completion_rate(stats.user),
                }
            )
    
    elif leaderboard.leaderboard_type == Leaderboard.LeaderboardType.FORUM_ACTIVITY:
        users_data = UserStats.objects.select_related('user').annotate(
            forum_score=F('forum_posts') + F('forum_replies') + (F('helpful_replies') * 2)
        ).order_by('-forum_score')[:100]
        
        for rank, stats in enumerate(users_data, 1):
            forum_score = stats.forum_posts + stats.forum_replies + (stats.helpful_replies * 2)
            LeaderboardEntry.objects.create(
                leaderboard=leaderboard,
                user=stats.user,
                rank=rank,
                score=forum_score,
                metadata={
                    'posts': stats.forum_posts,
                    'replies': stats.forum_replies,
                    'helpful_replies': stats.helpful_replies,
                }
            )
    
    elif leaderboard.leaderboard_type == Leaderboard.LeaderboardType.STREAK:
        users_data = UserStats.objects.select_related('user').order_by('-current_login_streak')[:100]
        
        for rank, stats in enumerate(users_data, 1):
            LeaderboardEntry.objects.create(
                leaderboard=leaderboard,
                user=stats.user,
                rank=rank,
                score=stats.current_login_streak,
                metadata={
                    'longest_streak': stats.longest_login_streak,
                    'last_login': stats.last_login_date.isoformat() if stats.last_login_date else None,
                }
            )
    
    # Update last reset time
    leaderboard.last_reset = timezone.now()
    leaderboard.save()


def calculate_completion_rate(user) -> float:
    """Calculate user's overall completion rate"""
    try:
        from courses.models import Enrollment
        from lessons.models import LessonProgress
        
        enrollments = Enrollment.objects.filter(user=user, is_active=True)
        if not enrollments:
            return 0.0
        
        total_lessons = 0
        completed_lessons = 0
        
        for enrollment in enrollments:
            course_lessons = enrollment.course.get_total_lessons()  # type: ignore[attr-defined]
            total_lessons += course_lessons
            
            completed = LessonProgress.objects.filter(
                student=user,
                lesson__section__course=enrollment.course,
                is_completed=True
            ).count()
            completed_lessons += completed
        
        return (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0
    
    except Exception:
        return 0.0


def get_user_rank(user, leaderboard_type: str) -> int:
    """Get user's rank in a specific leaderboard"""
    try:
        leaderboard = Leaderboard.objects.get(leaderboard_type=leaderboard_type, is_active=True)
        entry = LeaderboardEntry.objects.get(leaderboard=leaderboard, user=user)
        return entry.rank
    except (Leaderboard.DoesNotExist, LeaderboardEntry.DoesNotExist):
        return 0


def get_next_level_progress(user) -> Dict[str, Any]:
    """Get user's progress toward next level"""
    stats = get_or_create_user_stats(user)
    
    if not stats.current_level:
        return {}
    
    from .models import UserLevel
    next_level = UserLevel.objects.filter(
        level__gt=stats.current_level.level
    ).order_by('level').first()
    
    if not next_level:
        return {
            'is_max_level': True,
            'current_points': stats.total_points,
        }
    
    points_needed = next_level.min_points - stats.total_points
    progress_percentage = ((stats.total_points - stats.current_level.min_points) / 
                          (next_level.min_points - stats.current_level.min_points)) * 100
    
    return {
        'current_level': stats.current_level.level,
        'next_level': next_level.level,
        'current_points': stats.total_points,
        'points_needed': max(0, points_needed),
        'next_level_points': next_level.min_points,
        'progress_percentage': min(100, max(0, progress_percentage)),
        'next_level_name': next_level.name,
        'next_level_perks': next_level.perks,
    }


def create_default_badges():
    """Create default badge types"""
    default_badges = [
        # Learning badges
        {'name': 'First Steps', 'description': 'Completed your first lesson', 'category': 'learning', 'points_required': 0},
        {'name': 'Learning Enthusiast', 'description': 'Completed 10 lessons', 'category': 'learning', 'points_required': 100},
        {'name': 'Knowledge Seeker', 'description': 'Completed 50 lessons', 'category': 'learning', 'points_required': 500},
        {'name': 'Master Learner', 'description': 'Completed 100 lessons', 'category': 'learning', 'points_required': 1000},
        
        # Course completion badges
        {'name': 'Course Finisher', 'description': 'Completed your first course', 'category': 'achievement', 'points_required': 100},
        {'name': 'Course Collector', 'description': 'Completed 5 courses', 'category': 'achievement', 'points_required': 500},
        {'name': 'Course Master', 'description': 'Completed 10 courses', 'category': 'achievement', 'points_required': 1000},
        
        # Social badges
        {'name': 'Conversation Starter', 'description': 'Posted your first forum message', 'category': 'social', 'points_required': 5},
        {'name': 'Community Member', 'description': 'Posted 10 forum messages', 'category': 'social', 'points_required': 50},
        {'name': 'Community Leader', 'description': 'Posted 50 forum messages', 'category': 'social', 'points_required': 250},
        {'name': 'Helpful Member', 'description': 'Received 5 helpful votes', 'category': 'social', 'points_required': 50},
        
        # Achievement badges
        {'name': 'Perfectionist', 'description': 'Scored 100% on 5 quizzes', 'category': 'achievement', 'points_required': 125},
        {'name': 'Streak Starter', 'description': '7-day login streak', 'category': 'achievement', 'points_required': 14},
        {'name': 'Dedication', 'description': '30-day login streak', 'category': 'achievement', 'points_required': 60},
        
        # Points badges
        {'name': 'Point Collector', 'description': 'Earned 100 points', 'category': 'achievement', 'points_required': 100},
        {'name': 'Point Hunter', 'description': 'Earned 500 points', 'category': 'achievement', 'points_required': 500},
        {'name': 'Point Master', 'description': 'Earned 1000 points', 'category': 'achievement', 'points_required': 1000},
        {'name': 'Point Legend', 'description': 'Earned 5000 points', 'category': 'achievement', 'points_required': 5000},
    ]
    
    for badge_data in default_badges:
        BadgeType.objects.get_or_create(
            name=badge_data['name'],
            defaults=badge_data
        )


def create_default_levels():
    """Create default user levels"""
    from .models import UserLevel
    
    default_levels = [
        {'level': 1, 'name': 'Beginner', 'min_points': 0, 'max_points': 99},
        {'level': 2, 'name': 'Student', 'min_points': 100, 'max_points': 249},
        {'level': 3, 'name': 'Learner', 'min_points': 250, 'max_points': 499},
        {'level': 4, 'name': 'Scholar', 'min_points': 500, 'max_points': 999},
        {'level': 5, 'name': 'Expert', 'min_points': 1000, 'max_points': 1999},
        {'level': 6, 'name': 'Master', 'min_points': 2000, 'max_points': 3999},
        {'level': 7, 'name': 'Guru', 'min_points': 4000, 'max_points': 7999},
        {'level': 8, 'name': 'Legend', 'min_points': 8000, 'max_points': 15999},
        {'level': 9, 'name': 'Champion', 'min_points': 16000, 'max_points': 31999},
        {'level': 10, 'name': 'Grandmaster', 'min_points': 32000, 'max_points': None},
    ]
    
    for level_data in default_levels:
        UserLevel.objects.get_or_create(
            level=level_data['level'],
            defaults=level_data
        )


def create_default_leaderboards():
    """Create default leaderboards"""
    default_leaderboards = [
        {
            'name': 'Overall Points',
            'leaderboard_type': Leaderboard.LeaderboardType.OVERALL_POINTS,
            'description': 'Top learners by total points earned',
            'reset_frequency': 'never'
        },
        {
            'name': 'Monthly Points',
            'leaderboard_type': Leaderboard.LeaderboardType.MONTHLY_POINTS,
            'description': 'Top earners this month',
            'reset_frequency': 'monthly'
        },
        {
            'name': 'Course Completion',
            'leaderboard_type': Leaderboard.LeaderboardType.COURSE_COMPLETION,
            'description': 'Most courses completed',
            'reset_frequency': 'never'
        },
        {
            'name': 'Forum Activity',
            'leaderboard_type': Leaderboard.LeaderboardType.FORUM_ACTIVITY,
            'description': 'Most active in forums',
            'reset_frequency': 'never'
        },
        {
            'name': 'Login Streak',
            'leaderboard_type': Leaderboard.LeaderboardType.STREAK,
            'description': 'Longest login streaks',
            'reset_frequency': 'never'
        },
    ]
    
    for leaderboard_data in default_leaderboards:
        Leaderboard.objects.get_or_create(
            leaderboard_type=leaderboard_data['leaderboard_type'],
            defaults=leaderboard_data
        )