import os
import shutil
import zipfile
from pathlib import Path

from snapshotServer.utils.utils import getTestDirectory
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import File
from django.contrib.auth.models import Permission
from django.conf import settings
from commonsServer.tests.test_api import TestApi

from PIL import Image
from io import BytesIO


class TestViewsetFile(TestApi):
    fixtures = ['snapshotServer.yaml']
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    data_dir = getTestDirectory()

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_file = ContentType.objects.get_for_model(File)

    def tearDown(self):
        """
        Remove generated files
        """

        super().tearDown()

        for f in os.listdir(self.media_dir):
            if f.startswith('engie') or f.startswith('replyDetection'):
                os.remove(self.media_dir + os.sep + f)


    def test_upload_image_file(self):
        """
        Check file is uploaded
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_file', content_type=self.content_type_file)))
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post('/snapshot/api/file/', data={'stepResult': 1, 'file': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201')

            file = File.objects.filter(stepResult__id=1).last()
            self.assertTrue(file.file.name.endswith(".png"))
            self.assertTrue(Path(file.file.path).exists())


    def test_delete_file(self):
        """
        Check file is uploaded
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_file', content_type=self.content_type_file)))
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post('/snapshot/api/file/', data={'stepResult': 1, 'file': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201')

            file = File.objects.filter(stepResult__id=1).last()
            file_path = Path(file.file.path)
            self.assertTrue(file_path.exists())
            file.delete()
            self.assertFalse(file_path.exists())

    def test_upload_html_file(self):
        """
        Check file is uploaded and zipped at the same time
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_file', content_type=self.content_type_file)))
        with open('snapshotServer/tests/data/test.html', 'rb') as fp:
            response = self.client.post('/snapshot/api/file/', data={'stepResult': 1, 'file': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201')

            file = File.objects.filter(stepResult__id=1).last()
            self.assertTrue(file.file.name.endswith(".zip"))
            self.assertTrue(Path(file.file.path).exists())

            with zipfile.ZipFile(file.file.path) as zip:
                with zip.open('test.html', 'r') as myfile:
                    self.assertTrue('<html>' in myfile.read().decode('utf-8'))

    def test_upload_html_file_in_error(self):
        """
        Check file is uploaded and zipped at the same time
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_file', content_type=self.content_type_file)))
        response = self.client.post('/snapshot/api/file/', data={'stepResult': 1})
        self.assertEqual(response.status_code, 500, 'status code should be 201')


    def _create_file(self, expected_status):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post('/snapshot/api/file/', data={'stepResult': 1, 'file': fp, 'name': 'engie.png'})
            self.assertEqual(expected_status, response.status_code)
            if expected_status == 201:
                self.assertEqual(1, len(File.objects.filter(name='engie.png')))

    def test_file_create_with_model_permission(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_file', content_type=self.content_type_file)))
        self._create_file(201)

    def test_file_other_verbs_forbidden(self):
        """
        Check we cann only post sessions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)
                                                                                      | Q(codename='change_file', content_type=self.content_type_file)
                                                                                      | Q(codename='delete_file', content_type=self.content_type_file)))
        response = self.client.patch('/snapshot/api/file/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/file/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/file/1/')
        self.assertEqual(405, response.status_code)

    def test_file_create_no_api_security(self):
        """
        Check it's possible to add a file when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_file(201)

    def test_file_create_forbidden(self):
        """
        Check it's NOT possible to add a file without 'add_file' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        self._create_file(403)

    def test_file_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_file permission
        - has NOT app1 permission

        User can add test session
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_file', content_type=self.content_type_file)))
            self._create_file(201)

    def test_file_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_file permission
        - has app1 permission

        User can add test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_file(201)

    def test_file_create_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_file permission
        - has app1 permission

        User can NOT add test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._create_file(403)

    def test_file_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_file permission
        - has NOT app1 permission

        User can NOT add test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_file')))
            self._create_file(403)

    def _retrieve_file_content(self, file_id, expected_status, content_type, file_name, attachment_name):
        """

        :param file_id: id on the file in database
        :param expected_status:
        :param content_type: expected content type to be returned
        :param file_name: file to copy
        :param attachment_name:
        :return:
        """

        shutil.copyfile(Path(self.data_dir) / file_name, Path(self.media_dir) / file_name)

        response = self.client.get(f'/snapshot/api/file/{file_id}/download/')
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual(content_type, response.headers['Content-Type'])
            self.assertEqual(f'attachment; filename="{attachment_name}"', response.headers['Content-Disposition'])
            byte_content = b''.join(response.streaming_content)

            return byte_content


    def test_file_retrieve_content_with_model_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        byte_content = self._retrieve_file_content(1, 200, 'image/png', 'test_Image1.png', 'test_Image1.png')

        image = Image.open(BytesIO(byte_content))
        image.verify()

    def test_file_retrieve_content_with_application_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._retrieve_file_content(1, 200, 'image/png', 'test_Image1.png', 'test_Image1.png')

    def test_html_file_retrieve_content_with_model_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        byte_content = self._retrieve_file_content(2, 200, 'text/html', 'test.html', 'documents/test.html')
        text = byte_content.decode("utf-8")
        self.assertTrue('html' in text)

    def test_txt_file_retrieve_content_with_model_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        byte_content = self._retrieve_file_content(3, 200, 'text/plain', 'test.txt', "test_file.txt")
        text = byte_content.decode("utf-8")
        self.assertTrue('foo' in text)

    def test_avi_file_retrieve_content_with_model_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        byte_content = self._retrieve_file_content(4, 200, 'video/x-msvideo', 'test.avi', 'documents/test.avi')
        text = byte_content.decode("utf-8")
        self.assertTrue('avi' in text)

    def test_mp4_file_retrieve_content_with_model_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        byte_content = self._retrieve_file_content(5, 200, 'video/mp4', 'test.mp4', 'test.mp4')
        text = byte_content.decode("utf-8")
        self.assertTrue('mp4' in text)

    def test_zip_file_retrieve_content_with_model_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        byte_content = self._retrieve_file_content(6, 200, 'application/zip', 'test.zip', 'test.zip')
        text = byte_content.decode("utf-8")
        self.assertTrue('zip' in text)

    def test_har_file_retrieve_content_with_model_permission(self):
        """
        Test it's possible to get file content and headers / content are correct
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        byte_content = self._retrieve_file_content(7, 200, 'application/octet-stream', 'test.har', 'test.har')
        text = byte_content.decode("utf-8")
        self.assertTrue('har' in text)

    def _retrieve_file(self, expected_status):
        response = self.client.get('/snapshot/api/file/1/')
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual('test_Image1.png', response.data['name'])

    def test_file_retrieve_with_model_permission(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        self._retrieve_file(200)

    def test_file_retrieve_non_existent(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_file', content_type=self.content_type_file)))
        response = self.client.get('/snapshot/api/file/12345/')
        self.assertEqual(404, response.status_code)

    def test_file_retrieve_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT change_file permission
        - has app1 permission

        User can update test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._retrieve_file(200)

    def test_file_retrieve_with_application_restriction_and_app1_permission_non_existent(self):
        """
        User
        - has NOT change_file permission
        - has app2 permission

        User can update test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            response = self.client.get('/snapshot/api/file/12345/')
            self.assertEqual(403, response.status_code)

    def test_file_retrieve_with_application_restriction_and_app2_permission(self):
        """
        User
        - has NOT change_file permission
        - has app2 permission

        User can NOT update test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._retrieve_file(403)
