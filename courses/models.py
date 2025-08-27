from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet


class Category(models.Model):
    """Course categories for organization"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon class
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    if TYPE_CHECKING:
        courses: 'QuerySet[Course]'
    
    class Meta:
        db_table = 'course_categories'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_course_count(self):
        return self.courses.filter(is_published=True).count()


class Course(models.Model):
    """Main course model supporting both self-paced and structured learning"""
    
    class CourseType(models.TextChoices):
        SELF_PACED = 'self_paced', 'Self-Paced (Udemy Style)'
        STRUCTURED = 'structured', 'Structured Class (Google Classroom Style)'
    
    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
    
    class CourseStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'
        ARCHIVED = 'archived', 'Archived'
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    
    # Course metadata
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_courses'
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    course_type = models.CharField(max_length=20, choices=CourseType.choices)
    difficulty_level = models.CharField(max_length=20, choices=DifficultyLevel.choices)
    
    # Media
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    preview_video = models.FileField(upload_to='course_previews/', blank=True, null=True)
    
    # Pricing (for self-paced courses)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_free = models.BooleanField(default=False)
    
    # Course content
    learning_objectives = models.JSONField(default=list)  # List of learning objectives
    prerequisites = models.JSONField(default=list)  # List of prerequisites
    target_audience = models.JSONField(default=list)  # List of target audience
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=CourseStatus.choices, default=CourseStatus.DRAFT)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    # Tracking
    total_duration_minutes = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    
    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    if TYPE_CHECKING:
        reviews: 'QuerySet[CourseReview]'
        batches: 'QuerySet[CourseBatch]'
        enrollments: 'QuerySet[Enrollment]'
        lessons: 'QuerySet'  # Related to lessons app
        
        # Django-generated methods for choice fields
        def get_course_type_display(self) -> str: ...
        def get_difficulty_level_display(self) -> str: ...
        def get_status_display(self) -> str: ...
    
    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course_type', 'status']),
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['instructor', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_course_type_display()})"
    
    def save(self, *args, **kwargs):
        if self.status == self.CourseStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
            self.is_published = True
        elif self.status != self.CourseStatus.PUBLISHED:
            self.is_published = False
        super().save(*args, **kwargs)
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0
    
    @property
    def total_reviews(self):
        return self.reviews.filter(is_approved=True).count()
    
    def get_active_batches(self):
        """Get active batches for structured courses"""
        if self.course_type == self.CourseType.STRUCTURED:
            return self.batches.filter(
                status=CourseBatch.BatchStatus.ACTIVE,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
        return CourseBatch.objects.none()


class CourseBatch(models.Model):
    """Batches for structured courses (Google Classroom style)"""
    
    class BatchStatus(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=100)  # e.g., "September 2024 Batch"
    description = models.TextField(blank=True)
    
    # Schedule
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    enrollment_start = models.DateTimeField()
    enrollment_end = models.DateTimeField()
    
    # Capacity
    max_students = models.IntegerField(validators=[MinValueValidator(1)])
    current_enrollments = models.IntegerField(default=0)
    
    # Pricing (can override course pricing)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.UPCOMING)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_batches'
        ordering = ['start_date']
        unique_together = ['course', 'name']
    
    def __str__(self):
        return f"{self.course.title} - {self.name}"
    
    @property
    def is_enrollment_open(self):
        now = timezone.now()
        return (self.enrollment_start <= now <= self.enrollment_end and 
                self.current_enrollments < self.max_students and
                self.status == self.BatchStatus.UPCOMING)
    
    @property
    def available_spots(self):
        return self.max_students - self.current_enrollments


class Enrollment(models.Model):
    """Student enrollments in courses"""
    
    class EnrollmentStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        SUSPENDED = 'suspended', 'Suspended'
        REFUNDED = 'refunded', 'Refunded'
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    batch = models.ForeignKey(
        CourseBatch, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='enrollments'
    )
    
    # Status and progress
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    
    # Payment information
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)
    
    if TYPE_CHECKING:
        lesson_progress: 'QuerySet'  # Related to lessons app
    
    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"
    
    def calculate_progress(self):
        """Calculate and update progress percentage"""
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            self.progress_percentage = Decimal('0.00')
        else:
            completed_lessons = self.lesson_progress.filter(is_completed=True).count()
            self.progress_percentage = Decimal(str((completed_lessons / total_lessons) * 100))
        self.save(update_fields=['progress_percentage'])
        return self.progress_percentage


class CourseReview(models.Model):
    """Course reviews and ratings"""
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='course_reviews'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_reviews'
        unique_together = ['student', 'course']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.student.email} for {self.course.title} ({self.rating}★)"


class CourseWishlist(models.Model):
    """Course wishlist for students"""
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wishlisted_courses'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'course_wishlists'
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.email} wishlisted {self.course.title}"


class CourseTag(models.Model):
    """Tags for courses"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        db_table = 'course_tags'
    
    def __str__(self):
        return self.name


class CourseTagging(models.Model):
    """Many-to-many relationship between courses and tags"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tags')
    tag = models.ForeignKey(CourseTag, on_delete=models.CASCADE, related_name='tagged_courses')
    
    class Meta:
        db_table = 'course_taggings'
        unique_together = ['course', 'tag']