from rest_framework import serializers
from .models import (
    UserRecommendationProfile, UserCourseInteraction, 
    Recommendation, RecommendationFeedback, RecommendationSettings
)
from courses.serializers import CourseListSerializer
from accounts.serializers import UserSerializer


class UserRecommendationProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserRecommendationProfile model"""
    
    user = UserSerializer(read_only=True)
    completed_courses = CourseListSerializer(many=True, read_only=True)
    viewed_courses = CourseListSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserRecommendationProfile
        fields = [
            'id', 'user', 'preferred_categories', 'preferred_difficulty_levels',
            'preferred_learning_styles', 'completed_courses', 'viewed_courses',
            'last_active', 'total_learning_time', 'feature_vector',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCourseInteractionSerializer(serializers.ModelSerializer):
    """Serializer for UserCourseInteraction model"""
    
    user = UserSerializer(read_only=True)
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = UserCourseInteraction
        fields = [
            'id', 'user', 'course', 'interaction_type', 'rating',
            'time_spent', 'interaction_date', 'metadata'
        ]
        read_only_fields = ['id', 'interaction_date']


class RecommendationSerializer(serializers.ModelSerializer):
    """Serializer for Recommendation model"""
    
    user = UserSerializer(read_only=True)
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'user', 'recommendation_type', 'course', 
            'recommended_item_id', 'algorithm_used', 'score',
            'reason', 'reason_data', 'generated_at', 'expires_at',
            'is_clicked', 'clicked_at', 'is_dismissed', 'dismissed_at'
        ]
        read_only_fields = [
            'id', 'generated_at', 'expires_at', 'is_clicked', 
            'clicked_at', 'is_dismissed', 'dismissed_at'
        ]


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for RecommendationFeedback model"""
    
    user = UserSerializer(read_only=True)
    recommendation = RecommendationSerializer(read_only=True)
    
    class Meta:
        model = RecommendationFeedback
        fields = [
            'id', 'user', 'recommendation', 'feedback_type', 
            'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RecommendationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for RecommendationSettings model"""
    
    class Meta:
        model = RecommendationSettings
        fields = [
            'id', 'default_algorithm', 'max_recommendations_per_user',
            'recommendation_expiry_days', 'auto_refresh_enabled',
            'refresh_interval_hours', 'exclude_completed_courses',
            'exclude_enrolled_courses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']