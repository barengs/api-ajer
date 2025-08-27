from django.apps import AppConfig


class GamificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore[assignment]
    name = 'gamification'
    verbose_name = 'Gamification System'
    
    def ready(self):
        # Import signals when the app is ready
        try:
            import gamification.signals  # noqa: F401
        except ImportError:
            pass