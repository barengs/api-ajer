from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from .models import UserCourseInteraction, RecommendationSettings
from .services import recommendation_service
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserCourseInteraction)
def update_recommendations_on_interaction(sender, instance, created, **kwargs):
    """
    Update recommendations when a user interaction is created or updated
    """
    try:
        # Check if auto-refresh is enabled
        settings_obj = RecommendationSettings.get_settings()
        if not settings_obj.auto_refresh_enabled:
            return
            
        # Check if enough time has passed since last refresh
        last_refresh = getattr(instance.user, '_last_recommendation_refresh', None)
        if last_refresh:
            time_since_refresh = timezone.now() - last_refresh
            if time_since_refresh.total_seconds() < (settings_obj.refresh_interval_hours * 3600):
                return
        
        # Update user profile
        recommendation_service.generate_user_profile(instance.user)
        
        # Mark the last refresh time
        instance.user._last_recommendation_refresh = timezone.now()
        
        logger.info(f"Recommendations updated for user {instance.user.id} after interaction")
    except Exception as e:
        logger.error(f"Error updating recommendations on interaction: {e}")