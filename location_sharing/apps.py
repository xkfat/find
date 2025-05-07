from django.apps import AppConfig


class LocationSharingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'location_sharing'

    def ready(self):
        import location_sharing.signals