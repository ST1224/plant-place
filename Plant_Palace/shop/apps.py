from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'Plant Palace Shop'

    def ready(self):
        """Import signal handlers when the app is ready."""
        import shop.signals  # noqa: F401
