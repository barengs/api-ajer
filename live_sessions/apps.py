from django.apps import AppConfig


class LiveSessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'live_sessions'
    verbose_name = 'Live Sessions'
    
    def ready(self):
        # Import signals here to ensure they are registered
        pass