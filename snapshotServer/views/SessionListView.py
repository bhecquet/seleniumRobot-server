'''
Created on 26 juil. 2017

@author: worm
'''
from datetime import datetime

from django.shortcuts import render_to_response
from django.views.generic.base import TemplateView

from snapshotServer.models import Version, TestSession, TestEnvironment, \
    TestCaseInSession, TestCase
from snapshotServer.views.ApplicationVersionListView import ApplicationVersionListView


class SessionListView(TemplateView):
    template_name = "snapshotServer/compare.html"

    def get(self, request, versionId):
        try:
            Version.objects.get(pk=versionId)
        except:
            return render_to_response(ApplicationVersionListView.template_name, {'error': "Application version %s does not exist" % versionId})
        
        return super(SessionListView, self).get(request, versionId)
    
    def get_context_data(self, **kwargs):
        
        context = super(SessionListView, self).get_context_data(**kwargs)
        
        sessions = TestSession.objects.filter(version=self.kwargs['versionId'], compareSnapshot=True)

        context['browsers'] = list(set([s.browser for s in TestSession.objects.all()]))
        context['selectedBrowser'] = self.request.GET.getlist('browser')
        sessions = sessions.filter(browser__in=context['selectedBrowser'])
        
        context['environments'] = TestEnvironment.objects.all()
        context['selectedEnvironments'] = TestEnvironment.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('environment')])
        sessions = sessions.filter(environment__in=context['selectedEnvironments'])
        
        # build the list of TestCase objects which can be selected by user
        context['testCases'] = list(set([tcs.testCase for tcs in TestCaseInSession.objects.filter(session__version=self.kwargs['versionId'])]))
        context['selectedTestCases'] = TestCase.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('testcase')])
        sessions = sessions.filter(testcaseinsession__testCase__in=context['selectedTestCases'])
        
        context['sessionFrom'] = self.request.GET.get('sessionFrom')
        if context['sessionFrom']:
            sessions = sessions.filter(date__gte=datetime.strptime(context['sessionFrom'], '%d-%m-%Y'))
            
        context['sessionTo'] = self.request.GET.get('sessionTo')
        if context['sessionTo']:
            sessions = sessions.filter(date__lte=datetime.strptime(context['sessionTo'], '%d-%m-%Y'))

        # display error when no option of one select list is choosen
        errors = []
        if not list(self.request.GET.getlist('browser')):
            errors.append("Choose at least one browser")
        if not list(self.request.GET.getlist('environment')):
            errors.append("Choose at least one environment")
        if not list(self.request.GET.getlist('testcase')):
            errors.append("Choose at least one test case")
        
        if errors:
            context['error'] = ', '.join(errors)
        
        # filter session according to request parameters
        context['sessions'] = sessions
    
        return context