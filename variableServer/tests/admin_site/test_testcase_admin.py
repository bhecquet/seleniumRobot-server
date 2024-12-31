
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

import commonsServer
from variableServer.models import Application
from variableServer.admin_site.test_case_admin import TestCaseAdmin
from variableServer.tests.test_admin import request, MockRequest, TestAdmin,\
    MockRequestWithApplication
from variableServer.models import TestCase
import variableServer

class TestTestCaseAdmin(TestAdmin):
    
    def test_testcase_queryset_without_application_restriction(self):
        """
        Check that list of testcases contains variables for all application when restriction is not set
        """
        testcase_admin = TestCaseAdmin(model=commonsServer.models.TestCase, admin_site=AdminSite())
        query_set = testcase_admin.get_queryset(request)
        
        app_list = []
        for test_case in query_set:
            app_list.append(test_case.application)
        
        self.assertEqual(len(list(set(app_list))), 2) # at least 2 applications
          
    def test_testcase_queryset_with_application_restriction(self):
        """
        Check that list of testcases contains only test cases for 'app1', the only application user is able to see
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            
            testcase_admin = TestCaseAdmin(model=variableServer.models.TestCase, admin_site=AdminSite())
            query_set = testcase_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for test_case in query_set:
                app_list.append(test_case.application)
            
            self.assertEqual(len(list(set(app_list))), 1) # 'app1'
            self.assertTrue(Application.objects.get(pk=1) in app_list)
    
          
    def test_testcase_queryset_with_application_restriction_and_not_allowed(self):
        """
        Check that list of testcases is empty as user as no right to see any application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
            
            testcase_admin = TestCaseAdmin(model=commonsServer.models.TestCase, admin_site=AdminSite())
            query_set = testcase_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for test_case in query_set:
                app_list.append(test_case.application)
            
            self.assertEqual(app_list, []) # no application

       
    def test_testcase_queryset_with_application_restriction_and_veiw_testcase_permission(self):
        """
        Check that list of testcases has all testcases with view_permission
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testcase', content_type=self.content_type_testcase)))
            
            testcase_admin = TestCaseAdmin(model=commonsServer.models.TestCase, admin_site=AdminSite())
            query_set = testcase_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for test_case in query_set:
                app_list.append(test_case.application.name)
            
            self.assertEqual(sorted(list(set(app_list))), ['app1', 'app5NoVar']) # no application

       
    def test_user_can_see_testcases_without_global_rights_and_application_permissions(self):
        """
        Check  user can view / change / delete / add with only application specific rights: can_view_application_app1
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = TestCaseAdmin(model=TestCase, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_cannot_see_testcases_without_global_rights_without_application_permissions(self):
        """
        Check  user cannot view / change / delete / add with only application specific rights: can_view_application_app1
        when application restriction are NOT applied
        """
        Application.objects.get(pk=1).save()

        testcase_admin = TestCaseAdmin(model=TestCase, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
        self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=1)))
        self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
        self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=1)))
        self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
        self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=TestCase.objects.get(pk=1)))
        self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))