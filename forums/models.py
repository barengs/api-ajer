from django.db import models
from django.conf import settings
from django.db import models
from django.utils import timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet


class Forum(models.Model):
    """Forums for course discussions"""
    
    class ForumType(models.TextChoices):
        GENERAL = 'general', 'General Discussion'
        QNA = 'qna', 'Q&A'
        ANNOUNCEMENTS = 'announcements', 'Announcements'
        ASSIGNMENTS = 'assignments', 'Assignment Discussion'
        BATCH_SPECIFIC = 'batch_specific', 'Batch Specific'
    
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='forums')
    batch = models.ForeignKey(
        'courses.CourseBatch', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='forums'
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    forum_type = models.CharField(max_length=20, choices=ForumType.choices, default=ForumType.GENERAL)
    
    # Permissions
    allow_student_posts = models.BooleanField(default=True)
    require_moderation = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)  # Only for enrolled students
    
    # Ordering
    sort_order = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forums'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['course', 'forum_type']),
            models.Index(fields=['batch', 'is_active']),
        ]
    
    def __str__(self):
        course_title = self.course.title
        if self.batch:
            return f"{course_title} ({self.batch.name}) - {self.name}"
        return f"{course_title} - {self.name}"
    
    @property
    def total_posts(self) -> int:
        return self.posts.filter(is_approved=True).count()  # type: ignore[attr-defined]
    
    @property
    def latest_post(self):
        return self.posts.filter(is_approved=True).order_by('-created_at').first()  # type: ignore[attr-defined]


class ForumPost(models.Model):
    """Posts in forum discussions"""
    
    class PostType(models.TextChoices):
        DISCUSSION = 'discussion', 'Discussion'
        QUESTION = 'question', 'Question'
        ANNOUNCEMENT = 'announcement', 'Announcement'
        POLL = 'poll', 'Poll'
    
    class PostStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        PENDING = 'pending', 'Pending Approval'
        REJECTED = 'rejected', 'Rejected'
    
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    
    # Content
    title = models.CharField(max_length=300)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.DISCUSSION)
    
    # Question specific fields
    is_question_resolved = models.BooleanField(default=False)
    accepted_answer = models.ForeignKey(
        'ForumReply', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='accepted_for_posts'
    )
    
    # Moderation
    status = models.CharField(max_length=20, choices=PostStatus.choices, default=PostStatus.PUBLISHED)
    is_approved = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    # Engagement
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    
    # Tags
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_posts'
        ordering = ['-is_pinned', '-last_activity_at']
        indexes = [
            models.Index(fields=['forum', 'status']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['post_type', 'is_approved']),
            models.Index(fields=['-last_activity_at']),
        ]
    
    def __str__(self):
        return f"{self.forum.course.title} - {self.title}"
    
    @property
    def reply_count(self) -> int:
        return self.replies.filter(is_approved=True).count()  # type: ignore[attr-defined]
    
    @property
    def latest_reply(self):
        return self.replies.filter(is_approved=True).order_by('-created_at').first()  # type: ignore[attr-defined]
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])


