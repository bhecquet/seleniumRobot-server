import json
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import ExcludeZone
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewsetExcludeZone(TestApi):
    fixtures = ['snapshotServer.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_excludezone = ContentType.objects.get_for_model(ExcludeZone)

    def _create_excludezone(self, expected_status):
        response = self.client.post('/snapshot/api/exclude/', data={'snapshot': 1, 'x': 0, 'y': 0, 'width': 10, 'height': 10})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 201:
            self.assertEqual(1, len(ExcludeZone.objects.filter(snapshot__id=1)))

    def test_excludezone_create(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_excludezone', content_type=self.content_type_excludezone)))
        self._create_excludezone(201)

    def test_excludezone_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_excludezone', content_type=self.content_type_excludezone)
                                                                                      | Q(codename='change_excludezone', content_type=self.content_type_excludezone)
                                                                                      | Q(codename='delete_excludezone', content_type=self.content_type_excludezone)))
        response = self.client.get('/snapshot/api/exclude/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/exclude/1/')
        self.assertEqual(405, response.status_code)

    def test_excludezone_create_no_api_security(self):
        """
        Check it's possible to add a excludezone when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_excludezone(201)

    def test_excludezone_create_forbidden(self):
        """
        Check it's NOT possible to add a excludezone without 'add_excludezone' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_excludezone', content_type=self.content_type_excludezone)))
        self._create_excludezone(403)

    def test_excludezone_create_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_excludezone permission
        - has NOT app1 permission

        User can add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_excludezone', content_type=self.content_type_excludezone)))
            self._create_excludezone(201)

    def test_excludezone_create_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_excludezone permission
        - has app1 permission

        User can add test info on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_excludezone(201)

    def test_excludezone_create_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_excludezone permission
        - has app1 permission

        User can NOT add test info on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._create_excludezone(403)

    def test_excludezone_create_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_excludezone permission
        - has NOT app1 permission

        User can NOT add test info
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_excludezone')))
            self._create_excludezone(403)


    def test_excludezone_create_already_created(self):
        """
        Check it's not possible to create the same ExcludeZone twice
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._create_excludezone(201)
            self._create_excludezone(201)

    def _update_excludezone(self, expected_status):
        exclude_zone = ExcludeZone(x=0, y=0, width=10, height=10, snapshot_id=1)
        exclude_zone.save()
        response = self.client.patch(f'/snapshot/api/exclude/{exclude_zone.id}/', data={'x': 2})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual(2, ExcludeZone.objects.get(id=exclude_zone.id).x)

    def test_excludezone_update_with_model_permission(self):
        """
        Test it's possible to update session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_excludezone', content_type=self.content_type_excludezone)))
        self._update_excludezone(200)

    def test_excludezone_update_non_existent_object(self):
        """
        Check we get 404 when object does not exist
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_excludezone', content_type=self.content_type_excludezone)))
        response = self.client.patch(f'/snapshot/api/exclude/12345/', data={'x': 2})
        self.assertEqual(404, response.status_code)

    def test_excludezone_update_non_existent_object2(self):
        """
        Check we get 403 when object does not exist and user has not permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_excludezone', content_type=self.content_type_excludezone)))
        response = self.client.patch(f'/snapshot/api/exclude/12345/', data={'x': 2})
        self.assertEqual(403, response.status_code)

    def test_excludezone_update_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT change_excludezone permission
        - has app1 permission

        User can update test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._update_excludezone(200)

    def test_excludezone_update_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT change_excludezone permission
        - has app1 permission

        User can NOT update test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._update_excludezone(403)

    def _delete_excludezone(self, expected_status):
        exclude_zone = ExcludeZone(x=0, y=0, width=10, height=10, snapshot_id=1)
        exclude_zone.save()
        response = self.client.delete(f'/snapshot/api/exclude/{exclude_zone.id}/')
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 204:

            # exclude zone has been deleted
            self.assertEqual(0, len(ExcludeZone.objects.filter(id=exclude_zone.id)))

    def test_excludezone_delete_with_model_permission(self):
        """
        Test it's possible to delete session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_excludezone', content_type=self.content_type_excludezone)))
        self._delete_excludezone(204)

    def test_excludezone_delete_non_existent_object(self):
        """
        Check we get 404 when object does not exist
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_excludezone', content_type=self.content_type_excludezone)))
        response = self.client.delete(f'/snapshot/api/exclude/12345/')
        self.assertEqual(404, response.status_code)

    def test_excludezone_delete_non_existent_object2(self):
        """
        Check we get 403 when object does not exist and user has not permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_excludezone', content_type=self.content_type_excludezone)))
        response = self.client.delete(f'/snapshot/api/exclude/12345/')
        self.assertEqual(403, response.status_code)

    def test_excludezone_delete_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT change_excludezone permission
        - has app1 permission

        User can delete test session on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp')))
            self._delete_excludezone(204)

    def test_excludezone_delete_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT change_excludezone permission
        - has app1 permission

        User can NOT delete test session on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            self._delete_excludezone(403)