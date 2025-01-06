'''
Created on 3 déc. 2024

@author: S047432
'''
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional
from django.views.generic.list import ListView
from snapshotServer.models import TestSession, TestCaseInSession
import json

class TestSessionSummaryView(LoginRequiredMixinConditional, ListView):
    """
    View displaying a summary of tests executed during a test session
    This view will link to individual test results
    """
    
    template_name = "snapshotServer/testsSummary.html"
      
    def get_queryset(self):
        
        session_id = self.kwargs['sessionId']

        return {test_case_in_session: (test_case_in_session.isOkWithSnapshots(),                                   # no problem with snapshot comparison
                                       len(test_case_in_session.stepresult.all()),                                 # number of steps
                                       len([sr for sr in test_case_in_session.stepresult.all() if not sr.result]), # number of failed steps
                                       int(test_case_in_session.duration() / 1000),                                # duration
                                       {info.name: json.loads(info.info) for info in test_case_in_session.testInfos.all()} # test infos
                                       )  for test_case_in_session in TestCaseInSession.objects.filter(session = session_id).order_by("date")}
            
    def get_context_data(self, **kwargs):
        
        context = super(TestSessionSummaryView, self).get_context_data(**kwargs)
        
        session_id = self.kwargs['sessionId']
        context['testSession'] = TestSession.objects.get(id=session_id)
        
        context['testInfoList'] = []
        for test_case_in_session in context['testSession'].testcaseinsession_set.all():
            for test_info in test_case_in_session.testInfos.all():
                if test_info.name not in context['testInfoList']:
                    context['testInfoList'].append(test_info.name)
        
        return context
    