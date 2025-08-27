from django.urls import path
from . import views

urlpatterns = [
    # Live sessions management
    path('', views.LiveSessionListView.as_view(), name='live_sessions'),
    path('<int:pk>/', views.LiveSessionDetailView.as_view(), name='live_session_detail'),
    
    # Session control
    path('<int:session_id>/start/', views.start_session, name='start_session'),
    path('<int:session_id>/end/', views.end_session, name='end_session'),
    
    # Session attendance
    path('<int:session_id>/attendance/', views.SessionAttendanceListView.as_view(), name='session_attendance'),
    path('<int:session_id>/join/', views.join_session, name='join_session'),
    path('<int:session_id>/leave/', views.leave_session, name='leave_session'),
    
    # Session resources
    path('<int:session_id>/resources/', views.SessionResourceListView.as_view(), name='session_resources'),
    
    # Session chat
    path('<int:session_id>/chat/', views.SessionChatListView.as_view(), name='session_chat'),
    
    # Session polls
    path('<int:session_id>/polls/', views.SessionPollListView.as_view(), name='session_polls'),
    path('poll/<int:poll_id>/respond/', views.respond_to_poll, name='respond_to_poll'),
    path('poll/<int:poll_id>/close/', views.close_poll, name='close_poll'),
    
    # Session recordings
    path('recordings/', views.SessionRecordingListView.as_view(), name='session_recordings'),
    
    # Analytics
    path('<int:session_id>/analytics/', views.session_analytics, name='session_analytics'),
]