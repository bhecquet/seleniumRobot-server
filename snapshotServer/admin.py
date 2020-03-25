from django.contrib import admin
from snapshotServer.models import TestSession, Snapshot
from django.contrib.admin.utils import get_deleted_objects

# Register your models here.

class TestSessionAdmin(admin.ModelAdmin): 
    list_display = ('sessionId', 'name', 'date', 'environment', 'ttl')
    list_filter = ('version__application',)
    search_fields = ['name']
    actions = ['delete_selected']
    
    def get_deleted_objects(self, test_sessions, request):
        
        deletable_objects, model_count, perms_needed, protected =  get_deleted_objects(test_sessions, request, self.admin_site)
        
        # Search all snapshots related to test sessions to delete and check if they are reference for others
        snapshots_to_delete = Snapshot.objects.filter(stepResult__testCase__session__in=test_sessions)
        snapshots_reference_for_other = Snapshot.objects.filter(refSnapshot__in=snapshots_to_delete)
        if snapshots_reference_for_other:
            deletable_objects.append('__delete_reference_snapshots__')
        
        return deletable_objects, model_count, perms_needed, protected

admin.site.register(TestSession, TestSessionAdmin)
