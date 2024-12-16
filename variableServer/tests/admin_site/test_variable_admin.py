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
from variableServer.admin_site.variable_admin import VariableAdmin
from variableServer.models import Variable
from variableServer.tests.test_admin import MockRequest, request


class TestVariableAdmin(TestCase):

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
        
### Variable Form ###
        
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