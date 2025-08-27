from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from typing import cast, Any

from .models import (
    BadgeType, UserBadge, PointsTransaction, UserLevel, UserStats,
    Achievement, UserAchievement, Leaderboard, LeaderboardEntry
)
from .utils import (
    get_or_create_user_stats, award_points, check_user_badges,
    check_user_achievements, get_next_level_progress
)
from .signals import trigger_daily_login

User = get_user_model()


class GamificationModelsTest(TestCase):
    """Test gamification models"""
    
    def setUp(self):
        self.user = cast('User', User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        ))
        
        # Create test level
        self.level = UserLevel.objects.create(
            level=1,
            name='Beginner',
            min_points=0,
            max_points=99
        )
        
        # Create test badge type
        self.badge_type = BadgeType.objects.create(
            name='First Steps',
            description='Complete your first lesson',
            category='learning',
            points_required=10
        )
        
        # Create test achievement
        self.achievement = Achievement.objects.create(
            name='Test Achievement',
            description='Test description',
            achievement_type='milestone',
            requirements={'lessons_completed': 1},
            points_reward=20
        )
    
    def test_user_stats_creation(self):
        """Test user stats creation and point addition"""
        stats = get_or_create_user_stats(self.user)
        
        self.assertEqual(stats.user, self.user)
        self.assertEqual(stats.total_points, 0)
        self.assertIsNone(stats.current_level)
        
        # Add points
        stats.add_points(
            50, 
            PointsTransaction.TransactionType.LESSON_COMPLETE,
            'Completed first lesson'
        )
        
        self.assertEqual(stats.total_points, 50)
        self.assertIsNotNone(stats.current_level)
    
    def test_badge_earning(self):
        """Test badge earning functionality"""
        # Award badge
        user_badge = UserBadge.objects.create(
            user=self.user,
            badge_type=self.badge_type
        )
        
        self.assertEqual(user_badge.user, self.user)
        self.assertEqual(user_badge.badge_type, self.badge_type)
        
        # Test unique constraint
        with self.assertRaises(Exception):
            UserBadge.objects.create(
                user=self.user,
                badge_type=self.badge_type
            )
    
    def test_points_transaction(self):
        """Test points transaction creation"""
        transaction = PointsTransaction.objects.create(
            user=self.user,
            points=25,
            transaction_type=PointsTransaction.TransactionType.LESSON_COMPLETE,
            description='Completed lesson'
        )
        
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.points, 25)
    
    def test_achievement_earning(self):
        """Test achievement earning"""
        user_achievement = UserAchievement.objects.create(
            user=self.user,
            achievement=self.achievement
        )
        
        self.assertEqual(user_achievement.user, self.user)
        self.assertEqual(user_achievement.achievement, self.achievement)


class GamificationUtilsTest(TestCase):
    """Test gamification utility functions"""
    
    def setUp(self):
        self.user = cast('User', User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        ))
        
        # Create levels
        UserLevel.objects.create(level=1, name='Beginner', min_points=0, max_points=99)
        UserLevel.objects.create(level=2, name='Novice', min_points=100, max_points=199)
        
        # Create badge type
        self.badge_type = BadgeType.objects.create(
            name='Points Collector',
            description='Earn 100 points',
            category='achievement',
            points_required=100
        )
    
    def test_award_points(self):
        """Test points awarding function"""
        award_points(
            self.user,
            50,
            PointsTransaction.TransactionType.LESSON_COMPLETE,
            'Completed lesson'
        )
        
        stats = UserStats.objects.get(user=self.user)
        self.assertEqual(stats.total_points, 50)
        
        # Check transaction was created
        transaction = PointsTransaction.objects.get(user=self.user)
        self.assertEqual(transaction.points, 50)
    
    def test_level_progression(self):
        """Test level progression"""
        award_points(
            self.user,
            150,
            PointsTransaction.TransactionType.COURSE_COMPLETE,
            'Completed course'
        )
        
        stats = UserStats.objects.get(user=self.user)
        self.assertEqual(stats.current_level.level, 2)
        self.assertEqual(stats.current_level.name, 'Novice')
    
    def test_next_level_progress(self):
        """Test next level progress calculation"""
        award_points(
            self.user,
            50,
            PointsTransaction.TransactionType.LESSON_COMPLETE,
            'Lesson completed'
        )
        
        progress = get_next_level_progress(self.user)
        
        self.assertIn('current_points', progress)
        self.assertIn('next_level', progress)
        self.assertIn('points_needed', progress)
        self.assertIn('progress_percentage', progress)
    
    def test_check_user_badges(self):
        """Test badge checking functionality"""
        # Award enough points to earn badge
        award_points(
            self.user,
            100,
            PointsTransaction.TransactionType.COURSE_COMPLETE,
            'Course completed'
        )
        
        # Check badges
        check_user_badges(self.user)
        
        # Verify badge was awarded
        self.assertTrue(
            UserBadge.objects.filter(
                user=self.user,
                badge_type=self.badge_type
            ).exists()
        )


