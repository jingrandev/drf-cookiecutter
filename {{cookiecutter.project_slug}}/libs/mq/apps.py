from django.apps import AppConfig


class MQConfig(AppConfig):
    name = "libs.mq"

    def ready(self):
        from libs.logging.celery_signals import connect_celery_logging_signals

        connect_celery_logging_signals()
