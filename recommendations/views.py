from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    Recommendation, RecommendationFeedback, 
    RecommendationSettings, UserRecommendationProfile
)
from .serializers import (
    RecommendationSerializer, RecommendationFeedbackSerializer,
    RecommendationSettingsSerializer, UserRecommendationProfileSerializer,
    UserCourseInteractionSerializer
)
from .services import recommendation_service
from courses.models import Course


class RecommendationListView(generics.ListAPIView):
    """View to list recommendations for the authenticated user"""
    
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Recommendation.objects.filter(
            user=self.request.user,
            expires_at__gt=timezone.now()
        ).select_related('course').order_by('-score')


class RecommendationDetailView(generics.RetrieveAPIView):
    """View to retrieve a specific recommendation"""
    
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_recommendations_view(request):
    """
    Generate new recommendations for the authenticated user
    """
    try:
        recommendations = recommendation_service.generate_recommendations(
            request.user, force_refresh=True
        )
        serializer = RecommendationSerializer(recommendations, many=True)
        return Response({
            'message': 'Recommendations generated successfully',
            'recommendations': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Failed to generate recommendations: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_recommendation_clicked_view(request, recommendation_id):
    """
    Mark a recommendation as clicked by the user
    """
    try:
        recommendation = recommendation_service.mark_recommendation_clicked(
            recommendation_id, request.user
        )
        if recommendation:
            return Response({
                'message': 'Recommendation marked as clicked'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Recommendation not found'
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to mark recommendation as clicked: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback_view(request, recommendation_id):
    """
    Submit feedback on a recommendation
    """
    try:
        feedback_type = request.data.get('feedback_type')
        comment = request.data.get('comment', '')
        
        if not feedback_type:
            return Response({
                'error': 'feedback_type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        feedback = recommendation_service.submit_feedback(
            recommendation_id, request.user, feedback_type, comment
        )
        
        if feedback:
            serializer = RecommendationFeedbackSerializer(feedback)
            return Response({
                'message': 'Feedback submitted successfully',
                'feedback': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Recommendation not found'
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to submit feedback: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendationFeedbackListView(generics.ListAPIView):
    """View to list feedback for recommendations"""
    
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RecommendationFeedback.objects.filter(
            user=self.request.user
        ).select_related('recommendation')


class UserRecommendationProfileView(generics.RetrieveUpdateAPIView):
    """View to retrieve and update user recommendation profile"""
    
    serializer_class = UserRecommendationProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        profile, created = UserRecommendationProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_course_interaction_view(request):
    """
    Track user interaction with a course
    """
    try:
        course_id = request.data.get('course_id')
        interaction_type = request.data.get('interaction_type')
        
        if not course_id or not interaction_type:
            return Response({
                'error': 'course_id and interaction_type are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course = get_object_or_404(Course, id=course_id)
        
        # Additional data for the interaction
        rating = request.data.get('rating')
        time_spent = request.data.get('time_spent', 0)
        
        interaction_data = {}
        if rating:
            interaction_data['rating'] = rating
        if time_spent:
            interaction_data['time_spent'] = time_spent
        
        interaction = recommendation_service.track_user_interaction(
            request.user, course, interaction_type, **interaction_data
        )
        
        if interaction:
            serializer = UserCourseInteractionSerializer(interaction)
            return Response({
                'message': 'Interaction tracked successfully',
                'interaction': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to track interaction'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            'error': f'Failed to track interaction: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendationSettingsView(generics.RetrieveUpdateAPIView):
    """View to retrieve and update recommendation settings"""
    
    serializer_class = RecommendationSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return RecommendationSettings.get_settings()