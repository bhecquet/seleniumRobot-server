'''
Created on 28 mars 2018

@author: s047432
'''
from django.test.testcases import TestCase
from variableServer.admin import ApplicationAdmin, VariableAdmin, is_user_authorized
from commonsServer.models import Application, Version
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Permission, Group
from variableServer.models import Variable
from django.test.client import Client
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

import variableServer
import commonsServer
from django.urls.base import reverse
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
import re

from django.utils import timezone
import datetime

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
        
        return user, client
    
    def _format_content(self, content):
        return re.sub('>\s+<', '><', str(content).replace('\\n', ''))
        
    
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
        self.assertEquals(variable_admin.get_list_display(request=MockRequest(user=super_user)), ('nameWithApp', 'value', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate'))
        
        
    def test_variable_get_list_display_with_unauthorized_user(self):
        """
        Check protected variable values are not displayed with disallowed user
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        self.assertEquals(variable_admin.get_list_display(request=MockRequest(user=user)), ('nameWithApp', 'valueProtected', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate'))
        
    def test_variable_qeryset_without_application_restriction(self):
        """
        Check that list of variables contains variables for all application when restriction is not set
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        query_set = variable_admin.get_queryset(request)
        
        app_list = []
        for var in query_set:
            app_list.append(var.application)
        
        self.assertTrue(len(list(set(app_list))), 2) # at least 'None' and 2 other applications
        
       
    def test_variable_qeryset_with_application_restriction(self):
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
        user.is_staff = True
        user.save()

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'copyTo',
                'index': '0',}
        response = client.post(change_url, data)
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
     
    def test_variable_copy_to(self):
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))
        user.is_staff = True
        user.save()

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
        self.assertEqual(default_values['reservable'], False)
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
        user.is_staff = True
        user.save()

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'changeValuesAtOnce',
                'index': '0',}
        response = client.post(change_url, data)
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
     
    def test_variable_change(self):
        
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))
        user.is_staff = True
        user.save()

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
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable'), content_type=ct))
        user.is_staff = True
        user.save()

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
            user.is_staff = True
            user.save()
            
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
                Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable') | Q(codename='can_view_application_app1')))

            user.is_staff = True
            user.save()
            
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
        user.is_staff = True
        user.save()
        
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
        
        
        
            
            
            
            
            
        