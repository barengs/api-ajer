import django.dispatch
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.apps import apps

from .models import PointsTransaction, UserStats
from .utils import award_points, check_user_badges, check_user_achievements, POINTS_CONFIG

User = get_user_model()

# Custom signals
level_up = django.dispatch.Signal()
badge_earned = django.dispatch.Signal()
achievement_unlocked = django.dispatch.Signal()


@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    """Create user stats when a new user is created"""
    if created:
        from .utils import get_or_create_user_stats
        get_or_create_user_stats(instance)


def award_lesson_completion_points(user, lesson):
    """Award points for lesson completion"""
    points = POINTS_CONFIG['lesson_complete']
    
    # Bonus points for first lesson
    stats, created = UserStats.objects.get_or_create(user=user)
    if stats.lessons_completed == 0:
        points += 10  # First lesson bonus
    
    award_points(
        user,
        points,
        PointsTransaction.TransactionType.LESSON_COMPLETE,
        f"Completed lesson: {lesson.title}",
        lesson=lesson,
        course=lesson.section.course if hasattr(lesson, 'section') else None
    )
    
    # Update stats
    stats.lessons_completed += 1
    stats.save()
    
    # Check for badges and achievements
    check_user_badges(user)
    check_user_achievements(user)


def award_assignment_submission_points(user, assignment):
    """Award points for assignment submission"""
    points = POINTS_CONFIG['assignment_submit']
    
    award_points(
        user,
        points,
        PointsTransaction.TransactionType.ASSIGNMENT_SUBMIT,
        f"Submitted assignment: {assignment.title}",
        assignment=assignment,
        course=assignment.course
    )
    
    # Update stats
    stats, created = UserStats.objects.get_or_create(user=user)
    stats.assignments_submitted += 1
    stats.save()
    
    check_user_badges(user)
    check_user_achievements(user)


def award_quiz_completion_points(user, quiz, score_percentage):
    """Award points for quiz completion"""
    points = POINTS_CONFIG['quiz_pass']
    transaction_type = PointsTransaction.TransactionType.QUIZ_PASS
    description = f"Passed quiz: {getattr(quiz, 'title', 'Quiz')}"
    
    # Bonus for perfect score
    if score_percentage >= 100:
        points = POINTS_CONFIG['quiz_perfect']
        description = f"Perfect score on quiz: {getattr(quiz, 'title', 'Quiz')}"
        
        # Update perfect score count
        stats, created = UserStats.objects.get_or_create(user=user)
        stats.perfect_scores += 1
        stats.save()
    
    award_points(
        user,
        points,
        transaction_type,
        description,
        lesson=quiz.lesson if hasattr(quiz, 'lesson') else None,
        metadata={'score_percentage': score_percentage}
    )
    
    # Update stats
    stats, created = UserStats.objects.get_or_create(user=user)
    stats.quizzes_passed += 1
    stats.save()
    
    check_user_badges(user)
    check_user_achievements(user)


def award_course_completion_points(user, course):
    """Award points for course completion"""
    points = POINTS_CONFIG['course_complete']
    
    # Bonus for first course
    stats, created = UserStats.objects.get_or_create(user=user)
    if stats.courses_completed == 0:
        points += POINTS_CONFIG['first_course']
    
    award_points(
        user,
        points,
        PointsTransaction.TransactionType.COURSE_COMPLETE,
        f"Completed course: {course.title}",
        course=course
    )
    
    # Update stats
    stats.courses_completed += 1
    stats.save()
    
    check_user_badges(user)
    check_user_achievements(user)


def award_forum_activity_points(user, activity_type, post_title=""):
    """Award points for forum activities"""
    points_map = {
        'post': POINTS_CONFIG['forum_post'],
        'reply': POINTS_CONFIG['forum_reply'],
        'helpful_reply': POINTS_CONFIG['helpful_reply'],
    }
    
    points = points_map.get(activity_type, 0)
    if not points:
        return
    
    transaction_map = {
        'post': PointsTransaction.TransactionType.FORUM_POST,
        'reply': PointsTransaction.TransactionType.FORUM_REPLY,
        'helpful_reply': PointsTransaction.TransactionType.HELPFUL_REPLY,
    }
    
    description_map = {
        'post': f"Created forum post: {post_title}",
        'reply': f"Replied to forum post: {post_title}",
        'helpful_reply': f"Received helpful vote: {post_title}",
    }
    
    award_points(
        user,
        points,
        transaction_map[activity_type],
        description_map[activity_type],
        metadata={'activity_type': activity_type}
    )
    
    # Update stats
    stats, created = UserStats.objects.get_or_create(user=user)
    if activity_type == 'post':
        stats.forum_posts += 1
    elif activity_type == 'reply':
        stats.forum_replies += 1
    elif activity_type == 'helpful_reply':
        stats.helpful_replies += 1
    stats.save()
    
    check_user_badges(user)
    check_user_achievements(user)


