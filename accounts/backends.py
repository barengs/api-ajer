from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class CaseInsensitiveAuth(ModelBackend):
    """
    Custom authentication backend that allows case-insensitive email authentication
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        
        if username is None or password is None:
            return None
            
        try:
            # Look for user with case-insensitive email match
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing difference
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Handle case where multiple users have the same email (shouldn't happen)
            return None
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
            
        return None