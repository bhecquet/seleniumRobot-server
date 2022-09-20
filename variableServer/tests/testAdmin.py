'''
Created on 28 mars 2018

@author: s047432
'''
import datetime
import re

from django import forms
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.test.client import Client
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

import commonsServer
from commonsServer.models import Application, Version
import variableServer
from variableServer.admin import ApplicationAdmin, VariableAdmin, is_user_authorized, \
    BaseServerModelAdmin, VariableForm, VersionFilter, EnvironmentFilter, \
    TestCaseAdmin, VersionAdmin
from variableServer.models import Variable


# tests we should add to check admin view behavior
# - when permissions are set for application, 
#   - cannot delete Variable of application whose user does not have right for
#   - cannot delete TestCase of application whose user does not have right for
#   - cannot delete Version of application whose user does not have right for
#   - variable belonging to restricted application are not shown
#   - test case belonging to restricted application are not shown
#   - version belonging to restricted application are not shown
#   - cannot change several variable at once to/from restricted application
#   - cannot copy several variable to/from restricted application
#   - cannot add variable to a restricted application
#   - cannot add testcase to a restricted application
#   - cannot add version to a restricted application
#   - for unrestricted applications, check the above behavior are not active
# - change multiple variables at once
# - copy multiple variables
# - copy several variables, one with tests, other without and check that resulting test is none
# - copy several variables, all with tests and check that resulting tests are the same as from variables
# - check filtering of tests and version when modifying a variable
class MockRequest(object):
    def __init__(self, user=None):
        self.user = user
        self.method = 'GET'
        self.GET = {}
        
class MockRequestWithApplication(object):
    def __init__(self, user=None):
        self.user = user
        self.POST = {'application': '1'}
        self.method = 'POST'

class MockSuperUser:
    def has_perm(self, perm, obj=None):
        return True


request = MockRequest()
request.user = MockSuperUser()

# https://stackoverflow.com/questions/6498488/testing-admin-modeladmin-in-django
class TestAdmin(TestCase):
    
    fixtures = ['varServer']
    
    def _create_and_authenticate_user_with_permissions(self, permissions):
        """
        @param permissions: example: Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable'), content_type=ct)
        """
        
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        client = Client()
        client.login(username='user', password='pass')
        
        variable_users_group, created = Group.objects.get_or_create(name='Variable Users')
        
        variable_users_group.permissions.add(*permissions)
        variable_users_group.user_set.add(user)
        
        user.is_staff = True
        user.save()
        
        return user, client
    
    def _format_content(self, content):
        return re.sub('>\s+<', '><', str(content).replace('\\n', ''))
        
    
    
### ApplicationAdmin ###

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
        