def award_daily_login_points(user):
    """Award points for daily login and update streak"""
    stats, created = UserStats.objects.get_or_create(user=user)
    
    # Update login streak
    stats.update_login_streak()
    
    # Award daily points
    award_points(
        user,
        POINTS_CONFIG['daily_login'],
        PointsTransaction.TransactionType.DAILY_LOGIN,
        "Daily login bonus",
        metadata={'streak': stats.current_login_streak}
    )


def award_referral_points(referrer_user, referred_user):
    """Award points for successful referral"""
    award_points(
        referrer_user,
        POINTS_CONFIG['referral'],
        PointsTransaction.TransactionType.REFERRAL,
        f"Referred new user: {referred_user.username}",
        metadata={'referred_user_id': referred_user.id}
    )


@receiver(level_up)
def handle_level_up(sender, user, old_level, new_level, **kwargs):
    """Handle level up event"""
    # Award bonus points for leveling up
    bonus_points = new_level.level * 10
    award_points(
        user,
        bonus_points,
        PointsTransaction.TransactionType.BONUS,
        f"Level up bonus: {old_level.name} → {new_level.name}",
        metadata={
            'old_level': old_level.level,
            'new_level': new_level.level,
            'level_up_bonus': True
        }
    )
    
    # Check for level-based badges
    check_user_badges(user)


@receiver(badge_earned)
def handle_badge_earned(sender, user, badge, **kwargs):
    """Handle badge earned event"""
    # Could trigger notifications, social sharing, etc.
    pass


@receiver(achievement_unlocked)
def handle_achievement_unlocked(sender, user, achievement, **kwargs):
    """Handle achievement unlocked event"""
    # Could trigger special effects, notifications, etc.
    pass


# Signal connections for other apps
try:
    # Connect to lesson completion signals
    from lessons.signals import lesson_completed  # type: ignore[import]
    
    @receiver(lesson_completed)
    def on_lesson_completed(sender, user, lesson, **kwargs):
        award_lesson_completion_points(user, lesson)
        
except ImportError:
    pass

try:
    # Connect to assignment submission signals
    from assignments.signals import assignment_submitted  # type: ignore[import]
    
    @receiver(assignment_submitted)
    def on_assignment_submitted(sender, user, assignment, **kwargs):
        award_assignment_submission_points(user, assignment)
        
except ImportError:
    pass

try:
    # Connect to course completion signals
    from courses.signals import course_completed  # type: ignore[import]
    
    @receiver(course_completed)
    def on_course_completed(sender, user, course, **kwargs):
        award_course_completion_points(user, course)
        
except ImportError:
    pass

try:
    # Connect to forum activity signals
    from forums.signals import forum_post_created, forum_reply_created, reply_marked_helpful  # type: ignore[import]
    
    @receiver(forum_post_created)
    def on_forum_post_created(sender, user, post, **kwargs):
        award_forum_activity_points(user, 'post', post.title)
    
    @receiver(forum_reply_created)
    def on_forum_reply_created(sender, user, reply, **kwargs):
        award_forum_activity_points(user, 'reply', reply.post.title)
    
    @receiver(reply_marked_helpful)
    def on_reply_marked_helpful(sender, user, reply, **kwargs):
        award_forum_activity_points(user, 'helpful_reply', reply.post.title)
        
except ImportError:
    pass


# Manual signal triggers for when signals from other apps don't exist
def trigger_lesson_completion(user, lesson):
    """Manual trigger for lesson completion"""
    award_lesson_completion_points(user, lesson)


def trigger_assignment_submission(user, assignment):
    """Manual trigger for assignment submission"""
    award_assignment_submission_points(user, assignment)


def trigger_quiz_completion(user, quiz, score_percentage):
    """Manual trigger for quiz completion"""
    award_quiz_completion_points(user, quiz, score_percentage)


def trigger_course_completion(user, course):
    """Manual trigger for course completion"""
    award_course_completion_points(user, course)


def trigger_forum_activity(user, activity_type, post_title=""):
    """Manual trigger for forum activities"""
    award_forum_activity_points(user, activity_type, post_title)


def trigger_daily_login(user):
    """Manual trigger for daily login"""
    award_daily_login_points(user)


def trigger_referral(referrer_user, referred_user):
    """Manual trigger for referral"""
    award_referral_points(referrer_user, referred_user)