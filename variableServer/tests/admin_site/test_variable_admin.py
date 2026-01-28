import datetime
import os.path

from django import forms
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q
from django.test import override_settings
from django.urls.base import reverse
from django.utils import timezone

from variableServer.admin_site.variable_admin import VariableAdmin, VariableForm
from variableServer.models import Application, Version
from variableServer.models import Variable
from variableServer.tests.test_admin import MockRequest, request, TestAdmin, \
    MockRequestWithApplication


@override_settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=False)
class TestVariableAdmin(TestAdmin):
    
    def setUp(self)->None:
        TestAdmin.setUp(self)
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        

    def test_variable_get_list_display_with_authorized_user(self):
        """
        Check variable values are displayed even protected value with allowed user
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        super_user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertEqual(variable_admin.get_list_display(request=MockRequest(user=super_user)), ('nameWithApp', 'value', 'uploadFileReforged', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate'))
        
        
    def test_variable_get_list_display_with_unauthorized_user(self):
        """
        Check protected variable values are not displayed with disallowed user
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        self.assertEqual(variable_admin.get_list_display(request=MockRequest(user=user)), ('nameWithApp', 'valueProtected', 'uploadFileReforged', 'application', 'environment', 'version', 'allTests', 'reservable', 'releaseDate', 'creationDate'))
        
    def test_variable_queryset_without_application_restriction(self):
        """
        Check that list of variables contains variables for all application when restriction is not set
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        query_set = variable_admin.get_queryset(request)
        
        app_list = []
        for var in query_set:
            app_list.append(var.application)
        
        self.assertTrue(len(list(set(app_list))), 6) # at least 'None' and 2 other applications
        
       
    def test_variable_queryset_with_application_restriction(self):
        """
        Check that list of variables contains only variables for 'app1', the only application user is able to see
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            
            variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            query_set = variable_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for var in query_set:
                app_list.append(var.application)
            
            self.assertEqual(len(list(set(app_list))), 1) # 'None' and 'app1'
            self.assertTrue(Application.objects.get(pk=1) in app_list)
        
    def test_variable_queryset_with_application_restriction_and_view_variable_permission(self):
        """
        Check that list of variables contains all variables when 'view_variable' permission is set
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
            
            variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            query_set = variable_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for var in query_set:
                app_list.append(var.application)
            
            self.assertEqual(len(list(set(app_list))), 7)
        
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

    def test_variable_save_standard_with_file(self):
        """
        Check saving is done with a file
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        variable = Variable.objects.get(pk=666)

        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        variable_admin.save_model(obj=variable, request=MockRequest(user=user), form=None, change=None)
        self.assertEqual(Variable.objects.get(pk=666).value, '')
        self.assertEqual(Variable.objects.get(pk=666).uploadFile, 'http://127.0.0.1:8000/media/varAppFile/fauxfile.xlsx')

    def test_variable_clean_no_concurrent_file_value(self):
        """
        Check that you can't save a variable with both a file and a value
        """
        form = VariableForm(instance=Variable.objects.get(pk=999))
        form.cleaned_data = {"name": "both", "value": "filetxt", "uploadFile": "itssupposedtobeafilebutaslongasitsnotnullitsokforthetest"}
        self.assertRaisesRegex(ValidationError, ".*A variable can't be both a value and a file. Choose only one..*", form.clean)

    def test_variable_clean_file_wrong_type(self):
        """
        Check that you can't save a variable with a file type other than csv, xls, json
        """
        file_path = 'variableServer/tests/data/engie.png'
        with open(file_path, 'rb') as f:
            in_memory_uploaded_file = InMemoryUploadedFile(f, 'uploadFile', 'engie.png', 'application/png', os.path.getsize(file_path), None)
            form = VariableForm(data={'name': 'foo'}, files={'uploadFile': in_memory_uploaded_file})
            self.assertFalse(form.is_valid())
            self.assertRaisesRegex(ValidationError, ".*is an unsupported file type. Please, select csv, xls or json file..*", form.clean)

    def test_variable_clean_file_wrong_type_txt(self):
        """
        Check that you can't save a variable with a file type other than csv, xls, json
        """
        file_path = 'variableServer/tests/data/dummy.txt'
        with open(file_path, 'rb') as f:
            in_memory_uploaded_file = InMemoryUploadedFile(f, 'uploadFile', 'dummy.txt', 'text/plain', os.path.getsize(file_path), None)
            form = VariableForm(data={'name': 'foo'}, files={'uploadFile': in_memory_uploaded_file})
            self.assertFalse(form.is_valid())
            self.assertRaisesRegex(ValidationError, ".*is an unsupported file type. Please, select csv, xls or json file..*", form.clean)

    def test_variable_clean_file_too_large(self):
        """
        Check that you can't save a variable with a file larger than 10Mo
        """
        file_path = 'variableServer/tests/data/toobig.csv'
        with open(file_path, 'rb') as f:
            in_memory_uploaded_file = InMemoryUploadedFile(f, 'uploadFile', 'toobig.csv', 'text/csv', os.path.getsize(file_path), None)
            form = VariableForm(data={'name': 'foo'}, files={'uploadFile': in_memory_uploaded_file})
            self.assertFalse(form.is_valid())
            self.assertRaisesRegex(ValidationError, ".*File too large. 10Mo max.*", form.clean)

    def test_variable_save_protected_variable_with_authorized_user(self):
        """
        Check value is modified when user has the right to do
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        variable = Variable.objects.get(pk=102)
        self.assertTrue(variable.protected) # check variable is protected
        variable.value = 'azerty'
        variable.protected = False
   
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='see_protected_var')))
        
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
        """
        Test copy when no source variable is provided
        """
        
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'copy_to',
                'index': '0',}
        response = client.post(change_url, data)
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
     
    def _test_variable_copy_to(self, permissions, variable_ids):
        """
        Test variable copy
        @param permissions: permissions given to user
        @param variable_ids: ids of variables to copy
        """
        
        user, client = self._create_and_authenticate_user_with_permissions(permissions)

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'copy_to',
                ACTION_CHECKBOX_NAME: variable_ids,
                'index': '0',}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        return content
     
    def test_variable_copy_to(self):
        """
        Test copy variable with all permissions
        """
        content = self._test_variable_copy_to(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')), [3, 4])

        self.assertTrue('<form action="/variable/copyVariables" method="post">' in content)
        self.assertTrue('<option value="1" selected>app1</option>' in content) # check 'app1' is already selected as both variables have the same application
        self.assertTrue('Version:</label><select name="version" id="id_version"><option value="" selected>---------</option>' in content) # check no version is selected as variables have the same
        
    def test_variable_copy_to_no_add_variable(self):
        """
        Test it's not possible to copy variable if 'add_variable' permission is not given to user
        """
        content = self._test_variable_copy_to(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable')), [3, 4])

        self.assertTrue('<form action="/variable/copyVariables" method="post">' in content)
        self.assertTrue('<select name="application" id="id_application"><option value="" selected>' in content) # no app selected
        self.assertTrue('<select name="version" id="id_version"><option value="" selected>' in content) # check no version is selected 
       
    def test_variable_copy_to_multiple_application(self):
        """
        Check it's possible to copy multiple variables when global variable permission are given to user
        """
        content = self._test_variable_copy_to(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')), [3, 4, 9, 10])
        
        self.assertTrue('<input type="hidden" name="ids" value=3,4,9,10 />' in content) # check 4 variables will be copied
     
    def test_variable_copy_to_with_application_restrictions(self):
        """
        Check it's possible to copy multiple variables when application specific permission is set 
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            content = self._test_variable_copy_to(Permission.objects.filter(Q(codename='can_view_application_app1')), [3, 4, 9, 10]) # 3 & 4: app1; 9: no app; 10: app3, 
        
            self.assertTrue('<input type="hidden" name="ids" value=3,4 />' in content) # check both variables will be copied
     
    def test_variable_copy_to_with_application_restrictions_and_global_change_variable(self):
        """
        Check it's possible to copy multiple variables when application specific permission is set and add_variable permission is given to user
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            content = self._test_variable_copy_to(Permission.objects.filter(Q(codename='add_variable') | Q(codename='view_variable')), [3, 4, 9, 10]) # 3 & 4: app1; 9: no app; 10: app3,

            self.assertTrue('<input type="hidden" name="ids" value=3,4,9,10 />' in content) # check both variables will be copied
     
    def test_variable_copy_to_with_application_restrictions_and_without_global_add_variable(self):
        """
        Check it's NOT possible to copy multiple variables when application specific permission is set and change_variable permission is given to user
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            content = self._test_variable_copy_to(Permission.objects.filter(Q(codename='change_variable')), [4, 9, 10]) # 4: app1; 9: no app; 10: app3,  

            self.assertTrue('<input type="hidden" name="ids" value= />' in content) # check no variable is kept => no permissions

     
    def test_variable_copy_to_with_application_restrictions_on_variable_from_other_application(self):
        """
        Check it's not possible to copy multiple variables when application specific permission is set and variable is not linked to that application
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            content = self._test_variable_copy_to(Permission.objects.filter(Q(codename='can_view_application_app1')), [4, 9, 10]) # 4: app1; 9: no app; 10: app3,  

            self.assertTrue('<input type="hidden" name="ids" value=4 />' in content) # check only variable which is associated to application 1 is kept
        
    def test_variable_get_default_values_single_variable(self):
        """
        Check default values are the one from the variable
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        default_values = variable_admin._get_default_values([7])
        
        self.assertEqual(default_values['environment'].name, 'DEV1')
        self.assertEqual(default_values['application'].name, 'app1')
        self.assertEqual(default_values['version'].name, '2.5')
        self.assertTrue(default_values['reservable'])
        self.assertEqual(len(default_values['test'].all()), 1)
        
    def test_variable_get_default_values_no_variables(self):
        """
        Check default values are the one from the variable
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        default_values = variable_admin._get_default_values([])
        
        self.assertIsNone(default_values['environment'])
        self.assertIsNone(default_values['application'])
        self.assertIsNone(default_values['version'])
        self.assertFalse(default_values['reservable'])
        self.assertIsNone(default_values['test'])
        
    def test_variable_get_default_values_multiple_variables(self):
        """
        Check default values are the one common to first variable and others
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        default_values = variable_admin._get_default_values([7, 8])
        
        self.assertEqual(default_values['environment'].name, 'DEV1')
        self.assertEqual(default_values['application'].name, 'app1')
        self.assertEqual(default_values['version'], None)
        self.assertFalse(default_values['reservable'])
        self.assertEqual(default_values['test'], None)
       
    def _test_variable_deletion(self, permissions, variable_id):
        """
        Test variable deletion
        @param permissions: permissions given to user
        @param variable_id: id of the variable to delete
        """
        
        user, client = self._create_and_authenticate_user_with_permissions(permissions)

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'delete_selected',
                'index': '0',
                ACTION_CHECKBOX_NAME: [variable_id]}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        
        return content
     
    def test_variable_delete_selected_no_restriction(self):
        """
        Check that we can delete selected variable if no restriction applies on applications
        """
        content = self._test_variable_deletion(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable') | Q(codename='delete_variable')), 3)
       
        self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
        self.assertTrue('<li>Variable: <a href="/admin/variableServer/variable/3/change/">appName</a></li></ul>' in content) # variable 'appName' is ready to be deleted
     
    def test_variable_delete_selected_no_restriction_no_delete_permission(self):
        """
        Check that we can NOT delete selected variable if delete_variable is not given to user
        """
        content = self._test_variable_deletion(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')), 3)
       
        self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
        self.assertTrue('<h2>Objects</h2><ul></ul>' in content) # no variable can be deleted
     
    def test_variable_delete_selected_with_restriction_and_no_delete_permission(self):
        """
        Check that we cannot delete selected variable when 'delete_variable' is not set
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            content = self._test_variable_deletion(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')), 3)
       
            self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
            self.assertTrue('<h2>Objects</h2><ul></ul>' in content) # no variable can be deleted
     
    def test_variable_delete_selected_with_restriction_and_delete_permission(self):
        """
        Check that we can NOT delete selected variable as restriction apply on this application but global variable permission are given
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            content = self._test_variable_deletion(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable') | Q(codename='delete_variable')), 3)
       
            self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
            self.assertTrue('<li>Variable: <a href="/admin/variableServer/variable/3/change/">appName</a></li></ul>' in content) # variable 'appName' is ready to be deleted
     
    def test_variable_delete_selected_with_application_restrictions_and_app1_permission(self):
        """
        Check that we can delete selected variable as user has right to use this application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            content = self._test_variable_deletion(Permission.objects.filter(Q(codename='can_view_application_app1')), 3)
       
            self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
            self.assertTrue('<li>Variable: <a href="/admin/variableServer/variable/3/change/">appName</a></li></ul>' in content) # variable 'appName' is ready to be deleted
            
    def test_variable_delete_with_restriction_and_no_linked_application(self):
        """
        Check that we cannot delete variable without linked application when application specific permission is the only available
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            content = self._test_variable_deletion(Permission.objects.filter(Q(codename='can_view_application_app1')), 9)
       
            self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
            self.assertTrue('<h2>Objects</h2><ul></ul>' in content) # no variable can be deleted
            
     
    def test_variable_delete_selected_with_restriction_and_other_application_permission(self):
        """
        Check that we cannot delete selected variable if variable does not belong to the application user has permissions for
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            content = self._test_variable_deletion(Permission.objects.filter(Q(codename='can_view_application_app1')), 301)

            self.assertTrue('<title>Are you sure? | Django site admin</title>' in content) # variable is ready to be deleted
            self.assertTrue('<h2>Objects</h2><ul></ul>' in content) # no variable can be deleted
            
     
    def _test_variable_unreserve(self, permissions, app_of_application):
        
        user, client = self._create_and_authenticate_user_with_permissions(permissions)
        
        # reserve variable
        reservable_var = Variable(name='var1', value='value1', application=app_of_application, version=Version.objects.get(pk=1), releaseDate=timezone.now() + datetime.timedelta(seconds=60))
        reservable_var.save()

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'unreserve_variable',
                'index': '0',
                ACTION_CHECKBOX_NAME: [reservable_var.id]}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
        self.assertEqual(response.url, '/admin/variableServer/variable/')
        
        return reservable_var
     
    def test_variable_unreserve(self):
        """
        Check it's possible to unreserve a variable when global variable permission are given to user
        """
        reservable_var = self._test_variable_unreserve(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')), Application.objects.get(pk=1))
        
        self.assertIsNone(Variable.objects.get(pk=reservable_var.id).releaseDate)
     
    def test_variable_unreserve_no_change_permission(self):
        """
        Check it's possible to unreserve a variable when global variable permission are given to user
        """
        reservable_var = self._test_variable_unreserve(Permission.objects.filter(Q(codename='view_variable') | Q(codename='add_variable')), Application.objects.get(pk=1))
        
        self.assertIsNotNone(Variable.objects.get(pk=reservable_var.id).releaseDate)
     
    def test_variable_unreserve_with_application_restrictions(self):
        """
        Check it's possible to unreserve a variable when application specific permission is set 
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            reservable_var = self._test_variable_unreserve(Permission.objects.filter(Q(codename='can_view_application_app1')), Application.objects.get(pk=1))
        
            self.assertIsNone(Variable.objects.get(pk=reservable_var.id).releaseDate)
     
    def test_variable_unreserve_with_application_restrictions_and_global_change_variable(self):
        """
        Check it's possible to unreserve a variable when application specific permission is set and change_variable permission is given to user
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            reservable_var = self._test_variable_unreserve(Permission.objects.filter(Q(codename='change_variable')), Application.objects.get(pk=1))

            self.assertIsNone(Variable.objects.get(pk=reservable_var.id).releaseDate)
     
    def test_variable_unreserve_with_application_restrictions_and_without_global_change_variable(self):
        """
        Check it's possible to unreserve a variable when application specific permission is set and change_variable permission is given to user
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        
            # reserve variable
            reservable_var = Variable(name='var1', value='value1', application=Application.objects.get(pk=1), version=Version.objects.get(pk=1), releaseDate=timezone.now() + datetime.timedelta(seconds=60))
            reservable_var.save()
    
            change_url = reverse('admin:variableServer_variable_changelist')
            data = {'action': 'unreserve_variable',
                    'index': '0',
                    ACTION_CHECKBOX_NAME: [reservable_var.id]}
            response = client.post(change_url, data)
            content = self._format_content(response.content)
            
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))

            self.assertIsNotNone(Variable.objects.get(pk=reservable_var.id).releaseDate)
     
    def test_variable_unreserve_with_application_restrictions_on_variable_from_other_application(self):
        """
        Check it's not possible to unreserve a variable when application specific permission is set and variable is not linked to that application
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            reservable_var = self._test_variable_unreserve(Permission.objects.filter(Q(codename='can_view_application_app1')), Application.objects.get(pk=2))

            # check variables are not updated when we have no rights on them
            self.assertIsNotNone(Variable.objects.get(pk=reservable_var.id).releaseDate)
            
        
    def _test_variable_change_values_at_once(self, permissions, variable_ids):
        
        user, client = self._create_and_authenticate_user_with_permissions(permissions)

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'change_values_at_once',
                'index': '0',
                ACTION_CHECKBOX_NAME: variable_ids}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
        
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
        self.assertTrue('<form action="/variable/changeVariables" method="post">' in content)
        
        return content
    
    def test_variable_change_no_variables(self):
        """
        Check modify of variable information when there is no source variable
        """
        
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'change_values_at_once',
                'index': '0',}
        response = client.post(change_url, data)
        self.assertEqual(response.status_code, 302, 'status code should be 302: ' + str(response.content))
     

    def test_variable_change_values_at_once(self):
        """
        Check it's possible to change multiple variables when global variable permission are given to user
        """
        content = self._test_variable_change_values_at_once(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')), [3, 4])
        
        self.assertTrue('<option value="1" selected>app1</option>' in content) # check 'app1' is already selected as both variables have the same application
        self.assertTrue('Version:</label><select name="version" id="id_version"><option value="" selected>---------</option>' in content) # check no version is selected as variables have the the same
        self.assertTrue('<input type="hidden" name="ids" value=3,4 />' in content) # check both variables will be modified

    def test_variable_change_values_at_once_no_change_permission(self):
        """
        Check it's not possible to change multiple variables when global change variable permission are NOT given to user
        """
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))

        change_url = reverse('admin:variableServer_variable_changelist')
        data = {'action': 'change_values_at_once',
                'index': '0',
                ACTION_CHECKBOX_NAME: [3, 4]}
        response = client.post(change_url, data)
        content = self._format_content(response.content)
    
        self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))
     
    def test_variable_change_values_at_once_multiple_application(self):
        """
        Check it's possible to change multiple variables when global variable permission are given to user
        """
        content = self._test_variable_change_values_at_once(Permission.objects.filter(Q(codename='view_variable') | Q(codename='change_variable') | Q(codename='add_variable')), [3, 4, 9, 10])
        
        self.assertTrue('<input type="hidden" name="ids" value=3,4,9,10 />' in content) # check 4 variables will be modified
     
    def test_variable_change_values_at_once_with_application_restrictions(self):
        """
        Check it's possible to change multiple variables when application specific permission is set 
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            content = self._test_variable_change_values_at_once(Permission.objects.filter(Q(codename='can_view_application_app1')), [3, 4, 9, 10]) # 3 & 4: app1; 9: no app; 10: app3, 
        
            self.assertTrue('<input type="hidden" name="ids" value=3,4 />' in content) # check both variables will be modified
     
    def test_variable_change_values_at_once_with_application_restrictions_and_global_change_variable(self):
        """
        Check it's possible to change multiple variables when application specific permission is set and change_variable permission is given to user
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            content = self._test_variable_change_values_at_once(Permission.objects.filter(Q(codename='change_variable')), [3, 4, 9, 10]) # 3 & 4: app1; 9: no app; 10: app3,

            self.assertTrue('<input type="hidden" name="ids" value=3,4,9,10 />' in content) # check both variables will be modified
     
    def test_variable_change_values_at_once_with_application_restrictions_and_without_global_change_variable(self):
        """
        Check it's possible to change multiple variables when application specific permission is set and change_variable permission is given to user
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))

            change_url = reverse('admin:variableServer_variable_changelist')
            data = {'action': 'change_values_at_once',
                    'index': '0',
                    ACTION_CHECKBOX_NAME: [3, 4]}
            response = client.post(change_url, data)
            content = self._format_content(response.content)
        
            self.assertEqual(response.status_code, 403, 'status code should be 403: ' + str(response.content))

     
    def test_variable_change_values_at_once_with_application_restrictions_on_variable_from_other_application(self):
        """
        Check it's not possible to change multiple variables when application specific permission is set and variable is not linked to that application
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            content = self._test_variable_change_values_at_once(Permission.objects.filter(Q(codename='can_view_application_app1')), [4, 9, 10]) # 4: app1; 9: no app; 10: app3,  

            self.assertTrue('<input type="hidden" name="ids" value=4 />' in content) # check only variable which is associated to application 1 is kept
        
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
        Check that if application defined for the variable, fields "version" and "test" are enabled
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
        
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='see_protected_var')))
        
        instance = Variable.objects.get(pk=102)
        instance.user = user
        
        form = VariableForm(instance=instance)
        self.assertEqual(type(form.fields['protected'].widget), type(forms.CheckboxInput()))
        self.assertEqual(form.initial['value'], 'azertyuiop')
        
    
       
    def test_user_can_see_variables_without_global_rights_and_application_permissions(self):
        """
        Check  user can view / change / delete / add variable with only application specific rights: can_view_application_app1
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):

            variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(variable_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertTrue(variable_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(variable_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=301)))
            self.assertTrue(variable_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertTrue(variable_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(variable_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertTrue(variable_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(variable_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=301)))
            self.assertTrue(variable_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(variable_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertTrue(variable_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(variable_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=301)))
            self.assertTrue(variable_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
           
    def test_user_can_see_variables_with_application_restrictions_and_view_permission(self):
        """
        Check  user can view / change / delete / add with global view permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_can_add_variables_with_application_restrictions_and_add_permission(self):
        """
        Check  user can view / change / delete / add with global add permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_can_change_variables_with_application_restrictions_and_change_permission(self):
        """
        Check  user can view / change / delete / add with global change permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_can_delete_variables_with_application_restrictions_and_delete_permission(self):
        """
        Check  user can view / change / delete / add with global change permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_cannot_see_testcases_without_global_rights_without_application_permissions(self):
        """
        Check  user cannot view / change / delete / add variable with only application specific rights: can_view_application_app1
        when application restriction are NOT applied
        """
        testcase_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
        self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
        self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
        self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
        self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
        self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
        self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
        self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))