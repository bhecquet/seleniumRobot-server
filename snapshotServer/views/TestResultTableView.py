'''
Created on 1 août 2017

@author: worm
'''
from django.views.generic.base import TemplateView
from snapshotServer.models import Version, TestSession, TestEnvironment,\
    TestCaseInSession, TestCase
from snapshotServer.views.ApplicationVersionListView import ApplicationVersionListView
from datetime import datetime, timedelta
from django.shortcuts import render_to_response

class TestResultTableView(TemplateView):
    """
    View displaying a table with results of all tests for the sessions selected by user
    """
    
    template_name = "snapshotServer/testResults.html"

    def get(self, request, versionId):
        try:
            Version.objects.get(pk=versionId)
        except:
            return render_to_response(ApplicationVersionListView.template_name, {'error': "Application version %s does not exist" % versionId})
        
        return super(TestResultTableView, self).get(request, versionId)
    
    def get_context_data(self, **kwargs):
        
        context = super(TestResultTableView, self).get_context_data(**kwargs)
        
        sessions = TestSession.objects.filter(version=self.kwargs['versionId'])

        context['browsers'] = list(set([s.browser for s in TestSession.objects.all()]))
        
        # by default, select all browsers
        if 'browser' not in self.request.GET:
            context['selectedBrowser'] = context['browsers']
        else:
            context['selectedBrowser'] = self.request.GET.getlist('browser')
        sessions = sessions.filter(browser__in=context['selectedBrowser'])
        
        context['environments'] = TestEnvironment.objects.all()
        context['selectedEnvironments'] = TestEnvironment.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('environment')])
        sessions = sessions.filter(environment__in=context['selectedEnvironments'])
        
        # build the list of TestCase objects which can be selected by user
        context['testCases'] = list(set([tcs.testCase for tcs in TestCaseInSession.objects.filter(session__version=self.kwargs['versionId'])]))
        
        # by default, select all test cases
        if 'testcase' not in self.request.GET:
            context['selectedTestCases'] = context['testCases']
        else:
            context['selectedTestCases'] = TestCase.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('testcase')])
        sessions = sessions.filter(testcaseinsession__testCase__in=context['selectedTestCases'])
        
        if self.request.GET.get('sessionFrom') is None:
            context['sessionFrom'] = (datetime.now() - timedelta(days=15)).strftime('%d-%m-%Y')
        else:
            context['sessionFrom'] = self.request.GET.get('sessionFrom')
        sessions = sessions.filter(date__gte=datetime.strptime(context['sessionFrom'], '%d-%m-%Y'))
            
        if self.request.GET.get('sessionTo') is None:
            context['sessionTo'] = datetime.now().strftime('%d-%m-%Y')
        else:
            context['sessionTo'] = self.request.GET.get('sessionTo')
        sessions = sessions.filter(date__lte=datetime.strptime(context['sessionTo'], '%d-%m-%Y'))
        
        # filter session according to request parameters
        context['sessions'] = sessions
        
        # get all TestCaseInSession associated to these sessions
        testCaseInSessions = TestCaseInSession.objects.filter(session__in=sessions)
        testCases = list(set([tcs.testCase for tcs in testCaseInSessions]))
        
        testCaseTable = {}
        for testCase in testCases:
            testCaseTable[testCase] = []
            sessionsForTestCase = [tcs.session for tcs in testCaseInSessions.filter(testCase=testCase)]
            for session in sessions:
                if session in sessionsForTestCase:
                    tcs = TestCaseInSession.objects.filter(session=session, testCase=testCase)[0]
                    testCaseTable[testCase].append((tcs, tcs.isOkWithResult()))
                else:
                    testCaseTable[testCase].append((None, None))
            
        context['testCaseTable'] = testCaseTable
    
        return context