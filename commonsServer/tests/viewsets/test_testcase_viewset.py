from commonsServer.tests.test_api import TestApi
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls.base import reverse
from commonsServer.models import TestCase, TestEnvironment
from variableServer.models import Application
from django.contrib.contenttypes.models import ContentType
import variableServer
from commonsServer.views.viewsets import ApplicationViewSet,\
    RetrieveByNameViewSet, VersionViewSet, TestEnvironmentViewSet


class TestTestCaseViewset(TestApi):
    
    fixtures = ['commons_server.yaml']
    
    def setUp(self):
        
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_testcase = ContentType.objects.get_for_model(variableServer.models.TestCase, for_concrete_model=False)

    def _create_testcase(self, expected_status):
        response = self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 201:
            self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))

    def test_create_testcase(self):
        """
        Check it's possible to add a testcase with 'add_testcase' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
        self._create_testcase(201)

    def test_create_testcase_mission_application(self):
        """
        Check it's possible to add a testcase with 'add_testcase' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
        response = self.client.post(reverse('testcase'), data={'name': 'myTestCase'})
        self.assertEqual(400, response.status_code)

    def test_create_testcase_no_api_security(self):
        """
        Check it's possible to add a testcase when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._create_testcase(201)
        
    def test_create_testcase_forbidden(self):
        """
        Check it's NOT possible to add a testcase without 'add_testcase' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
        self._create_testcase(403)
    
    def test_create_testcase_already_created(self):
        """
        Check it's possible to add a testcase with 'add_testcase' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
        self._create_testcase(201)
        
        # if we try to create the same test case an other time, the same is returned
        self._create_testcase(201)
    
    def test_create_testcase_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_testcase permission
        - has NOT app1 permission
        
        User can add test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
            self._create_testcase(201)
    
    def test_create_testcase_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_testcase permission
        - has app1 permission
        
        User can add test case on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self._create_testcase(201)
    
    def test_create_testcase_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT add_testcase permission
        - has app1 permission
        
        User can NOT add test case on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self._create_testcase(403)
        
    def test_create_testcase_with_application_restriction_and_change_permission(self):
        """
        User
        - has change_testcase permission
        - has NOT app1 permission
        
        User can NOT add test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testcase')))
            self._create_testcase(403)

    def test_testcase_other_verbs_forbidden(self):
        """
        Check we cann only post info
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)
                                                                                      | Q(codename='change_testcase', content_type=self.content_type_testcase)
                                                                                      | Q(codename='delete_testcase', content_type=self.content_type_testcase)))

        response = self.client.patch('/commons/api/testcase/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/commons/api/testcase/1/')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/commons/api/testcase/1/')
        self.assertEqual(405, response.status_code)

    def _get_testcase(self, expected_status):
        response = self.client.get(reverse('testcase'), data={'name': 'test1 with some spaces', 'application': 1})
        self.assertEqual(expected_status, response.status_code)
        if expected_status == 200:
            self.assertEqual(1, response.data['id'])

    def test_get_testcase_by_name(self):
        """
        Check it's possible to get a test case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
        self._get_testcase(200)

    def test_get_testcase_by_name_missing_application(self):
        """
        Check it's possible to get a test case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
        response = self.client.get(reverse('testcase'), data={'name': 'test1 with some spaces'})
        self.assertEqual(200, response.status_code)

    def test_get_testcase_by_name_missing_name(self):
        """
        Check it's possible to get a test case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
        response = self.client.get(reverse('testcase'), data={'application': 1})
        self.assertEqual(400, response.status_code)

    def test_get_testcase_by_name_no_api_security(self):
        """
        Check it's possible to get a test case by name when API security is disabled
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._get_testcase(200)
        
    def test_get_testcase_by_name_with_application_restriction_and_view_permission(self):
        """
        User
        - has view_testcase permission
        - has NOT app1 permission
        
        user can get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
            self._get_testcase(200)
        
    def test_get_testcase_by_name_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT view_testcase permission
        - has app1 permission
        
        user can get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self._get_testcase(200)
        
    def test_get_testcase_by_name_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT view_testcase permission
        - has app1 permission
        
        test case belongs to an other application
        
        user can NOT get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self._get_testcase(403)
        
    def test_get_testcase_by_name_with_application_restriction_and_no_permission2(self):
        """
        User
        - has NOT view_testcase permission
        - has NOT permission
        
        user can NOT get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            self._get_testcase(403)



