from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, UserActivity, EmailVerification, PasswordResetToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'verification_status', 'is_active', 'date_joined')
    list_filter = ('role', 'verification_status', 'is_active', 'is_email_verified')
    search_fields = ('email', 'username', 'full_name')
    ordering = ('-date_joined',)
    
    fieldsets = list(UserAdmin.fieldsets or []) + [
        ('Profile Information', {
            'fields': ('full_name', 'bio', 'profile_image', 'birth_date', 'phone', 'country', 'city')
        }),
        ('Role & Verification', {
            'fields': ('role', 'verification_status', 'is_email_verified', 'instructor_bio', 'expertise_areas')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'marketing_emails', 'language_preference')
        }),
    ]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_visibility', 'created_at')
    list_filter = ('profile_visibility',)
    search_fields = ('user__email', 'user__username')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__email', 'description')
    readonly_fields = ('timestamp',)


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')