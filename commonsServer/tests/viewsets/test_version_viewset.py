from commonsServer.tests.test_api import TestApi
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls.base import reverse
from variableServer.models import Application, Version
from django.contrib.contenttypes.models import ContentType
import variableServer
from commonsServer.views.viewsets import VersionViewSet, \
    RetrieveByNameViewSet

class TestVersionViewSet(TestApi):

    fixtures = ['commons_server.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_version = ContentType.objects.get_for_model(variableServer.models.Version, for_concrete_model=False)

    def test_version_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_version', content_type=self.content_type_version)
                                                                                      | Q(codename='change_version', content_type=self.content_type_version)
                                                                                      | Q(codename='delete_version', content_type=self.content_type_version)))

        response = self.client.get('/commons/api/version/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.patch('/commons/api/version/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/commons/api/version/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/commons/api/version/1/')
        self.assertEqual(405, response.status_code)

    def _create_version(self, expected_status):
        response = self.client.post(reverse('version'), data={'name': 'newversion', 'application': 1})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 201:
            self.assertEqual(1, len(Version.objects.filter(name='newversion')))

    def test_create_version(self):
        """
        Check it's possible to add an version with 'add_version' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_version', content_type=self.content_type_version)))
        self._create_version(201)

    def test_create_version_twice(self):
        """
        Check a version cannot be created if it has the same parameters
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_version', content_type=self.content_type_version)))
        self._create_version(201)
        self._create_version(201)

    def test_create_version_missing_application(self):
        """
        Check it's possible to add an version with 'add_version' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_version', content_type=self.content_type_version)))
        response = self.client.post(reverse('version'), data={'name': 'newversion'})
        self.assertEqual(400, response.status_code)

    def test_create_version_no_api_security(self):
        """
        Check it's possible to add an version when API security is disabled and no permission given to user
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_version(201)

    def test_create_version_forbidden(self):
        """
        Check it's NOT possible to add an version without 'add_version' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_version', content_type=self.content_type_version)))
        self._create_version(403)

    def test_create_version_with_application_permission(self):
        """
        Check it's possible to add a version with application specific permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self._create_version(201)

    def test_create_version_without_application_permission(self):
        """
        Check it's NOT possible to add a version on an application on which user has no right
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self._create_version(403)

    def test_create_version_with_application_restriction_and_model_permission(self):
        """
        Check it's possible to add an version with 'add_version' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_version')))
            self._create_version(201)