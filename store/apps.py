from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'
    verbose_name = 'EYTGaming Store'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import store.signals  # noqa
        except ImportError:
            pass
