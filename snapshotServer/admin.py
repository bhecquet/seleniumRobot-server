from django.contrib import admin
from snapshotServer.models import TestSession, Snapshot, StepReference
from django.contrib.admin.utils import get_deleted_objects
from django.contrib.admin.filters import SimpleListFilter

# Register your models here.

class TestSessionAdmin(admin.ModelAdmin): 
    list_display = ('sessionId', 'name', 'date', 'environment', 'ttl')
    list_filter = ('version__application',)
    search_fields = ['name']
    actions = ['delete_selected']
    
    def get_deleted_objects(self, test_sessions, request):
        """
        Method getting the list of objects related to test sessions that will be deleted
        If we find related snapshots that are reference for other snapshot, add an item in object list. This item (__delete_reference_snapshots__) will be
        interpreted by custom admin templates to display a warning
        """
        
        deletable_objects, model_count, perms_needed, protected =  get_deleted_objects(test_sessions, request, self.admin_site)
        
        # Search all snapshots related to test sessions to delete and check if they are reference for others
        snapshots_to_delete = Snapshot.objects.filter(stepResult__testCase__session__in=test_sessions)
        snapshots_reference_for_other = Snapshot.objects.filter(refSnapshot__in=snapshots_to_delete)
        if snapshots_reference_for_other:
            deletable_objects.append('__delete_reference_snapshots__')
        
        return deletable_objects, model_count, perms_needed, protected
    
class TestCaseFilter(SimpleListFilter):
    """
    Depending on selected application, will show only related test cases
    """
    title = 'Test Case'
    parameter_name = 'test_case_id'

    def lookups(self, request, model_admin):
        if 'version__application__id__exact' in request.GET:
            app_id = request.GET['version__application__id__exact']
            test_cases = set([sr.testCase for sr in model_admin.model.objects.filter(version__application=app_id)])
        else:
            test_cases = set([sr.testCase for sr in model_admin.model.objects.all()])
        return [(tc.id, str(tc)) for tc in test_cases if tc is not None]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(stepResult__testCase__testCase__id__exact=self.value())
            
        else:
            return StepReference.objects.none()
    
class StepReferenceAdmin(admin.ModelAdmin):
    list_display = ('step_name', 'image_tag')
    list_filter = ('version__application', TestCaseFilter,)

admin.site.register(TestSession, TestSessionAdmin)
admin.site.register(StepReference, StepReferenceAdmin)
