import json
import os
from pathlib import Path

from django.conf import settings

from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import ExecutionLogs
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewsetExecutionLogs(TestApi):
    fixtures = ['snapshotServer.yaml']
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_executionlogs = ContentType.objects.get_for_model(ExecutionLogs)

    def tearDown(self):
        """
        Remove generated files
        """

        super().tearDown()

        for f in os.listdir(self.media_dir):
            if f.startswith('engie') or f.startswith('replyDetection'):
                os.remove(self.media_dir + os.sep + f)

    def _create_executionlogs(self, expected_status):
        with open('snapshotServer/tests/data/logs.txt', 'r') as f:
            response = self.client.post('/snapshot/api/logs/', data={'testCase': 1, 'file': f})
            self.assertEqual(expected_status, response.status_code)
            if expected_status == 201:
                self.assertEqual(1, len(ExecutionLogs.objects.filter(file__contains='logs')))

    def test_executionlogs_create(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_executionlogs', content_type=self.content_type_executionlogs)))
        self._create_executionlogs(201)

    def test_executionlogs_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_executionlogs', content_type=self.content_type_executionlogs)
                                                                                      | Q(codename='change_executionlogs', content_type=self.content_type_executionlogs)
                                                                                      | Q(codename='delete_executionlogs', content_type=self.content_type_executionlogs)))
        response = self.client.get('/snapshot/api/logs/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.patch('/snapshot/api/logs/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/logs/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/logs/1/')
        self.assertEqual(405, response.status_code)

    def test_executionlogs_create_no_api_security(self):
        """
        Check it's possible to add a executionlogs when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_executionlogs(201)

    def test_executionlogs_create_forbidden(self):
        """
        Check it's NOT possible to add a executionlogs without 'add_executionlogs' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_executionlogs', content_type=self.content_type_executionlogs)))
        self._create_executionlogs(403)

    def test_executionlogs_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_executionlogs permission
        - has NOT app1 permission

        User can add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_executionlogs', content_type=self.content_type_executionlogs)))
            self._create_executionlogs(201)

    def test_executionlogs_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_executionlogs permission
        - has app1 permission

        User can add test info on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_executionlogs(201)

    def test_executionlogs_create_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_executionlogs permission
        - has app1 permission

        User can NOT add test info on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._create_executionlogs(403)

    def test_executionlogs_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_executionlogs permission
        - has NOT app1 permission

        User can NOT add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_executionlogs')))
            self._create_executionlogs(403)


    def test_executionlogs_create_already_created(self):
        """
        Check it's possible to create the same ExecutionLogs twice
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_executionlogs(201)
            with open('snapshotServer/tests/data/logs.txt', 'r') as f:
                response = self.client.post('/snapshot/api/logs/', data={'testCase': 1, 'file': f})
                self.assertEqual(201, response.status_code)
                self.assertEqual(2, len(ExecutionLogs.objects.filter(file__contains='logs')))

    def test_delete_file(self):
        """
        Check file is uploaded
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            with open('snapshotServer/tests/data/test.html', 'rb') as fp:
                response = self.client.post('/snapshot/api/logs/', data={'testCase': 1, 'file': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201')

                file = ExecutionLogs.objects.filter(testCase__id=1).last()
                file_path = Path(file.file.path)
                self.assertTrue(file_path.exists())
                file.delete()
                self.assertFalse(file_path.exists())