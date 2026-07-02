from django.contrib import admin, messages

from snapshotServer.models import TestSession, Snapshot, StepReference, ExcludeZone
from django.contrib.admin.utils import get_deleted_objects
from django.contrib.admin.filters import SimpleListFilter

from variableServer.admin_site.application_admin import ApplicationFromVersionFilter
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin
from variableServer.admin_site.environment_admin import EnvironmentFilter


# Register your models here.

class TestCaseFilterForSession(SimpleListFilter):
    """
    Depending on selected application, will show only related test cases
    """
    title = 'Test Case'
    parameter_name = 'test_case_id'

    def lookups(self, request, model_admin):
        if 'version__application__id__exact' in request.GET:
            app_id = request.GET['version__application__id__exact']
            test_cases = {test_case.testCase for session in model_admin.model.objects.filter(version__application=app_id) for test_case in session.testcaseinsession_set.all()}
        else:
            test_cases = {test_case.testCase for session in model_admin.model.objects.all() for test_case in session.testcaseinsession_set.all()}

        return [(tc.id, tc.name) for tc in test_cases if tc is not None]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(testcaseinsession__testCase__id=self.value())

        else:
            return queryset


class TestSessionAdmin(BaseServerModelAdmin):
    list_display = ('pk', 'link', 'name', 'version__application', 'date', 'environment', 'browser', 'allTests', 'ttl')
    list_filter = (ApplicationFromVersionFilter, EnvironmentFilter, 'browser', TestCaseFilterForSession)
    search_fields = ['name', 'testcaseinsession_set__testCase__name']
    actions = ['delete_selected']

    application_field_path = 'version__application'

    def get_queryset(self, request):
        """
        Filter the returned variables with the application user is allowed to see
        """
        return super().get_queryset(request, '')


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

        if self.parameter_name not in request.GET:
            model_admin.message_user(request, "Select at least a test case", messages.WARNING)

        if 'version__application__id__exact' in request.GET:
            app_id = request.GET['version__application__id__exact']
            test_cases = {sr.testCase for sr in model_admin.model.objects.filter(version__application=app_id)}
        else:
            test_cases = {sr.testCase for sr in model_admin.model.objects.all()}

        return [(tc.id, tc.name) for tc in test_cases if tc is not None]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(testCase__id=self.value())
            
        else:

            return StepReference.objects.none()
    
class StepReferenceAdmin(BaseServerModelAdmin):
    list_display = ('step_name', 'image_tag')
    list_filter = (ApplicationFromVersionFilter, TestCaseFilter,)
    application_field_path = 'version__application'

    def get_queryset(self, request):
        """
        Filter the returned variables with the application user is allowed to see
        """
        return super().get_queryset(request, 'snapshotServer.view_stepreference')


admin.site.register(TestSession, TestSessionAdmin)
admin.site.register(StepReference, StepReferenceAdmin)
