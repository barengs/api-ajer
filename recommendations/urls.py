from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # Recommendation endpoints
    path('', views.RecommendationListView.as_view(), name='recommendation-list'),
    path('<int:pk>/', views.RecommendationDetailView.as_view(), name='recommendation-detail'),
    path('generate/', views.generate_recommendations_view, name='generate-recommendations'),
    path('<int:recommendation_id>/click/', views.mark_recommendation_clicked_view, name='mark-recommendation-clicked'),
    path('<int:recommendation_id>/feedback/', views.submit_feedback_view, name='submit-feedback'),
    
    # User profile endpoints
    path('profile/', views.UserRecommendationProfileView.as_view(), name='user-profile'),
    
    # Interaction tracking
    path('track-interaction/', views.track_course_interaction_view, name='track-interaction'),
    
    # Feedback endpoints
    path('feedback/', views.RecommendationFeedbackListView.as_view(), name='feedback-list'),
    
    # Settings endpoints
    path('settings/', views.RecommendationSettingsView.as_view(), name='settings'),
]