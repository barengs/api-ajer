from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    RoleDefinition, 
    UserRoleAssignment, 
    RoleChangeHistory, 
    RolePermissionGroup, 
    UserRoleRequest
)

User = get_user_model()


@admin.register(RoleDefinition)
class RoleDefinitionAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'hierarchy_level', 'is_active', 'users_count', 'created_at']
    list_filter = ['name', 'is_active', 'hierarchy_level', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['hierarchy_level', 'name']
    readonly_fields = ['created_at', 'updated_at', 'users_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('Hierarchy & Permissions', {
            'fields': ('hierarchy_level', 'max_users_manageable', 'can_manage_users', 
                      'can_manage_courses', 'can_manage_content', 'can_view_analytics',
                      'can_manage_payments', 'can_manage_system', 'can_moderate_forums',
                      'can_support_users', 'is_assignable')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'users_count'),
            'classes': ('collapse',)
        })
    )
    
    def users_count(self, obj):
        count = obj.user_assignments.filter(status='active').count()
        if count > 0:
            url = reverse('admin:role_management_userroleassignment_changelist')
            return format_html(
                '<a href="{}?role__id__exact={}">{} users</a>',
                url, obj.id, count
            )
        return count
    users_count.short_description = 'Active Users'  # type: ignore


class UserRoleAssignmentInline(admin.TabularInline):
    model = UserRoleAssignment
    fk_name = 'user'
    extra = 0
    fields = ['role', 'status', 'assigned_by', 'assigned_at', 'effective_until']
    readonly_fields = ['assigned_by', 'assigned_at']


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'user_info', 'role', 'status', 
        'assigned_by', 'assigned_at', 'effective_until'
    ]
    list_filter = [
        'status', 'role__name', 'assigned_at', 
        'effective_until', 'role'
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'role__name'
    ]
    date_hierarchy = 'assigned_at'
    ordering = ['-assigned_at']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('user', 'role', 'status')
        }),
        ('Assignment Info', {
            'fields': ('assigned_by', 'assigned_at', 'effective_from', 'effective_until', 
                      'assignment_reason', 'notes')
        }),
        ('Revocation Info', {
            'fields': ('revoked_by', 'revoked_at', 'revocation_reason'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['assigned_by', 'assigned_at', 'updated_at']
    
    def user_info(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
    user_info.short_description = 'User'  # type: ignore
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set assigned_by for new assignments
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RoleChangeHistory)
class RoleChangeHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user_info', 'role', 'change_type', 
        'changed_by', 'changed_at', 'reason_short'
    ]
    list_filter = ['change_type', 'changed_at', 'role__name']
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'role__name', 'reason'
    ]
    date_hierarchy = 'changed_at'
    ordering = ['-changed_at']
    readonly_fields = ['changed_at']
    
    fieldsets = (
        ('Change Details', {
            'fields': ('user', 'role', 'change_type', 'reason')
        }),
        ('Change Info', {
            'fields': ('changed_by', 'changed_at', 'context')
        })
    )
    
    def user_info(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username}"
    user_info.short_description = 'User'  # type: ignore
    
    def reason_short(self, obj):
        if obj.reason:
            return obj.reason[:50] + ('...' if len(obj.reason) > 50 else '')
        return '-'
    reason_short.short_description = 'Reason'  # type: ignore
    
    def has_add_permission(self, request):
        # History records should not be added manually
        return False
    
    def has_change_permission(self, request, obj=None):
        # History records should not be modified
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion only for superusers
        return getattr(request.user, 'is_superuser', False)


@admin.register(RolePermissionGroup)
class RolePermissionGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'permissions_count', 'roles_count', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Group Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def permissions_count(self, obj):
        return len(obj.permissions) if obj.permissions else 0
    permissions_count.short_description = 'Permissions'  # type: ignore
    
    def roles_count(self, obj):
        count = obj.roles.count()
        if count > 0:
            url = reverse('admin:role_management_roledefinition_changelist')
            return format_html(
                '<a href="{}?permission_groups__id__exact={}">{} roles</a>',
                url, obj.id, count
            )
        return count
    roles_count.short_description = 'Roles Using'  # type: ignore


@admin.register(UserRoleRequest)
class UserRoleRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user_info', 'requested_role', 'status', 'current_role',
        'created_at', 'reviewed_by', 'reviewed_at'
    ]
    list_filter = [
        'status', 'current_role', 'requested_role__name', 
        'created_at', 'reviewed_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name',
        'user__last_name', 'requested_role__name', 'justification'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Details', {
            'fields': ('user', 'requested_role', 'justification', 'current_role')
        }),
        ('Processing', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def user_info(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
    user_info.short_description = 'User'  # type: ignore
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status in ['approved', 'rejected'] and not obj.reviewed_by:
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests approved.')
    approve_requests.short_description = 'Approve selected requests'  # type: ignore
    
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests rejected.')
    reject_requests.short_description = 'Reject selected requests'  # type: ignore


# Extend User admin to show role information
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserRoleInline(admin.TabularInline):
    model = UserRoleAssignment
    fk_name = 'user'
    extra = 0
    fields = ['role', 'status', 'assigned_at', 'effective_until']
    readonly_fields = ['assigned_at']


# Unregister the default User admin and register our custom one
try:
    admin.site.unregister(User)
except Exception:  # admin.sites.NotRegistered
    pass

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = list(BaseUserAdmin.inlines) + [UserRoleInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('role_assignments__role')