from commonsServer.tests.test_api import TestApi
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls.base import reverse
from variableServer.models import Application, TestEnvironment
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
        self.content_type_environment = ContentType.objects.get_for_model(variableServer.models.TestEnvironment, for_concrete_model=False)

    def _create_environment(self, expected_status):
        response = self.client.post(reverse('environment'), data={'name': 'newenv'})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 201:
            self.assertEqual(1, len(TestEnvironment.objects.filter(name='newenv')))

    def test_create_environment(self):
        """
        Check it's possible to add an environment with 'add_environment' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testenvironment', content_type=self.content_type_environment)))
        self._create_environment(201)

    def test_create_environment_twice(self):
        """
        Check the same environment cannot be created twice
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testenvironment', content_type=self.content_type_environment)))
        self._create_environment(201)
        self._create_environment(201)

    def test_create_environment_no_name(self):
        """
        Check error is raised when name is not provided
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testenvironment', content_type=self.content_type_environment)))
        response = self.client.post(reverse('environment'), data={'noname': 'newenv'})
        self.assertEqual(400, response.status_code)

    def test_create_environment_no_api_security(self):
        """
        Check it's possible to add an environment when application restriction is set and the application does not correspond to app on which user has permission
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_environment(201)

    def test_create_environment_forbidden(self):
        """
        Check it's NOT possible to add an environment without 'add_environment' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testenvironment', content_type=self.content_type_environment)))
        self._create_environment(403)

    def test_create_environment_with_application_restriction(self):
        """
        Check it's NOT possible to add an environment without 'add_environment' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self._create_environment(403)

    def test_create_environment_with_application_restriction2(self):
        """
        Check it's possible to add an environment with 'add_environment' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testenvironment')))
            self._create_environment(201)

    def _get_environment(self, expected_status):
        response = self.client.get(reverse('environment'), data={'name': 'DEV'})
        self.assertEquals(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual(1, response.data['id'])

    def test_get_environment_by_name(self):
        """
        Check it's possible to get an environment case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testenvironment', content_type=self.content_type_environment)))
        self._get_environment(200)

    def test_get_environment_by_name_bad_model_permission(self):
        """
        Check it's possible to get an environment case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testenvironment', content_type=self.content_type_environment)))
        self._get_environment(403)

    def test_get_environment_by_name_no_api_security(self):
        """
        Check it's possible to get an environment case by name when application restriction is set and the application does not correspond to app on which user has permission
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._get_environment(200)

    def test_get_environment_by_name_with_application_restriction(self):
        """
        Check it's possible to get an environment by name when application restriction is set
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self._get_environment(200)

    def test_environment_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testenvironment', content_type=self.content_type_environment)
                                                                                      | Q(codename='change_testenvironment', content_type=self.content_type_environment)
                                                                                      | Q(codename='delete_testenvironment', content_type=self.content_type_environment)))

        response = self.client.patch('/commons/api/environment/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/commons/api/environment/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/commons/api/environment/1/')
        self.assertEqual(405, response.status_code)
