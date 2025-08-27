from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse, NoReverseMatch
from typing import TYPE_CHECKING, Dict, Any, List, Optional
import json

# Handle optional import of role_management module
try:
    import role_management.models
    ROLE_MANAGEMENT_AVAILABLE = True
except ImportError:
    role_management = None
    ROLE_MANAGEMENT_AVAILABLE = False

if TYPE_CHECKING:
    from django.db.models import QuerySet
    # Define UserRoleAssignment for type checking if it's not available
    if not ROLE_MANAGEMENT_AVAILABLE:
        from django.contrib.auth.models import User
        class UserRoleAssignment:
            user: User
            role: Any
            is_active: bool
            status: str


class MenuGroup(models.Model):
    """
    Menu groups for organizing navigation items (e.g., 'Main Navigation', 'Admin Panel')
    """
    
    class GroupType(models.TextChoices):
        MAIN = 'main', 'Main Navigation'
        ADMIN = 'admin', 'Admin Panel'
        STUDENT = 'student', 'Student Dashboard'
        INSTRUCTOR = 'instructor', 'Instructor Panel'
        MOBILE = 'mobile', 'Mobile Navigation'
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    group_type = models.CharField(max_length=20, choices=GroupType.choices, default=GroupType.MAIN)
    
    # Display settings
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    # Role-based visibility
    min_role_level = models.IntegerField(
        default=10,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
        help_text="Minimum role level required to see this menu group (10=Student, 100=Super Admin)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_menu_groups'
    )
    
    if TYPE_CHECKING:
        items: 'QuerySet[MenuItem]'
    
    class Meta:
        db_table = 'navigation_menu_groups'
        ordering = ['sort_order', 'name']
        verbose_name = 'Menu Group'
        verbose_name_plural = 'Menu Groups'
    
    def __str__(self):
        return self.name
    
    def get_active_items(self) -> 'QuerySet[MenuItem]':
        """Get active menu items for this group"""
        return self.items.filter(is_active=True).order_by('sort_order', 'title')
    
    def get_items_for_user(self, user) -> 'QuerySet[MenuItem]':
        """Get menu items visible to a specific user based on their role"""
        if not user.is_authenticated:
            return self.items.filter(
                is_active=True,
                requires_authentication=False
            ).order_by('sort_order', 'title')
        
        # Get user's role level
        user_role_level = self._get_user_role_level(user)
        
        return self.items.filter(
            is_active=True,
            min_role_level__lte=user_role_level
        ).order_by('sort_order', 'title')
    
    def _get_user_role_level(self, user) -> int:
        """Get user's role level from role management system"""
        if ROLE_MANAGEMENT_AVAILABLE and role_management is not None:
            try:
                # Access UserRoleAssignment dynamically to avoid static analysis issues
                UserRoleAssignment = getattr(role_management.models, 'UserRoleAssignment')
                assignment = UserRoleAssignment.objects.filter(
                    user=user, 
                    status=UserRoleAssignment.AssignmentStatus.ACTIVE
                ).first()
                if assignment and assignment.role:
                    # Map role names to levels based on user preference
                    role_levels = {
                        'student': 10,
                        'teaching_assistant': 20,
                        'instructor': 30,
                        'course_coordinator': 40,
                        'department_head': 50,
                        'dean': 60,
                        'system_admin': 70,
                        'platform_admin': 80,
                        'admin': 90,
                        'super_admin': 100,
                    }
                    return role_levels.get(assignment.role.name, 10)
            except Exception:
                # Handle any other exceptions that might occur
                pass
        
        # Fallback to Django's built-in permissions
        if user.is_superuser:
            return 100
        elif user.is_staff:
            return 70
        else:
            return 10


class MenuItem(models.Model):
    """
    Individual menu items with hierarchical structure and role-based access control
    """
    
    class TargetType(models.TextChoices):
        INTERNAL = 'internal', 'Internal Link'
        EXTERNAL = 'external', 'External Link'
        API_ENDPOINT = 'api_endpoint', 'API Endpoint'
    
    # Hierarchy
    menu_group = models.ForeignKey(MenuGroup, on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # Menu item details
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon identifier or class (e.g., 'home', 'user')"
    )
    
    # URL configuration
    target_type = models.CharField(max_length=20, choices=TargetType.choices, default=TargetType.INTERNAL)
    url_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Django URL name for internal links"
    )
    url_path = models.CharField(
        max_length=200,
        blank=True,
        help_text="Direct URL path or external URL"
    )
    url_params = models.JSONField(
        default=dict,
        blank=True,
        help_text="URL parameters as JSON object"
    )
    
    # Link behavior
    opens_in_new_window = models.BooleanField(
        default=False,
        help_text="Open link in new window/tab"
    )
    
    # Display settings
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    # UI customization
    css_classes = models.CharField(
        max_length=200,
        blank=True,
        help_text="Additional CSS classes for styling"
    )
    badge_text = models.CharField(
        max_length=20,
        blank=True,
        help_text="Badge text to display (e.g., 'New', 'Beta')"
    )
    badge_color = models.CharField(
        max_length=20,
        blank=True,
        help_text="Badge color (e.g., 'primary', 'success', 'warning')"
    )
    
    # Role-based access control
    min_role_level = models.IntegerField(
        default=10,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
        help_text="Minimum role level required to see this menu item"
    )
    
    # Authentication requirements
    requires_authentication = models.BooleanField(default=True)
    hide_for_authenticated = models.BooleanField(
        default=False,
        help_text="Hide this item for authenticated users (useful for login/register links)"
    )
    
    # Conditional visibility
    show_only_if_has_permission = models.CharField(
        max_length=100,
        blank=True,
        help_text="Django permission codename (e.g., 'courses.add_course')"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_menu_items'
    )
    
    if TYPE_CHECKING:
        children: 'QuerySet[MenuItem]'
        permissions: 'QuerySet[MenuItemPermission]'
        click_tracking: 'QuerySet[MenuClickTracking]'
    
    class Meta:
        db_table = 'navigation_menu_items'
        ordering = ['menu_group', 'sort_order', 'title']
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        unique_together = ['menu_group', 'title', 'parent']
    
    def __str__(self):
        return f"{self.menu_group.name} > {self.title}"
    
    def get_url(self) -> str:
        """Get the resolved URL for this menu item"""
        if self.target_type == self.TargetType.EXTERNAL:
            return self.url_path
        
        if self.url_name:
            try:
                if self.url_params:
                    return reverse(self.url_name, kwargs=self.url_params)
                else:
                    return reverse(self.url_name)
            except NoReverseMatch:
                return self.url_path or '#'
        
        return self.url_path or '#'
    
    def is_visible_to_user(self, user) -> bool:
        """Check if this menu item should be visible to the given user"""
        # Check authentication requirements
        if not user.is_authenticated:
            if self.requires_authentication:
                return False
        else:
            if self.hide_for_authenticated:
                return False
        
        # Check role level
        if user.is_authenticated:
            user_role_level = self._get_user_role_level(user)
            if user_role_level < self.min_role_level:
                return False
        
        # Check specific permissions
        if self.show_only_if_has_permission:
            if not user.has_perm(self.show_only_if_has_permission):
                return False
        
        return True
    
    def _get_user_role_level(self, user) -> int:
        """Get user's role level from role management system"""
        if ROLE_MANAGEMENT_AVAILABLE and role_management is not None:
            try:
                # Access UserRoleAssignment dynamically to avoid static analysis issues
                UserRoleAssignment = getattr(role_management.models, 'UserRoleAssignment')
                assignment = UserRoleAssignment.objects.filter(
                    user=user, 
                    status=UserRoleAssignment.AssignmentStatus.ACTIVE
                ).first()
                if assignment and assignment.role:
                    role_levels = {
                        'student': 10,
                        'teaching_assistant': 20,
                        'instructor': 30,
                        'course_coordinator': 40,
                        'department_head': 50,
                        'dean': 60,
                        'system_admin': 70,
                        'platform_admin': 80,
                        'admin': 90,
                        'super_admin': 100,
                    }
                    return role_levels.get(assignment.role.name, 10)
            except Exception:
                # Handle any other exceptions that might occur
                pass
        
        # Fallback
        if user.is_superuser:
            return 100
        elif user.is_staff:
            return 70
        else:
            return 10
    
    def get_children_for_user(self, user) -> 'QuerySet[MenuItem]':
        """Get child menu items visible to the user"""
        children = self.children.filter(is_active=True)
        visible_children = []
        
        for child in children:
            if child.is_visible_to_user(user):
                # Access child.id dynamically to avoid static analysis issues
                visible_children.append(getattr(child, 'id'))
        
        return self.children.filter(id__in=visible_children).order_by('sort_order', 'title')
    
    @property
    def level(self) -> int:
        """Get the depth level of this menu item in the hierarchy"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level


class MenuItemPermission(models.Model):
    """
    Additional role-based permissions for menu items
    """
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='permissions')
    role = models.ForeignKey(
        'role_management.RoleDefinition',
        on_delete=models.CASCADE,
        related_name='menu_permissions'
    )
    can_view = models.BooleanField(default=True)
    can_access = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'navigation_menu_item_permissions'
        unique_together = ['menu_item', 'role']
        verbose_name = 'Menu Item Permission'
        verbose_name_plural = 'Menu Item Permissions'
    
    def __str__(self):
        return f"{self.menu_item.title} - {self.role.name}"


class MenuClickTracking(models.Model):
    """
    Track menu item clicks for analytics (API usage tracking)
    """
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='click_tracking')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='menu_clicks'
    )
    
    # Click details
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    api_endpoint = models.CharField(max_length=200, blank=True, help_text="API endpoint that was accessed")
    referrer = models.CharField(
        max_length=200,
        blank=True,
        help_text="HTTP Referer header"
    )
    
    # Context
    session_key = models.CharField(max_length=40, blank=True)
    
    class Meta:
        db_table = 'navigation_menu_click_tracking'
        ordering = ['-clicked_at']
        verbose_name = 'Menu Click Tracking'
        verbose_name_plural = 'Menu Click Tracking'
        indexes = [
            models.Index(fields=['menu_item', 'clicked_at']),
            models.Index(fields=['user', 'clicked_at']),
            models.Index(fields=['clicked_at']),
        ]
    
    def __str__(self):
        user_info = self.user.email if self.user else f"Anonymous ({self.ip_address})"
        return f"{self.menu_item.title} clicked by {user_info}"


class MenuConfiguration(models.Model):
    """
    Configuration settings for navigation system
    """
    
    class ConfigType(models.TextChoices):
        THEME = 'theme', 'Theme Configuration'
        BEHAVIOR = 'behavior', 'Behavior Settings'
        CACHE = 'cache', 'Cache Settings'
        API = 'api', 'API Configuration'
        FEATURES = 'features', 'Feature Flags'
        ANALYTICS = 'analytics', 'Analytics Settings'
    
    key = models.CharField(max_length=100, unique=True)
    config_type = models.CharField(max_length=20, choices=ConfigType.choices)
    description = models.TextField(blank=True)
    value = models.TextField(
        help_text="Configuration value in JSON format or plain text"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'navigation_menu_configuration'
        ordering = ['config_type', 'key']
        verbose_name = 'Menu Configuration'
        verbose_name_plural = 'Menu Configurations'
    
    def __str__(self):
        return f"{self.key} ({self.config_type})"
    
    def get_value(self):
        """Get parsed configuration value"""
        if not self.value:
            return None
            
        try:
            # Try to parse as JSON
            return json.loads(self.value)
        except (json.JSONDecodeError, ValueError):
            # Return as string if not valid JSON
            return self.value
    
    def set_value(self, value):
        """Set configuration value, auto-converting to JSON if needed"""
        if isinstance(value, (dict, list)):
            self.value = json.dumps(value, indent=2)
        else:
            self.value = str(value)