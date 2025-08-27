from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from PIL import Image


class User(AbstractUser):
    """Custom User model with role-based system"""
    
    class UserRole(models.TextChoices):
        STUDENT = 'student', 'Student'
        INSTRUCTOR = 'instructor', 'Instructor'
        ADMIN = 'admin', 'Admin'
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'
    
    # Core fields
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    
    # Profile information
    full_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Location
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Account status
    is_email_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.PENDING
    )
    
    # Instructor specific fields
    instructor_application_date = models.DateTimeField(blank=True, null=True)
    instructor_approval_date = models.DateTimeField(blank=True, null=True)
    instructor_bio = models.TextField(max_length=1000, blank=True)
    expertise_areas = models.JSONField(default=list, blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    language_preference = models.CharField(max_length=10, default='en')
    
    # Tracking
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        role_display = dict(self.UserRole.choices).get(self.role, self.role)
        return f"{self.email} ({role_display})"
    
    @property
    def display_name(self):
        return self.full_name or self.username
    
    def save(self, *args, **kwargs):
        # Resize profile image
        if self.profile_image:
            super().save(*args, **kwargs)
            img = Image.open(self.profile_image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_image.path)
        else:
            super().save(*args, **kwargs)
    
    def get_courses_count(self):
        """Get count of courses for instructor or enrolled courses for student"""
        if self.role == self.UserRole.INSTRUCTOR:
            return getattr(self, 'created_courses', self.__class__.objects.none()).filter(is_published=True).count()
        elif self.role == self.UserRole.STUDENT:
            return getattr(self, 'enrollments', self.__class__.objects.none()).filter(is_active=True).count()
        return 0
    
    def can_create_courses(self):
        """Check if user can create courses"""
        return (self.role == self.UserRole.INSTRUCTOR and 
                self.verification_status == self.VerificationStatus.VERIFIED)


class UserProfile(models.Model):
    """Extended profile information for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Social links
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    github = models.URLField(blank=True)
    
    # Education background
    education = models.JSONField(default=list, blank=True)  # List of education entries
    
    # Work experience
    experience = models.JSONField(default=list, blank=True)  # List of work experiences
    
    # Skills and interests
    skills = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('students_only', 'Students Only'),
            ('private', 'Private')
        ],
        default='public'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"{self.user.email} Profile"


class UserActivity(models.Model):
    """Track user activities for analytics"""
    
    class ActivityType(models.TextChoices):
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        COURSE_VIEW = 'course_view', 'Course View'
        LESSON_COMPLETE = 'lesson_complete', 'Lesson Complete'
        ASSIGNMENT_SUBMIT = 'assignment_submit', 'Assignment Submit'
        FORUM_POST = 'forum_post', 'Forum Post'
        COURSE_PURCHASE = 'course_purchase', 'Course Purchase'
        COURSE_ENROLL = 'course_enroll', 'Course Enroll'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        activity_display = dict(self.ActivityType.choices).get(self.activity_type, self.activity_type)
        return f"{self.user.email} - {activity_display}"


class EmailVerification(models.Model):
    """Email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verifications'
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Email verification for {self.user.email}"


class PasswordResetToken(models.Model):
    """Password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Password reset for {self.user.email}"