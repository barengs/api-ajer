from django.contrib import admin
from .models import (
    UserRecommendationProfile, UserCourseInteraction, 
    Recommendation, RecommendationFeedback, RecommendationSettings
)


@admin.register(UserRecommendationProfile)
class UserRecommendationProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'last_active', 'total_learning_time', 'created_at']
    list_filter = ['last_active', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


@admin.register(UserCourseInteraction)
class UserCourseInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'interaction_type', 'rating', 'interaction_date']
    list_filter = ['interaction_type', 'rating', 'interaction_date']
    search_fields = ['user__email', 'user__username', 'course__title']
    readonly_fields = ['interaction_date']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'course')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation_type', 'course', 'algorithm_used', 'score', 'generated_at']
    list_filter = ['recommendation_type', 'algorithm_used', 'generated_at']
    search_fields = ['user__email', 'user__username', 'course__title']
    readonly_fields = ['generated_at', 'expires_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'course')


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation', 'feedback_type', 'created_at']
    list_filter = ['feedback_type', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recommendation')


@admin.register(RecommendationSettings)
class RecommendationSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'default_algorithm', 'max_recommendations_per_user', 
        'recommendation_expiry_days', 'auto_refresh_enabled'
    ]
    readonly_fields = ['created_at', 'updated_at']