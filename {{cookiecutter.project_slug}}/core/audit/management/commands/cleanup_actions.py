from django.core.management.base import BaseCommand

from core.audit.services.handler import ActionHandler


class Command(BaseCommand):
    help = "Remove audit actions older than ACTION_RETENTION_DAYS"

    def handle(self, *args, **options):
        count = ActionHandler.cleanup()
        self.stdout.write(self.style.SUCCESS(f"Cleaned up {count} old actions"))
