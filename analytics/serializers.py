from rest_framework import serializers
from decimal import Decimal
from datetime import date, timedelta
from .models import (
    PlatformMetrics, InstructorMetrics, CourseMetrics, 
    StudentMetrics, AnalyticsSnapshot
)


class PlatformMetricsSerializer(serializers.ModelSerializer):
    """Serializer for platform metrics"""
    
    growth_rate = serializers.SerializerMethodField()
    revenue_growth = serializers.SerializerMethodField()
    
    class Meta:
        model = PlatformMetrics
        fields = [
            'date', 'total_users', 'new_users', 'active_users',
            'total_courses', 'new_courses', 'published_courses',
            'total_revenue', 'daily_revenue', 'refunds',
            'total_enrollments', 'new_enrollments', 'completed_courses',
            'forum_posts', 'lesson_completions', 'assignment_submissions',
            'growth_rate', 'revenue_growth'
        ]
    
    def get_growth_rate(self, obj):
        """Calculate user growth rate compared to previous day"""
        try:
            previous_day = PlatformMetrics.objects.filter(
                date=obj.date - timedelta(days=1)
            ).first()
            
            if previous_day and previous_day.total_users > 0:
                growth = ((obj.total_users - previous_day.total_users) / previous_day.total_users) * 100
                return round(float(growth), 2)
            return 0.0
        except:
            return 0.0
    
    def get_revenue_growth(self, obj):
        """Calculate revenue growth compared to previous day"""
        try:
            previous_day = PlatformMetrics.objects.filter(
                date=obj.date - timedelta(days=1)
            ).first()
            
            if previous_day and previous_day.total_revenue > 0:
                growth = ((obj.total_revenue - previous_day.total_revenue) / previous_day.total_revenue) * 100
                return round(float(growth), 2)
            return 0.0
        except:
            return 0.0


class InstructorMetricsSerializer(serializers.ModelSerializer):
    """Serializer for instructor metrics"""
    
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    instructor_email = serializers.CharField(source='instructor.email', read_only=True)
    earnings_growth = serializers.SerializerMethodField()
    student_growth = serializers.SerializerMethodField()
    
    class Meta:
        model = InstructorMetrics
        fields = [
            'instructor_name', 'instructor_email', 'date',
            'total_courses', 'published_courses', 'draft_courses',
            'total_students', 'new_students', 'active_students',
            'total_earnings', 'daily_earnings', 'earnings_growth',
            'average_rating', 'total_reviews', 'completion_rate',
            'forum_interactions', 'student_questions', 'response_time_hours',
            'student_growth'
        ]
    
    def get_earnings_growth(self, obj):
        """Calculate earnings growth compared to previous day"""
        try:
            previous_day = InstructorMetrics.objects.filter(
                instructor=obj.instructor,
                date=obj.date - timedelta(days=1)
            ).first()
            
            if previous_day and previous_day.total_earnings > 0:
                growth = ((obj.total_earnings - previous_day.total_earnings) / previous_day.total_earnings) * 100
                return round(float(growth), 2)
            return 0.0
        except:
            return 0.0
    
    def get_student_growth(self, obj):
        """Calculate student growth compared to previous day"""
        try:
            previous_day = InstructorMetrics.objects.filter(
                instructor=obj.instructor,
                date=obj.date - timedelta(days=1)
            ).first()
            
            if previous_day and previous_day.total_students > 0:
                growth = ((obj.total_students - previous_day.total_students) / previous_day.total_students) * 100
                return round(float(growth), 2)
            return 0.0
        except:
            return 0.0


