from django.apps import AppConfig


class PlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.platform"
    verbose_name = "Platform Data"
    
    def ready(self):
        """Import signals when Django starts"""
        import apps.platform.signals  # noqa
