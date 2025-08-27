from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import Optional, Dict, Any
import logging

from .models import MenuClickTracking

User = get_user_model()
logger = logging.getLogger(__name__)


def get_user_role_level(user) -> int:
    """
    Get user's role level from role management system
    
    Args:
        user: Django User instance
        
    Returns:
        int: Role level (10-100)
    """
    if not user or not user.is_authenticated:
        return 10  # Default student level
    
    try:
        from role_management.models import UserRoleAssignment
        
        # Get active role assignment
        assignment = UserRoleAssignment.objects.filter(
            user=user, 
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).select_related('role').first()
        
        if assignment and assignment.role:
            # Map role names to levels based on user preference (9-level hierarchy)
            role_levels = {
                'student': 10,
                'assistant': 20,
                'instructor': 30,
                'moderator': 40,
                'support': 50,
                'admin': 90,
            }
            return role_levels.get(assignment.role.name, 10)
            
    except ImportError:
        logger.warning("Role management module not available, falling back to Django permissions")
    except Exception as e:
        logger.error(f"Error getting user role level: {e}")
    
    # Fallback to Django's built-in permissions
    if user.is_superuser:
        return 100
    elif user.is_staff:
        return 70
    else:
        return 10


def get_user_permissions_list(user) -> list:
    """
    Get list of user permissions
    
    Args:
        user: Django User instance
        
    Returns:
        list: List of permission strings
    """
    if not user or not user.is_authenticated:
        return []
    
    try:
        return list(user.get_all_permissions())
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return []


def track_menu_click(menu_item, user=None, request=None) -> Optional[MenuClickTracking]:
    """
    Track a menu item click for analytics
    
    Args:
        menu_item: MenuItem instance
        user: User who clicked (optional for anonymous)
        request: HttpRequest instance
        
    Returns:
        MenuClickTracking: Created tracking record or None if failed
    """
    try:
        # Get IP address
        ip_address = get_client_ip(request) if request else '127.0.0.1'
        
        # Get user agent
        user_agent = ''
        if request and hasattr(request, 'META'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Truncate
        
        # Get referrer
        referrer = ''
        if request and hasattr(request, 'META'):
            referrer = request.META.get('HTTP_REFERER', '')[:200]  # Truncate
        
        # Get session key
        session_key = ''
        if request and hasattr(request, 'session'):
            session_key = request.session.session_key or ''
        
        # Create tracking record
        tracking = MenuClickTracking.objects.create(
            menu_item=menu_item,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            session_key=session_key
        )
        
        logger.info(f"Menu click tracked: {menu_item.title} by {user or 'anonymous'}")
        return tracking
        
    except Exception as e:
        logger.error(f"Error tracking menu click: {e}")
        return None


def get_client_ip(request) -> str:
    """
    Get client IP address from request
    
    Args:
        request: HttpRequest instance
        
    Returns:
        str: Client IP address
    """
    if not request:
        return '127.0.0.1'
    
    # Check for forwarded headers (load balancer, proxy)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    
    # Check for real IP header
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    
    # Fallback to remote address
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def build_menu_tree(menu_items, parent=None) -> list:
    """
    Build hierarchical menu tree from flat list of menu items
    
    Args:
        menu_items: QuerySet or list of MenuItem instances
        parent: Parent menu item (None for root items)
        
    Returns:
        list: Hierarchical menu structure
    """
    tree = []
    
    for item in menu_items:
        if item.parent == parent:
            # Get children
            children = build_menu_tree(menu_items, item)
            
            # Add children to item data
            item_data = {
                'id': item.id,
                'title': item.title,
                'url': item.get_url(),
                'icon': item.icon,
                'level': item.level,
                'children': children
            }
            
            tree.append(item_data)
    
    return tree


def filter_menu_by_role(menu_items, user) -> list:
    """
    Filter menu items based on user role and permissions
    
    Args:
        menu_items: List or QuerySet of MenuItem instances
        user: Django User instance
        
    Returns:
        list: Filtered menu items visible to user
    """
    visible_items = []
    
    for item in menu_items:
        if item.is_visible_to_user(user):
            visible_items.append(item)
    
    return visible_items


def get_menu_statistics() -> Dict[str, Any]:
    """
    Get overall menu statistics
    
    Returns:
        dict: Menu statistics
    """
    try:
        from .models import MenuGroup, MenuItem, MenuClickTracking
        from django.db.models import Count
        
        stats = {
            'total_groups': MenuGroup.objects.count(),
            'active_groups': MenuGroup.objects.filter(is_active=True).count(),
            'total_items': MenuItem.objects.count(),
            'active_items': MenuItem.objects.filter(is_active=True).count(),
            'total_clicks': MenuClickTracking.objects.count(),
            'clicks_today': MenuClickTracking.objects.filter(
                clicked_at__date=timezone.now().date()
            ).count(),
            'most_clicked_item': None
        }
        
        # Get most clicked item
        most_clicked = MenuClickTracking.objects.values(
            'menu_item__title'
        ).annotate(
            click_count=Count('id')
        ).order_by('-click_count').first()
        
        if most_clicked:
            stats['most_clicked_item'] = {
                'title': most_clicked['menu_item__title'],
                'clicks': most_clicked['click_count']
            }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting menu statistics: {e}")
        return {}


def validate_menu_structure(menu_group) -> Dict[str, Any]:
    """
    Validate menu structure for circular references and other issues
    
    Args:
        menu_group: MenuGroup instance
        
    Returns:
        dict: Validation results
    """
    issues = []
    warnings = []
    
    try:
        items = menu_group.items.all()
        
        # Check for circular references
        for item in items:
            if item.parent:
                # Trace parent chain
                visited = set()
                current = item.parent
                
                while current:
                    if current.id in visited:
                        issues.append(f"Circular reference detected for item '{item.title}'")
                        break
                    
                    visited.add(current.id)
                    current = current.parent
        
        # Check for orphaned items (parent not in same group)
        for item in items:
            if item.parent and item.parent.menu_group != item.menu_group:
                issues.append(f"Item '{item.title}' has parent from different group")
        
        # Check for items without URLs
        for item in items:
            if not item.url_name and not item.url_path:
                warnings.append(f"Item '{item.title}' has no URL configured")
        
        # Check role level consistency
        for item in items:
            if item.parent and item.min_role_level < item.parent.min_role_level:
                warnings.append(
                    f"Item '{item.title}' has lower role requirement than parent"
                )
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'total_items': len(items)
        }
        
    except Exception as e:
        logger.error(f"Error validating menu structure: {e}")
        return {
            'is_valid': False,
            'issues': [f"Validation error: {str(e)}"],
            'warnings': [],
            'total_items': 0
        }


