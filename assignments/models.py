from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Assignment(models.Model):
    """Assignments for structured courses"""
    
    class AssignmentType(models.TextChoices):
        INDIVIDUAL = 'individual', 'Individual Assignment'
        GROUP = 'group', 'Group Assignment'
        PEER_REVIEW = 'peer_review', 'Peer Review Assignment'
        PROJECT = 'project', 'Project'
        PRESENTATION = 'presentation', 'Presentation'
    
    class GradingType(models.TextChoices):
        POINTS = 'points', 'Points (0-100)'
        LETTER = 'letter', 'Letter Grade (A-F)'
        PASS_FAIL = 'pass_fail', 'Pass/Fail'
        RUBRIC = 'rubric', 'Rubric Based'
    
    # Basic information
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='assignments')
    batch = models.ForeignKey(
        'courses.CourseBatch', 
        on_delete=models.CASCADE, 
        related_name='assignments',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    
    # Assignment settings
    assignment_type = models.CharField(max_length=20, choices=AssignmentType.choices)
    grading_type = models.CharField(max_length=20, choices=GradingType.choices, default=GradingType.POINTS)
    max_points = models.IntegerField(default=100, validators=[MinValueValidator(1)])
    
    # Timing
    assigned_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    late_submission_allowed = models.BooleanField(default=True)
    late_penalty_percentage = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Submission settings
    allow_file_uploads = models.BooleanField(default=True)
    allowed_file_types = models.JSONField(default=list)  # ['pdf', 'docx', 'txt']
    max_file_size_mb = models.IntegerField(default=10)
    max_files_count = models.IntegerField(default=5)
    allow_text_submission = models.BooleanField(default=True)
    allow_url_submission = models.BooleanField(default=False)
    
    # Group assignment settings
    max_group_size = models.IntegerField(null=True, blank=True)
    allow_self_selection = models.BooleanField(default=True)
    
    # Auto grading (for future implementation)
    is_auto_gradable = models.BooleanField(default=False)
    auto_grade_criteria = models.JSONField(default=dict, blank=True)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignments'
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['course', 'batch']),
            models.Index(fields=['due_date', 'is_published']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    @property
    def time_remaining(self):
        if self.is_overdue:
            return None
        return self.due_date - timezone.now()
    
    def can_submit(self):
        """Check if assignment accepts submissions"""
        if not self.is_published:
            return False
        if self.is_overdue and not self.late_submission_allowed:
            return False
        return True
    
    def get_submission_count(self):
        """Get the count of submissions for this assignment"""
        from django.apps import apps
        AssignmentSubmission = apps.get_model('assignments', 'AssignmentSubmission')
        return AssignmentSubmission.objects.filter(assignment=self).count()
    
    def get_graded_count(self):
        """Get the count of graded submissions for this assignment"""
        from django.apps import apps
        AssignmentSubmission = apps.get_model('assignments', 'AssignmentSubmission')
        return AssignmentSubmission.objects.filter(assignment=self).exclude(grade=None).count()
    



class AssignmentGroup(models.Model):
    """Groups for group assignments"""
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Group leader (optional)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_groups'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assignment_groups'
        unique_together = ['assignment', 'name']
    
    def __str__(self):
        return f"{self.assignment.title} - {self.name}"
    
    @property
    def member_count(self):
        """Get the count of members in this group"""
        from django.apps import apps
        AssignmentGroupMember = apps.get_model('assignments', 'AssignmentGroupMember')
        return AssignmentGroupMember.objects.filter(group=self).count()
    

    
    def can_add_member(self):
        max_size = self.assignment.max_group_size
        if max_size is None:
            return True
        return self.member_count < max_size


class AssignmentGroupMember(models.Model):
    """Members of assignment groups"""
    
    group = models.ForeignKey(AssignmentGroup, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assignment_group_members'
        unique_together = ['group', 'student']
    
    def __str__(self):
        return f"{self.student.email} in {self.group.name}"


class AssignmentSubmission(models.Model):
    """Student submissions for assignments"""
    
    class SubmissionStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'
        RETURNED = 'returned', 'Returned for Revision'
        LATE = 'late', 'Late Submission'
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='assignment_submissions'
    )
    group = models.ForeignKey(
        AssignmentGroup, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='submissions'
    )
    
    # Submission content
    text_submission = models.TextField(blank=True)
    url_submission = models.URLField(blank=True)
    
    # Status and grading
    status = models.CharField(max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.DRAFT)
    is_late = models.BooleanField(default=False)
    
    # Grading
    grade = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    
    # Feedback
    instructor_feedback = models.TextField(blank=True)
    private_notes = models.TextField(blank=True)  # Internal notes for instructors
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignment_submissions'
        unique_together = ['assignment', 'student']
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.email} - {self.assignment.title}"
    
    def submit(self):
        """Mark submission as submitted"""
        if self.status == self.SubmissionStatus.DRAFT:
            self.status = self.SubmissionStatus.SUBMITTED
            self.submitted_at = timezone.now()
            
            # Check if late
            if timezone.now() > self.assignment.due_date:
                self.is_late = True
                self.status = self.SubmissionStatus.LATE
            
            self.save()
    
    @property
    def final_grade(self):
        """Calculate final grade considering late penalty"""
        if self.grade is None:
            return None
        
        if self.is_late and self.assignment.late_penalty_percentage > 0:
            penalty = (self.assignment.late_penalty_percentage / 100) * self.grade
            return max(0, self.grade - penalty)
        
        return self.grade


