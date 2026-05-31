{%- if cookiecutter.use_celery == "yes" %}
from celery import shared_task

from core.audit.services.handler import ActionHandler


@shared_task(name="core.audit.tasks.cleanup_old_actions")
def cleanup_old_actions():
    count = ActionHandler.cleanup()
    return f"Cleaned up {count} old actions"
{%- endif %}
