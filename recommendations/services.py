from django.db import models
from django.db.models import Count, Avg, Q, F, Case, When, Value, FloatField
from django.utils import timezone
from django.conf import settings
from courses.models import Course, Category
from accounts.models import User
from .models import (
    Recommendation, UserRecommendationProfile, UserCourseInteraction,
    RecommendationType, RecommendationAlgorithm, RecommendationSettings
)
import numpy as np
from collections import defaultdict
import logging
from typing import List, Dict, Tuple, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service class for generating AI-powered recommendations
    """
    
    def __init__(self):
        try:
            self.settings = RecommendationSettings.get_settings()
        except Exception:
            # Use default settings if table doesn't exist yet
            self.settings = None
    
    def generate_user_profile(self, user: User) -> UserRecommendationProfile:
        """
        Generate or update user recommendation profile
        """
        profile, created = UserRecommendationProfile.objects.get_or_create(user=user)
        
        # Update learning history
        enrolled_courses = user.enrollments.filter(
            status='active'
        ).values_list('course_id', flat=True)
        
        completed_courses = user.enrollments.filter(
            status='completed'
        ).values_list('course_id', flat=True)
        
        # Update profile
        profile.viewed_courses.set(
            UserCourseInteraction.objects.filter(
                user=user,
                interaction_type=UserCourseInteraction.VIEWED
            ).values_list('course_id', flat=True)
        )
        
        profile.completed_courses.set(completed_courses)
        profile.last_active = timezone.now()
        profile.save()
        
        # Update feature vector
        self._update_user_feature_vector(profile)
        
        return profile
    
    def _update_user_feature_vector(self, profile: UserRecommendationProfile):
        """
        Update user feature vector based on their interactions
        """
        user = profile.user
        
        # Get user interactions
        interactions = UserCourseInteraction.objects.filter(user=user)
        
        # Calculate features
        feature_vector = {
            'total_interactions': interactions.count(),
            'completed_courses_count': profile.completed_courses.count(),
            'enrolled_courses_count': user.enrollments.filter(
                status='active'
            ).count(),
            'avg_rating_given': interactions.filter(
                interaction_type=UserCourseInteraction.RATED
            ).aggregate(avg=Avg('rating'))['avg'] or 0,
            'total_learning_time': profile.total_learning_time,
            'categories_interacted_with': list(interactions.values_list(
                'course__category_id', flat=True
            ).distinct()),
            'difficulty_levels_interacted_with': list(interactions.values_list(
                'course__difficulty_level', flat=True
            ).distinct()),
        }
        
        profile.feature_vector = feature_vector
        profile.save()
    
    def generate_recommendations(self, user: User, force_refresh: bool = False) -> List[Recommendation]:
        """
        Generate recommendations for a user using hybrid approach
        """
        # Check if we need to refresh recommendations
        if not force_refresh and self.settings:
            recent_recommendations = Recommendation.objects.filter(
                user=user,
                generated_at__gte=timezone.now() - timedelta(
                    days=self.settings.recommendation_expiry_days
                )
            ).order_by('-generated_at')
            
            if recent_recommendations.exists():
                return list(recent_recommendations)
        
        # Generate user profile
        profile = self.generate_user_profile(user)
        
        # Clear old recommendations
        Recommendation.objects.filter(user=user).delete()
        
        # Generate recommendations using different algorithms
        recommendations = []
        
        # 1. Collaborative filtering recommendations
        collab_recs = self._collaborative_filtering_recommendations(user, profile)
        recommendations.extend(collab_recs)
        
        # 2. Content-based recommendations
        content_recs = self._content_based_recommendations(user, profile)
        recommendations.extend(content_recs)
        
        # 3. Popularity-based recommendations
        popularity_recs = self._popularity_based_recommendations(user, profile)
        recommendations.extend(popularity_recs)
        
        # 4. Knowledge-based recommendations
        knowledge_recs = self._knowledge_based_recommendations(user, profile)
        recommendations.extend(knowledge_recs)
        
        # Combine and rank recommendations
        final_recommendations = self._combine_and_rank_recommendations(
            recommendations, user
        )
        
        # Save recommendations
        saved_recommendations = []
        for rec_data in final_recommendations:
            recommendation = Recommendation.objects.create(**rec_data)
            saved_recommendations.append(recommendation)
        
        return saved_recommendations
    
    def _collaborative_filtering_recommendations(
        self, user: User, profile: UserRecommendationProfile
    ) -> List[Dict]:
        """
        Generate recommendations using collaborative filtering
        """
        recommendations = []
        
        # Find similar users based on interaction patterns
        similar_users = self._find_similar_users(user, profile)
        
        # Get courses that similar users liked but current user hasn't interacted with
        for similar_user, similarity_score in similar_users[:10]:  # Top 10 similar users
            # Get highly rated courses by similar user
            highly_rated_courses = UserCourseInteraction.objects.filter(
                user=similar_user,
                interaction_type=UserCourseInteraction.RATED,
                rating__gte=4  # 4+ star ratings
            ).exclude(
                course__in=UserCourseInteraction.objects.filter(user=user).values_list('course', flat=True)
            ).select_related('course')
            
            for interaction in highly_rated_courses[:3]:  # Max 3 courses per similar user
                recommendations.append({
                    'user': user,
                    'recommendation_type': RecommendationType.COURSE,
                    'course': interaction.course,
                    'algorithm_used': RecommendationAlgorithm.COLLABORATIVE_FILTERING,
                    'score': (similarity_score * interaction.rating) / 5.0,  # Normalize to 0-1
                    'reason': f"Users with similar interests to you highly rated this course",
                    'reason_data': {
                        'similar_user_id': similar_user.id,
                        'similarity_score': similarity_score,
                        'rating': interaction.rating
                    }
                })
        
        return recommendations
    
    def _content_based_recommendations(
        self, user: User, profile: UserRecommendationProfile
    ) -> List[Dict]:
        """
        Generate recommendations based on user's content preferences
        """
        recommendations = []
        
        # Get user's preferred categories
        preferred_categories = profile.preferred_categories
        
        # If we don't have explicit preferences, infer from interactions
        if not preferred_categories:
            category_interactions = UserCourseInteraction.objects.filter(
                user=user
            ).values('course__category').annotate(
                count=Count('id')
            ).order_by('-count')
            
            preferred_categories = [
                item['course__category'] for item in category_interactions[:3]
            ]
        
        # Get courses from preferred categories that user hasn't interacted with
        courses = Course.objects.filter(
            category_id__in=preferred_categories,
            status=Course.CourseStatus.PUBLISHED
        ).exclude(
            id__in=UserCourseInteraction.objects.filter(
                user=user
            ).values_list('course_id', flat=True)
        ).annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating')[:10]
        
        for i, course in enumerate(courses):
            score = 0.8 - (i * 0.05)  # Decreasing score for lower ranked courses
            recommendations.append({
                'user': user,
                'recommendation_type': RecommendationType.COURSE,
                'course': course,
                'algorithm_used': RecommendationAlgorithm.CONTENT_BASED,
                'score': max(0.1, score),  # Minimum score of 0.1
                'reason': f"Based on your interest in {course.category.name if course.category else 'similar topics'}",
                'reason_data': {
                    'category_id': course.category.id if course.category else None,
                    'category_name': course.category.name if course.category else 'Unknown'
                }
            })
        
        return recommendations
    
    def _popularity_based_recommendations(
        self, user: User, profile: UserRecommendationProfile
    ) -> List[Dict]:
        """
        Generate recommendations based on course popularity
        """
        recommendations = []
        
        # Get popular courses (high enrollment, high ratings)
        popular_courses = Course.objects.filter(
            status=Course.CourseStatus.PUBLISHED
        ).annotate(
            enrollment_count=Count('enrollments'),
            avg_rating=Avg('reviews__rating'),
            popularity_score=F('enrollment_count') * 0.7 + 
                           (F('avg_rating') * 10 if F('avg_rating') else 0) * 0.3
        ).exclude(
            id__in=UserCourseInteraction.objects.filter(
                user=user
            ).values_list('course_id', flat=True)
        ).order_by('-popularity_score')[:10]
        
        for i, course in enumerate(popular_courses):
            score = 0.7 - (i * 0.05)  # Decreasing score for lower ranked courses
            recommendations.append({
                'user': user,
                'recommendation_type': RecommendationType.COURSE,
                'course': course,
                'algorithm_used': RecommendationAlgorithm.POPULARITY,
                'score': max(0.1, score),  # Minimum score of 0.1
                'reason': f"Popular course with {course.enrollment_count} enrollments and {course.avg_rating:.1f} average rating",
                'reason_data': {
                    'enrollment_count': course.enrollment_count,
                    'avg_rating': float(course.avg_rating) if course.avg_rating else 0
                }
            })
        
        return recommendations
    
    def _knowledge_based_recommendations(
        self, user: User, profile: UserRecommendationProfile
    ) -> List[Dict]:
        """
        Generate recommendations based on explicit knowledge and rules
        """
        recommendations = []
        
        # Recommend courses that complement completed courses
        completed_courses = profile.completed_courses.all()
        
        if completed_courses.exists():
            # Get categories of completed courses
            completed_categories = completed_courses.values_list(
                'category_id', flat=True
            ).distinct()
            
            # Recommend advanced courses in same categories
            advanced_courses = Course.objects.filter(
                category_id__in=completed_categories,
                difficulty_level=Case(
                    When(difficulty_level='beginner', then=Value('intermediate')),
                    When(difficulty_level='intermediate', then=Value('advanced')),
                    default=Value('advanced')
                ),
                status=Course.CourseStatus.PUBLISHED
            ).exclude(
                id__in=UserCourseInteraction.objects.filter(
                    user=user
                ).values_list('course_id', flat=True)
            )[:5]
            
            for course in advanced_courses:
                recommendations.append({
                    'user': user,
                    'recommendation_type': RecommendationType.COURSE,
                    'course': course,
                    'algorithm_used': RecommendationAlgorithm.KNOWLEDGE_BASED,
                    'score': 0.9,  # High confidence
                    'reason': f"Next step after completing {course.category.name if course.category else 'related'} courses",
                    'reason_data': {
                        'based_on_completed_category': course.category.id if course.category else None
                    }
                })
        
        # Recommend trending courses
        trending_courses = Course.objects.filter(
            status=Course.CourseStatus.PUBLISHED,
            created_at__gte=timezone.now() - timedelta(days=30)  # Last 30 days
        ).annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:5]
        
        for course in trending_courses:
            recommendations.append({
                'user': user,
                'recommendation_type': RecommendationType.COURSE,
                'course': course,
                'algorithm_used': RecommendationAlgorithm.KNOWLEDGE_BASED,
                'score': 0.8,
                'reason': f"New and trending course with {course.enrollment_count} recent enrollments",
                'reason_data': {
                    'recent_enrollments': course.enrollment_count,
                    'days_old': (timezone.now() - course.created_at).days
                }
            })
        
        return recommendations
    
    def _find_similar_users(self, user: User, profile: UserRecommendationProfile) -> List[Tuple[User, float]]:
        """
        Find users with similar interaction patterns
        """
        # Get all users who have interacted with courses
        all_users = User.objects.filter(
            course_interactions__isnull=False
        ).distinct()
        
        similarities = []
        
        # Calculate similarity with each user
        for other_user in all_users:
            if other_user.id == user.id:
                continue
                
            similarity = self._calculate_user_similarity(user, other_user)
            if similarity > 0.1:  # Only consider users with some similarity
                similarities.append((other_user, similarity))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def _calculate_user_similarity(self, user1: User, user2: User) -> float:
        """
        Calculate similarity between two users based on their interactions
        """
        # Get interactions for both users
        user1_interactions = set(UserCourseInteraction.objects.filter(
            user=user1
        ).values_list('course_id', flat=True))
        
        user2_interactions = set(UserCourseInteraction.objects.filter(
            user=user2
        ).values_list('course_id', flat=True))
        
        if not user1_interactions or not user2_interactions:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(user1_interactions & user2_interactions)
        union = len(user1_interactions | user2_interactions)
        
        if union == 0:
            return 0.0
            
        return intersection / union
    
    def _combine_and_rank_recommendations(
        self, recommendations: List[Dict], user: User
    ) -> List[Dict]:
        """
        Combine recommendations from different algorithms and rank them
        """
        # Group recommendations by course
        course_recommendations = defaultdict(list)
        
        for rec in recommendations:
            if rec['course']:
                course_recommendations[rec['course'].id].append(rec)
        
        # Combine scores for each course
        final_recommendations = []
        
        for course_id, recs in course_recommendations.items():
            # Calculate weighted score based on algorithm
            total_score = 0
            weight_sum = 0
            reasons = []
            reason_data = {}
            
            for rec in recs:
                # Assign weights to different algorithms
                weight = self._get_algorithm_weight(rec['algorithm_used'])
                total_score += rec['score'] * weight
                weight_sum += weight
                
                reasons.append(rec['reason'])
                reason_data.update(rec['reason_data'])
            
            # Average the weighted scores
            if weight_sum > 0:
                avg_score = total_score / weight_sum
            else:
                avg_score = sum(rec['score'] for rec in recs) / len(recs)
            
            # Use the first recommendation as base and update score
            final_rec = recs[0].copy()
            final_rec['score'] = avg_score
            final_rec['reason'] = ' | '.join(reasons[:3])  # Limit to 3 reasons
            final_rec['reason_data'] = reason_data
            
            final_recommendations.append(final_rec)
        
        # Sort by score and limit to max recommendations
        final_recommendations.sort(key=lambda x: x['score'], reverse=True)
        max_recommendations = self.settings.max_recommendations_per_user if self.settings else 10
        return final_recommendations[:max_recommendations]
    
    def _get_algorithm_weight(self, algorithm: str) -> float:
        """
        Get weight for recommendation algorithm (can be customized)
        """
        weights = {
            RecommendationAlgorithm.COLLABORATIVE_FILTERING: 0.3,
            RecommendationAlgorithm.CONTENT_BASED: 0.25,
            RecommendationAlgorithm.POPULARITY: 0.2,
            RecommendationAlgorithm.KNOWLEDGE_BASED: 0.25,
        }
        return weights.get(algorithm, 0.2)
    
    def track_user_interaction(
        self, user: User, course: Course, interaction_type: str, **kwargs
    ):
        """
        Track user interaction with a course for recommendation purposes
        """
        try:
            interaction, created = UserCourseInteraction.objects.update_or_create(
                user=user,
                course=course,
                interaction_type=interaction_type,
                defaults=kwargs
            )
            
            # Update user profile
            self.generate_user_profile(user)
            
            return interaction
        except Exception as e:
            logger.error(f"Error tracking user interaction: {e}")
            return None
    
    def get_user_recommendations(self, user: User) -> List[Recommendation]:
        """
        Get current recommendations for a user
        """
        return Recommendation.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        ).select_related('course').order_by('-score')
    
    def mark_recommendation_clicked(self, recommendation_id: int, user: User):
        """
        Mark a recommendation as clicked by the user
        """
        try:
            recommendation = Recommendation.objects.get(
                id=recommendation_id,
                user=user
            )
            recommendation.is_clicked = True
            recommendation.clicked_at = timezone.now()
            recommendation.save()
            return recommendation
        except Recommendation.DoesNotExist:
            return None
    
    def submit_feedback(
        self, recommendation_id: int, user: User, feedback_type: str, comment: str = ""
    ):
        """
        Submit feedback on a recommendation
        """
        from .models import RecommendationFeedback
        
        try:
            recommendation = Recommendation.objects.get(
                id=recommendation_id,
                user=user
            )
            
            feedback, created = RecommendationFeedback.objects.update_or_create(
                user=user,
                recommendation=recommendation,
                defaults={
                    'feedback_type': feedback_type,
                    'comment': comment
                }
            )
            
            return feedback
        except Recommendation.DoesNotExist:
            return None


# Singleton instance
recommendation_service = RecommendationService()