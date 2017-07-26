'''
Created on 26 juil. 2017

@author: worm
'''
from django.views.generic.list import ListView

from snapshotServer.models import TestCaseInSession


class StepListView(ListView):
    template_name = "snapshotServer/stepList.html"
    
    def get_queryset(self):
        try:
            testSteps = TestCaseInSession.objects.get(id=self.args[1]).testSteps.all()
            return dict([(s, s.isOkWithSnapshots(self.args[0], self.args[1])) for s in testSteps])
        except:
            return []
        
    def get_context_data(self, **kwargs):
        context = super(StepListView, self).get_context_data(**kwargs)
        context['testCaseId'] = self.args[1]
        context['sessionId'] = self.args[0]
        return context