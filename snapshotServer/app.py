from django.apps import AppConfig
import os

class SnapshotServerConfig(AppConfig):
    name = 'snapshotServer'
    verbose_name = "Snapshot Server"
    
    def ready(self):
        from snapshotServer.management.commands import scheduler

        if os.environ.get('RUN_MAIN', False):
            scheduler.start()