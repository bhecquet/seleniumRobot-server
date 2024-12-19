
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Permission
from django.db.models import Q

import commonsServer
from variableServer.models import Application

from variableServer.admin_site.application_admin import ApplicationAdmin
from variableServer.models import Variable
from variableServer.tests.test_admin import request, MockRequest, TestAdmin


class TestApplicationAdmin(TestAdmin):
    
    fixtures = ['varServer']

    def test_application_fieldset_with_variables(self):
        """
        Check error message is displayed when an application has variables
        """
        app = Application.objects.get(pk=1)
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        fieldset = application_admin.get_fieldsets(request, app)
        
        self.assertEqual(len(fieldset), 1)
        self.assertEqual(fieldset[0], (None, {'fields': ('name', 'linkedApplication'), 'description': '<div style="font-size: 16px;color: red;">All tests / variables must be deleted before this application can be deleted</div>'}))
    
    def test_application_fieldset_without_variables(self):
        """
        Check no error message is displayed when an application has no variable
        """
        app = Application.objects.get(pk=5)
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        fieldset = application_admin.get_fieldsets(request, app)
        
        self.assertEqual(len(fieldset), 1)
        self.assertEqual(fieldset[0], (None, {'fields': ['name', 'linkedApplication']}))
    
    def test_application_has_no_associated_actions(self):
        """
        Check all actions are deactivated so that deleting an application must be done from detailed view
        """

        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        self.assertIsNone(application_admin.actions)

    def test_application_has_delete_permission_allowed_and_authenticated_without_linked_variables_or_tests(self):
        """
        Check we can delete application when no variable or tests are linked to
        user:
        - is authenticated
        - can delete application
        
        no variable/test linked to this application exist
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_application')))
        
        # search an application which has variable and no test
        app_with_tests = [t.application.id for t in commonsServer.models.TestCase.objects.all()]
        app_with_variables = [v.application.id for v in Variable.objects.exclude(application=None)]
        app_no_test_no_variable = Application.objects.exclude(id__in=app_with_tests + app_with_variables)[0]
        
        self.assertTrue(application_admin.has_delete_permission(request=MockRequest(user=user), obj=Application.objects.filter(pk=app_no_test_no_variable.id)[0])) # 'app2' has only variable linked to it
          

    def test_application_has_delete_permission_allowed_and_authenticated_with_linked_variables(self):
        """
        Check we cannot delete application when variable are linked to it
        user:
        - is authenticated
        - can delete application
        
        a variable linked to this application exist
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_application')))
        
        # search an application which has variable and no test
        app_with_tests = [t.application.id for t in commonsServer.models.TestCase.objects.all()]
        app_with_variables = [v.application.id for v in Variable.objects.exclude(application=None)]
        app_no_test = Application.objects.exclude(id__in=app_with_tests).filter(id__in=app_with_variables)[0]
        
        self.assertFalse(application_admin.has_delete_permission(request=MockRequest(user=user), obj=Application.objects.filter(pk=app_no_test.id)[0])) # 'app2' has only variable linked to it
              
            
    def test_application_has_delete_permission_allowed_and_authenticated_with_linked_tests(self):
        """
        Check we cannot delete application when tests are linked to it
        user:
        - is authenticated
        - can delete application
        
        a test linked to this application exist
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_application')))
        
        # search an application which has variable and no test
        app_with_tests = [t.application.id for t in commonsServer.models.TestCase.objects.all()]
        app_with_variables = [v.application.id for v in Variable.objects.exclude(application=None)]
        app_no_variable = Application.objects.exclude(id__in=app_with_variables).filter(id__in=app_with_tests)[0]
        
        self.assertFalse(application_admin.has_delete_permission(request=MockRequest(user=user), obj=Application.objects.filter(pk=app_no_variable.id)[0])) # 'app5NoVar' has tests
              
    def test_application_has_delete_permission_allowed_and_authenticated_none_application(self):
        """
        delete application without being allowed to
        user:
        - is authenticated
        - can delete application
        
        application is NONE
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_application')))
        self.assertTrue(application_admin.has_delete_permission(request=MockRequest(user=user)))
              
    def test_application_has_delete_permission_not_allowed_and_authenticated_none_application(self):
        """
        delete application without being allowed to
        user:
        - is authenticated
        - can NOT delete application
        
        application is NONE
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_application')))
        self.assertFalse(application_admin.has_delete_permission(request=MockRequest(user=user)))
        
        
    def test_save_application(self):
        """
        Check permission is created with the application
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        super_user = User.objects.create_superuser(username='super', email='super@email.org',
                                           password='pass')
        
        application_admin.save_model(obj=Application(name="toto1"), request=MockRequest(user=super_user),
                                  form=None, change=None)
        
        # if permission is created, no error is raised
        Permission.objects.get(codename='can_view_application_toto1')
        
    def test_rename_application(self):
        """
        Simulate the case where application has already been created and we rename an other application to this name
        Permission should not be recreated
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        super_user = User.objects.create_superuser(username='super', email='super@email.org',
                                           password='pass')
        
        application_admin.save_model(obj=Application(name="toto2"), request=MockRequest(user=super_user),
                                  form=None, change=None)
        application_admin.save_model(obj=Application(name="toto2"), request=MockRequest(user=super_user),
                                  form=None, change=None)
        
        # if permission is created, no error is raised
        Permission.objects.get(codename='can_view_application_toto2')
        
    def test_delete_application(self):
        """
        Check that deleting an application also deletes it's Permission
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        super_user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        
        application_admin.save_model(obj=Application(name="toto3"), request=MockRequest(user=super_user),
                                  form=None, change=None)
        
        # if permission is created, no error is raised
        Permission.objects.get(codename='can_view_application_toto3')
        
        app = Application.objects.get(name="toto3")
        application_admin.delete_model(obj=app, request=MockRequest(user=super_user))
        self.assertEqual(len(Permission.objects.filter(codename='can_view_application_toto3')), 0)
        
    def test_user_cannot_see_applications_without_global_rights(self):
        """
        Check  user cannot list application with only application specific rights: can_view_application_app1
        """
        application_admin = ApplicationAdmin(model=Application, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
        self.assertFalse(application_admin.has_view_permission(request=MockRequest(user=user)))
        self.assertFalse(application_admin.has_view_permission(request=MockRequest(user=user), obj=Application.objects.get(pk=1)))
        self.assertFalse(application_admin.has_add_permission(request=MockRequest(user=user)))
        self.assertFalse(application_admin.has_change_permission(request=MockRequest(user=user)))
        self.assertFalse(application_admin.has_delete_permission(request=MockRequest(user=user)))
        
        