### is_user_authorized ###    
    def test_is_user_authorized_standard_user(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        self.assertFalse(is_user_authorized(user))
       
    def test_is_user_authorized_authenticated_user_no_permission(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        client = Client()
        client.login(username='user', password='pass')
        
        self.assertFalse(is_user_authorized(user))
       
    def test_is_user_authorized_authenticated_user_with_permission(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        client = Client()
        client.login(username='user', password='pass')
        
        variable_users_group, created = Group.objects.get_or_create(name='Variable Users')
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        variable_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable') | Q(codename='delete_variable') | Q(codename='see_protected_var') , content_type=ct))
        variable_users_group.user_set.add(user)
        
        self.assertTrue(is_user_authorized(user))
       
    def test_is_user_authorized_none_user(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        self.assertFalse(is_user_authorized(None))
     
    def test_is_user_authorized_super_user(self):
        """
        Check that super user will have right to see protected variabls
        """
        user = User.objects.create_superuser(username='user', email='user@email.org', password='pass')
        self.assertTrue(is_user_authorized(user))
     
### VariableAdmin ###
    def test_variable_get_list_display_with_authorized_user(self):
        """
        Check variable values are displayed even protected value with allowed user
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        super_user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertEqual(variable_admin.get_list_display(request=MockRequest(user=super_user)), ('nameWithApp', 'value', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate'))
        
        
    def test_variable_get_list_display_with_unauthorized_user(self):
        """
        Check protected variable values are not displayed with disallowed user
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        self.assertEqual(variable_admin.get_list_display(request=MockRequest(user=user)), ('nameWithApp', 'valueProtected', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate'))
        
    def test_variable_queryset_without_application_restriction(self):
        """
        Check that list of variables contains variables for all application when restriction is not set
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        query_set = variable_admin.get_queryset(request)
        
        app_list = []
        for var in query_set:
            app_list.append(var.application)
        
        self.assertTrue(len(list(set(app_list))), 2) # at least 'None' and 2 other applications
        
       
    def test_variable_queryset_with_application_restriction(self):
        """
        Check that list of variables contains only variables for 'app1', the only application user is able to see
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            ct = ContentType.objects.get_for_model(commonsServer.models.Application)
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1'), content_type=ct))
            
            variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            query_set = variable_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for var in query_set:
                app_list.append(var.application)
            
            self.assertEqual(len(list(set(app_list))), 2) # 'None' and 'app1'
            self.assertTrue(Application.objects.get(pk=1) in app_list)
        
    def test_variable_save_standard(self):
        """
        Check saving is done
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        variable = Variable.objects.get(pk=1)
        self.assertFalse(variable.protected)
        variable.value = 'proxy.com'
        
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        variable_admin.save_model(obj=variable, request=MockRequest(user=user), form=None, change=None)
        self.assertEqual(Variable.objects.get(pk=1).value, 'proxy.com')
        
    def test_variable_save_protected_variable_with_authorized_user(self):
        """
        Check value is modified when user has the right to do
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        variable = Variable.objects.get(pk=102)
        self.assertTrue(variable.protected) # check variable is protected
        variable.value = 'azerty'
        variable.protected = False
   
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='see_protected_var'), content_type=ct))
        
        variable_admin.save_model(obj=variable, request=MockRequest(user=user), form=None, change=None)
        self.assertEqual(Variable.objects.get(pk=102).value, 'azerty')
        self.assertFalse(Variable.objects.get(pk=102).protected)
        
    def test_variable_save_protected_variable_with_unauthorized_user(self):
        """
        Check value of protected var is not modified when user has not the right to do
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        variable = Variable.objects.get(pk=102)
        self.assertTrue(variable.protected) # check variable is protected
        variable.value = 'azerty'
        variable.protected = False
   
        user = User.objects.create_user(username='user', email='user@email.org', password='pass') # user without permission
        
        variable_admin.save_model(obj=variable, request=MockRequest(user=user), form=None, change=None)
        self.assertEqual(Variable.objects.get(pk=102).value, 'azertyuiop') # value not changed
        self.assertTrue(Variable.objects.get(pk=102).protected) # value not changed
        
    def test_variable_copy_to_no_variables(self):
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'copyTo',
                'index': '0',}
        response = client.post(change_url, data)
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
     
    def test_variable_copy_to(self):
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'copyTo',
                ACTION_CHECKBOX_NAME: [3, 4],
                'index': '0',}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        self.assertTrue('<form action="/variable/copyVariables" method="post">' in content)
        self.assertTrue('<option value="1" selected>app1</option>' in content) # check 'app1' is already selected as both variables have the same application
        self.assertTrue('Version:</label><select name="version" id="id_version"><option value="" selected>---------</option>' in content) # check no version is selected as variables have the the same
        
    def test_variable_get_default_values_single_variable(self):
        """
        Check default values are the one from the variable
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        default_values = variable_admin._get_default_values([7])
        
        self.assertEqual(default_values['environment'].name, 'DEV1')
        self.assertEqual(default_values['application'].name, 'app1')
        self.assertEqual(default_values['version'].name, '2.5')
        self.assertEqual(default_values['reservable'], True)
        self.assertEqual(len(default_values['test'].all()), 1)
        
    def test_variable_get_default_values_multiple_variables(self):
        """
        Check default values are the one common to first variable and others
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        default_values = variable_admin._get_default_values([7, 8])
        
        self.assertEqual(default_values['environment'].name, 'DEV1')
        self.assertEqual(default_values['application'].name, 'app1')
        self.assertEqual(default_values['version'], None)
        self.assertEqual(default_values['reservable'], False)
        self.assertEqual(default_values['test'], None)
       
        
    def test_variable_change_no_variables(self):
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'changeValuesAtOnce',
                'index': '0',}
        response = client.post(change_url, data)
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
     
    def test_variable_change(self):
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'changeValuesAtOnce',
                'index': '0',
                ACTION_CHECKBOX_NAME: [3, 4]}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        self.assertTrue('<form action="/variable/changeVariables" method="post">' in content)
        self.assertTrue('<option value="1" selected>app1</option>' in content) # check 'app1' is already selected as both variables have the same application
        self.assertTrue('Version:</label><select name="version" id="id_version"><option value="" selected>---------</option>' in content) # check no version is selected as variables have the the same
       
     
    def test_variable_delete_selected_no_restriction(self):
        """
        Check that we can delete selected variable if no restriction applies on applications
        """
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable') | Q(codename='delete_variable'), content_type=ct))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'delete_selected',
                'index': '0',
                ACTION_CHECKBOX_NAME: [3]}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
        self.assertTrue('<li>Variable: <a href="/admin/variableServer/variable/3/change/">appName</a></li></ul>' in content) # variable 'appName' is ready to be deleted
     
     
    def test_variable_cannot_delete_selected_with_restriction(self):
        """
        Check that we cannot delete selected variable as restriction apply on this application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))
            
            change_url = reverse('admin:variableServer_variable_changelist')
            data = {'action': 'delete_selected',
                    'index': '0',
                    ACTION_CHECKBOX_NAME: [3]}
            response = client.post(change_url, data)
            content = self._format_content(response.content)
            
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
            self.assertTrue('<h2>Objects</h2><ul></ul>' in content) # no variable will be deleted, we do not have rights on this application
     
    def test_variable_can_be_delete_selected_with_restriction(self):
        """
        Check that we can delete selected variable as user has right to use this application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            # be sure permission for application is created
            Application.objects.get(pk=1).save()
            
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(
                Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable') | Q(codename='delete_variable') | Q(codename='can_view_application_app1')))
            
            change_url = reverse('admin:variableServer_variable_changelist')
            data = {'action': 'delete_selected',
                    'index': '0',
                    ACTION_CHECKBOX_NAME: [3]}
            response = client.post(change_url, data)
            content = self._format_content(response.content)
            
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
            self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
            self.assertTrue('<li>Variable: <a href="/admin/variableServer/variable/3/change/">appName</a></li></ul>' in content) # variable 'appName' is ready to be deleted
            
     
    def test_variable_unreserve(self):
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))
        
        # reserve variable
        reservable_var = Variable(name='var1', value='value1', application=Application.objects.get(pk=1), version=Version.objects.get(pk=1), releaseDate=timezone.now() + datetime.timedelta(seconds=60))
        reservable_var.save()

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'unreserveVariable',
                'index': '0',
                ACTION_CHECKBOX_NAME: [reservable_var.id]}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
        self.assertEqual(response.url, '/admin/variableServer/variable/')
        
        self.assertIsNone(Variable.objects.get(pk=reservable_var.id).releaseDate)
        
        
### BaseServerModelAdmin ###

    def test_has_add_permission_superuser(self):
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
        
    def test_has_add_permission_allowed_and_authenticated(self):
        """
        Add variable on application
        user:
        - is authenticated
        - can add variable
        - can view app1
        
        restriction on application is not applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='add_variable')))
        self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_add_permission_allowed_and_authenticated_with_restrictions(self):
        """
        Add variable on application
        user:
        - is authenticated
        - can add variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='add_variable')))
            self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_add_permission_not_allowed_and_authenticated_with_restrictions(self):
        """
        Add variable on application
        user:
        - is authenticated
        - can add variable
        - can NOT view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
            self.assertFalse(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_add_permission_not_allowed_and_authenticated(self):
        """
        Add variable on application without being allowed to add variable
        user:
        - is authenticated
        - can NOT add variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_add_permission(request=MockRequest(user=user)))
            

    def test_has_change_permission_superuser(self):
        
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=1)))
        
    def test_has_change_permission_superuser_with_application(self):
        """
        Change permission on variable with application
        """
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_change_permission_superuser_with_application_and_restrictions(self):
        """
        Change permission on variable with application, when restrictions are applied
        """
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
            self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_change_permission_allowed_and_authenticated(self):
        """
        change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is not applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
        self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_change_permission_allowed_and_authenticated_with_restrictions(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_change_permission_not_allowed_and_authenticated(self):
        """
        Change variable on application without being allowed to change variable
        user:
        - is authenticated
        - can NOT change variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequest(user=user)))
            
    def test_has_change_permission_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_change_permission_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
              
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
              
    def test_has_change_permission_not_allowed_and_authenticated_none_variable(self):
        """
        Change variable on application without being allowed to change variable
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        variable is NONE
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user)))
            

    def test_has_delete_permission_superuser(self):
        
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=1)))
        
    def test_has_delete_permission_superuser_with_application(self):
        """
        delete permission on variable with application
        """
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_delete_permission_superuser_with_application_and_restrictions(self):
        """
        delete permission on variable with application, when restrictions are applied
        """
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_delete_permission_allowed_and_authenticated(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is not applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
        self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_delete_permission_not_allowed_and_authenticated_with_restrictions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_delete_permission_not_allowed_and_authenticated(self):
        """
        delete variable on application without being allowed to delete variable
        user:
        - is authenticated
        - can NOT delete variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequest(user=user)))
            
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_delete_permission_not_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
              
            
    def test_has_delete_permission_not_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
              
    def test_has_delete_permission_not_allowed_and_authenticated_none_variable(self):
        """
        delete variable on application without being allowed to delete variable
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        variable is NONE
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user)))
            
