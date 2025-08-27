from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.apps import apps

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile = apps.get_model('accounts', 'UserProfile')
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=User)
def log_user_activity(sender, instance, created, **kwargs):
    """Log user activity when user is created or updated"""
    if created:
        UserActivity = apps.get_model('accounts', 'UserActivity')
        UserActivity.objects.create(
            user=instance,
            activity_type='registration',
            description=f'User {instance.username} registered with email {instance.email}'
        )