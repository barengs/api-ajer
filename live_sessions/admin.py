from django.contrib import admin
from .models import (
    LiveSession, SessionAttendance, SessionResource,
    SessionRecording, SessionChat, SessionPoll, PollResponse
)


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'course', 'instructor', 'scheduled_start',
        'status', 'platform', 'attendee_count'
    )
    list_filter = ('status', 'platform', 'is_recorded', 'created_at')
    search_fields = ('title', 'course__title', 'instructor__email')
    readonly_fields = ('actual_start', 'actual_end', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Session Information', {
            'fields': ('course', 'batch', 'instructor', 'title', 'description')
        }),
        ('Scheduling', {
            'fields': ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
        }),
        ('Platform Integration', {
            'fields': (
                'platform', 'meeting_url', 'meeting_id', 'meeting_password',
                'external_meeting_data'
            )
        }),
        ('Settings', {
            'fields': ('max_participants', 'is_recorded', 'recording_url', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Attendees')
    def attendee_count(self, obj):
        return obj.attendances.count()


@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'session', 'student', 'status', 'joined_at',
        'total_duration_minutes', 'attendance_percentage'
    )
    list_filter = ('status', 'registered_at')
    search_fields = ('session__title', 'student__email', 'student__full_name')
    readonly_fields = ('registered_at', 'attendance_percentage')
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session', 'student', 'status')
        }),
        ('Attendance Tracking', {
            'fields': ('joined_at', 'left_at', 'total_duration_minutes')
        }),
        ('Engagement Metrics', {
            'fields': ('questions_asked', 'chat_messages')
        }),
        ('Registration', {
            'fields': ('registered_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SessionResource)
class SessionResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'session', 'resource_type', 'shared_by', 'shared_at', 'is_public')
    list_filter = ('resource_type', 'is_public', 'shared_at')
    search_fields = ('title', 'session__title', 'shared_by__email')
    readonly_fields = ('shared_at',)


@admin.register(SessionRecording)
class SessionRecordingAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'session', 'duration_minutes', 'processing_status',
        'is_public', 'is_available'
    )
    list_filter = ('processing_status', 'is_public', 'created_at')
    search_fields = ('title', 'session__title')
    readonly_fields = ('created_at', 'processed_at', 'is_available')
    
    fieldsets = (
        ('Recording Information', {
            'fields': ('session', 'title', 'duration_minutes', 'file_size_mb')
        }),
        ('Files', {
            'fields': ('video_file', 'external_url', 'thumbnail')
        }),
        ('Processing', {
            'fields': ('processing_status', 'processed_at')
        }),
        ('Access Control', {
            'fields': ('is_public', 'available_until')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SessionChat)
class SessionChatAdmin(admin.ModelAdmin):
    list_display = (
        'session', 'sender', 'message_type', 'is_visible',
        'is_highlighted', 'sent_at'
    )
    list_filter = ('message_type', 'is_visible', 'is_highlighted', 'sent_at')
    search_fields = ('session__title', 'sender__email', 'message')
    readonly_fields = ('sent_at',)
    
    fieldsets = (
        ('Message Information', {
            'fields': ('session', 'sender', 'message', 'message_type')
        }),
        ('Threading', {
            'fields': ('parent_message',)
        }),
        ('Moderation', {
            'fields': ('is_visible', 'is_highlighted')
        }),
        ('Timestamp', {
            'fields': ('sent_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SessionPoll)
class SessionPollAdmin(admin.ModelAdmin):
    list_display = (
        'question_preview', 'session', 'created_by', 'is_active',
        'response_count', 'created_at'
    )
    list_filter = ('is_active', 'is_multiple_choice', 'is_anonymous', 'created_at')
    search_fields = ('question', 'session__title', 'created_by__email')
    readonly_fields = ('created_at', 'closed_at', 'response_count')
    
    @admin.display(description='Question')
    def question_preview(self, obj):
        return obj.question[:50] + ('...' if len(obj.question) > 50 else '')


class PollResponseInline(admin.TabularInline):
    model = PollResponse
    readonly_fields = ('student', 'selected_options', 'submitted_at')
    extra = 0


@admin.register(PollResponse)
class PollResponseAdmin(admin.ModelAdmin):
    list_display = ('poll_question_preview', 'student', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('poll__question', 'student__email')
    readonly_fields = ('submitted_at',)
    
    @admin.display(description='Poll Question')
    def poll_question_preview(self, obj):
        return obj.poll.question[:50] + ('...' if len(obj.poll.question) > 50 else '')