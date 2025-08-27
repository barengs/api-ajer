from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import (
    MenuGroup, MenuItem, MenuItemPermission, 
    MenuClickTracking, MenuConfiguration
)


@admin.register(MenuGroup)
class MenuGroupAdmin(admin.ModelAdmin):
    """Admin interface for menu groups"""
    
    list_display = [
        'name', 'group_type', 'min_role_level', 'item_count', 
        'is_active', 'sort_order', 'created_at'
    ]
    list_filter = ['group_type', 'is_active', 'min_role_level', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'group_type')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Access Control', {
            'fields': ('min_role_level',),
            'description': 'Role levels: 10=Student, 30=Instructor, 70=Admin, 100=Super Admin'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            item_count=Count('items')
        )
    
    @admin.display(description='Items')
    def item_count(self, obj):
        count = getattr(obj, 'item_count', obj.items.count())
        if count > 0:
            url = reverse('admin:navigation_menuitem_changelist')
            return format_html(
                '<a href="{}?menu_group__id__exact={}">{} items</a>',
                url, obj.id, count
            )
        return '0 items'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class MenuItemPermissionInline(admin.TabularInline):
    """Inline for menu item permissions"""
    model = MenuItemPermission
    extra = 0
    fields = ['role', 'can_view', 'can_access']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Admin interface for menu items"""
    
    list_display = [
        'indented_title', 'menu_group', 'target_type', 'url_display',
        'min_role_level', 'is_active', 'sort_order', 'click_count'
    ]
    list_filter = [
        'menu_group', 'target_type', 'is_active', 'requires_authentication',
        'min_role_level', 'created_at'
    ]
    search_fields = ['title', 'description', 'url_name', 'url_path']
    ordering = ['menu_group', 'sort_order', 'title']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('menu_group', 'parent', 'title', 'description', 'icon')
        }),
        ('URL Configuration', {
            'fields': ('target_type', 'url_name', 'url_path', 'url_params'),
            'description': 'For internal links, use url_name. For external links, use url_path.'
        }),
        ('Display Settings', {
            'fields': (
                'is_active', 'sort_order', 'opens_in_new_window',
                'css_classes', 'badge_text', 'badge_color'
            )
        }),
        ('Access Control', {
            'fields': (
                'min_role_level', 'requires_authentication', 
                'hide_for_authenticated', 'show_only_if_has_permission'
            ),
            'description': 'Control who can see and access this menu item'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MenuItemPermissionInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'menu_group', 'parent', 'created_by'
        ).annotate(
            click_count=Count('click_tracking')
        )
    
    @admin.display(description='Menu Item')
    def indented_title(self, obj):
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * obj.level
        icon = f'<i class="{obj.icon}"></i> ' if obj.icon else ''
        
        status_color = 'green' if obj.is_active else 'red'
        status_indicator = f'<span style="color: {status_color};">●</span> '
        
        return format_html(
            '{}{}{}{} {}',
            mark_safe(indent),
            status_indicator,
            mark_safe(icon),
            obj.title,
            f'<small style="color: #666;">(Level {obj.min_role_level}+)</small>'
        )
    
    @admin.display(description='URL')
    def url_display(self, obj):
        try:
            url = obj.get_url()
            if url and url != '#':
                if obj.target_type == MenuItem.TargetType.EXTERNAL:
                    return format_html('<a href="{}" target="_blank">{}</a>', url, url[:50])
                else:
                    return format_html('<code>{}</code>', url[:50])
            return '-'
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e)[:30])
    
    @admin.display(description='Clicks')
    def click_count(self, obj):
        count = getattr(obj, 'click_count', obj.click_tracking.count())
        if count > 0:
            url = reverse('admin:navigation_menuclicktracking_changelist')
            return format_html(
                '<a href="{}?menu_item__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return '0'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MenuItemPermission)
class MenuItemPermissionAdmin(admin.ModelAdmin):
    """Admin interface for menu item permissions"""
    
    list_display = ['menu_item', 'role', 'can_view', 'can_access', 'created_at']
    list_filter = ['can_view', 'can_access', 'role', 'created_at']
    search_fields = ['menu_item__title', 'role__name']
    ordering = ['menu_item', 'role']
    
    fieldsets = (
        ('Permission Details', {
            'fields': ('menu_item', 'role', 'can_view', 'can_access')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at']


@admin.register(MenuClickTracking)
class MenuClickTrackingAdmin(admin.ModelAdmin):
    """Admin interface for menu click tracking"""
    
    list_display = [
        'menu_item', 'user_display', 'clicked_at', 
        'ip_address', 'referrer_display'
    ]
    list_filter = ['clicked_at', 'menu_item__menu_group']
    search_fields = [
        'menu_item__title', 'user__email', 'user__username', 
        'ip_address', 'referrer'
    ]
    ordering = ['-clicked_at']
    date_hierarchy = 'clicked_at'
    
    fieldsets = (
        ('Click Details', {
            'fields': ('menu_item', 'user', 'clicked_at')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'referrer', 'session_key'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['clicked_at']
    
    @admin.display(description='User')
    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:accounts_user_change', args=[obj.user.id]),
                obj.user.email
            )
        return f'Anonymous ({obj.ip_address})'
    
    @admin.display(description='Referrer')
    def referrer_display(self, obj):
        if obj.referrer:
            return format_html('<code>{}</code>', obj.referrer[:50])
        return '-'
    
    def has_add_permission(self, request):
        # Prevent manual creation of click tracking records
        return False


@admin.register(MenuConfiguration)
class MenuConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for menu configuration"""
    
    list_display = ['key', 'config_type', 'value_preview', 'is_active', 'updated_at']
    list_filter = ['config_type', 'is_active', 'created_at']
    search_fields = ['key', 'description', 'value']
    ordering = ['config_type', 'key']
    
    fieldsets = (
        ('Configuration Details', {
            'fields': ('key', 'config_type', 'description')
        }),
        ('Value', {
            'fields': ('value', 'is_active'),
            'description': 'Use JSON format for complex values'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @admin.display(description='Value')
    def value_preview(self, obj):
        preview = obj.value[:100]
        if len(obj.value) > 100:
            preview += '...'
        return format_html('<code>{}</code>', preview)


# Custom admin site configuration
admin.site.site_header = "Navigation Management"
admin.site.site_title = "Navigation Admin"
admin.site.index_title = "Welcome to Navigation Management"