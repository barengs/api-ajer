from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course
from accounts.models import User
import json


class RecommendationType(models.TextChoices):
    """Types of recommendations that can be generated"""
    COURSE = 'course', 'Course Recommendation'
    LESSON = 'lesson', 'Lesson Recommendation'
    INSTRUCTOR = 'instructor', 'Instructor Recommendation'
    CATEGORY = 'category', 'Category Recommendation'
    SIMILAR_USER = 'similar_user', 'Similar User Recommendation'


class RecommendationAlgorithm(models.TextChoices):
    """Algorithms used for generating recommendations"""
    COLLABORATIVE_FILTERING = 'collaborative', 'Collaborative Filtering'
    CONTENT_BASED = 'content', 'Content-Based Filtering'
    HYBRID = 'hybrid', 'Hybrid Approach'
    POPULARITY = 'popularity', 'Popularity-Based'
    KNOWLEDGE_BASED = 'knowledge', 'Knowledge-Based'


class UserRecommendationProfile(models.Model):
    """
    Stores user profile data used for generating recommendations
    This includes interests, learning history, preferences, etc.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendation_profile'
    )
    
    # Learning preferences
    preferred_categories = models.JSONField(
        default=list,
        help_text="List of category IDs the user prefers"
    )
    
    preferred_difficulty_levels = models.JSONField(
        default=list,
        help_text="List of preferred difficulty levels (beginner, intermediate, advanced)"
    )
    
    preferred_learning_styles = models.JSONField(
        default=list,
        help_text="List of preferred learning styles (video, text, interactive, etc.)"
    )
    
    # Learning history
    completed_courses = models.ManyToManyField(
        Course,
        related_name='completed_by_users',
        blank=True
    )
    
    viewed_courses = models.ManyToManyField(
        Course,
        related_name='viewed_by_users',
        blank=True,
        through='UserViewedCourse'
    )
    
    # Behavioral data
    last_active = models.DateTimeField(default=timezone.now)
    total_learning_time = models.PositiveIntegerField(
        default=0,
        help_text="Total time spent learning in minutes"
    )
    
    # AI model features
    feature_vector = models.JSONField(
        default=dict,
        help_text="User feature vector for machine learning algorithms"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_recommendation_profiles'
        verbose_name = 'User Recommendation Profile'
        verbose_name_plural = 'User Recommendation Profiles'
        indexes = [
            models.Index(fields=['last_active']),
            models.Index(fields=['total_learning_time']),
        ]
    
    def __str__(self):
        return f"Recommendation Profile for {self.user.email}"


class UserCourseInteraction(models.Model):
    """
    Tracks user interactions with courses for recommendation algorithms
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    
    # Interaction types
    VIEWED = 'viewed'
    ENROLLED = 'enrolled'
    COMPLETED = 'completed'
    RATED = 'rated'
    WISHLISTED = 'wishlisted'
    SEARCHED = 'searched'
    
    INTERACTION_TYPES = [
        (VIEWED, 'Viewed'),
        (ENROLLED, 'Enrolled'),
        (COMPLETED, 'Completed'),
        (RATED, 'Rated'),
        (WISHLISTED, 'Wishlisted'),
        (SEARCHED, 'Searched'),
    ]
    
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_TYPES
    )
    
    # Interaction metadata
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Rating given by user (1-5)"
    )
    
    time_spent = models.PositiveIntegerField(
        default=0,
        help_text="Time spent on course in minutes"
    )
    
    interaction_date = models.DateTimeField(default=timezone.now)
    
    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context about the interaction"
    )
    
    class Meta:
        db_table = 'user_course_interactions'
        verbose_name = 'User Course Interaction'
        verbose_name_plural = 'User Course Interactions'
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['course', 'interaction_type']),
            models.Index(fields=['interaction_date']),
        ]
        unique_together = ['user', 'course', 'interaction_type']
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title} - {self.interaction_type}"


