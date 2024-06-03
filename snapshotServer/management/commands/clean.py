import logging

from django.core.management.base import BaseCommand

from snapshotServer.management.commands import scheduler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean test sessions"

    def handle(self, *args, **options):
        scheduler.daily_clean()
            
def start():
    Command().handle()