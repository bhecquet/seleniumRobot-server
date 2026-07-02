
from django.contrib.admin.sites import AdminSite

from commonsServer.tests.test_parent import TestWebAndAdmin, MockRequest, MockSuperUser
from variableServer.models import Variable, TestEnvironment, Application
from variableServer.admin_site.variable_admin import VariableAdmin
from commonsServer.admin_site.environment_admin import EnvironmentFilter,\
    EnvironmentAdmin
from django.contrib.auth.models import Permission
from django.db.models import Q

class TestEnvironmentAdmin(TestWebAndAdmin):

    fixtures = ['varServer']
    
    def test_environment_filter_lookup_without_application(self):
        """
        Check that all versions of all application, where a variable exist are displayed, when no application is selected
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testenvironment')))
        request = MockRequest(user=user)
        
        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        filtered_environments = environment_filter.lookups(request=request, model_admin=environment_admin)
        
        # all environments are displayed
        self.assertEqual(filtered_environments,  [(2, 'ASS'), (1, 'DEV'), (3, 'DEV1'), (4, 'DEV2'), ('_None_', 'None')])
        
    def test_environment_filter_lookup_with_application(self):
        """
        Check only the environments of the selected application are displayed
        """
        Application.objects.get(pk=1).save()
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
        request = MockRequest(user=user)
        request.GET = {'application': 1}
        
        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        filtered_environments = environment_filter.lookups(request=request, model_admin=environment_admin)
        
        # only environments where a variable exist for the application app1 are returned
        self.assertEqual(filtered_environments, [(2, 'ASS'), (1, 'DEV'), (3, 'DEV1'), ('_None_', 'None')])
    
    def test_environment_filter_queryset_without_value(self):
        """
        Check the case where no filtering is required, all variables are returned
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testenvironment')))
        request = MockRequest(user=user)
        
        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # no filtering, all variables are returned
        self.assertEqual(len(queryset), len(Variable.objects.all()))
    
    def test_environment_filter_queryset_with_none_value(self):
        """
        Check the case where filtering is required with "no version"
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testenvironment')))
        request = MockRequest(user=user)
        
        environment_filter = EnvironmentFilter(request, {'environment': ['_None_']}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), len(Variable.objects.filter(environment=None)))
    
    def test_environment_filter_queryset_with_value(self):
        """
        Check the case where filtering is required with environment '1'
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testenvironment')))
        request = MockRequest(user=user)
        
        environment_filter = EnvironmentFilter(request, {'environment': [1]}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), len(Variable.objects.filter(environment__id=1)))
    
    def test_environment_filter_queryset_with_invalid_value(self):
        """
        Check the case where filtering is done with invalid environment
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testenvironment')))
        request = MockRequest(user=user)
        
        environment_filter = EnvironmentFilter(request, {'environment': [10265]}, Variable, environment_admin)
        queryset = environment_filter.queryset(request=request, queryset=Variable.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), 0)
        
       
    def test_environment_filter_lookup_with_allowed_environments(self):
        """
        Check that a user without global nor application permission only sees the environments
        he has specific rights on (here 'DEV'), when no application is selected
        """
        # make sure the environment specific permission 'can_view_environment_DEV' exists
        TestEnvironment.objects.get(pk=1).save()

        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_environment_DEV')))
        request = MockRequest(user=user)

        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        filtered_environments = environment_filter.lookups(request=request, model_admin=environment_admin)

        # only the environment the user has specific rights on is displayed
        self.assertEqual(filtered_environments, [(1, 'DEV'), ('_None_', 'None')])

    def test_environment_filter_lookup_with_application_and_allowed_environments(self):
        """
        Check that a user without global nor application permission only sees the environments
        he has specific rights on, restricted to the environments of the selected application
        """
        # make sure the environment specific permission 'can_view_environment_DEV' exists
        TestEnvironment.objects.get(pk=1).save()

        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_environment_DEV')))
        request = MockRequest(user=user)
        request.GET = {'application': 1}

        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        filtered_environments = environment_filter.lookups(request=request, model_admin=environment_admin)

        # among the environments of app1 (ASS, DEV, DEV1), only 'DEV' is allowed for the user
        self.assertEqual(filtered_environments, [(1, 'DEV'), ('_None_', 'None')])

    def test_environment_filter_lookup_without_allowed_environments(self):
        """
        Check that a user without any permission (global, application or environment) sees no environment
        """
        environment_admin = VariableAdmin(model=Variable, admin_site=AdminSite())

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.none())
        request = MockRequest(user=user)

        environment_filter = EnvironmentFilter(request, {}, Variable, environment_admin)
        filtered_environments = environment_filter.lookups(request=request, model_admin=environment_admin)

        # no environment allowed, only the 'None' entry is displayed
        self.assertEqual(filtered_environments, [('_None_', 'None')])

    def test_user_cannot_see_environments_without_global_rights(self):
        """
        Check  user cannot list environment with only application specific rights: can_view_application_app1
        """
        environment_admin = EnvironmentAdmin(model=TestEnvironment, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
        self.assertFalse(environment_admin.has_view_permission(request=MockRequest(user=user)))
        self.assertFalse(environment_admin.has_view_permission(request=MockRequest(user=user), obj=TestEnvironment.objects.get(pk=1)))
        self.assertFalse(environment_admin.has_add_permission(request=MockRequest(user=user)))
        self.assertFalse(environment_admin.has_change_permission(request=MockRequest(user=user)))
        self.assertFalse(environment_admin.has_delete_permission(request=MockRequest(user=user)))