class CourseMetricsSerializer(serializers.ModelSerializer):
    """Serializer for course metrics"""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    instructor_name = serializers.CharField(source='course.instructor.get_full_name', read_only=True)
    enrollment_growth = serializers.SerializerMethodField()
    revenue_growth = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseMetrics
        fields = [
            'course_title', 'course_slug', 'instructor_name', 'date',
            'total_enrollments', 'new_enrollments', 'active_students', 'completed_students',
            'average_progress', 'completion_rate', 'dropout_rate',
            'revenue', 'daily_revenue', 'enrollment_growth', 'revenue_growth',
            'lesson_views', 'assignment_submissions', 'forum_posts', 'quiz_attempts',
            'average_rating', 'total_reviews'
        ]
    
    def get_enrollment_growth(self, obj):
        """Calculate enrollment growth compared to previous day"""
        try:
            previous_day = CourseMetrics.objects.filter(
                course=obj.course,
                date=obj.date - timedelta(days=1)
            ).first()
            
            if previous_day and previous_day.total_enrollments > 0:
                growth = ((obj.total_enrollments - previous_day.total_enrollments) / previous_day.total_enrollments) * 100
                return round(float(growth), 2)
            return 0.0
        except:
            return 0.0
    
    def get_revenue_growth(self, obj):
        """Calculate revenue growth compared to previous day"""
        try:
            previous_day = CourseMetrics.objects.filter(
                course=obj.course,
                date=obj.date - timedelta(days=1)
            ).first()
            
            if previous_day and previous_day.revenue > 0:
                growth = ((obj.revenue - previous_day.revenue) / previous_day.revenue) * 100
                return round(float(growth), 2)
            return 0.0
        except:
            return 0.0


class StudentMetricsSerializer(serializers.ModelSerializer):
    """Serializer for student metrics"""
    
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    learning_progress = serializers.SerializerMethodField()
    activity_score = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentMetrics
        fields = [
            'student_name', 'student_email', 'date',
            'courses_enrolled', 'courses_completed', 'courses_in_progress',
            'lessons_completed', 'assignments_submitted', 'quizzes_taken', 'forum_posts',
            'total_study_time_minutes', 'daily_study_time_minutes', 'login_streak',
            'average_quiz_score', 'completion_rate', 'learning_progress',
            'total_points', 'badges_earned', 'achievements_unlocked', 'activity_score'
        ]
    
    def get_learning_progress(self, obj):
        """Calculate overall learning progress"""
        if obj.courses_enrolled > 0:
            progress = (obj.courses_completed / obj.courses_enrolled) * 100
            return round(float(progress), 2)
        return 0.0
    
    def get_activity_score(self, obj):
        """Calculate activity score based on various metrics"""
        score = 0
        score += obj.lessons_completed * 2
        score += obj.assignments_submitted * 5
        score += obj.quizzes_taken * 3
        score += obj.forum_posts * 1
        score += obj.login_streak * 1
        return score


class PlatformAnalyticsSerializer(serializers.Serializer):
    """Comprehensive platform analytics serializer"""
    
    # Overview metrics
    total_users = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_instructors = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Growth metrics
    user_growth_rate = serializers.FloatField()
    course_growth_rate = serializers.FloatField()
    revenue_growth_rate = serializers.FloatField()
    
    # Engagement metrics
    active_users_percentage = serializers.FloatField()
    course_completion_rate = serializers.FloatField()
    average_session_duration = serializers.FloatField()
    
    # Popular content
    popular_courses = CourseMetricsSerializer(many=True)
    top_instructors = InstructorMetricsSerializer(many=True)
    
    # Time series data
    daily_metrics = PlatformMetricsSerializer(many=True)
    
    # Financial breakdown
    revenue_breakdown = serializers.DictField()
    refund_rate = serializers.FloatField()


class InstructorAnalyticsSerializer(serializers.Serializer):
    """Comprehensive instructor analytics serializer"""
    
    # Overview metrics
    total_students = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    
    # Growth metrics
    student_growth_rate = serializers.FloatField()
    earnings_growth_rate = serializers.FloatField()
    
    # Performance metrics
    completion_rate = serializers.FloatField()
    engagement_score = serializers.FloatField()
    response_time = serializers.FloatField()
    
    # Course performance
    best_performing_courses = CourseMetricsSerializer(many=True)
    recent_enrollments = serializers.DictField()
    
    # Student insights
    student_demographics = serializers.DictField()
    student_feedback = serializers.DictField()
    
    # Time series data
    daily_metrics = InstructorMetricsSerializer(many=True)


class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for analytics snapshots"""
    
    class Meta:
        model = AnalyticsSnapshot
        fields = [
            'snapshot_type', 'period_start', 'period_end',
            'platform_data', 'instructor_data', 'course_data', 'student_data',
            'created_at'
        ]