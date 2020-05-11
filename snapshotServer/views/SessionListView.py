'''
Created on 26 juil. 2017

@author: worm
'''
from datetime import datetime, timedelta

from django.shortcuts import render
from django.views.generic.base import TemplateView

from snapshotServer.models import Version, TestSession, TestEnvironment, \
    TestCaseInSession, TestCase
from snapshotServer.views.ApplicationVersionListView import ApplicationVersionListView
from snapshotServer.views.LoginRequiredMixinConditional import LoginRequiredMixinConditional


class SessionListView(LoginRequiredMixinConditional, TemplateView):
    """
    View displaying the session list depending on filters given by user
    """
    
    template_name = "snapshotServer/compare.html"

    def get(self, request, version_id):
        try:
            Version.objects.get(pk=version_id)
        except:
            return render(request, ApplicationVersionListView.template_name, {'error': "Application version %s does not exist" % version_id})
        
        return super(SessionListView, self).get(request, version_id)
    
    def get_context_data(self, **kwargs):
        
        context = super(SessionListView, self).get_context_data(**kwargs)
        
        sessions = TestSession.objects.filter(version=self.kwargs['version_id'], compareSnapshot=True)
        
        context['environments'] = TestEnvironment.objects.all()
        context['selectedEnvironments'] = TestEnvironment.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('environment')])
        sessions = sessions.filter(environment__in=context['selectedEnvironments'])

        context['sessionNames'] = [s['name'] for s in sessions.values('name').order_by('name').distinct()]
        context['selectedSessionNames'] = self.request.GET.getlist('sessionName')
        sessions = sessions.filter(name__in=context['selectedSessionNames'])

        context['browsers'] = list(set([s.browser for s in sessions]))
        context['selectedBrowser'] = self.request.GET.getlist('browser')
        sessions = sessions.filter(browser__in=context['selectedBrowser'])
        
        # build the list of TestCase objects which can be selected by user
        context['testCases'] = list(set([tcs.testCase for tcs in TestCaseInSession.objects.filter(session__version=self.kwargs['version_id'])]))
        context['selectedTestCases'] = TestCase.objects.filter(pk__in=[int(e) for e in self.request.GET.getlist('testcase')])
        sessions = sessions.filter(testcaseinsession__testCase__in=context['selectedTestCases'])
        
        context['sessionFrom'] = self.request.GET.get('sessionFrom')
        if context['sessionFrom'] and context['sessionFrom'] != 'None':
            sessions = sessions.filter(date__gte=datetime.strptime(context['sessionFrom'], '%d-%m-%Y'))
            
        context['sessionTo'] = self.request.GET.get('sessionTo')
        if context['sessionTo'] and context['sessionTo'] != 'None':
            sessions = sessions.filter(date__lte=datetime.strptime(context['sessionTo'], '%d-%m-%Y') + timedelta(days=1))

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