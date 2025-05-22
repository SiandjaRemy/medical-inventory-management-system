from django.apps import AppConfig


class WarehouseAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "warehouse_app"


    def ready(self):
        import warehouse_app.signals
        