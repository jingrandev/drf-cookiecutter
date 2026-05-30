from datetime import datetime

from django.db.utils import OperationalError
from django.db.utils import ProgrammingError
from django.utils import timezone
from django_celery_beat.models import PeriodicTask


def fetch_periodic_task_last_run(task_name: str) -> datetime | None:
    try:
        periodic_task = (
            PeriodicTask.objects.filter(task=task_name, last_run_at__isnull=False)
            .order_by("-last_run_at")
            .only("last_run_at")
            .first()
        )
    except (ProgrammingError, OperationalError):
        return None

    last_run = getattr(periodic_task, "last_run_at", None)
    if last_run is None:
        return None

    if timezone.is_naive(last_run):
        last_run = timezone.make_aware(
            last_run,
            timezone.get_default_timezone(),
        )

    return last_run
