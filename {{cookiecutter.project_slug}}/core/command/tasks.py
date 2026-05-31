{%- if cookiecutter.use_celery == "yes" %}
from celery import shared_task

from core.command.services.handler import CommandHandler


@shared_task(name="core.command.tasks.cleanup_old_commands")
def cleanup_old_commands():
    count = CommandHandler.cleanup()
    return f"Cleaned up {count} old commands"
{%- endif %}
