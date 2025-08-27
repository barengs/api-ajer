"""
Pipeline functions for social authentication
"""
from accounts.models import UserProfile


def save_profile(backend, user, response, *args, **kwargs):
    """
    Create a UserProfile for the user if it doesn't exist and update with Google data
    """
    if backend.name == 'google-oauth2':
        # Create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Update user data with Google information if it's a new user
        if 'name' in response and (not user.full_name or user.full_name == ''):
            user.full_name = response['name']
            # Also update username to be based on email if it's still the default
            if user.username == user.email.split('@')[0]:
                user.username = user.email.split('@')[0]
        
        # Update profile with Google data if available
        if 'link' in response:
            profile.website = response['link']
            
        profile.save()
        
        # Save user if any changes were made
        user.save()