from commonsServer.tests.test_api import TestApi
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls.base import reverse
from variableServer.models import Application
from django.contrib.contenttypes.models import ContentType
import variableServer
from commonsServer.views.viewsets import ApplicationViewSet, \
    RetrieveByNameViewSet

class TestApplicationViewSet(TestApi):

    fixtures = ['commons_server.yaml']

    def setUp(self):

        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)

    def test_version_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_application', content_type=self.content_type_application)
                                                                                      | Q(codename='change_application', content_type=self.content_type_application)
                                                                                      | Q(codename='delete_application', content_type=self.content_type_application)))

        response = self.client.patch('/commons/api/application/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/commons/api/application/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/commons/api/application/1/')
        self.assertEqual(405, response.status_code)

    def _get_application_by_name(self, expected_status):
        response = self.client.get(reverse('application'), data={'name': 'app1'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual(1, response.data['id'])

    def test_get_application_by_name(self):
        """
        Check it's possible to get an application case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_application', content_type=self.content_type_application)))
        self._get_application_by_name(200)

    def test_get_application_no_name(self):
        """
        Check error is raised when name is missing
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_application', content_type=self.content_type_application)))
        response = self.client.get(reverse('application'), data={'noname': 'app1'})
        self.assertEqual(400, response.status_code)

    def test_get_application_by_name_bad_model_permission(self):
        """
        Check it's possible to get an application case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_application', content_type=self.content_type_application)))
        self._get_application_by_name(403)

    def test_get_application_by_name_no_api_security(self):
        """
        Check it's possible to get an application case by name when API security is disabled and no permission given to user
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._get_application_by_name(200)

    def test_get_application_by_name_with_application_restriction(self):
        """
        Check it's possible to get an application case by name when application restriction is set
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1', content_type=self.content_type_application)))
            self._get_application_by_name(200)

    def test_get_application_by_name_with_application_restriction2(self):
        """
        Check it's NOT possible to get an application case by name when application restriction is set and the application does not correspond to app on which user has permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self._get_application_by_name(403)

    def test_get_application_by_name_with_application_restriction_inexistent(self):
        """
        Check we get 403 if application is unknown
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1', content_type=self.content_type_application)))
            response = self.client.get(reverse('application'), data={'name': 'appNotFound'})
            self.assertEqual(403, response.status_code)

    def _create_application(self, expected_status):
        response = self.client.post(reverse('application'), data={'name': 'newapp'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 201:
            self.assertEqual(1, len(Application.objects.filter(name='newapp')))

    def test_create_application(self):
        """
        Check it's possible to add an application with 'add_application' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_application', content_type=self.content_type_application)))
        self._create_application(201)

    def test_create_application_twice(self):
        """
        Check the same application cannot be created twice
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_application', content_type=self.content_type_application)))
        self._create_application(201)
        self._create_application(201)

    def test_create_application_no_name(self):
        """
        Check error raised when name is missing
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_application', content_type=self.content_type_application)))
        response = self.client.post(reverse('application'), data={'noname': 'newapp'})
        self.assertEqual(400, response.status_code)

    def test_create_application_no_api_security(self):
        """
        Check it's possible to add an application when API security is disabled and no permission given to user
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_application(201)

    def test_create_application_forbidden(self):
        """
        Check it's NOT possible to add an application without 'add_application' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_application', content_type=self.content_type_application)))
        self._create_application(403)

    def test_create_application_with_application_restriction(self):
        """
        Check it's NOT possible to add an application without 'add_application' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self._create_application(403)

    def test_create_application_with_application_restriction2(self):
        """
        Check it's possible to add an application with 'add_application' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_application')))
            self._create_application(201)