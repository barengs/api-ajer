from django.apps import AppConfig


class RoleManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore[assignment]
    name = 'role_management'
    verbose_name = 'Role Management'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import role_management.signals  # type: ignore
        except ImportError:
            pass