from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore[assignment]
    name = 'analytics'
    verbose_name = 'Analytics'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import analytics.signals  # type: ignore
        except ImportError:
            pass