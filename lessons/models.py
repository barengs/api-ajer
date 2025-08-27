from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Lesson(models.Model):
    """Individual lessons within course sections"""
    
    class LessonType(models.TextChoices):
        VIDEO = 'video', 'Video'
        TEXT = 'text', 'Text/Article'
        QUIZ = 'quiz', 'Quiz'
        ASSIGNMENT = 'assignment', 'Assignment'
        LIVE_SESSION = 'live_session', 'Live Session'
        DOWNLOADABLE = 'downloadable', 'Downloadable Resource'
    
    class LessonStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    # Basic information
    section = models.ForeignKey('Section', on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    
    # Content
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices)
    content = models.TextField(blank=True)  # Text content or HTML
    
    # Media files
    video_file = models.FileField(upload_to='lesson_videos/', blank=True, null=True)
    video_url = models.URLField(blank=True)  # External video URL (YouTube, Vimeo, etc.)
    audio_file = models.FileField(upload_to='lesson_audios/', blank=True, null=True)
    
    # Resources
    downloadable_resources = models.JSONField(default=list)  # List of file URLs and names
    
    # Lesson metadata
    duration_minutes = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    is_preview = models.BooleanField(default=False)  # Can be viewed without enrollment
    is_mandatory = models.BooleanField(default=True)  # Required for course completion
    
    # Status
    status = models.CharField(max_length=20, choices=LessonStatus.choices, default=LessonStatus.DRAFT)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lessons'
        ordering = ['sort_order']
        unique_together = ['section', 'sort_order']
        indexes = [
            models.Index(fields=['section', 'status']),
            models.Index(fields=['lesson_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.section.course.title} - {self.title}"
    
    @property
    def course(self):
        return self.section.course
    
    def can_be_accessed_by_user(self, user):
        """Check if user can access this lesson"""
        if self.is_preview:
            return True
        
        # Check if user is enrolled in the course
        from courses.models import Enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=user, 
                course=self.section.course,
                status=Enrollment.EnrollmentStatus.ACTIVE
            )
            return True
        except Enrollment.DoesNotExist:
            return False


class Section(models.Model):
    """Course sections to organize lessons"""
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_sections'
        ordering = ['sort_order']
        unique_together = ['course', 'sort_order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def total_lessons(self):
        return self.lessons.count()  # type: ignore[attr-defined]
    
    @property
    def total_duration(self):
        return self.lessons.aggregate(  # type: ignore[attr-defined]
            total=models.Sum('duration_minutes')
        )['total'] or 0


class LessonProgress(models.Model):
    """Track student progress through lessons"""
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='lesson_progress'
    )
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='student_progress')
    
    # Progress tracking
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    time_spent_minutes = models.IntegerField(default=0)
    
    # Video specific tracking
    video_progress_seconds = models.IntegerField(default=0)  # Current position in video
    video_duration_seconds = models.IntegerField(default=0)  # Total video duration
    
    # Timestamps
    first_accessed_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'lesson_progress'
        unique_together = ['student', 'lesson']
        indexes = [
            models.Index(fields=['student', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.student.email} - {self.lesson.title} ({self.completion_percentage}%)"
    
    def mark_completed(self):
        """Mark lesson as completed"""
        if not self.is_completed:
            self.is_completed = True
            self.completion_percentage = Decimal('100.00')
            self.completed_at = timezone.now()
            self.save()
            
            # Update course progress
            enrollment = self.student.enrollments.filter(
                course=self.lesson.section.course,
                status='active'
            ).first()
            if enrollment:
                enrollment.calculate_progress()


class Quiz(models.Model):
    """Quizzes within lessons"""
    
    lesson = models.OneToOneField('Lesson', on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Quiz settings
    time_limit_minutes = models.IntegerField(null=True, blank=True)
    max_attempts = models.IntegerField(default=1)
    passing_score = models.IntegerField(default=70)  # Percentage
    show_correct_answers = models.BooleanField(default=True)
    randomize_questions = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quizzes'
    
    def __str__(self):
        return f"Quiz: {self.title}"
    
    @property
    def total_questions(self):
        return self.questions.count()  # type: ignore[attr-defined]


class QuizQuestion(models.Model):
    """Questions in quizzes"""
    
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', 'Multiple Choice'
        TRUE_FALSE = 'true_false', 'True/False'
        SHORT_ANSWER = 'short_answer', 'Short Answer'
        ESSAY = 'essay', 'Essay'
    
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    points = models.IntegerField(default=1)
    sort_order = models.IntegerField(default=0)
    
    # Multiple choice options (JSON)
    options = models.JSONField(default=list)  # [{"text": "Option A", "is_correct": true}, ...]
    
    # Correct answer for other question types
    correct_answer = models.TextField(blank=True)
    
    # Explanation
    explanation = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quiz_questions'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"Q{self.sort_order}: {self.question_text[:50]}..."


class QuizAttempt(models.Model):
    """Student quiz attempts"""
    
    class AttemptStatus(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        ABANDONED = 'abandoned', 'Abandoned'
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, related_name='attempts')
    
    # Attempt details
    attempt_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=AttemptStatus.choices, default=AttemptStatus.IN_PROGRESS)
    
    # Scoring
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    earned_points = models.IntegerField(default=0)
    percentage_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'quiz_attempts'
        unique_together = ['student', 'quiz', 'attempt_number']
        indexes = [
            models.Index(fields=['student', 'quiz']),
            models.Index(fields=['quiz', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.email} - {self.quiz.title} (Attempt {self.attempt_number})"
    
    @property
    def is_passed(self):
        return self.percentage_score >= self.quiz.passing_score


class QuizAnswer(models.Model):
    """Student answers to quiz questions"""
    
    attempt = models.ForeignKey('QuizAttempt', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('QuizQuestion', on_delete=models.CASCADE, related_name='student_answers')
    
    # Answer data
    answer_text = models.TextField()  # Student's answer
    selected_options = models.JSONField(default=list)  # For multiple choice
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    
    # Timing
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quiz_answers'
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Answer by {self.attempt.student.email} for Q{self.question.sort_order}"


class LessonComment(models.Model):
    """Comments on lessons for Q&A and discussions"""
    
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField()
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_instructor_reply = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lesson_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['lesson', 'parent']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.lesson.title}"


class LessonNote(models.Model):
    """Student notes for lessons"""
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='lesson_notes'
    )
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='student_notes')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # For video lessons - timestamp where note was taken
    timestamp_seconds = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lesson_notes'
        ordering = ['timestamp_seconds', 'created_at']
        indexes = [
            models.Index(fields=['student', 'lesson']),
        ]
    
    def __str__(self):
        return f"Note by {self.student.email}: {self.title}"