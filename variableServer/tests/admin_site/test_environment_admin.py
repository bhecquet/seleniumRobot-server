
from django.contrib.admin.sites import AdminSite

from django.test.testcases import TestCase


from variableServer.models import Variable
from variableServer.admin_site.variable_admin import VariableAdmin
from variableServer.tests.test_admin import MockRequest
from variableServer.admin_site.environment_admin import EnvironmentFilter

class TestEnvironmentAdmin(TestCase):
    
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