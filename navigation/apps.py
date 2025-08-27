from django.apps import AppConfig


class NavigationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'navigation'
    verbose_name = 'Navigation Management'
    
    def ready(self):
        """Initialize the navigation module when Django starts"""
        try:
            import navigation.signals  # noqa
        except ImportError:
            pass