### VariableForm ###

    def test_variable_form_with_existing_variable_no_application_defined(self):
        """
        Check that if application is not defined for the variable, fields "version" and "test" are disabled
        """
        
        form = VariableForm(instance=Variable.objects.get(pk=1))
        self.assertEqual(form.fields['test'].help_text, "Select an application, click 'save and continue editing' to display the list of related tests")
        self.assertTrue(form.fields['test'].disabled) # check field is disabled when no application is selected
        self.assertEqual(form.fields['version'].help_text, "Select an application, click 'save and continue editing' to display the list of related versions")
        self.assertTrue(form.fields['version'].disabled) # check field is disabled when no application is selected
        

    def test_variable_form_with_existing_variable_application_defined(self):
        """
        Check that if application not defined for the variable, fields "version" and "test" are enabled
        """
        
        form = VariableForm(instance=Variable.objects.get(pk=3))
        self.assertEqual(form.fields['test'].help_text, "If 'application' value is modified, click 'save and continue editing' to display the related list of tests")
        self.assertFalse(form.fields['test'].disabled) # check field is disabled when no application is selected
        self.assertEqual(len(form.fields['test'].queryset), 2)
        self.assertTrue(2 in [v.id for v in form.fields['test'].queryset])
        self.assertEqual(form.fields['version'].help_text, "If 'application' value is modified, click 'save and continue editing' to display the related list of versions")
        self.assertFalse(form.fields['version'].disabled) # check field is disabled when no application is selected
        self.assertEqual(len(form.fields['version'].queryset), 2) # check only versions for app1 (the application related to variable is present
        self.assertTrue(1 in [v.id for v in form.fields['version'].queryset])
        self.assertTrue(2 in [v.id for v in form.fields['version'].queryset])
        
    def test_variable_form_with_protected_var_and_not_authorized(self):  
        """
        Check value is not display if user is not authorized or no user defined
        """
        form = VariableForm(instance=Variable.objects.get(pk=102))
        self.assertEqual(type(form.fields['protected'].widget), type(forms.HiddenInput()))
        self.assertEqual(form.initial['value'], '****')
        
    def test_variable_form_with_protected_var_and_authorized(self):  
        """
        Check value is not display if user is not authorized or no user defined
        """
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='see_protected_var'), content_type=ct))
        
        instance = Variable.objects.get(pk=102)
        instance.user = user
        
        form = VariableForm(instance=instance)
        self.assertEqual(type(form.fields['protected'].widget), type(forms.CheckboxInput()))
        self.assertEqual(form.initial['value'], 'azertyuiop')
       
