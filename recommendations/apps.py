from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommendations'
    verbose_name = 'AI Recommendations'

    def ready(self):
        # Import signals when the app is ready
        try:
            import recommendations.signals  # noqa
        except ImportError:
            pass