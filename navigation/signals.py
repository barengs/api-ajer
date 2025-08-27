from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

from .models import MenuGroup, MenuItem, MenuItemPermission
from .utils import clear_menu_cache

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=MenuGroup)
def menu_group_saved(sender, instance, created, **kwargs):
    """
    Handle menu group save events
    """
    try:
        # Clear navigation cache
        clear_menu_cache()
        
        if created:
            logger.info(f"New menu group created: {instance.name}")
        else:
            logger.info(f"Menu group updated: {instance.name}")
            
    except Exception as e:
        logger.error(f"Error in menu_group_saved signal: {e}")


@receiver(post_delete, sender=MenuGroup)
def menu_group_deleted(sender, instance, **kwargs):
    """
    Handle menu group deletion
    """
    try:
        # Clear navigation cache
        clear_menu_cache()
        
        logger.info(f"Menu group deleted: {instance.name}")
        
    except Exception as e:
        logger.error(f"Error in menu_group_deleted signal: {e}")


@receiver(post_save, sender=MenuItem)
def menu_item_saved(sender, instance, created, **kwargs):
    """
    Handle menu item save events
    """
    try:
        # Clear navigation cache
        clear_menu_cache()
        
        # Validate menu structure after save
        from .utils import validate_menu_structure
        validation = validate_menu_structure(instance.menu_group)
        
        if not validation['is_valid']:
            logger.warning(
                f"Menu structure validation issues for group {instance.menu_group.name}: "
                f"{validation['issues']}"
            )
        
        if created:
            logger.info(f"New menu item created: {instance.title}")
        else:
            logger.info(f"Menu item updated: {instance.title}")
            
    except Exception as e:
        logger.error(f"Error in menu_item_saved signal: {e}")


@receiver(post_delete, sender=MenuItem)
def menu_item_deleted(sender, instance, **kwargs):
    """
    Handle menu item deletion
    """
    try:
        # Clear navigation cache
        clear_menu_cache()
        
        # Update parent items that might reference this item
        children = MenuItem.objects.filter(parent=instance)
        if children.exists():
            # Move children to parent's parent or make them root items
            for child in children:
                child.parent = instance.parent
                child.save()
                logger.info(f"Moved child item {child.title} to new parent")
        
        logger.info(f"Menu item deleted: {instance.title}")
        
    except Exception as e:
        logger.error(f"Error in menu_item_deleted signal: {e}")


@receiver(post_save, sender=MenuItemPermission)
def menu_permission_saved(sender, instance, created, **kwargs):
    """
    Handle menu permission save events
    """
    try:
        # Clear navigation cache
        clear_menu_cache()
        
        if created:
            logger.info(
                f"New menu permission created: {instance.menu_item.title} "
                f"for role {instance.role.name}"
            )
        else:
            logger.info(
                f"Menu permission updated: {instance.menu_item.title} "
                f"for role {instance.role.name}"
            )
            
    except Exception as e:
        logger.error(f"Error in menu_permission_saved signal: {e}")


@receiver(post_delete, sender=MenuItemPermission)
def menu_permission_deleted(sender, instance, **kwargs):
    """
    Handle menu permission deletion
    """
    try:
        # Clear navigation cache
        clear_menu_cache()
        
        logger.info(
            f"Menu permission deleted: {instance.menu_item.title} "
            f"for role {instance.role.name}"
        )
        
    except Exception as e:
        logger.error(f"Error in menu_permission_deleted signal: {e}")


# Role management integration signals
try:
    from role_management.models import UserRoleAssignment
    
    @receiver(post_save, sender=UserRoleAssignment)
    def role_assignment_changed(sender, instance, created, **kwargs):
        """
        Handle role assignment changes to update user navigation
        """
        try:
            # Clear user-specific navigation cache
            user_cache_key = f"user_navigation_{instance.user.id}"
            cache.delete(user_cache_key)
            
            if created:
                logger.info(f"Role assigned to user {instance.user.email}: {instance.role.name}")
            else:
                logger.info(f"Role assignment updated for user {instance.user.email}")
                
        except Exception as e:
            logger.error(f"Error in role_assignment_changed signal: {e}")
    
    @receiver(post_delete, sender=UserRoleAssignment)
    def role_assignment_deleted(sender, instance, **kwargs):
        """
        Handle role assignment deletion
        """
        try:
            # Clear user-specific navigation cache
            user_cache_key = f"user_navigation_{instance.user.id}"
            cache.delete(user_cache_key)
            
            logger.info(f"Role unassigned from user {instance.user.email}: {instance.role.name}")
            
        except Exception as e:
            logger.error(f"Error in role_assignment_deleted signal: {e}")

except ImportError:
    logger.warning("Role management module not available for signal integration")


@receiver(post_save, sender=User)
def user_saved(sender, instance, created, **kwargs):
    """
    Handle user save events for navigation cache management
    """
    try:
        if not created:  # Only for updates
            # Clear user-specific navigation cache
            user_cache_key = f"user_navigation_{instance.id}"
            cache.delete(user_cache_key)
            
        # Check if user status changed (staff, superuser)
        if hasattr(instance, '_original_is_staff') and hasattr(instance, '_original_is_superuser'):
            # Access attributes with getattr to avoid type checking issues
            current_is_staff = getattr(instance, 'is_staff', False)  # type: ignore[attr-defined]
            current_is_superuser = getattr(instance, 'is_superuser', False)  # type: ignore[attr-defined]
            original_is_staff = getattr(instance, '_original_is_staff', False)
            original_is_superuser = getattr(instance, '_original_is_superuser', False)
            
            if (current_is_staff != original_is_staff or 
                current_is_superuser != original_is_superuser):
                # User permissions changed, clear navigation cache
                clear_menu_cache()
                
    except Exception as e:
        logger.error(f"Error in user_saved signal: {e}")


def setup_signal_tracking():
    """
    Setup additional signal tracking for User model
    """
    def pre_save_user(sender, instance, **kwargs):
        """Track original user values before save"""
        if instance.pk:
            try:
                original = User.objects.get(pk=instance.pk)
                instance._original_is_staff = getattr(original, 'is_staff', False)  # type: ignore[attr-defined]
                instance._original_is_superuser = getattr(original, 'is_superuser', False)  # type: ignore[attr-defined]
            except User.DoesNotExist:
                pass
    
    # Connect the pre_save signal
    from django.db.models.signals import pre_save
    pre_save.connect(pre_save_user, sender=User)


# Initialize signal tracking when module loads
setup_signal_tracking()