class AssignmentFile(models.Model):
    """Files uploaded for assignments"""
    
    submission = models.ForeignKey(
        AssignmentSubmission, 
        on_delete=models.CASCADE, 
        related_name='files'
    )
    file = models.FileField(upload_to='assignment_submissions/')
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assignment_files'
    
    def __str__(self):
        return f"{self.original_filename} - {self.submission.student.email}"


class AssignmentRubric(models.Model):
    """Rubrics for assignment grading"""
    
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='rubric')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignment_rubrics'
    
    def __str__(self):
        return f"Rubric for {self.assignment.title}"
    
    @property
    def total_points(self):
        """Get the total points for this rubric"""
        from django.apps import apps
        RubricCriterion = apps.get_model('assignments', 'RubricCriterion')
        result = RubricCriterion.objects.filter(rubric=self).aggregate(
            total=models.Sum('points')
        )
        return result['total'] or 0
    



class RubricCriterion(models.Model):
    """Individual criteria in assignment rubrics"""
    
    rubric = models.ForeignKey(AssignmentRubric, on_delete=models.CASCADE, related_name='criteria')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points = models.IntegerField(validators=[MinValueValidator(1)])
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'rubric_criteria'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"{self.rubric.assignment.title} - {self.name}"


class RubricLevel(models.Model):
    """Performance levels for rubric criteria"""
    
    criterion = models.ForeignKey(RubricCriterion, on_delete=models.CASCADE, related_name='levels')
    name = models.CharField(max_length=100)  # e.g., "Excellent", "Good", "Needs Improvement"
    description = models.TextField()
    points = models.IntegerField(validators=[MinValueValidator(0)])
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'rubric_levels'
        ordering = ['-points']
    
    def __str__(self):
        return f"{self.criterion.name} - {self.name}"


class RubricGrade(models.Model):
    """Grades given using rubrics"""
    
    submission = models.ForeignKey(
        AssignmentSubmission, 
        on_delete=models.CASCADE, 
        related_name='rubric_grades'
    )
    criterion = models.ForeignKey(RubricCriterion, on_delete=models.CASCADE, related_name='grades')
    level = models.ForeignKey(RubricLevel, on_delete=models.CASCADE, related_name='assigned_grades')
    points_earned = models.IntegerField()
    comments = models.TextField(blank=True)
    
    graded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rubric_grades'
        unique_together = ['submission', 'criterion']
    
    def __str__(self):
        return f"{self.submission.student.email} - {self.criterion.name}: {self.points_earned} pts"


class PeerReview(models.Model):
    """Peer review assignments"""
    
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='peer_review')
    reviews_per_submission = models.IntegerField(default=3)
    reviewer_anonymity = models.BooleanField(default=True)
    
    # Review period
    review_start_date = models.DateTimeField()
    review_end_date = models.DateTimeField()
    
    # Instructions for reviewers
    review_instructions = models.TextField()
    review_criteria = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'peer_reviews'
    
    def __str__(self):
        return f"Peer Review for {self.assignment.title}"


class PeerReviewAssignment(models.Model):
    """Assignment of reviewers to submissions"""
    
    peer_review = models.ForeignKey(PeerReview, on_delete=models.CASCADE, related_name='review_assignments')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='assigned_reviews'
    )
    submission_to_review = models.ForeignKey(
        AssignmentSubmission, 
        on_delete=models.CASCADE, 
        related_name='peer_review_assignments'
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'peer_review_assignments'
        unique_together = ['reviewer', 'submission_to_review']
    
    def __str__(self):
        return f"{self.reviewer.email} reviewing {self.submission_to_review.student.email}"


class PeerReviewSubmission(models.Model):
    """Peer review submissions"""
    
    review_assignment = models.OneToOneField(
        PeerReviewAssignment, 
        on_delete=models.CASCADE, 
        related_name='review_submission'
    )
    
    # Review content
    overall_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    criteria_scores = models.JSONField(default=dict)  # {"criterion1": 4, "criterion2": 3}
    written_feedback = models.TextField()
    suggestions = models.TextField(blank=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    instructor_notes = models.TextField(blank=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'peer_review_submissions'
    
    def __str__(self):
        return f"Review by {self.review_assignment.reviewer.email}"

