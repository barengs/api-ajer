from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # type: ignore[assignment]
    name = 'accounts'
    verbose_name = 'Accounts'

    def ready(self):
        import accounts.signals  # noqa