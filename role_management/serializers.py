from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import Dict, Any

from .models import (
    RoleDefinition, UserRoleAssignment, RoleChangeHistory,
    RolePermissionGroup, RolePermissionAssignment, UserRoleRequest
)

User = get_user_model()


class RoleDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for role definitions"""
    
    active_assignments_count = serializers.SerializerMethodField()
    total_assignments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RoleDefinition
        fields = [
            'id', 'name', 'display_name', 'description',
            'can_manage_users', 'can_manage_courses', 'can_manage_content',
            'can_view_analytics', 'can_manage_payments', 'can_manage_system',
            'can_moderate_forums', 'can_support_users',
            'hierarchy_level', 'max_users_manageable',
            'is_active', 'is_assignable',
            'active_assignments_count', 'total_assignments_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_active_assignments_count(self, obj):
        """Get count of active role assignments"""
        return obj.user_assignments.filter(
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).count()
    
    def get_total_assignments_count(self, obj):
        """Get total count of role assignments"""
        return obj.user_assignments.count()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for role management"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'username', 'date_joined']


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for user role assignments"""
    
    user_details = UserBasicSerializer(source='user', read_only=True)
    role_details = RoleDefinitionSerializer(source='role', read_only=True)
    assigned_by_name = serializers.CharField(
        source='assigned_by.get_full_name',
        read_only=True
    )
    revoked_by_name = serializers.CharField(
        source='revoked_by.get_full_name',
        read_only=True
    )
    is_currently_active = serializers.ReadOnlyField()
    days_since_assignment = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRoleAssignment
        fields = [
            'id', 'user', 'role', 'user_details', 'role_details',
            'assigned_by', 'assigned_by_name', 'assigned_at',
            'status', 'effective_from', 'effective_until',
            'assignment_reason', 'notes',
            'revoked_by', 'revoked_by_name', 'revoked_at', 'revocation_reason',
            'is_currently_active', 'days_since_assignment',
            'updated_at'
        ]
        read_only_fields = [
            'assigned_at', 'revoked_at', 'is_currently_active',
            'days_since_assignment', 'updated_at'
        ]
    
    def get_days_since_assignment(self, obj):
        """Calculate days since role was assigned"""
        if obj.assigned_at:
            delta = timezone.now() - obj.assigned_at
            return delta.days
        return 0
    
    def validate(self, attrs):
        """Validate role assignment data"""
        effective_from = attrs.get('effective_from')
        effective_until = attrs.get('effective_until')
        
        if effective_until and effective_from and effective_from >= effective_until:
            raise serializers.ValidationError(
                "Effective until must be after effective from"
            )
        
        return attrs


