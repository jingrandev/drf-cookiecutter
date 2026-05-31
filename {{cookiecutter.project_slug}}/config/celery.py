import os

from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.local"),
)

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@setup_logging.connect
def configure_celery_logging(*args, **kwargs):
    from libs.logging.setup import setup_logging as setup_loguru_logging

    setup_loguru_logging()
