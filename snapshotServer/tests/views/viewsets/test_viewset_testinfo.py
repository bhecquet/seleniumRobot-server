import json
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import TestInfo
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewsetTestInfo(TestApi):
    fixtures = ['snapshotServer.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_testinfo = ContentType.objects.get_for_model(TestInfo)

    def _create_testinfo(self, expected_status):
        response = self.client.post('/snapshot/api/testinfo/', data={'testCase': 1, 'name': 'bla'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status < 300:
            self.assertEqual(1, len(TestInfo.objects.filter(name='bla')))

    def test_testinfo_create(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testinfo', content_type=self.content_type_testinfo)))
        self._create_testinfo(201)

    def test_testinfo_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testinfo', content_type=self.content_type_testinfo)
                                                                                      | Q(codename='change_testinfo', content_type=self.content_type_testinfo)
                                                                                      | Q(codename='delete_testinfo', content_type=self.content_type_testinfo)))
        response = self.client.get('/snapshot/api/testinfo/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.patch('/snapshot/api/testinfo/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/testinfo/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/testinfo/1/')
        self.assertEqual(405, response.status_code)

    def test_testinfo_create_no_api_security(self):
        """
        Check it's possible to add a testinfo when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_testinfo(201)

    def test_testinfo_create_forbidden(self):
        """
        Check it's NOT possible to add a testinfo without 'add_testinfo' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testinfo', content_type=self.content_type_testinfo)))
        self._create_testinfo(403)

    def test_testinfo_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_testinfo permission
        - has NOT app1 permission

        User can add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testinfo', content_type=self.content_type_testinfo)))
            self._create_testinfo(201)

    def test_testinfo_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_testinfo permission
        - has app1 permission

        User can add test info on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_testinfo(201)

    def test_testinfo_create_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_testinfo permission
        - has app1 permission

        User can NOT add test info on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._create_testinfo(403)

    def test_testinfo_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_testinfo permission
        - has NOT app1 permission

        User can NOT add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testinfo')))
            self._create_testinfo(403)


    def test_testinfo_create_already_created(self):
        """
        Check it's possible to create the same TestInfo twice
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_testinfo(201)
            response = self.client.post('/snapshot/api/testinfo/', data={'testCase': 1, 'name': 'bla'})
            self.assertEqual(201, response.status_code)
            self.assertEqual(2, len(TestInfo.objects.filter(name='bla')))