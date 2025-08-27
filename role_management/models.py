from django.db import models
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet


class RoleDefinition(models.Model):
    """Model to define available roles and their permissions"""
    
    class RoleType(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        INSTRUCTOR = 'instructor', 'Instructor'
        STUDENT = 'student', 'Student'
        MODERATOR = 'moderator', 'Moderator'
        ASSISTANT = 'assistant', 'Teaching Assistant'
        SUPPORT = 'support', 'Support Staff'
    
    name = models.CharField(max_length=50, choices=RoleType.choices, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Permission flags
    can_manage_users = models.BooleanField(default=False)
    can_manage_courses = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    can_manage_payments = models.BooleanField(default=False)
    can_manage_system = models.BooleanField(default=False)
    can_moderate_forums = models.BooleanField(default=False)
    can_support_users = models.BooleanField(default=False)
    
    # Role hierarchy and limits
    hierarchy_level = models.IntegerField(
        default=1,
        help_text="Lower numbers have higher privileges (1=highest, 10=lowest)"
    )
    max_users_manageable = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Maximum number of users this role can manage (null = unlimited)"
    )
    
    # Role status
    is_active = models.BooleanField(default=True)
    is_assignable = models.BooleanField(
        default=True,
        help_text="Whether this role can be assigned to users"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'role_definitions'
        ordering = ['hierarchy_level', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['hierarchy_level']),
            models.Index(fields=['is_active', 'is_assignable']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"
    
    def clean(self):
        """Validate role definition"""
        if self.hierarchy_level < 1:
            raise ValidationError("Hierarchy level must be at least 1")
        
        if self.max_users_manageable is not None and self.max_users_manageable < 0:
            raise ValidationError("Max users manageable cannot be negative")


class UserRoleAssignment(models.Model):
    """Model to track user role assignments and changes"""
    
    class AssignmentStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        REVOKED = 'revoked', 'Revoked'
        EXPIRED = 'expired', 'Expired'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    role = models.ForeignKey(
        RoleDefinition,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    
    # Assignment details
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    # Status and validity
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.ACTIVE
    )
    effective_from = models.DateTimeField(default=timezone.now)
    effective_until = models.DateTimeField(null=True, blank=True)
    
    # Assignment reason and notes
    assignment_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Revocation details
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_roles'
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_role_assignments'
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['role', 'status']),
            models.Index(fields=['assigned_at']),
            models.Index(fields=['effective_from', 'effective_until']),
        ]
        unique_together = [
            ['user', 'role', 'status']  # One active assignment per user-role combination
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.role.display_name} ({self.status})"
    
    def clean(self):
        """Validate role assignment"""
        if self.effective_until and self.effective_from >= self.effective_until:
            raise ValidationError("Effective until must be after effective from")
        
        if self.status == self.AssignmentStatus.REVOKED and not self.revoked_at:
            self.revoked_at = timezone.now()
    
    @property
    def is_currently_active(self):
        """Check if the role assignment is currently active"""
        now = timezone.now()
        
        if self.status != self.AssignmentStatus.ACTIVE:
            return False
        
        if self.effective_from > now:
            return False
        
        if self.effective_until and self.effective_until <= now:
            return False
        
        return True
    
    def revoke(self, revoked_by=None, reason=""):
        """Revoke the role assignment"""
        self.status = self.AssignmentStatus.REVOKED
        self.revoked_by = revoked_by
        self.revoked_at = timezone.now()
        self.revocation_reason = reason
        self.save()


class RoleChangeHistory(models.Model):
    """Model to track history of role changes for audit purposes"""
    
    class ChangeType(models.TextChoices):
        ASSIGNED = 'assigned', 'Role Assigned'
        REVOKED = 'revoked', 'Role Revoked'
        SUSPENDED = 'suspended', 'Role Suspended'
        REACTIVATED = 'reactivated', 'Role Reactivated'
        EXPIRED = 'expired', 'Role Expired'
        MODIFIED = 'modified', 'Role Modified'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_change_history'
    )
    role = models.ForeignKey(
        RoleDefinition,
        on_delete=models.CASCADE,
        related_name='change_history'
    )
    role_assignment = models.ForeignKey(
        UserRoleAssignment,
        on_delete=models.CASCADE,
        related_name='change_history'
    )
    
    # Change details
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_changes_made'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    
    # Previous and new values (JSON for flexibility)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Change reason and context
    reason = models.TextField(blank=True)
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context about the change (IP, user agent, etc.)"
    )
    
    class Meta:
        db_table = 'role_change_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['user', 'changed_at']),
            models.Index(fields=['role', 'changed_at']),
            models.Index(fields=['change_type', 'changed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.role.display_name} - {self.change_type}"


class RolePermissionGroup(models.Model):
    """Model to group permissions for easier role management"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Grouped permissions
    permissions = models.JSONField(
        default=list,
        help_text="List of permission identifiers in this group"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Many-to-many relationship with roles
    roles = models.ManyToManyField(
        RoleDefinition,
        through='RolePermissionAssignment',
        related_name='permission_groups'
    )
    
    class Meta:
        db_table = 'role_permission_groups'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class RolePermissionAssignment(models.Model):
    """Through model for role-permission group assignments"""
    
    role = models.ForeignKey(
        RoleDefinition,
        on_delete=models.CASCADE
    )
    permission_group = models.ForeignKey(
        RolePermissionGroup,
        on_delete=models.CASCADE
    )
    
    # Assignment details
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'role_permission_assignments'
        unique_together = ['role', 'permission_group']
    
    def __str__(self):
        return f"{self.role.display_name} - {self.permission_group.name}"


class UserRoleRequest(models.Model):
    """Model for users to request role changes"""
    
    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_requests'
    )
    requested_role = models.ForeignKey(
        RoleDefinition,
        on_delete=models.CASCADE,
        related_name='role_requests'
    )
    
    # Request details
    current_role = models.CharField(max_length=50, blank=True)
    justification = models.TextField()
    supporting_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of document URLs or references"
    )
    
    # Request status
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )
    
    # Review details
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_role_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_role_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['requested_role', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} requests {self.requested_role.display_name}"
    
    def approve(self, approved_by, notes=""):
        """Approve the role request"""
        self.status = self.RequestStatus.APPROVED
        self.reviewed_by = approved_by
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def reject(self, rejected_by, notes=""):
        """Reject the role request"""
        self.status = self.RequestStatus.REJECTED
        self.reviewed_by = rejected_by
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()