'''
Created on 26 juil. 2017

@author: worm
'''
from django.views.generic.list import ListView

from snapshotServer.models import TestCaseInSession


class TestListView(ListView):
    template_name = "snapshotServer/testList.html"
    
    def get_queryset(self):
        testCases = TestCaseInSession.objects.filter(session=self.args[0])
        return dict([(t, t.isOkWithSnapshots()) for t in testCases])
    
    def get_context_data(self, **kwargs):
        context = super(TestListView, self).get_context_data(**kwargs)
        context['sessionId'] = self.args[0]
        
        return context
    