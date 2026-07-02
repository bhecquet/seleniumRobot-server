from commonsServer.tests.test_parent import TestWebAndAdmin, MockRequest
from snapshotServer.models import TestSession
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User, Group
from django.db.models import Q


from snapshotServer.admin_site.testsession_admin import TestSessionAdmin, TestCaseFilterForSession
from variableServer.models import Application, TestEnvironment
    
class TestTestSessionAdmin(TestWebAndAdmin):
    
    fixtures = ['snapshotServer.yaml']

    def setUp(self):
        # add permissions for application and environment
        Application.objects.get(pk=1).save()
        TestEnvironment.objects.get(pk=1).save()

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