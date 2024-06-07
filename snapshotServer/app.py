from django.apps import AppConfig
import os
from django.conf import settings

class SnapshotServerConfig(AppConfig):
    name = 'snapshotServer'
    verbose_name = "Snapshot Server"
    
    def ready(self):

        from snapshotServer.management.commands import scheduler

        # RUN_MAIN environment is set when running development server (called twice when test execute)
        if not os.environ.get('RUN_MAIN', False) and settings.EMBED_SCHEDULER == 'True':
            scheduler.start()