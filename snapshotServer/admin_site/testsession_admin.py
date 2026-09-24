from seleniumRobotServer.permissions.permissions import ContextPermissionChecker
from snapshotServer.models import Snapshot, Application
from django.contrib.admin.utils import get_deleted_objects
from django.contrib.admin.filters import SimpleListFilter

from commonsServer.admin_site.application_admin import ApplicationFromVersionFilter
from commonsServer.admin_site.base_model_admin import BaseServerModelAdmin
from commonsServer.admin_site.environment_admin import EnvironmentFilter, EnvironmentFilterForTestSession


# Register your models here.

class TestCaseFilterForSession(SimpleListFilter):
    """
    Depending on selected application, will show only related test cases
    """
    title = 'Test Case'
    parameter_name = 'test_case_id'

    def lookups(self, request, model_admin):
        if 'application' in request.GET:

            allowed_applications = ContextPermissionChecker.get_allowed_applications(request)
            app_id = request.GET['application']
            if Application.objects.get(id=app_id).name not in allowed_applications:
                test_cases = []
            else:
                test_cases = {test_case.testCase for session in model_admin.model.objects.filter(version__application=app_id) for test_case in session.testcaseinsession_set.all()}
        else:
            test_cases = [] # test cases can be seen only when application is selected

        return [(tc.id, tc.name) for tc in test_cases if tc is not None]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(testcaseinsession__testCase__id=self.value())

        else:
            return queryset


class TestSessionAdmin(BaseServerModelAdmin):
    list_display = ('pk', 'link', 'name', 'version__application', 'date', 'environment', 'browser', 'allTests', 'ttl')
    list_filter = (ApplicationFromVersionFilter, EnvironmentFilterForTestSession, 'browser', TestCaseFilterForSession)
    search_fields = ['name', 'testcaseinsession_set__testCase__name']
    actions = ['delete_selected']

    application_field_path = 'version__application'

    def get_queryset(self, request):
        """
        Filter the returned test sessions with the application user is allowed to see
        view_testenvironment won't allow to view all test sessions
        """
        return super().get_queryset(request, '').prefetch_related("testcaseinsession_set__testCase")


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