def export_menu_structure(menu_group) -> Dict[str, Any]:
    """
    Export menu structure as JSON for backup or migration
    
    Args:
        menu_group: MenuGroup instance
        
    Returns:
        dict: Menu structure data
    """
    try:
        items = menu_group.items.all().order_by('sort_order')
        
        def serialize_item(item):
            return {
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'icon': item.icon,
                'target_type': item.target_type,
                'url_name': item.url_name,
                'url_path': item.url_path,
                'url_params': item.url_params,
                'sort_order': item.sort_order,
                'is_active': item.is_active,
                'min_role_level': item.min_role_level,
                'requires_authentication': item.requires_authentication,
                'parent_id': item.parent.id if item.parent else None,
                'children': [
                    serialize_item(child) for child in item.children.all()
                ]
            }
        
        # Get root items (no parent)
        root_items = items.filter(parent=None)
        
        return {
            'menu_group': {
                'name': menu_group.name,
                'slug': menu_group.slug,
                'description': menu_group.description,
                'group_type': menu_group.group_type,
                'min_role_level': menu_group.min_role_level
            },
            'items': [serialize_item(item) for item in root_items],
            'exported_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting menu structure: {e}")
        return {}


def clear_menu_cache():
    """
    Clear menu-related cache (if implemented)
    """
    try:
        from django.core.cache import cache
        
        # Clear navigation cache keys
        cache_keys = [
            'navigation_tree_*',
            'menu_groups_*',
            'menu_items_*'
        ]
        
        for key_pattern in cache_keys:
            cache.delete_many([key_pattern])
        
        logger.info("Menu cache cleared")
        
    except Exception as e:
        logger.error(f"Error clearing menu cache: {e}")