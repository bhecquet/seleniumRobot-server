from django.contrib import messages

from snapshotServer.models import StepReference
from django.contrib.admin.filters import SimpleListFilter

from commonsServer.admin_site.application_admin import ApplicationFromVersionFilter
from commonsServer.admin_site.base_model_admin import BaseServerModelAdmin


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