class RoleChangeHistorySerializer(serializers.ModelSerializer):
    """Serializer for role change history"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    role_name = serializers.CharField(source='role.display_name', read_only=True)
    changed_by_name = serializers.CharField(
        source='changed_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = RoleChangeHistory
        fields = [
            'id', 'user', 'user_name', 'role', 'role_name',
            'role_assignment', 'change_type',
            'changed_by', 'changed_by_name', 'changed_at',
            'previous_values', 'new_values', 'reason', 'context'
        ]
        read_only_fields = ['changed_at']


class RolePermissionGroupSerializer(serializers.ModelSerializer):
    """Serializer for role permission groups"""
    
    roles_count = serializers.SerializerMethodField()
    assigned_roles = RoleDefinitionSerializer(source='roles', many=True, read_only=True)
    
    class Meta:
        model = RolePermissionGroup
        fields = [
            'id', 'name', 'description', 'permissions',
            'is_active', 'roles_count', 'assigned_roles',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_roles_count(self, obj):
        """Get count of roles using this permission group"""
        return obj.roles.count()


class UserRoleRequestSerializer(serializers.ModelSerializer):
    """Serializer for user role requests"""
    
    user_details = UserBasicSerializer(source='user', read_only=True)
    requested_role_details = RoleDefinitionSerializer(source='requested_role', read_only=True)
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.get_full_name',
        read_only=True
    )
    days_pending = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRoleRequest
        fields = [
            'id', 'user', 'user_details', 'requested_role', 'requested_role_details',
            'current_role', 'justification', 'supporting_documents',
            'status', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'review_notes', 'days_pending',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'reviewed_by', 'reviewed_at', 'days_pending',
            'created_at', 'updated_at'
        ]
    
    def get_days_pending(self, obj):
        """Calculate days since request was created"""
        if obj.status == UserRoleRequest.RequestStatus.PENDING:
            delta = timezone.now() - obj.created_at
            return delta.days
        return 0


class UserRoleManagementSerializer(serializers.Serializer):
    """Comprehensive serializer for user role management"""
    
    user_id = serializers.IntegerField()
    role_id = serializers.IntegerField()
    action = serializers.ChoiceField(
        choices=['assign', 'revoke', 'suspend', 'reactivate']
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    effective_from = serializers.DateTimeField(required=False)
    effective_until = serializers.DateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
    
    def validate_role_id(self, value):
        """Validate role exists and is assignable"""
        try:
            role = RoleDefinition.objects.get(id=value)
            if not role.is_assignable:
                raise serializers.ValidationError("Role is not assignable")
            return value
        except RoleDefinition.DoesNotExist:
            raise serializers.ValidationError("Role not found")
    
    def validate(self, attrs):
        """Cross-field validation"""
        effective_from = attrs.get('effective_from')
        effective_until = attrs.get('effective_until')
        
        if effective_until and effective_from and effective_from >= effective_until:
            raise serializers.ValidationError(
                "Effective until must be after effective from"
            )
        
        return attrs


class UserWithRolesSerializer(serializers.ModelSerializer):
    """Serializer for users with their role information"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    active_roles = serializers.SerializerMethodField()
    role_history_count = serializers.SerializerMethodField()
    current_primary_role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'date_joined',
            'active_roles', 'role_history_count', 'current_primary_role'
        ]
        read_only_fields = ['id', 'username', 'date_joined']
    
    def get_active_roles(self, obj):
        """Get active role assignments for user"""
        active_assignments = obj.role_assignments.filter(
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).select_related('role')
        
        return [
            {
                'id': assignment.id,
                'role_name': assignment.role.name,
                'role_display_name': assignment.role.display_name,
                'assigned_at': assignment.assigned_at,
                'effective_from': assignment.effective_from,
                'effective_until': assignment.effective_until
            }
            for assignment in active_assignments
        ]
    
    def get_role_history_count(self, obj):
        """Get count of role changes for user"""
        return obj.role_change_history.count()
    
    def get_current_primary_role(self, obj):
        """Get the user's primary (highest hierarchy) role"""
        active_assignment = obj.role_assignments.filter(
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).select_related('role').order_by('role__hierarchy_level').first()
        
        if active_assignment:
            return {
                'name': active_assignment.role.name,
                'display_name': active_assignment.role.display_name,
                'hierarchy_level': active_assignment.role.hierarchy_level
            }
        return None


class BulkRoleAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk role assignments"""
    
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    role_id = serializers.IntegerField()
    action = serializers.ChoiceField(
        choices=['assign', 'revoke']
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    effective_from = serializers.DateTimeField(required=False)
    effective_until = serializers.DateTimeField(required=False)
    
    def validate_user_ids(self, value):
        """Validate all users exist"""
        existing_users = User.objects.filter(id__in=value).values_list('id', flat=True)
        missing_users = set(value) - set(existing_users)
        
        if missing_users:
            raise serializers.ValidationError(
                f"Users not found: {list(missing_users)}"
            )
        
        return value
    
    def validate_role_id(self, value):
        """Validate role exists and is assignable"""
        try:
            role = RoleDefinition.objects.get(id=value)
            if not role.is_assignable:
                raise serializers.ValidationError("Role is not assignable")
            return value
        except RoleDefinition.DoesNotExist:
            raise serializers.ValidationError("Role not found")