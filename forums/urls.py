from django.urls import path
from . import views
from .views import ForumReplyListView  # Explicit import to ensure class is recognized

urlpatterns = [
    # Course forums
    path('course/<int:course_id>/', views.CourseForumListView.as_view(), name='course_forums'),
    
    # Forum posts
    path('<int:forum_id>/posts/', views.ForumPostListView.as_view(), name='forum_posts'),
    path('post/<int:pk>/', views.ForumPostDetailView.as_view(), name='post_detail'),
    
    # Forum replies
    path('post/<int:post_id>/replies/', views.ForumReplyListView.as_view(), name='post_replies'),
    path('reply/<int:pk>/', views.ForumReplyDetailView.as_view(), name='reply_detail'),
    
    # Voting
    path('post/<int:post_id>/vote/', views.vote_post, name='vote_post'),
    path('reply/<int:reply_id>/vote/', views.vote_reply, name='vote_reply'),
    
    # Q&A features
    path('reply/<int:reply_id>/accept/', views.accept_answer, name='accept_answer'),
    
    # Subscriptions
    path('post/<int:post_id>/subscribe/', views.subscribe_to_post, name='subscribe_post'),
    path('subscriptions/', views.UserForumSubscriptionListView.as_view(), name='user_subscriptions'),
    
    # Content moderation
    path('report/<str:content_type>/<int:content_id>/', views.report_content, name='report_content'),
    
    # Search
    path('search/', views.forum_search, name='forum_search'),
]