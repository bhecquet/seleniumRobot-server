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


class TestViewsets(TestApi):
    
    fixtures = ['commons_server.yaml']
    
    def setUp(self):
        
        Application.objects.get(pk=1).save()
        
        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_testcase = ContentType.objects.get_for_model(variableServer.models.TestCase, for_concrete_model=False)
        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)
        self.content_type_version = ContentType.objects.get_for_model(variableServer.models.Version, for_concrete_model=False)
        self.content_type_environment = ContentType.objects.get_for_model(variableServer.models.TestEnvironment, for_concrete_model=False)
    
    def test_create_testcase(self):
        """
        Check it's possible to add a testcase with 'add_testcase' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
        self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
        self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))
        
    def test_create_testcase_forbidden(self):
        """
        Check it's NOT possible to add a testcase without 'add_testcase' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
        response = self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
        self.assertEqual(403, response.status_code)
    
    def test_create_testcase_already_created(self):
        """
        Check it's possible to add a testcase with 'add_testcase' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
        self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
        self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))
        
        # if we try to create the same test case an other time, the same is returned
        self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
        self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))
    
    def test_create_testcase_with_application_restriction_and_add_permission(self):
        """
        User
        - has view_testcase permission
        - has NOT app1 permission
        
        User can add test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
            self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
            self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))
    
    def test_create_testcase_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT view_testcase permission
        - has app1 permission
        
        User can add test case on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
            self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))
    
    def test_create_testcase_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT view_testcase permission
        - has app1 permission
        
        User can NOT add test case on an other application than app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 2})
            self.assertEqual(403, response.status_code)
        
    def test_modify_testcase(self):
        """
        Check it's NOT possible to update testcase 
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testcase', content_type=self.content_type_testcase)))
        response = self.client.patch(reverse('testcase'), data={'application': 2})
        self.assertEqual(405, response.status_code)
        
    def test_delete_testcase(self):
        """
        Check it's NOT possible to delete testcase 
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_testcase', content_type=self.content_type_testcase)))
        response = self.client.delete(reverse('testcase'))
        self.assertEqual(405, response.status_code)
        
    def test_get_testcase_by_name(self):
        """
        Check it's possible to get a test case by name
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
        response = self.client.get(reverse('testcase'), data={'name': 'test1 with some spaces'})
        self.assertEqual(1, response.data['id'])
        
    def test_get_testcase_by_name_with_application_restriction_and_view_permission(self):
        """
        User
        - has view_testcase permission
        - has NOT app1 permission
        
        user can get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
            response = self.client.get(reverse('testcase'), data={'name': 'test1 with some spaces'})
            self.assertEqual(1, response.data['id'])
        
    def test_get_testcase_by_name_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT view_testcase permission
        - has app1 permission
        
        user can get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.get(reverse('testcase'), data={'name': 'test1 with some spaces'})
            self.assertEqual(1, response.data['id'])
        
    def test_get_testcase_by_name_with_application_restriction_and_app1_permission2(self):
        """
        User
        - has NOT view_testcase permission
        - has app1 permission
        
        test case belongs to an other application
        
        user can NOT get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.get(reverse('testcase'), data={'name': 'test3 with some spaces'})
            self.assertEqual(403, response.status_code)
        
    def test_get_testcase_by_name_with_application_restriction_and_no_permission2(self):
        """
        User
        - has NOT view_testcase permission
        - has NOT permission
        
        user can NOT get test case
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.get(reverse('testcase'), data={'name': 'test3 with some spaces'})
            self.assertEqual(403, response.status_code)
        
    def test_application_viewset(self):
        """
        As all viewsets share the same code base, do not repeat tests for each type, only check they inherit from RetrieveByNameViewSet
        """
        application_viewset = ApplicationViewSet()
        self.assertTrue(isinstance(application_viewset, RetrieveByNameViewSet))
        
    def test_create_application(self):
        """
        Check it's possible to add an application with 'add_application' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_application', content_type=self.content_type_application)))
        self.client.post(reverse('application'), data={'name': 'newapp'})
        self.assertEqual(1, len(Application.objects.filter(name='newapp')))
        
    def test_create_application_forbidden(self):
        """
        Check it's NOT possible to add an application without 'add_application' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_application', content_type=self.content_type_application)))
        response = self.client.post(reverse('application'), data={'name': 'newapp'})
        self.assertEqual(403, response.status_code)
        
    def test_create_application_with_application_restriction(self):
        """
        Check it's NOT possible to add an application without 'add_application' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.post(reverse('application'), data={'name': 'newapp'})
            self.assertEqual(403, response.status_code)
        
    def test_create_application_with_application_restriction2(self):
        """
        Check it's possible to add an application with 'add_application' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_application')))
            response = self.client.post(reverse('application'), data={'name': 'newapp'})
            self.assertEqual(201, response.status_code)
        
    def test_environment_viewset(self):
        """
        As all viewsets share the same code base, do not repeat tests for each type, only check they inherit from RetrieveByNameViewSet
        """
        environment_viewset = TestEnvironmentViewSet()
        self.assertTrue(isinstance(environment_viewset, RetrieveByNameViewSet))
        
    def test_create_environment(self):
        """
        Check it's possible to add an environment with 'add_environment' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testenvironment', content_type=self.content_type_environment)))
        self.client.post(reverse('environment'), data={'name': 'newenv'})
        self.assertEqual(1, len(TestEnvironment.objects.filter(name='newenv')))
        
    def test_create_environment_forbidden(self):
        """
        Check it's NOT possible to add an environment without 'add_environment' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testenvironment', content_type=self.content_type_environment)))
        response = self.client.post(reverse('environment'), data={'name': 'newenv'})
        self.assertEqual(403, response.status_code)
        
    def test_create_environment_with_application_restriction(self):
        """
        Check it's NOT possible to add an environment without 'add_environment' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = self.client.post(reverse('environment'), data={'name': 'newenv'})
            self.assertEqual(403, response.status_code)
        
    def test_create_environment_with_application_restriction2(self):
        """
        Check it's possible to add an environment with 'add_environment' permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testenvironment')))
            response = self.client.post(reverse('environment'), data={'name': 'newenv'})
            self.assertEqual(201, response.status_code)
        
    def test_version_viewset(self):
        """
        As all viewsets share the same code base, do not repeat tests for each type, only check they inherit from RetrieveByNameViewSet
        """
        version_viewset = VersionViewSet()
        self.assertTrue(isinstance(version_viewset, RetrieveByNameViewSet))
