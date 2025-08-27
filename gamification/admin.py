from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    BadgeType, UserBadge, PointsTransaction, UserLevel, UserStats,
    Achievement, UserAchievement, Leaderboard, LeaderboardEntry
)


@admin.register(BadgeType)
class BadgeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'points_required', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['category', 'points_required']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon', 'category')
        }),
        ('Requirements', {
            'fields': ('points_required', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            users_count=Count('userbadge')
        )


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'badge_type', 'earned_at']
    list_filter = ['badge_type__category', 'earned_at', 'badge_type']
    search_fields = ['user__username', 'user__email', 'badge_type__name']
    ordering = ['-earned_at']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'  # type: ignore[attr-defined]
    user_link.admin_order_field = 'user__username'  # type: ignore[attr-defined]


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'points', 'transaction_type', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'points']
    search_fields = ['user__username', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'points', 'transaction_type', 'description')
        }),
        ('Related Objects', {
            'fields': ('course', 'lesson', 'assignment'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'  # type: ignore[attr-defined]
    user_link.admin_order_field = 'user__username'  # type: ignore[attr-defined]


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ['level', 'name', 'min_points', 'max_points', 'users_count']
    ordering = ['level']
    
    def users_count(self, obj):
        return UserStats.objects.filter(current_level=obj).count()
    users_count.short_description = 'Users at this level'  # type: ignore[attr-defined]


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'total_points', 'current_level', 'courses_completed',
        'current_login_streak', 'updated_at'
    ]
    list_filter = ['current_level', 'updated_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-total_points']
    
    fieldsets = (
        ('User & Level', {
            'fields': ('user', 'total_points', 'current_level')
        }),
        ('Learning Stats', {
            'fields': (
                'courses_completed', 'lessons_completed', 'assignments_submitted',
                'quizzes_passed', 'perfect_scores', 'certificates_earned'
            )
        }),
        ('Social Stats', {
            'fields': ('forum_posts', 'forum_replies', 'helpful_replies')
        }),
        ('Streaks', {
            'fields': (
                'current_login_streak', 'longest_login_streak', 'last_login_date'
            )
        }),
        ('Timestamps', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['updated_at']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'  # type: ignore[attr-defined]
    user_link.admin_order_field = 'user__username'  # type: ignore[attr-defined]
    
    actions = ['recalculate_stats']
    
    def recalculate_stats(self, request, queryset):
        """Action to recalculate user stats"""
        for stats in queryset:
            # Add logic to recalculate stats if needed
            pass
        self.message_user(request, f"Recalculated stats for {queryset.count()} users.")
    recalculate_stats.short_description = "Recalculate selected user stats"  # type: ignore[attr-defined]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'achievement_type', 'points_reward', 'badge_reward',
        'is_active', 'is_hidden', 'users_earned_count'
    ]
    list_filter = ['achievement_type', 'is_active', 'is_hidden', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['achievement_type', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon', 'achievement_type')
        }),
        ('Requirements', {
            'fields': ('requirements',),
            'description': 'JSON object defining achievement requirements'
        }),
        ('Rewards', {
            'fields': ('points_reward', 'badge_reward')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_hidden')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at']
    
    def users_earned_count(self, obj):
        count = UserAchievement.objects.filter(achievement=obj).count()
        if count > 0:
            url = f"{reverse('admin:gamification_userachievement_changelist')}?achievement__id__exact={obj.id}"
            return format_html('<a href="{}">{}</a>', url, count)
        return 0
    users_earned_count.short_description = 'Users Earned'  # type: ignore[attr-defined]


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'achievement', 'earned_at']
    list_filter = ['achievement__achievement_type', 'earned_at']
    search_fields = ['user__username', 'achievement__name']
    ordering = ['-earned_at']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'  # type: ignore[attr-defined]
    user_link.admin_order_field = 'user__username'  # type: ignore[attr-defined]


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'leaderboard_type', 'is_active', 'reset_frequency',
        'last_reset', 'entries_count'
    ]
    list_filter = ['leaderboard_type', 'is_active', 'reset_frequency']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    actions = ['update_leaderboard']
    
    def entries_count(self, obj):
        count = obj.entries.count()  # type: ignore[attr-defined]
        if count > 0:
            url = f"{reverse('admin:gamification_leaderboardentry_changelist')}?leaderboard__id__exact={obj.id}"
            return format_html('<a href="{}">{}</a>', url, count)
        return 0
    entries_count.short_description = 'Entries'  # type: ignore[attr-defined]
    
    def update_leaderboard(self, request, queryset):
        """Action to update selected leaderboards"""
        from .utils import update_leaderboard
        
        for leaderboard in queryset:
            update_leaderboard(leaderboard)
        
        self.message_user(request, f"Updated {queryset.count()} leaderboards.")
    update_leaderboard.short_description = "Update selected leaderboards"  # type: ignore[attr-defined]


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ['leaderboard', 'rank', 'user_link', 'score', 'updated_at']
    list_filter = ['leaderboard', 'updated_at']
    search_fields = ['user__username', 'leaderboard__name']
    ordering = ['leaderboard', 'rank']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'  # type: ignore[attr-defined]
    user_link.admin_order_field = 'user__username'  # type: ignore[attr-defined]


# Custom admin site modifications
admin.site.site_header = "Hybrid LMS - Gamification Admin"
admin.site.site_title = "Gamification Admin"
admin.site.index_title = "Gamification Administration"