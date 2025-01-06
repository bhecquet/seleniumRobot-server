'''
Created on 26 juil. 2017

@author: worm
'''
from django.views.generic.list import ListView

from snapshotServer.models import TestCaseInSession
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional


class TestListView(LoginRequiredMixinConditional, ListView):
    """
    View displaying the list of test corresponding to a session
    """
    
    template_name = "snapshotServer/testList.html"
    
    def get_queryset(self):
        test_cases = TestCaseInSession.objects.filter(session=self.kwargs['sessionId']).order_by('id')
        return dict([(t, t.isOkWithSnapshots()) for t in test_cases])
    
    def get_context_data(self, **kwargs):
        context = super(TestListView, self).get_context_data(**kwargs)
        context['sessionId'] = self.kwargs['sessionId']
        
        return context
    