class ForumReply(models.Model):
    """Replies to forum posts"""
    
    class ReplyStatus(models.TextChoices):
        PUBLISHED = 'published', 'Published'
        PENDING = 'pending', 'Pending Approval'
        REJECTED = 'rejected', 'Rejected'
        SPAM = 'spam', 'Marked as Spam'
    
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_replies')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_replies')
    
    content = models.TextField()
    
    # Moderation
    status = models.CharField(max_length=20, choices=ReplyStatus.choices, default=ReplyStatus.PUBLISHED)
    is_approved = models.BooleanField(default=True)
    is_instructor_reply = models.BooleanField(default=False)
    is_answer = models.BooleanField(default=False)  # Marked as helpful answer
    
    # Engagement
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_replies'
        ordering = ['-is_answer', 'created_at']
        indexes = [
            models.Index(fields=['post', 'status']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"Reply by {self.author.email} to {self.post.title}"
    
    def save(self, *args, **kwargs):
        # Check if author is instructor
        if (self.author.role == 'instructor' and 
            self.author == self.post.forum.course.instructor):
            self.is_instructor_reply = True
        
        super().save(*args, **kwargs)
        
        # Update post activity
        self.post.update_activity()


class ForumVote(models.Model):
    """Votes for posts and replies"""
    
    class VoteType(models.TextChoices):
        UPVOTE = 'upvote', 'Upvote'
        DOWNVOTE = 'downvote', 'Downvote'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_votes')
    
    # Voting target (either post or reply)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    
    vote_type = models.CharField(max_length=10, choices=VoteType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_votes'
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(post__isnull=False) & models.Q(reply__isnull=True)) |
                    (models.Q(post__isnull=True) & models.Q(reply__isnull=False))
                ),
                name='vote_either_post_or_reply'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'post']),
            models.Index(fields=['user', 'reply']),
        ]
    
    def __str__(self):
        target = self.post or self.reply
        return f"{self.user.email} {self.vote_type} on {target}"
    
    def save(self, *args, **kwargs):
        # Remove any existing vote by this user on the same target
        if self.post:
            ForumVote.objects.filter(user=self.user, post=self.post).delete()
        elif self.reply:
            ForumVote.objects.filter(user=self.user, reply=self.reply).delete()
        
        super().save(*args, **kwargs)
        
        # Update vote counts
        self.update_vote_counts()
    
    def update_vote_counts(self):
        """Update vote counts on the target object"""
        target = self.post or self.reply
        if target:
            upvotes = target.votes.filter(vote_type=self.VoteType.UPVOTE).count()
            downvotes = target.votes.filter(vote_type=self.VoteType.DOWNVOTE).count()
            target.upvotes = upvotes
            target.downvotes = downvotes
            target.save(update_fields=['upvotes', 'downvotes'])


class ForumSubscription(models.Model):
    """User subscriptions to forum posts for notifications"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_subscriptions')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='subscribers')
    
    # Notification preferences
    notify_new_replies = models.BooleanField(default=True)
    notify_accepted_answer = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_subscriptions'
        unique_together = ['user', 'post']
    
    def __str__(self):
        return f"{self.user.email} subscribed to {self.post.title}"


class ForumReportedContent(models.Model):
    """Reports of inappropriate content"""
    
    class ReportReason(models.TextChoices):
        SPAM = 'spam', 'Spam'
        INAPPROPRIATE = 'inappropriate', 'Inappropriate Content'
        HARASSMENT = 'harassment', 'Harassment'
        OFF_TOPIC = 'off_topic', 'Off Topic'
        COPYRIGHT = 'copyright', 'Copyright Violation'
        OTHER = 'other', 'Other'
    
    class ReportStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        REVIEWED = 'reviewed', 'Reviewed'
        RESOLVED = 'resolved', 'Resolved'
        DISMISSED = 'dismissed', 'Dismissed'
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_reports')
    
    # Reported content (either post or reply)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    
    reason = models.CharField(max_length=20, choices=ReportReason.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    
    # Moderation
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports'
    )
    moderator_notes = models.TextField(blank=True)
    action_taken = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'forum_reported_content'
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(post__isnull=False) & models.Q(reply__isnull=True)) |
                    (models.Q(post__isnull=True) & models.Q(reply__isnull=False))
                ),
                name='report_either_post_or_reply'
            )
        ]
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['reporter']),
        ]
    
    def __str__(self):
        target = self.post or self.reply
        return f"Report by {self.reporter.email} on {target}"


class ForumActivity(models.Model):
    """Track forum activity for analytics"""
    
    class ActivityType(models.TextChoices):
        POST_CREATED = 'post_created', 'Post Created'
        POST_VIEWED = 'post_viewed', 'Post Viewed'
        REPLY_CREATED = 'reply_created', 'Reply Created'
        VOTE_CAST = 'vote_cast', 'Vote Cast'
        POST_SUBSCRIBED = 'post_subscribed', 'Post Subscribed'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_activities')
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    
    # Activity metadata
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_activities'
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['forum', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()}"  # type: ignore[attr-defined]