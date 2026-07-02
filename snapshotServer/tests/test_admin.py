
from django.test.testcases import TestCase
from snapshotServer.admin import StepReferenceAdmin, TestCaseFilter, TestSessionAdmin, TestCaseFilterForSession
from snapshotServer.models import StepReference, TestSession
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User, Group
from django.db.models import Q

from django.test.client import Client

from variableServer.models import Application, TestEnvironment


class Messages:
    def __init__(self):
        self.content = []
    def add(self, level, message, extraargs):
        self.content.append(message)

class MockRequest:
    def __init__(self, user=None):
        self.user = user
        self.method = 'GET'
        self.GET = {}
        self.META = {}
        self._messages = Messages()



    
class TestAdmin(TestCase):
    
    fixtures = ['snapshotServer.yaml']

    def setUp(self):
        # add permissions for application and environment
        Application.objects.get(pk=1).save()
        TestEnvironment.objects.get(pk=1).save()

    def _create_and_authenticate_user_with_permissions(self, permissions    ):
        """
        @param permissions: example: Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable'), content_type=ct)
        """

        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        client = Client()
        client.login(username='user', password='pass')

        variable_users_group, created = Group.objects.get_or_create(name='Variable Users')

        variable_users_group.permissions.add(*permissions)
        variable_users_group.user_set.add(user)

        user.is_staff = True
        user.save()

        return user, client


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

    def test_testsession_get_queryset_with_application_permission(self):
        """
        Check that user only see test session he has permissions for
        """
        session_admin = TestSessionAdmin(model=TestSession, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
        request = MockRequest(user)
        queryset = session_admin.get_queryset(request)
        self.assertEqual(sorted([ts.id for ts in TestSession.objects.filter(version__application__name='myapp')]), sorted([ts.id for ts in queryset]))

    def test_testsession_get_queryset_with_environment_permission(self):
        """
        Check that user only see test session he has permissions for
        """
        session_admin = TestSessionAdmin(model=TestSession, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_environment_DEV')))
        request = MockRequest(user)
        queryset = session_admin.get_queryset(request)
        self.assertEqual(sorted([ts.id for ts in TestSession.objects.filter(environment__name='DEV')]), sorted([ts.id for ts in queryset]))

    def test_testsession_get_queryset_with_application_no_permission(self):
        """
        Check that no test session can be found when no permission on application is present
        """
        session_admin = TestSessionAdmin(model=TestSession, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.none())
        request = MockRequest(user)
        queryset = session_admin.get_queryset(request)
        self.assertEqual(0, len(queryset))

    def test_lookup_without_application(self):
        """
        Check that all test case names recorded in a session are displayed
        """
        session_admin = TestSessionAdmin(model=TestSession, admin_site=AdminSite())

        request = MockRequest()

        test_case_filter = TestCaseFilterForSession(request, {}, TestSession, session_admin)
        filtered_test_cases = test_case_filter.lookups(request=request, model_admin=session_admin)

        # all distinct test case names, whatever the application
        self.assertEqual(sorted(filtered_test_cases),
                         sorted([(1, 'test1'), (2, 'test2'), (3, 'test3'),
                                 (4, 'test login'), (5, 'test1app2')]))

    def test_lookup_with_application(self):
        """
        Check only the test cases linked to the selected application are displayed
        """
        session_admin = TestSessionAdmin(model=TestSession, admin_site=AdminSite())

        request = MockRequest()
        request.GET = {'version__application__id__exact': 1}

        test_case_filter = TestCaseFilterForSession(request, {}, TestSession, session_admin)
        filtered_test_cases = test_case_filter.lookups(request=request, model_admin=session_admin)

        # 'test1app2' belongs to application 2 (version 3), so it is excluded
        self.assertEqual(sorted(filtered_test_cases),
                         sorted([(1, 'test1'), (2, 'test2'), (3, 'test3'),
                                 (4, 'test login')]))

    def test_queryset_without_value(self):
        """
        Check that without filtering value, all sessions are returned
        """
        session_admin = TestSessionAdmin(model=TestSession, admin_site=AdminSite())

        request = MockRequest()

        test_case_filter = TestCaseFilterForSession(request, {}, TestSession, session_admin)
        queryset = test_case_filter.queryset(request=request, queryset=TestSession.objects.all())

        # no filtering, all sessions returned
        self.assertEqual(len(queryset), len(TestSession.objects.all()))

    def test_queryset_with_value(self):
        """
        Check that filtering by a test case name only returns sessions containing it
        """
        session_admin = TestSessionAdmin(model=TestSession, admin_site=AdminSite())

        request = MockRequest()

        test_case_filter = TestCaseFilterForSession(request, {'test_case_id': '2'}, TestSession, session_admin)
        queryset = test_case_filter.queryset(request=request, queryset=TestSession.objects.all())

        self.assertEqual(len(queryset), len(TestSession.objects.filter(testcaseinsession__testCase__name='test2')))