class GamificationAPITest(APITestCase):
    """Test gamification API endpoints"""
    
    def setUp(self):
        self.user = cast('User', User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        ))
        
        self.admin_user = cast('User', User.objects.create_user(  # type: ignore
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        ))
        setattr(self.admin_user, 'role', 'admin')
        self.admin_user.save()
        
        # Create test data
        self.level = UserLevel.objects.create(
            level=1,
            name='Beginner',
            min_points=0,
            max_points=99
        )
        
        self.badge_type = BadgeType.objects.create(
            name='Test Badge',
            description='Test badge',
            category='learning'
        )
        
        # Create user stats
        self.stats = get_or_create_user_stats(self.user)
    
    def test_user_profile_endpoint(self):
        """Test user gamification profile endpoint"""
        self.client.force_authenticate(user=self.user)  # type: ignore
        url = reverse('user_gamification_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertIn('total_points', response.data)  # type: ignore
        self.assertIn('current_level', response.data)  # type: ignore
        self.assertIn('badges', response.data)  # type: ignore
    
    def test_user_badges_endpoint(self):
        """Test user badges listing endpoint"""
        # Award badge
        UserBadge.objects.create(user=self.user, badge_type=self.badge_type)
        
        self.client.force_authenticate(user=self.user)  # type: ignore
        url = reverse('user_badges')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.data['results']), 1)  # type: ignore
    
    def test_points_history_endpoint(self):
        """Test points history endpoint"""
        # Create transaction
        PointsTransaction.objects.create(
            user=self.user,
            points=50,
            transaction_type=PointsTransaction.TransactionType.LESSON_COMPLETE,
            description='Test transaction'
        )
        
        self.client.force_authenticate(user=self.user)  # type: ignore
        url = reverse('points_history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(len(response.data['results']), 1)  # type: ignore
    
    def test_award_points_admin_only(self):
        """Test award points endpoint (admin only)"""
        # Test non-admin access
        self.client.force_authenticate(user=self.user)  # type: ignore
        url = reverse('award_points')
        data = {
            'user_id': self.user.id,  # type: ignore
            'points': 50,
            'transaction_type': 'bonus',
            'description': 'Admin bonus'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore
        
        # Test admin access
        self.client.force_authenticate(user=self.admin_user)  # type: ignore
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
    
    def test_daily_login_endpoint(self):
        """Test daily login bonus endpoint"""
        self.client.force_authenticate(user=self.user)  # type: ignore
        url = reverse('daily_login')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertIn('points_awarded', response.data)  # type: ignore
        self.assertIn('current_streak', response.data)  # type: ignore
        
        # Test duplicate claim (should fail)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore
    
    def test_leaderboard_endpoints(self):
        """Test leaderboard endpoints"""
        # Create leaderboard
        leaderboard = Leaderboard.objects.create(
            name='Test Leaderboard',
            leaderboard_type='overall_points',
            description='Test leaderboard'
        )
        
        # Test list endpoint
        url = reverse('leaderboard_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        
        # Test detail endpoint
        url = reverse('leaderboard_detail', kwargs={'type': 'overall_points'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore


class GamificationSignalsTest(TestCase):
    """Test gamification signals"""
    
    def setUp(self):
        self.user = cast('User', User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        ))
    
    def test_daily_login_trigger(self):
        """Test daily login trigger"""
        # Trigger daily login
        trigger_daily_login(self.user)
        
        # Check stats updated
        stats = UserStats.objects.get(user=self.user)
        self.assertEqual(stats.current_login_streak, 1)
        
        # Check transaction created
        transaction = PointsTransaction.objects.filter(
            user=self.user,
            transaction_type=PointsTransaction.TransactionType.DAILY_LOGIN
        )
        self.assertTrue(transaction.exists())


class GamificationIntegrationTest(TestCase):
    """Integration tests for complete gamification workflows"""
    
    def setUp(self):
        self.user = cast('User', User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        ))
        
        # Create complete setup
        UserLevel.objects.create(level=1, name='Beginner', min_points=0, max_points=99)
        UserLevel.objects.create(level=2, name='Intermediate', min_points=100, max_points=299)
        
        BadgeType.objects.create(
            name='First Course',
            description='Complete first course',
            category='learning',
            points_required=50
        )
        
        Achievement.objects.create(
            name='Course Master',
            description='Complete 1 course',
            achievement_type='milestone',
            requirements={'courses_completed': 1},
            points_reward=100
        )
    
    def test_complete_learning_journey(self):
        """Test a complete learning journey with gamification"""
        # Start - user has no points
        stats = get_or_create_user_stats(self.user)
        self.assertEqual(stats.total_points, 0)
        
        # Complete lessons (simulate learning progress)
        for i in range(5):
            award_points(
                self.user,
                10,
                PointsTransaction.TransactionType.LESSON_COMPLETE,
                f'Completed lesson {i+1}'
            )
        
        # Complete course
        stats.courses_completed = 1
        stats.save()
        
        award_points(
            self.user,
            50,
            PointsTransaction.TransactionType.COURSE_COMPLETE,
            'Completed course'
        )
        
        # Check achievements
        check_user_achievements(self.user)
        
        # Check badges
        check_user_badges(self.user)
        
        # Final verification
        stats.refresh_from_db()
        
        # Should have points from lessons + course + achievement
        expected_points = (5 * 10) + 50 + 100  # 200 points
        self.assertEqual(stats.total_points, expected_points)
        
        # Should be at level 2
        self.assertEqual(stats.current_level.level, 2)
        
        # Should have earned badge
        self.assertTrue(
            UserBadge.objects.filter(
                user=self.user,
                badge_type__name='First Course'
            ).exists()
        )
        
        # Should have earned achievement
        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user,
                achievement__name='Course Master'
            ).exists()
        )