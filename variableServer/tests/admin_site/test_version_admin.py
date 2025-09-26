
from django.contrib.admin.sites import AdminSite

from django.db.models import Q

from variableServer.admin_site.version_admin import VersionFilter, VersionAdmin
from variableServer.models import Variable, Version, Application
from variableServer.admin_site.variable_admin import VariableAdmin
from variableServer.tests.test_admin import MockRequest, request, TestAdmin,\
    MockRequestWithApplication
from django.contrib.auth.models import Permission

class TestVersionAdmin(TestAdmin):
    
    def setUp(self)->None:
        TestAdmin.setUp(self)
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
    
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
        self.assertEqual(filtered_versions, [(1, 'app1-2.4'), (2, 'app1-2.5'), (3, 'app2-1.0'), (4, 'app3-1.0'), (5, 'app4-1.0'), (6, 'linkedApp4-1.0'), (7, 'app5NoVar-1.0'), ('_None_', 'None')])
        
    def test_version_filter_lookup_with_application(self):
        """
        Check only the versions of the selected application are displayed
        """
        variable_admin = VariableAdmin(model=Variable, admin_site=AdminSite())
        
        request = MockRequest()
        request.GET = {'application': 1}
        
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
        - has delete version permission
        
        no variable/test linked to this application exist
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version', content_type=self.content_type_version)))
        
        # search a version which has no variable
        version_with_variables = [v.version.id for v in Variable.objects.exclude(version=None)]
        version_no_variable = Version.objects.exclude(id__in=version_with_variables)[0]
        
        self.assertTrue(version_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.filter(pk=version_no_variable.id)[0])) # 
          
    def test_version_has_delete_permission_allowed_and_authenticated_with_linked_variables(self):
        """
        Check we cannot delete version when variable are linked to it
        user:
        - is authenticated
        - has delete version permission
        
        a variable linked to this application exist
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version', content_type=self.content_type_version)))
        
        # search a version which has no variable
        version_with_variables = [v.version for v in Variable.objects.exclude(version=None)][0]
        
        self.assertFalse(version_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.filter(pk=version_with_variables.id)[0])) # 'app1-2.5' has only variable linked to it
        
    def test_version_has_delete_permission_allowed_and_authenticated_none_version(self):
        """
        delete version 
        user:
        - is authenticated
        - has delete version permission
        
        application is NONE
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version', content_type=self.content_type_version)))
        self.assertTrue(version_admin.has_delete_permission(request=MockRequest(user=user)))
        
    def test_version_has_delete_permission_allowed_and_authenticated_with_application_restriction_and_application_permission(self):
        """
        delete version 
        user:
        - is authenticated
        - has NOT delete version permission
        - has app1 permission
        
        application is app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(version_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
        
    def test_version_has_delete_permission_allowed_and_authenticated_with_application_restriction_and_delete_permission(self):
        """
        delete version 
        user:
        - is authenticated
        - has NOT delete version permission
        - has app1 permission
        
        application is app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version', content_type=self.content_type_version)))
            self.assertTrue(version_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
        
    def test_version_has_delete_permission_allowed_and_authenticated_with_application_restriction_and_change_permission(self):
        """
        delete version 
        user:
        - is authenticated
        - has NOT delete version permission
        - has app1 permission
        
        application is app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_version', content_type=self.content_type_version)))
            self.assertFalse(version_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
              
    def test_version_has_delete_permission_not_allowed_and_authenticated_none_version(self):
        """
        delete version without being allowed to
        user:
        - is authenticated
        - has NOT delete version permission
        
        application is NONE
        """
        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_version', content_type=self.content_type_version)))
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
        Check that list of versions contains only versions for 'app1', the only application user is able to see
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            query_set = version_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for version in query_set:
                app_list.append(version.application)
            
            self.assertEqual(len(list(set(app_list))), 1) # 'app1'
            self.assertTrue(Application.objects.get(pk=1) in app_list)
    
    def test_version_queryset_with_application_restriction_and_global_view_version(self):
        """
        Check that list of versions contains versions for all application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_version', content_type=self.content_type_version)))
            
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            query_set = version_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for version in query_set:
                app_list.append(version.application)
            
            self.assertTrue(len(list(set(app_list))) > 2) # all versions should be visible
            self.assertTrue(Application.objects.get(pk=1) in app_list)
    
          
    def test_version_queryset_with_application_restriction_and_not_allowed(self):
        """
        Check that list of versions is empty as user as no right to see any application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
            
            version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            query_set = version_admin.get_queryset(request=MockRequest(user=user))
            
            app_list = []
            for version in query_set:
                app_list.append(version.application)
            
            self.assertEqual(app_list, []) # no application
            
    def test_user_can_see_versions_without_global_rights_and_application_permissions(self):
        """
        Check  user can view / change / delete / add with only application specific rights: can_view_application_app1
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            
            testcase_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1))) # version from app1
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3))) # version from app2
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1))) # cannot delete as version has linked variables
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_can_see_versions_with_application_restrictions_and_view_permission(self):
        """
        Check  user can view / change / delete / add with global view permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_version')))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_can_add_versions_with_application_restrictions_and_add_permission(self):
        """
        Check  user can view / change / delete / add with global add permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_version')))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_can_change_versions_with_application_restrictions_and_change_permission(self):
        """
        Check  user can view / change / delete / add with global change permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_version')))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertTrue(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_can_delete_versions_with_application_restrictions_and_delete_permission(self):
        """
        Check  user can view / change / delete / add with global change permission
        when application restriction are applied
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            Application.objects.get(pk=1).save()
            
            testcase_admin = VersionAdmin(model=Version, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_version')))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertFalse(testcase_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user)))
            self.assertFalse(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1))) # this version has linked variables and so cannot be deleted
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=3)))
            self.assertTrue(testcase_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
       
    def test_user_cannot_see_testcases_without_global_rights_without_application_permissions(self):
        """
        Check  user cannot view / change / delete / add with only application specific rights: can_view_application_app1
        when application restriction are NOT applied
        """
        Application.objects.get(pk=1).save()

        version_admin = VersionAdmin(model=Version, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
        self.assertFalse(version_admin.has_view_permission(request=MockRequest(user=user)))
        self.assertFalse(version_admin.has_view_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
        self.assertFalse(version_admin.has_add_permission(request=MockRequest(user=user)))
        self.assertFalse(version_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
        self.assertFalse(version_admin.has_change_permission(request=MockRequest(user=user)))
        self.assertFalse(version_admin.has_change_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
        self.assertFalse(version_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
        self.assertFalse(version_admin.has_delete_permission(request=MockRequest(user=user)))
        self.assertFalse(version_admin.has_delete_permission(request=MockRequest(user=user), obj=Version.objects.get(pk=1)))
        self.assertFalse(version_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
        