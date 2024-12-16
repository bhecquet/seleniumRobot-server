
from django.contrib.admin.sites import AdminSite
from django.test.testcases import TestCase

from django.db.models import Q

from variableServer.admin_site.version_admin import VersionFilter, VersionAdmin
from variableServer.models import Variable, Version, Application
from variableServer.admin_site.variable_admin import VariableAdmin
from variableServer.tests.test_admin import MockRequest, request
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import commonsServer

class TestVersionAdmin(TestCase):
    
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
        