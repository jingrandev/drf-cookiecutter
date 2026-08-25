from datetime import timedelta

from auditlog.models import LogEntry
from celery import shared_task
from django.conf import settings
from django.utils import timezone


@shared_task(name="libs.mq.tasks.cleanup_auditlog")
def cleanup_auditlog():
    retention_days = getattr(settings, "AUDITLOG_RETENTION_DAYS", 90)
    cutoff = timezone.now() - timedelta(days=retention_days)
    count, _ = LogEntry.objects.filter(timestamp__lt=cutoff).delete()
    return f"Cleaned up {count} audit log entries"
