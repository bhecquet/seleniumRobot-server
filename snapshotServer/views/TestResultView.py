'''
Created on 4 sept. 2017

@author: worm
'''
from django.views.generic.list import ListView
from snapshotServer.models import TestCaseInSession, StepResult, Snapshot

class TestResultView(ListView):
    """
    View displaying a single test result
    """
    
    template_name = "snapshotServer/testResult.html"
    
    def get_queryset(self):
        try:
            testCaseInSession = self.kwargs['testCaseInSessionId']
            testSteps = TestCaseInSession.objects.get(id=testCaseInSession).testSteps.all()
            
            stepSnapshots = {}
            for stepResult in StepResult.objects.filter(testCase=testCaseInSession, step__in=testSteps).order_by('id'):
                try:
                    stepSnapshots[stepResult] = Snapshot.objects.get(stepResult = stepResult)
                except:
                    stepSnapshots[stepResult] = None
            
            return stepSnapshots
                
        except:
            return []
        
    def get_context_data(self, **kwargs):
        context = super(TestResultView, self).get_context_data(**kwargs)
        context['currentTest'] = TestCaseInSession.objects.get(pk=self.kwargs['testCaseInSessionId'])
        if context['currentTest'].stacktrace:
            context['stacktrace'] = context['currentTest'].stacktrace.split('\n')
        else:
            context['stacktrace'] = ['no logs available']
            
        return context