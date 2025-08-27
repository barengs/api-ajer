from typing import TYPE_CHECKING
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta

if TYPE_CHECKING:
    from accounts.models import User
    from courses.models import Course
    from lessons.models import Lesson
    from assignments.models import Assignment

User = get_user_model()


class BadgeType(models.Model):
    """Badge types available in the system"""
    
    class BadgeCategory(models.TextChoices):
        LEARNING = 'learning', 'Learning'
        SOCIAL = 'social', 'Social'
        ACHIEVEMENT = 'achievement', 'Achievement'
        INSTRUCTOR = 'instructor', 'Instructor'
        SPECIAL = 'special', 'Special'
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/icons/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=BadgeCategory.choices)
    points_required = models.IntegerField(default=0, help_text="Points required to earn this badge")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['category', 'name']


class UserBadge(models.Model):
    """Badges earned by users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.ForeignKey(BadgeType, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional data about how badge was earned")
    
    class Meta:
        unique_together = ['user', 'badge_type']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge_type.name}"


class PointsTransaction(models.Model):
    """Track all points transactions for users"""
    
    class TransactionType(models.TextChoices):
        LESSON_COMPLETE = 'lesson_complete', 'Lesson Completed'
        ASSIGNMENT_SUBMIT = 'assignment_submit', 'Assignment Submitted'
        QUIZ_PASS = 'quiz_pass', 'Quiz Passed'
        FORUM_POST = 'forum_post', 'Forum Post'
        FORUM_REPLY = 'forum_reply', 'Forum Reply'
        HELPFUL_REPLY = 'helpful_reply', 'Helpful Reply'
        COURSE_COMPLETE = 'course_complete', 'Course Completed'
        PERFECT_SCORE = 'perfect_score', 'Perfect Score'
        FIRST_COURSE = 'first_course', 'First Course'
        DAILY_LOGIN = 'daily_login', 'Daily Login'
        STREAK_BONUS = 'streak_bonus', 'Streak Bonus'
        REFERRAL = 'referral', 'Referral Bonus'
        BONUS = 'bonus', 'Bonus Points'
        PENALTY = 'penalty', 'Points Deducted'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_transactions')
    points = models.IntegerField(help_text="Positive for earning, negative for deduction")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    description = models.CharField(max_length=200)
    
    # Related objects (optional)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, blank=True, null=True)
    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.CASCADE, blank=True, null=True)
    assignment = models.ForeignKey('assignments.Assignment', on_delete=models.CASCADE, blank=True, null=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.points} points ({self.transaction_type})"


class UserLevel(models.Model):
    """User levels based on total points"""
    
    level = models.IntegerField(unique=True, validators=[MinValueValidator(1)])
    name = models.CharField(max_length=50)
    min_points = models.IntegerField(validators=[MinValueValidator(0)])
    max_points = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    icon = models.ImageField(upload_to='levels/icons/', blank=True, null=True)
    perks = models.JSONField(default=list, blank=True, help_text="List of perks for this level")
    
    class Meta:
        ordering = ['level']
    
    def __str__(self):
        return f"Level {self.level}: {self.name}"
    
    @classmethod
    def get_level_for_points(cls, points):
        """Get the appropriate level for given points"""
        return cls.objects.filter(min_points__lte=points).order_by('-level').first()


class UserStats(models.Model):
    """Comprehensive user statistics for gamification"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    
    # Points and Level
    total_points = models.IntegerField(default=0)
    current_level = models.ForeignKey(UserLevel, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Learning Stats
    courses_completed = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    assignments_submitted = models.IntegerField(default=0)
    quizzes_passed = models.IntegerField(default=0)
    
    # Social Stats
    forum_posts = models.IntegerField(default=0)
    forum_replies = models.IntegerField(default=0)
    helpful_replies = models.IntegerField(default=0)
    
    # Streaks
    current_login_streak = models.IntegerField(default=0)
    longest_login_streak = models.IntegerField(default=0)
    last_login_date = models.DateField(blank=True, null=True)
    
    # Achievements
    perfect_scores = models.IntegerField(default=0)
    certificates_earned = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Stats"
    
    def add_points(self, points, transaction_type, description, **kwargs):
        """Add points and create transaction record"""
        self.total_points += points
        
        # Update level if necessary
        new_level = UserLevel.get_level_for_points(self.total_points)
        if new_level and (not self.current_level or new_level.level > self.current_level.level):
            old_level = self.current_level
            self.current_level = new_level
            self.save()
            
            # Create level up notification/event
            if old_level:
                from .signals import level_up  # type: ignore[attr-defined]
                level_up.send(
                    sender=self.__class__,
                    user=self.user,
                    old_level=old_level,
                    new_level=new_level
                )
        else:
            self.save()
        
        # Create transaction record
        PointsTransaction.objects.create(
            user=self.user,
            points=points,
            transaction_type=transaction_type,
            description=description,
            **kwargs
        )
        
        # Check for badge achievements
        self.check_badges()
    
    def check_badges(self):
        """Check if user has earned any new badges"""
        from .utils import check_user_badges  # type: ignore[attr-defined]
        check_user_badges(self.user)
    
    def update_login_streak(self):
        """Update login streak"""
        today = timezone.now().date()
        
        if not self.last_login_date:
            # First login
            self.current_login_streak = 1
            self.longest_login_streak = 1
        elif self.last_login_date == today - timedelta(days=1):
            # Consecutive day
            self.current_login_streak += 1
            if self.current_login_streak > self.longest_login_streak:
                self.longest_login_streak = self.current_login_streak
        elif self.last_login_date != today:
            # Streak broken
            self.current_login_streak = 1
        
        self.last_login_date = today
        self.save()
        
        # Award streak bonuses
        if self.current_login_streak in [7, 30, 100]:  # Weekly, monthly, 100-day milestones
            bonus_points = self.current_login_streak
            self.add_points(
                bonus_points,
                PointsTransaction.TransactionType.STREAK_BONUS,
                f"{self.current_login_streak}-day login streak bonus"
            )


class Achievement(models.Model):
    """Special achievements users can unlock"""
    
    class AchievementType(models.TextChoices):
        MILESTONE = 'milestone', 'Milestone'
        SPEED = 'speed', 'Speed'
        CONSISTENCY = 'consistency', 'Consistency'
        EXCELLENCE = 'excellence', 'Excellence'
        SOCIAL = 'social', 'Social'
        SPECIAL = 'special', 'Special'
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievements/icons/', blank=True, null=True)
    achievement_type = models.CharField(max_length=20, choices=AchievementType.choices)
    
    # Requirements (JSON field for flexible criteria)
    requirements = models.JSONField(
        help_text="JSON object defining achievement requirements"
    )
    
    points_reward = models.IntegerField(default=0)
    badge_reward = models.ForeignKey(BadgeType, on_delete=models.SET_NULL, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False, help_text="Hidden until unlocked")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['achievement_type', 'name']


class UserAchievement(models.Model):
    """Achievements earned by users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    progress_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class Leaderboard(models.Model):
    """Leaderboard configurations"""
    
    class LeaderboardType(models.TextChoices):
        OVERALL_POINTS = 'overall_points', 'Overall Points'
        MONTHLY_POINTS = 'monthly_points', 'Monthly Points'
        COURSE_COMPLETION = 'course_completion', 'Course Completion'
        FORUM_ACTIVITY = 'forum_activity', 'Forum Activity'
        STREAK = 'streak', 'Login Streak'
    
    name = models.CharField(max_length=100)
    leaderboard_type = models.CharField(max_length=20, choices=LeaderboardType.choices, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    reset_frequency = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='never'
    )
    last_reset = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class LeaderboardEntry(models.Model):
    """Cached leaderboard entries for performance"""
    
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rank = models.IntegerField()
    score = models.IntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['leaderboard', 'user']
        ordering = ['leaderboard', 'rank']
        indexes = [
            models.Index(fields=['leaderboard', 'rank']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.leaderboard.name} - Rank {self.rank}: {self.user.username}"