class UserViewedCourse(models.Model):
    """
    Intermediate model for UserRecommendationProfile.viewed_courses relationship
    """
    user_profile = models.ForeignKey(
        UserRecommendationProfile,
        on_delete=models.CASCADE
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    
    # Metadata from the interaction
    first_viewed = models.DateTimeField(default=timezone.now)
    last_viewed = models.DateTimeField(default=timezone.now)
    view_count = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'user_viewed_courses'
        unique_together = ['user_profile', 'course']
        verbose_name = 'User Viewed Course'
        verbose_name_plural = 'User Viewed Courses'
        indexes = [
            models.Index(fields=['user_profile', 'last_viewed']),
            models.Index(fields=['course', 'last_viewed']),
        ]
    
    def __str__(self):
        return f"{self.user_profile.user.email} viewed {self.course.title}"


class Recommendation(models.Model):
    """
    Stores generated recommendations for users
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    
    # Recommended item
    recommendation_type = models.CharField(
        max_length=20,
        choices=RecommendationType.choices
    )
    
    # For course recommendations
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recommended_to'
    )
    
    # For other recommendation types, store the ID
    recommended_item_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of recommended item (for non-course recommendations)"
    )
    
    # Recommendation details
    algorithm_used = models.CharField(
        max_length=20,
        choices=RecommendationAlgorithm.choices
    )
    
    score = models.FloatField(
        help_text="Recommendation score/confidence level (0.0 - 1.0)"
    )
    
    # Reasoning
    reason = models.TextField(
        blank=True,
        help_text="Explanation of why this recommendation was made"
    )
    
    reason_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured data explaining the recommendation"
    )
    
    # Metadata
    generated_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this recommendation expires"
    )
    
    # Tracking
    is_clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'recommendations'
        verbose_name = 'Recommendation'
        verbose_name_plural = 'Recommendations'
        indexes = [
            models.Index(fields=['user', 'generated_at']),
            models.Index(fields=['user', 'recommendation_type']),
            models.Index(fields=['generated_at']),
            models.Index(fields=['score']),
        ]
        ordering = ['-generated_at']
    
    def __str__(self):
        if self.course:
            return f"Recommendation for {self.user.email}: {self.course.title}"
        return f"Recommendation for {self.user.email}: {self.recommendation_type}"


class RecommendationFeedback(models.Model):
    """
    Stores user feedback on recommendations to improve the system
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    
    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    
    # Feedback types
    HELPFUL = 'helpful'
    NOT_HELPFUL = 'not_helpful'
    IRRELEVANT = 'irrelevant'
    MISLEADING = 'misleading'
    
    FEEDBACK_CHOICES = [
        (HELPFUL, 'Helpful'),
        (NOT_HELPFUL, 'Not Helpful'),
        (IRRELEVANT, 'Irrelevant'),
        (MISLEADING, 'Misleading'),
    ]
    
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES
    )
    
    # Additional feedback
    comment = models.TextField(
        blank=True,
        help_text="User's comment on the recommendation"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendation_feedback'
        verbose_name = 'Recommendation Feedback'
        verbose_name_plural = 'Recommendation Feedback'
        indexes = [
            models.Index(fields=['recommendation', 'feedback_type']),
            models.Index(fields=['user', 'created_at']),
        ]
        unique_together = ['user', 'recommendation']
    
    def __str__(self):
        return f"Feedback from {self.user.email} on recommendation {self.recommendation.id}"


class RecommendationSettings(models.Model):
    """
    System-wide settings for the recommendation engine
    """
    # Algorithm settings
    default_algorithm = models.CharField(
        max_length=20,
        choices=RecommendationAlgorithm.choices,
        default=RecommendationAlgorithm.HYBRID
    )
    
    # Recommendation limits
    max_recommendations_per_user = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of recommendations to generate per user"
    )
    
    recommendation_expiry_days = models.PositiveIntegerField(
        default=7,
        help_text="Number of days after which recommendations expire"
    )
    
    # Refresh settings
    auto_refresh_enabled = models.BooleanField(
        default=True,
        help_text="Whether to automatically refresh recommendations"
    )
    
    refresh_interval_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours between automatic recommendation refreshes"
    )
    
    # Content filtering
    exclude_completed_courses = models.BooleanField(
        default=True,
        help_text="Exclude courses the user has already completed"
    )
    
    exclude_enrolled_courses = models.BooleanField(
        default=True,
        help_text="Exclude courses the user is already enrolled in"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recommendation_settings'
        verbose_name = 'Recommendation Settings'
        verbose_name_plural = 'Recommendation Settings'
    
    def __str__(self):
        return "Recommendation System Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        try:
            settings, created = cls.objects.get_or_create(
                id=1,
                defaults={
                    'default_algorithm': RecommendationAlgorithm.HYBRID,
                    'max_recommendations_per_user': 10,
                    'recommendation_expiry_days': 7,
                    'auto_refresh_enabled': True,
                    'refresh_interval_hours': 24,
                    'exclude_completed_courses': True,
                    'exclude_enrolled_courses': True,
                }
            )
            return settings
        except Exception:
            # Return default settings if table doesn't exist yet
            return cls(
                id=1,
                default_algorithm=RecommendationAlgorithm.HYBRID,
                max_recommendations_per_user=10,
                recommendation_expiry_days=7,
                auto_refresh_enabled=True,
                refresh_interval_hours=24,
                exclude_completed_courses=True,
                exclude_enrolled_courses=True,
            )