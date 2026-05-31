from django.core.management.base import BaseCommand

from core.command.services.handler import CommandHandler


class Command(BaseCommand):
    help = "Remove commands older than COMMAND_RETENTION_DAYS"

    def handle(self, *args, **options):
        count = CommandHandler.cleanup()
        self.stdout.write(self.style.SUCCESS(f"Cleaned up {count} old commands"))
