import json
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import TestSession
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewsetTestSession(TestApi):
    fixtures = ['snapshotServer.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_testsession = ContentType.objects.get_for_model(TestSession)

    def _create_testsession(self, expected_status):
        response = self.client.post('/snapshot/api/session/', data={'sessionId': '12345', 'name': 'bla', 'version': 1, 'browser': 'BROWSER:chrome', 'environment': 'DEV', 'date': '2017-05-05T11:16:09.184106+01:00'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status < 300:
            self.assertEqual(1, len(TestSession.objects.filter(name='bla')))

    def test_testsession_create(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testsession', content_type=self.content_type_testsession)))
        self._create_testsession(201)

    def test_testsession_other_verbs_forbidden(self):
        """
        Check we cann only post sessions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testsession', content_type=self.content_type_testsession)
                                                                                      | Q(codename='change_testsession', content_type=self.content_type_testsession)
                                                                                      | Q(codename='delete_testsession', content_type=self.content_type_testsession)))
        response = self.client.get('/snapshot/api/session/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.patch('/snapshot/api/session/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/session/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/session/1/')
        self.assertEqual(405, response.status_code)

    def test_testsession_create_no_api_security(self):
        """
        Check it's possible to add a testsession when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_testsession(201)

    def test_testsession_create_forbidden(self):
        """
        Check it's NOT possible to add a testsession without 'add_testsession' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testsession', content_type=self.content_type_testsession)))
        self._create_testsession(403)

    def test_testsession_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_testsession permission
        - has NOT app1 permission

        User can add test session
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testsession', content_type=self.content_type_testsession)))
            self._create_testsession(201)

    def test_testsession_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_testsession permission
        - has app1 permission

        User can add test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_testsession(201)

    def test_testsession_create_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_testsession permission
        - has app1 permission

        User can NOT add test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._create_testsession(403)

    def test_testsession_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_testsession permission
        - has NOT app1 permission

        User can NOT add test session
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testsession')))
            self._create_testsession(403)


    def test_testsession_create_already_created(self):
        """
        Check it's possible to add a testsession with 'add_testsession' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_testsession(201)
            self._create_testsession(201)