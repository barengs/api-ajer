from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import Course, Category
from .models import (
    UserRecommendationProfile, UserCourseInteraction, 
    Recommendation, RecommendationFeedback, RecommendationSettings
)
from .services import RecommendationService

User = get_user_model()


class RecommendationModelsTest(TestCase):
    """Test cases for recommendation models"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='Test course description',
            instructor=self.user,
            category=self.category,
            price=99.99
        )
    
    def test_user_recommendation_profile_creation(self):
        """Test creation of user recommendation profile"""
        profile = UserRecommendationProfile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.preferred_categories, [])
        self.assertEqual(profile.preferred_difficulty_levels, [])
        
    def test_user_course_interaction_creation(self):
        """Test creation of user course interaction"""
        interaction = UserCourseInteraction.objects.create(
            user=self.user,
            course=self.course,
            interaction_type=UserCourseInteraction.VIEWED
        )
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.course, self.course)
        self.assertEqual(interaction.interaction_type, UserCourseInteraction.VIEWED)
        
    def test_recommendation_creation(self):
        """Test creation of recommendation"""
        recommendation = Recommendation.objects.create(
            user=self.user,
            recommendation_type='course',
            course=self.course,
            algorithm_used='content',
            score=0.85
        )
        self.assertEqual(recommendation.user, self.user)
        self.assertEqual(recommendation.course, self.course)
        self.assertEqual(recommendation.score, 0.85)
        
    def test_recommendation_feedback_creation(self):
        """Test creation of recommendation feedback"""
        recommendation = Recommendation.objects.create(
            user=self.user,
            recommendation_type='course',
            course=self.course,
            algorithm_used='content',
            score=0.85
        )
        
        feedback = RecommendationFeedback.objects.create(
            user=self.user,
            recommendation=recommendation,
            feedback_type=RecommendationFeedback.HELPFUL
        )
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.recommendation, recommendation)
        self.assertEqual(feedback.feedback_type, RecommendationFeedback.HELPFUL)


class RecommendationServiceTest(TestCase):
    """Test cases for recommendation service"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        # Create test courses
        self.course1 = Course.objects.create(
            title='Test Course 1',
            description='Test course 1 description',
            instructor=self.user,
            category=self.category,
            price=99.99
        )
        
        self.course2 = Course.objects.create(
            title='Test Course 2',
            description='Test course 2 description',
            instructor=self.user,
            category=self.category,
            price=149.99
        )
        
        # Initialize recommendation service
        self.service = RecommendationService()
    
    def test_generate_user_profile(self):
        """Test generating user recommendation profile"""
        profile = self.service.generate_user_profile(self.user)
        self.assertIsInstance(profile, UserRecommendationProfile)
        self.assertEqual(profile.user, self.user)
        
    def test_track_user_interaction(self):
        """Test tracking user interaction"""
        interaction = self.service.track_user_interaction(
            self.user,
            self.course1,
            UserCourseInteraction.VIEWED
        )
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.course, self.course1)
        self.assertEqual(interaction.interaction_type, UserCourseInteraction.VIEWED)
        
    def test_generate_recommendations(self):
        """Test generating recommendations"""
        # Track some interactions first
        self.service.track_user_interaction(
            self.user,
            self.course1,
            UserCourseInteraction.VIEWED
        )
        
        # Generate recommendations
        recommendations = self.service.generate_recommendations(self.user)
        self.assertIsInstance(recommendations, list)
        
    def test_mark_recommendation_clicked(self):
        """Test marking recommendation as clicked"""
        # Create a recommendation first
        recommendation = Recommendation.objects.create(
            user=self.user,
            recommendation_type='course',
            course=self.course1,
            algorithm_used='content',
            score=0.85
        )
        
        # Mark as clicked
        clicked_recommendation = self.service.mark_recommendation_clicked(
            recommendation.id, self.user
        )
        self.assertIsNotNone(clicked_recommendation)
        self.assertTrue(clicked_recommendation.is_clicked)
        self.assertIsNotNone(clicked_recommendation.clicked_at)
        
    def test_submit_feedback(self):
        """Test submitting feedback"""
        # Create a recommendation first
        recommendation = Recommendation.objects.create(
            user=self.user,
            recommendation_type='course',
            course=self.course1,
            algorithm_used='content',
            score=0.85
        )
        
        # Submit feedback
        feedback = self.service.submit_feedback(
            recommendation.id,
            self.user,
            RecommendationFeedback.HELPFUL,
            "This was very helpful"
        )
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback.feedback_type, RecommendationFeedback.HELPFUL)
        self.assertEqual(feedback.comment, "This was very helpful")


class RecommendationSettingsTest(TestCase):
    """Test cases for recommendation settings"""
    
    def test_get_settings(self):
        """Test getting recommendation settings"""
        settings = RecommendationSettings.get_settings()
        self.assertIsInstance(settings, RecommendationSettings)
        self.assertEqual(settings.default_algorithm, 'hybrid')
        self.assertEqual(settings.max_recommendations_per_user, 10)