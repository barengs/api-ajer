from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    BadgeType, UserBadge, PointsTransaction, UserLevel, UserStats,
    Achievement, UserAchievement, Leaderboard, LeaderboardEntry
)

User = get_user_model()


class BadgeTypeSerializer(serializers.ModelSerializer):
    """Serializer for badge types"""
    
    class Meta:
        model = BadgeType
        fields = [
            'id', 'name', 'description', 'icon', 'category',
            'points_required', 'is_active', 'created_at'
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for user badges"""
    
    badge_type = BadgeTypeSerializer(read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserBadge
        fields = [
            'id', 'badge_type', 'user_name', 'earned_at', 'metadata'
        ]


class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transactions"""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = PointsTransaction
        fields = [
            'id', 'user_name', 'points', 'transaction_type', 'description',
            'course_title', 'lesson_title', 'assignment_title',
            'metadata', 'created_at'
        ]


class UserLevelSerializer(serializers.ModelSerializer):
    """Serializer for user levels"""
    
    class Meta:
        model = UserLevel
        fields = [
            'level', 'name', 'min_points', 'max_points', 'icon', 'perks'
        ]


class UserStatsSerializer(serializers.ModelSerializer):
    """Serializer for user statistics"""
    
    current_level = UserLevelSerializer(read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    badges_count = serializers.SerializerMethodField()
    achievements_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserStats
        fields = [
            'user_name', 'total_points', 'current_level',
            'courses_completed', 'lessons_completed', 'assignments_submitted',
            'quizzes_passed', 'forum_posts', 'forum_replies', 'helpful_replies',
            'current_login_streak', 'longest_login_streak', 'last_login_date',
            'perfect_scores', 'certificates_earned', 'badges_count',
            'achievements_count', 'updated_at'
        ]
    
    def get_badges_count(self, obj):
        return obj.user.badges.count()  # type: ignore[attr-defined]
    
    def get_achievements_count(self, obj):
        return obj.user.achievements.count()  # type: ignore[attr-defined]


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for achievements"""
    
    badge_reward = BadgeTypeSerializer(read_only=True)
    is_earned = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'icon', 'achievement_type',
            'requirements', 'points_reward', 'badge_reward', 'is_active',
            'is_hidden', 'is_earned', 'progress'
        ]
    
    def get_is_earned(self, obj):
        """Check if current user has earned this achievement"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserAchievement.objects.filter(
                user=request.user, achievement=obj
            ).exists()
        return False
    
    def get_progress(self, obj):
        """Get user's progress toward this achievement"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_achievement = UserAchievement.objects.filter(
                user=request.user, achievement=obj
            ).first()
            if user_achievement:
                return user_achievement.progress_data
            else:
                # Calculate current progress based on requirements
                from .utils import calculate_achievement_progress  # type: ignore[attr-defined]
                return calculate_achievement_progress(request.user, obj)
        return {}


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for user achievements"""
    
    achievement = AchievementSerializer(read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement', 'user_name', 'earned_at', 'progress_data'
        ]


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for leaderboard configurations"""
    
    entries_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'name', 'leaderboard_type', 'description', 'is_active',
            'reset_frequency', 'last_reset', 'entries_count'
        ]
    
    def get_entries_count(self, obj):
        return obj.entries.count()  # type: ignore[attr-defined]


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """Serializer for leaderboard entries"""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.profile_picture', read_only=True)
    level_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaderboardEntry
        fields = [
            'rank', 'user_name', 'user_avatar', 'score', 'level_name',
            'metadata', 'updated_at'
        ]
    
    def get_level_name(self, obj):
        """Get user's current level name"""
        try:
            stats = obj.user.stats  # type: ignore[attr-defined]
            return stats.current_level.name if stats.current_level else "Beginner"
        except:
            return "Beginner"


class UserProfileStatsSerializer(serializers.Serializer):
    """Serializer for user profile gamification stats"""
    
    total_points = serializers.IntegerField()
    current_level = UserLevelSerializer()
    badges = UserBadgeSerializer(many=True)
    achievements = UserAchievementSerializer(many=True)
    recent_transactions = PointsTransactionSerializer(many=True)
    
    # Summary stats
    courses_completed = serializers.IntegerField()
    lessons_completed = serializers.IntegerField()
    forum_contributions = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    
    # Rankings
    overall_rank = serializers.IntegerField()
    monthly_rank = serializers.IntegerField()


class PointsAwardSerializer(serializers.Serializer):
    """Serializer for awarding points (admin use)"""
    
    user_id = serializers.IntegerField()
    points = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=PointsTransaction.TransactionType.choices)
    description = serializers.CharField(max_length=200)
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)
    assignment_id = serializers.IntegerField(required=False)
    metadata = serializers.JSONField(required=False)
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value
    
    def validate_points(self, value):
        """Validate points value"""
        if value == 0:
            raise serializers.ValidationError("Points cannot be zero")
        return value


class BadgeAwardSerializer(serializers.Serializer):
    """Serializer for awarding badges (admin use)"""
    
    user_id = serializers.IntegerField()
    badge_type_id = serializers.IntegerField()
    metadata = serializers.JSONField(required=False)
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value
    
    def validate_badge_type_id(self, value):
        """Validate badge type exists"""
        try:
            BadgeType.objects.get(id=value)
        except BadgeType.DoesNotExist:
            raise serializers.ValidationError("Badge type not found")
        return value
    
    def validate(self, attrs):
        """Check if user already has this badge"""
        user_id = attrs['user_id']
        badge_type_id = attrs['badge_type_id']
        
        if UserBadge.objects.filter(user_id=user_id, badge_type_id=badge_type_id).exists():
            raise serializers.ValidationError("User already has this badge")
        
        return attrs


class LeaderboardStatsSerializer(serializers.Serializer):
    """Serializer for leaderboard statistics"""
    
    total_participants = serializers.IntegerField()
    user_rank = serializers.IntegerField()
    user_score = serializers.IntegerField()
    top_10 = LeaderboardEntrySerializer(many=True)
    user_entry = LeaderboardEntrySerializer()
    leaderboard_info = LeaderboardSerializer()