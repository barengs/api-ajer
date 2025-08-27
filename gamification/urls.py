from django.urls import path
from . import views

urlpatterns = [
    # User gamification data
    path('profile/', views.UserGamificationProfileView.as_view(), name='user_gamification_profile'),
    path('badges/', views.UserBadgesView.as_view(), name='user_badges'),
    path('achievements/', views.UserAchievementsView.as_view(), name='user_achievements'),
    path('points/history/', views.PointsHistoryView.as_view(), name='points_history'),
    path('level/progress/', views.LevelProgressView.as_view(), name='level_progress'),
    
    # Leaderboards
    path('leaderboards/', views.LeaderboardListView.as_view(), name='leaderboard_list'),
    path('leaderboards/<str:type>/', views.LeaderboardDetailView.as_view(), name='leaderboard_detail'),
    
    # Browse achievements and badges
    path('browse/badges/', views.BadgeTypeListView.as_view(), name='badge_types'),
    path('browse/achievements/', views.AchievementListView.as_view(), name='achievements_browse'),
    path('browse/levels/', views.UserLevelListView.as_view(), name='user_levels'),
    
    # Admin/Instructor actions
    path('admin/award-points/', views.AwardPointsView.as_view(), name='award_points'),
    path('admin/award-badge/', views.AwardBadgeView.as_view(), name='award_badge'),
    path('admin/badges/', views.BadgeTypeManagementView.as_view(), name='manage_badges'),
    path('admin/achievements/', views.AchievementManagementView.as_view(), name='manage_achievements'),
    
    # Stats and analytics
    path('stats/', views.GamificationStatsView.as_view(), name='gamification_stats'),
    path('daily-login/', views.DailyLoginView.as_view(), name='daily_login'),
]