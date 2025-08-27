from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    PlatformMetrics, InstructorMetrics, CourseMetrics, 
    StudentMetrics, AnalyticsSnapshot
)


@admin.register(PlatformMetrics)
class PlatformMetricsAdmin(admin.ModelAdmin):
    """Admin interface for platform metrics"""
    
    list_display = [
        'date', 'total_users', 'total_courses', 'total_revenue_display',
        'new_users', 'new_enrollments', 'daily_revenue_display'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('date',)
        }),
        ('User Metrics', {
            'fields': ('total_users', 'new_users', 'active_users'),
            'classes': ('collapse',)
        }),
        ('Course Metrics', {
            'fields': ('total_courses', 'new_courses', 'published_courses'),
            'classes': ('collapse',)
        }),
        ('Financial Metrics', {
            'fields': ('total_revenue', 'daily_revenue', 'refunds'),
            'classes': ('collapse',)
        }),
        ('Enrollment Metrics', {
            'fields': ('total_enrollments', 'new_enrollments', 'completed_courses'),
            'classes': ('collapse',)
        }),
        ('Engagement Metrics', {
            'fields': ('forum_posts', 'lesson_completions', 'assignment_submissions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Total Revenue')
    def total_revenue_display(self, obj):
        return f"${obj.total_revenue:,.2f}"
    
    @admin.display(description='Daily Revenue')
    def daily_revenue_display(self, obj):
        return f"${obj.daily_revenue:,.2f}"


@admin.register(InstructorMetrics)
class InstructorMetricsAdmin(admin.ModelAdmin):
    """Admin interface for instructor metrics"""
    
    list_display = [
        'instructor_name', 'date', 'total_courses', 'total_students',
        'total_earnings_display', 'average_rating', 'completion_rate'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['instructor__first_name', 'instructor__last_name', 'instructor__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date', 'instructor__first_name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('instructor', 'date')
        }),
        ('Course Metrics', {
            'fields': ('total_courses', 'published_courses', 'draft_courses'),
        }),
        ('Student Metrics', {
            'fields': ('total_students', 'new_students', 'active_students'),
        }),
        ('Financial Metrics', {
            'fields': ('total_earnings', 'daily_earnings'),
        }),
        ('Performance Metrics', {
            'fields': ('average_rating', 'total_reviews', 'completion_rate'),
        }),
        ('Engagement Metrics', {
            'fields': ('forum_interactions', 'student_questions', 'response_time_hours'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Instructor')
    def instructor_name(self, obj):
        return obj.instructor.get_full_name() or obj.instructor.email
    
    @admin.display(description='Total Earnings')
    def total_earnings_display(self, obj):
        return f"${obj.total_earnings:,.2f}"


@admin.register(CourseMetrics)
class CourseMetricsAdmin(admin.ModelAdmin):
    """Admin interface for course metrics"""
    
    list_display = [
        'course_title', 'instructor_name', 'date', 'total_enrollments',
        'completion_rate', 'revenue_display', 'average_rating'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['course__title', 'course__instructor__first_name', 'course__instructor__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date', 'course__title']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('course', 'date')
        }),
        ('Enrollment Metrics', {
            'fields': ('total_enrollments', 'new_enrollments', 'active_students', 'completed_students'),
        }),
        ('Progress Metrics', {
            'fields': ('average_progress', 'completion_rate', 'dropout_rate'),
        }),
        ('Financial Metrics', {
            'fields': ('revenue', 'daily_revenue'),
        }),
        ('Engagement Metrics', {
            'fields': ('lesson_views', 'assignment_submissions', 'forum_posts', 'quiz_attempts'),
            'classes': ('collapse',)
        }),
        ('Rating Metrics', {
            'fields': ('average_rating', 'total_reviews'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Course')
    def course_title(self, obj):
        return obj.course.title
    
    @admin.display(description='Instructor')
    def instructor_name(self, obj):
        return obj.course.instructor.get_full_name() or obj.course.instructor.email
    
    @admin.display(description='Revenue')
    def revenue_display(self, obj):
        return f"${obj.revenue:,.2f}"


@admin.register(StudentMetrics)
class StudentMetricsAdmin(admin.ModelAdmin):
    """Admin interface for student metrics"""
    
    list_display = [
        'student_name', 'date', 'courses_enrolled', 'courses_completed',
        'total_study_time_display', 'total_points', 'login_streak'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'student__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date', 'student__first_name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('student', 'date')
        }),
        ('Learning Metrics', {
            'fields': ('courses_enrolled', 'courses_completed', 'courses_in_progress'),
        }),
        ('Activity Metrics', {
            'fields': ('lessons_completed', 'assignments_submitted', 'quizzes_taken', 'forum_posts'),
        }),
        ('Time Metrics', {
            'fields': ('total_study_time_minutes', 'daily_study_time_minutes', 'login_streak'),
        }),
        ('Performance Metrics', {
            'fields': ('average_quiz_score', 'completion_rate'),
        }),
        ('Gamification Metrics', {
            'fields': ('total_points', 'badges_earned', 'achievements_unlocked'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Student')
    def student_name(self, obj):
        return obj.student.get_full_name() or obj.student.email
    
    @admin.display(description='Study Time')
    def total_study_time_display(self, obj):
        hours = obj.total_study_time_minutes // 60
        minutes = obj.total_study_time_minutes % 60
        return f"{hours}h {minutes}m"


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    """Admin interface for analytics snapshots"""
    
    list_display = [
        'snapshot_type', 'period_start', 'period_end', 'created_at'
    ]
    list_filter = ['snapshot_type', 'period_start', 'created_at']
    search_fields = ['snapshot_type']
    readonly_fields = ['created_at']
    date_hierarchy = 'period_start'
    ordering = ['-period_end', 'snapshot_type']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('snapshot_type', 'period_start', 'period_end')
        }),
        ('Analytics Data', {
            'fields': ('platform_data', 'instructor_data', 'course_data', 'student_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )