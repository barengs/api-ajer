from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    MenuGroup, MenuItem, MenuItemPermission, 
    MenuClickTracking, MenuConfiguration
)

User = get_user_model()
class MenuConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for menu configuration"""
    
    value_parsed = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuConfiguration
        fields = [
            'id', 'key', 'config_type', 'description', 'value', 
            'value_parsed', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'value_parsed']
    
    def get_value_parsed(self, obj):
        """Get parsed configuration value"""
        return obj.get_value()


class MenuItemPermissionSerializer(serializers.ModelSerializer):
    """Serializer for menu item permissions"""
    
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_display_name = serializers.CharField(source='role.display_name', read_only=True)
    
    class Meta:
        model = MenuItemPermission
        fields = [
            'id', 'role', 'role_name', 'role_display_name',
            'can_view', 'can_access', 'created_at'
        ]
        read_only_fields = ['created_at']


class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for menu items with role-based filtering"""
    
    url = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    permissions = MenuItemPermissionSerializer(many=True, read_only=True)
    level = serializers.ReadOnlyField()
    is_visible = serializers.SerializerMethodField()
    has_children = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'title', 'description', 'icon', 'target_type',
            'url_name', 'url_path', 'url_params', 'url', 'sort_order',
            'is_active', 'min_role_level', 'requires_authentication', 
            'hide_for_authenticated', 'show_only_if_has_permission', 
            'level', 'has_children', 'children', 'permissions', 
            'is_visible', 'created_at', 'updated_at'
        ]
        read_only_fields = ['level', 'url', 'children', 'has_children', 'is_visible', 'created_at', 'updated_at']
    
    def get_url(self, obj):
        """Get the resolved URL for the menu item"""
        try:
            return obj.get_url()
        except Exception:
            return '#'
    
    def get_is_visible(self, obj):
        """Check if the menu item is visible to the current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.is_visible_to_user(request.user)
        return False
    
    def get_has_children(self, obj):
        """Check if the menu item has children"""
        return obj.children.filter(is_active=True).exists()
    
    def get_children(self, obj):
        """Get child menu items visible to the current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            children = obj.get_children_for_user(request.user)
            return MenuItemSerializer(
                children, 
                many=True, 
                context=self.context
            ).data
        return []


class MenuGroupSerializer(serializers.ModelSerializer):
    """Serializer for menu groups with nested items"""
    
    items = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuGroup
        fields = [
            'id', 'name', 'slug', 'description', 'group_type',
            'is_active', 'sort_order', 'min_role_level',
            'items', 'item_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['items', 'item_count', 'created_at', 'updated_at']
    
    def get_items(self, obj):
        """Get menu items visible to the current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            items = obj.get_items_for_user(request.user).filter(parent=None)
            return MenuItemSerializer(
                items, 
                many=True, 
                context=self.context
            ).data
        return []
    
    def get_item_count(self, obj):
        """Get total count of items in this group"""
        return obj.items.filter(is_active=True).count()


class NavigationTreeSerializer(serializers.Serializer):
    """Serializer for complete navigation tree"""
    
    menu_groups = MenuGroupSerializer(many=True, read_only=True)
    user_role_level = serializers.IntegerField(read_only=True)
    user_permissions = serializers.ListField(child=serializers.CharField(), read_only=True)
    
    class Meta:
        fields = ['menu_groups', 'user_role_level', 'user_permissions']


class MenuClickTrackingSerializer(serializers.ModelSerializer):
    """Serializer for menu click tracking"""
    
    menu_item_title = serializers.CharField(source='menu_item.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = MenuClickTracking
        fields = [
            'id', 'menu_item', 'menu_item_title', 'user', 'user_email',
            'clicked_at', 'ip_address', 'user_agent', 'api_endpoint', 'session_key'
        ]
        read_only_fields = ['clicked_at']


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating menu items"""
    
    class Meta:
        model = MenuItem
        fields = [
            'menu_group', 'parent', 'title', 'description', 'icon',
            'target_type', 'url_name', 'url_path', 'url_params',
            'is_active', 'sort_order', 'min_role_level', 
            'requires_authentication', 'hide_for_authenticated', 
            'show_only_if_has_permission'
        ]
    
    def validate(self, attrs):
        """Validate menu item data"""
        target_type = attrs.get('target_type')
        url_name = attrs.get('url_name')
        url_path = attrs.get('url_path')
        
        # Validate URL configuration based on target type
        if target_type == MenuItem.TargetType.INTERNAL:
            if not url_name and not url_path:
                raise serializers.ValidationError(
                    "Internal links must have either url_name or url_path"
                )
        elif target_type == MenuItem.TargetType.EXTERNAL:
            if not url_path:
                raise serializers.ValidationError(
                    "External links must have url_path"
                )
        elif target_type == MenuItem.TargetType.API_ENDPOINT:
            if not url_path:
                raise serializers.ValidationError(
                    "API endpoints must have url_path"
                )
        
        # Validate parent relationship
        parent = attrs.get('parent')
        menu_group = attrs.get('menu_group')
        
        if parent and parent.menu_group != menu_group:
            raise serializers.ValidationError(
                "Parent menu item must be in the same menu group"
            )
        
        return attrs


class MenuItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating menu items"""
    
    class Meta:
        model = MenuItem
        fields = [
            'title', 'description', 'icon', 'target_type',
            'url_name', 'url_path', 'url_params', 'is_active',
            'sort_order', 'min_role_level', 'requires_authentication',
            'hide_for_authenticated', 'show_only_if_has_permission'
        ]
    
    def validate(self, attrs):
        """Validate menu item update data"""
        # Handle case where self.instance might be None (e.g., during creation)
        if self.instance:
            target_type = attrs.get('target_type', self.instance.target_type)
            url_name = attrs.get('url_name', self.instance.url_name)
            url_path = attrs.get('url_path', self.instance.url_path)
        else:
            target_type = attrs.get('target_type')
            url_name = attrs.get('url_name')
            url_path = attrs.get('url_path')
        
        # Validate URL configuration
        if target_type == MenuItem.TargetType.INTERNAL:
            if not url_name and not url_path:
                raise serializers.ValidationError(
                    "Internal links must have either url_name or url_path"
                )
        elif target_type == MenuItem.TargetType.EXTERNAL:
            if not url_path:
                raise serializers.ValidationError(
                    "External links must have url_path"
                )
        elif target_type == MenuItem.TargetType.API_ENDPOINT:
            if not url_path:
                raise serializers.ValidationError(
                    "API endpoints must have url_path"
                )
        
        return attrs


class MenuAnalyticsSerializer(serializers.Serializer):
    """Serializer for menu analytics data"""
    
    menu_item_id = serializers.IntegerField()
    menu_item_title = serializers.CharField()
    click_count = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    last_clicked = serializers.DateTimeField()
    
    class Meta:
        fields = [
            'menu_item_id', 'menu_item_title', 'click_count',
            'unique_users', 'last_clicked'
        ]