import json
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import TestStep
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewsetTestStep(TestApi):
    fixtures = ['snapshotServer.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_teststep = ContentType.objects.get_for_model(TestStep)

    def _create_teststep(self, expected_status):
        response = self.client.post('/snapshot/api/teststep/', data={'name': 'bla'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status < 300:
            self.assertEqual(1, len(TestStep.objects.filter(name='bla')))

    def test_teststep_create(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_teststep', content_type=self.content_type_teststep)))
        self._create_teststep(201)

    def test_teststep_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_teststep', content_type=self.content_type_teststep)
                                                                                      | Q(codename='change_teststep', content_type=self.content_type_teststep)
                                                                                      | Q(codename='delete_teststep', content_type=self.content_type_teststep)))
        response = self.client.get('/snapshot/api/teststep/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.patch('/snapshot/api/teststep/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/teststep/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/teststep/1/')
        self.assertEqual(405, response.status_code)

    def test_teststep_create_no_api_security(self):
        """
        Check it's possible to add a teststep when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_teststep(201)

    def test_teststep_create_forbidden(self):
        """
        Check it's NOT possible to add a teststep without 'add_teststep' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_teststep', content_type=self.content_type_teststep)))
        self._create_teststep(403)

    def test_teststep_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_teststep permission
        - has NOT app1 permission

        User can add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_teststep', content_type=self.content_type_teststep)))
            self._create_teststep(201)

    def test_teststep_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_teststep permission
        - has app1 permission

        User can add test info on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_teststep(201)

    def test_teststep_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_teststep permission
        - has NOT app1 permission

        User can NOT add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_teststep')))
            self._create_teststep(403)


    def test_teststep_create_already_created(self):
        """
        Check it's possible to create the same TestStep twice
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_teststep(201)
            response = self.client.post('/snapshot/api/teststep/', data={'testCase': 1, 'name': 'bla'})
            self.assertEqual(201, response.status_code)
            self.assertEqual(1, len(TestStep.objects.filter(name='bla')))