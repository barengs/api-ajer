from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta


class LiveSession(models.Model):
    """Live video sessions for structured courses"""
    
    class SessionStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        LIVE = 'live', 'Live'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    class SessionPlatform(models.TextChoices):
        ZOOM = 'zoom', 'Zoom'
        GOOGLE_MEET = 'google_meet', 'Google Meet'
        MICROSOFT_TEAMS = 'teams', 'Microsoft Teams'
        JITSI = 'jitsi', 'Jitsi Meet'
        CUSTOM = 'custom', 'Custom Platform'
    
    # Session identification
    course = models.ForeignKey(
        'courses.Course', 
        on_delete=models.CASCADE, 
        related_name='live_sessions'
    )
    batch = models.ForeignKey(
        'courses.CourseBatch',
        on_delete=models.CASCADE,
        related_name='live_sessions',
        null=True,
        blank=True
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_sessions'
    )
    
    # Session details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Platform integration
    platform = models.CharField(max_length=20, choices=SessionPlatform.choices)
    meeting_url = models.URLField(blank=True)
    meeting_id = models.CharField(max_length=100, blank=True)
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # External platform data
    external_meeting_data = models.JSONField(default=dict, blank=True)
    
    # Session settings
    max_participants = models.IntegerField(null=True, blank=True)
    is_recorded = models.BooleanField(default=True)
    recording_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.SCHEDULED)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'live_sessions'
        ordering = ['scheduled_start']
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['instructor', 'scheduled_start']),
            models.Index(fields=['scheduled_start', 'status']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def is_upcoming(self):
        return self.status == self.SessionStatus.SCHEDULED and self.scheduled_start > timezone.now()
    
    @property
    def is_live_now(self):
        now = timezone.now()
        return (self.status == self.SessionStatus.LIVE or 
                (self.scheduled_start <= now <= self.scheduled_end and 
                 self.status == self.SessionStatus.SCHEDULED))
    
    @property
    def duration_minutes(self):
        if self.actual_start and self.actual_end:
            return int((self.actual_end - self.actual_start).total_seconds() / 60)
        return int((self.scheduled_end - self.scheduled_start).total_seconds() / 60)
    
    def start_session(self):
        """Mark session as started"""
        self.status = self.SessionStatus.LIVE
        self.actual_start = timezone.now()
        self.save(update_fields=['status', 'actual_start'])
    
    def end_session(self):
        """Mark session as completed"""
        self.status = self.SessionStatus.COMPLETED
        self.actual_end = timezone.now()
        self.save(update_fields=['status', 'actual_end'])


class SessionAttendance(models.Model):
    """Track student attendance in live sessions"""
    
    class AttendanceStatus(models.TextChoices):
        REGISTERED = 'registered', 'Registered'
        JOINED = 'joined', 'Joined'
        COMPLETED = 'completed', 'Completed'
        MISSED = 'missed', 'Missed'
    
    session = models.ForeignKey(
        LiveSession,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='session_attendances'
    )
    
    # Attendance tracking
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.REGISTERED)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    total_duration_minutes = models.IntegerField(default=0)
    
    # Engagement metrics
    questions_asked = models.IntegerField(default=0)
    chat_messages = models.IntegerField(default=0)
    
    # Registration
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'session_attendances'
        unique_together = ['session', 'student']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.email} - {self.session.title}"
    
    @property
    def attendance_percentage(self):
        if self.session.duration_minutes == 0:
            return 0
        return min(100, (self.total_duration_minutes / self.session.duration_minutes) * 100)


class SessionResource(models.Model):
    """Resources shared during live sessions"""
    
    class ResourceType(models.TextChoices):
        PRESENTATION = 'presentation', 'Presentation'
        DOCUMENT = 'document', 'Document'
        VIDEO = 'video', 'Video'
        LINK = 'link', 'Link'
        CODE = 'code', 'Code Sample'
        OTHER = 'other', 'Other'
    
    session = models.ForeignKey(
        LiveSession,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    
    # File or URL
    file = models.FileField(upload_to='session_resources/', null=True, blank=True)
    url = models.URLField(blank=True)
    
    # Sharing details
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_resources'
    )
    shared_at = models.DateTimeField(auto_now_add=True)
    
    # Access control
    is_public = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'session_resources'
        ordering = ['shared_at']
    
    def __str__(self):
        return f"{self.session.title} - {self.title}"


class SessionRecording(models.Model):
    """Session recordings for later viewing"""
    
    class ProcessingStatus(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'
    
    session = models.OneToOneField(
        LiveSession,
        on_delete=models.CASCADE,
        related_name='recording'
    )
    
    # Recording details
    title = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(default=0)
    file_size_mb = models.FloatField(default=0)
    
    # File storage
    video_file = models.FileField(upload_to='session_recordings/', null=True, blank=True)
    external_url = models.URLField(blank=True)
    thumbnail = models.ImageField(upload_to='recording_thumbnails/', null=True, blank=True)
    
    # Processing
    processing_status = models.CharField(
        max_length=20, 
        choices=ProcessingStatus.choices, 
        default=ProcessingStatus.PROCESSING
    )
    
    # Access control
    is_public = models.BooleanField(default=False)
    available_until = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'session_recordings'
    
    def __str__(self):
        return f"Recording: {self.session.title}"
    
    @property
    def is_available(self):
        if not self.processing_status == self.ProcessingStatus.READY:
            return False
        if self.available_until and timezone.now() > self.available_until:
            return False
        return True


class SessionChat(models.Model):
    """Chat messages during live sessions"""
    
    class MessageType(models.TextChoices):
        MESSAGE = 'message', 'Message'
        QUESTION = 'question', 'Question'
        ANSWER = 'answer', 'Answer'
        POLL = 'poll', 'Poll'
        ANNOUNCEMENT = 'announcement', 'Announcement'
    
    session = models.ForeignKey(
        LiveSession,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='session_messages'
    )
    
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.MESSAGE)
    
    # Threading
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Moderation
    is_visible = models.BooleanField(default=True)
    is_highlighted = models.BooleanField(default=False)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'session_chat'
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['session', 'sent_at']),
            models.Index(fields=['sender']),
        ]
    
    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}..."


class SessionPoll(models.Model):
    """Interactive polls during live sessions"""
    
    session = models.ForeignKey(
        LiveSession,
        on_delete=models.CASCADE,
        related_name='polls'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_polls'
    )
    
    question = models.CharField(max_length=500)
    options = models.JSONField()
    
    # Poll settings
    is_multiple_choice = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'session_polls'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Poll: {self.question[:50]}..."
    
    def close_poll(self):
        """Close the poll"""
        self.is_active = False
        self.closed_at = timezone.now()
        self.save(update_fields=['is_active', 'closed_at'])
    
    @property
    def response_count(self):
        return PollResponse.objects.filter(poll=self).count()


class PollResponse(models.Model):
    """Student responses to session polls"""
    
    poll = models.ForeignKey(
        SessionPoll,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='poll_responses'
    )
    
    selected_options = models.JSONField()
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'poll_responses'
        unique_together = ['poll', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.poll.question[:30]}..."