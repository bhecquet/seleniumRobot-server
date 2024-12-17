
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

import commonsServer
from commonsServer.models import Application
from variableServer.admin_site.test_case_admin import TestCaseAdmin
from variableServer.tests.test_admin import request, MockRequest, TestAdmin

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
        Check that list of testcases contains only variables for 'app1', the only application user is able to see
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            ct = ContentType.objects.get_for_model(commonsServer.models.Application)
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1'), content_type=ct))
            
            testcase_admin = TestCaseAdmin(model=commonsServer.models.TestCase, admin_site=AdminSite())
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

            ct = ContentType.objects.get_for_model(commonsServer.models.Application)
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable'), content_type=ct))
            
            testcase_admin = TestCaseAdmin(model=commonsServer.models.TestCase, admin_site=AdminSite())
            query_set = testcase_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for test_case in query_set:
                app_list.append(test_case.application)
            
            self.assertEqual(app_list, []) # no application

