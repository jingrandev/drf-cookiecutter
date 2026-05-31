from celery.signals import before_task_publish, task_postrun, task_prerun
from django_guid import get_guid

from libs.logging.handlers import clear_correlation_id, get_correlation_id, set_correlation_id

CORRELATION_ID_HEADER = "correlation_id"


def on_before_publish(sender=None, headers=None, body=None, **kwargs):
    guid = get_guid()
    if not guid:
        guid = get_correlation_id()
    if guid and guid != "-" and headers is not None:
        headers[CORRELATION_ID_HEADER] = guid


def on_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, headers=None, **extra):
    request = getattr(task, "request", None)
    if request:
        cid = getattr(request, CORRELATION_ID_HEADER, None) or request.headers.get(
            CORRELATION_ID_HEADER
        )
    else:
        cid = None
    set_correlation_id(str(cid or task_id))


def on_task_postrun(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    clear_correlation_id()


def connect_celery_logging_signals():
    before_task_publish.connect(on_before_publish, weak=False)
    task_prerun.connect(on_task_prerun, weak=False)
    task_postrun.connect(on_task_postrun, weak=False)
