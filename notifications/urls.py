from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    # Notification list and detail
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/', views.notification_detail, name='notification_detail'),
    
    # Notification actions
    path('<int:notification_id>/read/', views.mark_read, name='mark_notification_read'),
    path('<int:notification_id>/unread/', views.mark_unread, name='mark_notification_unread'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('<int:notification_id>/archive/', views.archive_notification, name='archive_notification'),
    
    # Bulk actions
    path('mark-all-read/', views.mark_all_read, name='mark_all_notifications_read'),
    path('bulk-read/', views.bulk_mark_read, name='bulk_mark_read'),
    
    # Preferences and stats
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification_preferences'),
    path('stats/', views.notification_stats, name='notification_stats'),
]
