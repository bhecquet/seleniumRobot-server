
from django.test.testcases import TestCase
from snapshotServer.admin import StepReferenceAdmin, TestCaseFilter
from snapshotServer.models import StepReference
from django.contrib.admin.sites import AdminSite
   
class MockRequest(object):
    def __init__(self, user=None):
        self.user = user
        self.method = 'GET'
        self.GET = {}
        
    
class TestAdmin(TestCase):
    
    fixtures = ['snapshotServer.yaml']
    
    
    def test_test_case_filter_lookup_without_application(self):
        """
        Check that all test cases that are recorded in a step reference are displayed
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        
        test_case_filter = TestCaseFilter(request, {}, StepReference, step_reference_admin)
        filtered_test_cases = test_case_filter.lookups(request=request, model_admin=step_reference_admin)
        
        # only test cases that are included in a step reference will be displayed
        self.assertEqual(filtered_test_cases, [(1, 'test1 - myapp'), (5, 'test1app2 - myapp2')])
        
    def test_test_case_filter_lookup_with_application(self):
        """
        Check only the versions of the selected application are displayed
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        request.GET = {'version__application': 1}
        
        test_case_filter = TestCaseFilter(request, {}, StepReference, step_reference_admin)
        filtered_test_cases = test_case_filter.lookups(request=request, model_admin=step_reference_admin)
        
        # only test cases where a step reference exist for the application app1 are returned
        self.assertEqual(filtered_test_cases, [(1, 'test1 - myapp')])
    
    def test_test_case_filter_queryset_without_value(self):
        """
        Check the case where no filtering is required, all variables are returned
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        
        test_case_filter = TestCaseFilter(request, {}, StepReference, step_reference_admin)
        queryset = test_case_filter.queryset(request=request, queryset=StepReference.objects.all())
        
        # no filtering, no step result returned to avoid loading many images
        self.assertEqual(len(queryset), len(StepReference.objects.none()))
    
    def test_test_case_filter_queryset_with_value(self):
        """
        Check the case where filtering is required with version '2'
        Only variables linked to this version should be returned
        """
        step_reference_admin = StepReferenceAdmin(model=StepReference, admin_site=AdminSite())
        
        request = MockRequest()
        
        test_case_filter = TestCaseFilter(request, {'test_case_id': 5}, StepReference, step_reference_admin)
        queryset = test_case_filter.queryset(request=request, queryset=StepReference.objects.all())
        
        # check only variables without version are displayed
        self.assertEqual(len(queryset), len(StepReference.objects.filter(stepResult__testCase__testCase__id=5)))