### Version filter ### 
    def test_version_filter_lookup_without_application(self):
        """
        Check that all versions of all application, where a variable exist are displayed, when no application is selected
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        version_filter = VersionFilter(request, {}, Variable, variable_admin)
        filtered_versions = version_filter.lookups(request=request, model_admin=variable_admin)
        
        # all versions of all apps are displayed if at least a variable is defined for this version
        # this explains why version 3 and 4 are not rendered
        self.assertEqual(filtered_versions, [(1, 'app1-2.4'), (2, 'app1-2.5'), (5, 'app4-1.0'), (6, 'linkedApp4-1.0'), ('_None_', 'None')])
        
    def test_version_filter_lookup_with_application(self):
        """
        Check only the versions of the selected application are displayed
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        request.GET = {'application__id__exact': 1}
        
        version_filter = VersionFilter(request, {}, Variable, variable_admin)
        filtered_versions = version_filter.lookups(request=request, model_admin=variable_admin)
        
        # only versions where a variable exist for the application app1 are returned
        self.assertEqual(filtered_versions, [(1, 'app1-2.4'), (2, 'app1-2.5'), ('_None_', 'None')])
    
    def test_version_filter_queryset_without_value(self):
        """
        Check the case where no filtering is required, all variables are returned
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        version_filter = VersionFilter(request, {}, Variable, variable_admin)
        queryset = version_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # no filtering, all variables are returned
        self.assertEqual(len(queryset), len(Variable.objects.all()))
    
    def test_version_filter_queryset_with_none_value(self):
        """
        Check the case where filtering is required with "no version"
        Only variables not linked to any version should be returned
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        version_filter = VersionFilter(request, {'version': '_None_'}, Variable, variable_admin)
        queryset = version_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), len(Variable.objects.filter(version=None)))
    
    def test_version_filter_queryset_with_value(self):
        """
        Check the case where filtering is required with version '2'
        Only variables linked to this version should be returned
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        version_filter = VersionFilter(request, {'version': 2}, Variable, variable_admin)
        queryset = version_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), len(Variable.objects.filter(version__id=2)))
    
### Environment Filter ###
    
    def test_environment_filter_lookup_without_application(self):
        """
        Check that all versions of all application, where a variable exist are displayed, when no application is selected
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        filtered_environments = environment_filter.lookups(request=request, model_admin=environment_admin)
        
        # all environments of all apps are displayed if at least a variable is defined for this environment
        self.assertEqual(filtered_environments,  [(1, 'DEV'), (2, 'ASS'), (3, 'DEV1'), ('_None_', 'None')])
        
    def test_environment_filter_lookup_with_application(self):
        """
        Check only the versions of the selected application are displayed
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        request.GET = {'application__id__exact': 1}
        
        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        filtered_environments = environment_filter.lookups(request=request, model_admin=environment_admin)
        
        # only environments where a variable exist for the application app1 are returned
        self.assertEqual(filtered_environments, [(2, 'ASS'), (3, 'DEV1'), ('_None_', 'None')])
    
    def test_environment_filter_queryset_without_value(self):
        """
        Check the case where no filtering is required, all variables are returned
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # no filtering, all variables are returned
        self.assertEqual(len(queryset), len(Variable.objects.all()))
    
    def test_environment_filter_queryset_with_none_value(self):
        """
        Check the case where filtering is required with "no version"
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        environment_filter = EnvironmentFilter(request, {'environment': '_None_'}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), len(Variable.objects.filter(environment=None)))
    
    def test_environment_filter_queryset_with_value(self):
        """
        Check the case where filtering is required with environment '1'
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        environment_filter = EnvironmentFilter(request, {'environment': 1}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), len(Variable.objects.filter(environment__id=1)))
    
    def test_environment_filter_queryset_with_invalid_value(self):
        """
        Check the case where filtering is done with invalid environment
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        
        environment_filter = EnvironmentFilter(request, {'environment': 10265}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), 0)
        
### TestCaseAdmin ###

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

### VersionAdmin ###

      
    def test_version_has_no_associated_actions(self):
        """
        Check all actions are deactivated so that deleting an application must be done from detailed view
        """

        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        self.assertIsNone(version_admin.actions)


    def test_version_fieldset_with_variables(self):
        """
        Check error message is displayed when a version has variables
        """
        version = Version.objects.get(pk=1)
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        fieldset = version_admin.get_fieldsets(request, version)
        
        self.assertEqual(len(fieldset), 1)
        self.assertEqual(fieldset[0], (None, {'fields': ('name', 'application'), 'description': '<div style="font-size: 16px;color: red;">This version will be deleted when all linked variables will be deleted</div>'}))
    
    def test_version_fieldset_without_variables(self):
        """
        Check no error message is displayed when a version has no variable
        """
        version = Version.objects.get(pk=7)
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        fieldset = version_admin.get_fieldsets(request, version)
        
        self.assertEqual(len(fieldset), 1)
        self.assertEqual(fieldset[0], (None, {'fields': ['application', 'name']}))
    
    
    def test_version_has_delete_permission_allowed_and_authenticated_without_linked_variables(self):
        """
        Check we can delete application when no variable or tests are linked to
        user:
        - is authenticated
        - can delete version
        
        no variable/test linked to this application exist
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version')))
        
        # search a version which has no variable
        version_with_variables = [v.version.id for v in Variable.objects.exclude(version=None)]
        version_no_variable = Version.objects.exclude(id__in=version_with_variables)[0]
        
        self.assertTrue(version_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.filter(pk=version_no_variable.id)[0])) # 
          
    def test_version_has_delete_permission_allowed_and_authenticated_with_linked_variables(self):
        """
        Check we cannot delete version when variable are linked to it
        user:
        - is authenticated
        - can delete version
        
        a variable linked to this application exist
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version')))
        
        # search a version which has no variable
        version_with_variables = [v.version for v in Variable.objects.exclude(version=None)][0]
        
        self.assertFalse(version_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.filter(pk=version_with_variables.id)[0])) # 'app1-2.5' has only variable linked to it
        
    def test_version_has_delete_permission_allowed_and_authenticated_none_version(self):
        """
        delete version without being allowed to
        user:
        - is authenticated
        - can delete version
        
        application is NONE
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version')))
        self.assertTrue(version_admin.has_delete_permission(request=MockRequest(user=user)))
              
    def test_version_has_delete_permission_not_allowed_and_authenticated_none_version(self):
        """
        delete version without being allowed to
        user:
        - is authenticated
        - can NOT delete version
        
        application is NONE
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_version')))
        self.assertFalse(version_admin.has_delete_permission(request=MockRequest(user=user)))
        
    def test_version_queryset_without_application_restriction(self):
        """
        Check that list of testcases contains variables for all application when restriction is not set
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        query_set = version_admin.get_queryset(request)
        
        app_list = []
        for version in query_set:
            app_list.append(version.application)
        
        self.assertTrue(len(list(set(app_list))) > 2) # at least 'None' and 2 other applications
          
    def test_version_queryset_with_application_restriction(self):
        """
        Check that list of testcases contains only variables for 'app1', the only application user is able to see
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            ct = ContentType.objects.get_for_model(commonsServer.models.Application)
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1'), content_type=ct))
            
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            query_set = version_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for version in query_set:
                app_list.append(version.application)
            
            self.assertEqual(len(list(set(app_list))), 1) # 'app1'
            self.assertTrue(Application.objects.get(pk=1) in app_list)
    
          
    def test_version_queryset_with_application_restriction_and_not_allowed(self):
        """
        Check that list of testcases is empty as user as no right to see any application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            ct = ContentType.objects.get_for_model(commonsServer.models.Application)
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable'), content_type=ct))
            
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            query_set = version_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for version in query_set:
                app_list.append(version.application)
            
            self.assertEqual(app_list, []) # no application
        