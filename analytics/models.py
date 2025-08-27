from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet


class PlatformMetrics(models.Model):
    """Daily platform metrics for tracking overall performance"""
    
    date = models.DateField(unique=True)
    
    # User metrics
    total_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    
    # Course metrics
    total_courses = models.IntegerField(default=0)
    new_courses = models.IntegerField(default=0)
    published_courses = models.IntegerField(default=0)
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    daily_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    refunds = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Enrollment metrics
    total_enrollments = models.IntegerField(default=0)
    new_enrollments = models.IntegerField(default=0)
    completed_courses = models.IntegerField(default=0)
    
    # Engagement metrics
    forum_posts = models.IntegerField(default=0)
    lesson_completions = models.IntegerField(default=0)
    assignment_submissions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_metrics'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"Platform metrics for {self.date}"


class InstructorMetrics(models.Model):
    """Daily metrics for individual instructors"""
    
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_metrics'
    )
    date = models.DateField()
    
    # Course metrics
    total_courses = models.IntegerField(default=0)
    published_courses = models.IntegerField(default=0)
    draft_courses = models.IntegerField(default=0)
    
    # Student metrics
    total_students = models.IntegerField(default=0)
    new_students = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)
    
    # Financial metrics
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    daily_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Performance metrics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    total_reviews = models.IntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Engagement metrics
    forum_interactions = models.IntegerField(default=0)
    student_questions = models.IntegerField(default=0)
    response_time_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'instructor_metrics'
        unique_together = ['instructor', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['instructor', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.instructor.get_full_name()} metrics for {self.date}"


class CourseMetrics(models.Model):
    """Daily metrics for individual courses"""
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='course_metrics'
    )
    date = models.DateField()
    
    # Enrollment metrics
    total_enrollments = models.IntegerField(default=0)
    new_enrollments = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)
    completed_students = models.IntegerField(default=0)
    
    # Progress metrics
    average_progress = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    dropout_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Financial metrics
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    daily_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Engagement metrics
    lesson_views = models.IntegerField(default=0)
    assignment_submissions = models.IntegerField(default=0)
    forum_posts = models.IntegerField(default=0)
    quiz_attempts = models.IntegerField(default=0)
    
    # Rating metrics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    total_reviews = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_metrics'
        unique_together = ['course', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['course', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.course.title} metrics for {self.date}"


class StudentMetrics(models.Model):
    """Daily metrics for individual students"""
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_metrics'
    )
    date = models.DateField()
    
    # Learning metrics
    courses_enrolled = models.IntegerField(default=0)
    courses_completed = models.IntegerField(default=0)
    courses_in_progress = models.IntegerField(default=0)
    
    # Activity metrics
    lessons_completed = models.IntegerField(default=0)
    assignments_submitted = models.IntegerField(default=0)
    quizzes_taken = models.IntegerField(default=0)
    forum_posts = models.IntegerField(default=0)
    
    # Time metrics
    total_study_time_minutes = models.IntegerField(default=0)
    daily_study_time_minutes = models.IntegerField(default=0)
    login_streak = models.IntegerField(default=0)
    
    # Performance metrics
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Gamification metrics
    total_points = models.IntegerField(default=0)
    badges_earned = models.IntegerField(default=0)
    achievements_unlocked = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_metrics'
        unique_together = ['student', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} metrics for {self.date}"


class AnalyticsSnapshot(models.Model):
    """Periodic snapshots for quick analytics retrieval"""
    
    class SnapshotType(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'
    
    snapshot_type = models.CharField(max_length=20, choices=SnapshotType.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Aggregated data stored as JSON
    platform_data = models.JSONField(default=dict)
    instructor_data = models.JSONField(default=dict)
    course_data = models.JSONField(default=dict)
    student_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_snapshots'
        unique_together = ['snapshot_type', 'period_start', 'period_end']
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['snapshot_type', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.snapshot_type} snapshot: {self.period_start} to {self.period_end}"