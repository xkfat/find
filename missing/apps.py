from django.apps import AppConfig


class MissingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'missing'
