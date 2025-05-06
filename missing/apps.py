from django.apps import AppConfig


class MissingConfig(AppConfig):
    name = 'missing'

    def ready(self):
        import missing.signals
