'''
Created on 26 juil. 2017

@author: worm
'''
from django.views.generic.list import ListView

from collections import OrderedDict
from snapshotServer.models import TestCaseInSession
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional

class StepListView(LoginRequiredMixinConditional, ListView):
    """
    View displaying the list of steps for a test case in a session
    """
    
    template_name = "snapshotServer/stepList.html"
    
    def get_queryset(self):
        """
        @param testCaseInSessionId
        """
        try:
            test_steps = TestCaseInSession.objects.get(id=self.kwargs['testCaseInSessionId']).testSteps.all().order_by('teststepsthroughtestcaseinsession__order')
            return OrderedDict([(s, s.isOkWithSnapshots(self.kwargs['testCaseInSessionId'])) for s in test_steps])
        except:
            return []
        
    def get_context_data(self, **kwargs):
        context = super(StepListView, self).get_context_data(**kwargs)
        context['testCaseId'] = self.kwargs['testCaseInSessionId']
        
        if self.request.GET.get('header', 'false') == 'true':
            context['header'] = True
        else:
            context['header'] = False
        return context