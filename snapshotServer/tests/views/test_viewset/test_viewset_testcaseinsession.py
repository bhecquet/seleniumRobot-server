
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import TestCaseInSession
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewsetTestCaseInSession(TestApi):
    fixtures = ['snapshotServer.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_testcaseinsession = ContentType.objects.get_for_model(TestCaseInSession)

    def _create_testcaseinsession(self, expected_status):
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'name': 'bla', 'testCase': 1, 'session': 1, 'status': 'SUCCESS', 'testSteps': [2, 3]})
        self.assertEqual(expected_status, response.status_code)
        if expected_status < 299:
            self.assertEqual(1, len(TestCaseInSession.objects.filter(name='bla')))

    def test_testcaseinsession_create_with_model_permission(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcaseinsession', content_type=self.content_type_testcaseinsession)))
        self._create_testcaseinsession(201)

    def test_testcaseinsession_other_verbs_forbidden(self):
        """
        Check we cann only post sessions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcaseinsession', content_type=self.content_type_testcaseinsession)
                                                                                      | Q(codename='change_testcaseinsession', content_type=self.content_type_testcaseinsession)
                                                                                      | Q(codename='delete_testcaseinsession', content_type=self.content_type_testcaseinsession)))
        response = self.client.put('/snapshot/api/testcaseinsession/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/testcaseinsession/1/')
        self.assertEqual(405, response.status_code)

    def test_testcaseinsession_create_no_api_security(self):
        """
        Check it's possible to add a testcaseinsession when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_testcaseinsession(201)

    def test_testcaseinsession_create_forbidden(self):
        """
        Check it's NOT possible to add a testcaseinsession without 'add_testcaseinsession' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcaseinsession', content_type=self.content_type_testcaseinsession)))
        self._create_testcaseinsession(403)

    def test_testcaseinsession_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_testcaseinsession permission
        - has NOT app1 permission

        User can add test session
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcaseinsession', content_type=self.content_type_testcaseinsession)))
            self._create_testcaseinsession(201)

    def test_testcaseinsession_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_testcaseinsession permission
        - has app1 permission

        User can add test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_testcaseinsession(201)

    def test_testcaseinsession_create_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_testcaseinsession permission
        - has app1 permission

        User can NOT add test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._create_testcaseinsession(403)

    def test_testcaseinsession_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_testcaseinsession permission
        - has NOT app1 permission

        User can NOT add test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testcaseinsession')))
            self._create_testcaseinsession(403)


    def test_testcaseinsession_create_already_created(self):
        """
        Check if a TestCaseInSession already exist, it's possible to recreate an other with same parameters
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_testcaseinsession(201)
            self._create_testcaseinsession(201)

            # only 1 item is created as serializer perform step update
            self.assertEqual(1, len(TestCaseInSession.objects.filter(name='bla')))

    def _update_testcaseinsession(self, expected_status):
        response = self.client.patch(f'/snapshot/api/testcaseinsession/1/', data={'name': 'bla2'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status < 300:
            self.assertEqual('bla2', TestCaseInSession.objects.get(pk=1).name)

    def test_testcaseinsession_update_with_model_permission(self):
        """
        Test it's possible to update session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testcaseinsession', content_type=self.content_type_testcaseinsession)))
        self._update_testcaseinsession(200)

    def test_testcaseinsession_update_non_existent_object(self):
        """
        Test it's possible to update session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testcaseinsession', content_type=self.content_type_testcaseinsession)))
        response = self.client.patch(f'/snapshot/api/testcaseinsession/12345/', data={'name': 'bla2'})
        self.assertEqual(404, response.status_code)

    def test_testcaseinsession_update_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT change_testcaseinsession permission
        - has app1 permission

        User can update test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._update_testcaseinsession(200)

    def test_testcaseinsession_update_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT change_testcaseinsession permission
        - has app1 permission

        User can NOT update test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._update_testcaseinsession(403)

    def _retrieve_testcaseinsession(self, expected_status):
        response = self.client.get('/snapshot/api/testcaseinsession/1/')
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual('foo', response.data['name'])

    def test_testcaseinsession_retrieve_with_model_permission(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcaseinsession', content_type=self.content_type_testcaseinsession)))
        self._retrieve_testcaseinsession(200)

    def test_testcaseinsession_retrieve_non_existent(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcaseinsession', content_type=self.content_type_testcaseinsession)))
        response = self.client.get('/snapshot/api/testcaseinsession/12345/')
        self.assertEqual(404, response.status_code)

    def test_testcaseinsession_retrieve_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT change_testcaseinsession permission
        - has app1 permission

        User can update test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._retrieve_testcaseinsession(200)

    def test_testcaseinsession_retrieve_with_application_restriction_and_app1_permission_non_existent(self):
        """
        User
        - has NOT change_testcaseinsession permission
        - has app2 permission

        User can update test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            response = self.client.get('/snapshot/api/testcaseinsession/12345/')
            self.assertEqual(403, response.status_code)

    def test_testcaseinsession_retrieve_with_application_restriction_and_app2_permission(self):
        """
        User
        - has NOT change_testcaseinsession permission
        - has app2 permission

        User can NOT update test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._retrieve_testcaseinsession(403)
