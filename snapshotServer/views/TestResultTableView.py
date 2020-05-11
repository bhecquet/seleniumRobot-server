'''
Created on 1 août 2017

@author: worm
'''
from django.views.generic.base import TemplateView
from snapshotServer.models import Version, TestSession, TestEnvironment,\
    TestCaseInSession, TestCase
from snapshotServer.views.ApplicationVersionListView import ApplicationVersionListView
from datetime import datetime, timedelta
from django.shortcuts import render
import pytz
from snapshotServer.views.LoginRequiredMixinConditional import LoginRequiredMixinConditional

class TestResultTableView(LoginRequiredMixinConditional, TemplateView):
    """
    View displaying a table with results of all tests for the sessions selected by user
    """
    
    template_name = "snapshotServer/testResults.html"

    def get(self, request, version_id):
        try:
            Version.objects.get(pk=version_id)
        except:
            return render(request, ApplicationVersionListView.template_name, {'error': "Application version %s does not exist" % version_id})
        
        return super(TestResultTableView, self).get(request, version_id)
    
    def get_context_data(self, **kwargs):
        
        context = super(TestResultTableView, self).get_context_data(**kwargs)
        
        sessions = TestSession.objects.filter(version=self.kwargs['version_id'])

        context['browsers'] = list(set([s.browser for s in TestSession.objects.all()]))
        
        # by default, select all browsers
        context['selectedBrowser'] = self.request.GET.getlist('browser', context['browsers'])
        sessions = sessions.filter(browser__in=context['selectedBrowser'])
        
        context['environments'] = TestEnvironment.objects.all()
        context['selectedEnvironments'] = TestEnvironment.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('environment', [])])
        sessions = sessions.filter(environment__in=context['selectedEnvironments'])
        
        # build the list of TestCase objects which can be selected by user
        context['test_cases'] = list(set([tcs.testCase for tcs in TestCaseInSession.objects.filter(session__version=self.kwargs['version_id'])]))
        
        # by default, select all test cases
        if 'testcase' not in self.request.GET:
            context['selectedTestCases'] = context['test_cases']
        else:
            context['selectedTestCases'] = TestCase.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('testcase')])
            
        sessions = sessions.filter(testcaseinsession__testCase__in=context['selectedTestCases'])
        
        context['sessionFrom'] = self.request.GET.get('sessionFrom', (datetime.now() - timedelta(days=15)).strftime('%d-%m-%Y'))
        session_from_date = datetime.strptime(context['sessionFrom'], '%d-%m-%Y')
        sessions = sessions.filter(date__gte=datetime(session_from_date.year, session_from_date.month, session_from_date.day, tzinfo=pytz.UTC))
            
        context['sessionTo'] = self.request.GET.get('sessionTo', datetime.now().strftime('%d-%m-%Y'))
        session_to_date = datetime.strptime(context['sessionTo'], '%d-%m-%Y')
        sessions = sessions.filter(date__lte=datetime(session_to_date.year, session_to_date.month, session_to_date.day, tzinfo=pytz.UTC))
        
        # filter session according to request parameters
        context['sessions'] = sessions
        
        # get all TestCaseInSession associated to these sessions
        test_case_in_sessions = TestCaseInSession.objects.filter(session__in=sessions)
        test_cases = list(set([tcs.testCase for tcs in test_case_in_sessions]))
        
        test_case_table = {}
        for test_case in test_cases:
            test_case_table[test_case] = []
            sessions_for_test_case = [tcs.session for tcs in test_case_in_sessions.filter(testCase=test_case)]
            for session in sessions:
                if session in sessions_for_test_case:
                    tcs = TestCaseInSession.objects.filter(session=session, testCase=test_case)[0]
                    test_case_table[test_case].append((tcs, tcs.isOkWithResult()))
                else:
                    test_case_table[test_case].append((None, None))
            
        context['testCaseTable'] = test_case_table
    
        return context