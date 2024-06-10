import logging

from django.core.management.base import BaseCommand

from snapshotServer.management.commands import scheduler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean test sessions"

    def handle(self, *args, **options):
        
        logger.info("start cleaning")
        scheduler.daily_clean()
        logger.info("stopped cleaning")
    