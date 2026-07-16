
from django.test.testcases import TestCase

from commonsServer.tests.test_parent import TestWebAndAdmin, MockRequest
from snapshotServer.models import StepReference
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User, Group
from django.db.models import Q

from django.test.client import Client

from snapshotServer.admin_site.stepreference_admin import StepReferenceAdmin, TestCaseFilter
from variableServer.models import Application, TestEnvironment

class TestStepReferenceAdmin(TestWebAndAdmin):
    
    fixtures = ['test_stepreference_admin.yaml']

    def setUp(self):
        super().setUp()

        # add permissions for application and environment
        Application.objects.get(pk=1).save()
        TestEnvironment.objects.get(pk=1).save()

    def test_stepreference_get_queryset_with_application_permission(self):
        """
        Check that user only see step references he has permissions for
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
        request = MockRequest(user)
        queryset = step_reference_admin.get_queryset(request)
        self.assertEqual(sorted([ts.id for ts in StepReference.objects.filter(version__application__name='myapp')]), sorted([ts.id for ts in queryset]))

    def test_stepreference_get_queryset_with_environment_permission(self):
        """
        Check that user only see test session he has permissions for
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_environment_DEV')))
        request = MockRequest(user)
        queryset = step_reference_admin.get_queryset(request)
        self.assertEqual(sorted([ts.id for ts in StepReference.objects.filter(environment__name='DEV')]), sorted([ts.id for ts in queryset]))

    def test_stepreference_get_queryset_with_application_no_permission(self):
        """
        Check that no step reference can be found when no permission on application is present
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.none())
        request = MockRequest(user)
        queryset = step_reference_admin.get_queryset(request)
        self.assertEqual(0, len(queryset))

    def test_test_case_filter_lookup_without_application(self):
        """
        Check that all test cases that are recorded in a step reference are displayed
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        
        test_case_filter = TestCaseFilter(request, {}, StepReference, step_reference_admin)
        filtered_test_cases = test_case_filter.lookups(request=request, model_admin=step_reference_admin)
        
        # only test cases that are included in a step reference will be displayed
        self.assertEqual(filtered_test_cases, [(1, 'test1'), (5, 'test1app2')])
        self.assertEqual(request._messages.content, ["Select at least a test case", "Select at least a test case"]) # present 2 times because filter init already calls 'lookup' method
        
    def test_test_case_filter_lookup_with_application(self):
        """
        Check only the versions of the selected application are displayed
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        request.GET = {'version__application__id__exact': 1}
        
        test_case_filter = TestCaseFilter(request, {}, StepReference, step_reference_admin)
        filtered_test_cases = test_case_filter.lookups(request=request, model_admin=step_reference_admin)
        
        # only test cases where a step reference exist for the application app1 are returned
        self.assertEqual(filtered_test_cases, [(1, 'test1')])
        self.assertEqual(request._messages.content, ["Select at least a test case", "Select at least a test case"]) # present 2 times because filter init already calls 'lookup' method


    def test_test_case_filter_lookup_with_application_and_testcase(self):
        """
        Check only the versions of the selected application are displayed
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())

        request = MockRequest()
        request.GET = {'version__application__id__exact': 1, 'test_case_id': [5]}

        test_case_filter = TestCaseFilter(request, {}, StepReference, step_reference_admin)
        filtered_test_cases = test_case_filter.lookups(request=request, model_admin=step_reference_admin)

        # only test cases where a step reference exist for the application app1 are returned
        self.assertEqual(filtered_test_cases, [(1, 'test1')])
        self.assertEqual(request._messages.content, [])


    def test_test_case_filter_queryset_without_value(self):
        """
        Check the case where no filtering is required, all variables are returned
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        
        test_case_filter = TestCaseFilter(request, {}, StepReference, step_reference_admin)
        queryset = test_case_filter.queryset(request=request, queryset=StepReference.objects.all())
        
        # no filtering, no step result returned to avoid loading many images
        self.assertEqual(len(queryset), len(StepReference.objects.none()))


    def test_test_case_filter_queryset_with_value(self):
        """
        Check the case where filtering is required with version '2'
        Only variables linked to this version should be returned
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        
        test_case_filter = TestCaseFilter(request, {'test_case_id': [5]}, StepReference, step_reference_admin)
        queryset = test_case_filter.queryset(request=request, queryset=StepReference.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(1, len(queryset))
        self.assertEqual(len(queryset), len(StepReference.objects.filter(testCase__id=5)))