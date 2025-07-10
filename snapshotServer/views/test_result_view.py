'''
Created on 4 sept. 2017

@author: worm
'''
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from snapshotServer.models import TestCaseInSession, StepResult, Snapshot
import json
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional

class TestResultView(LoginRequiredMixinConditional, ListView):
    """
    View displaying a single test result
    """
    
    template_name = "snapshotServer/testResult.html"
      
    def get_queryset(self):
        try:
            test_case_in_session = self.kwargs['test_case_in_session_id']
            test_steps = TestCaseInSession.objects.get(id=test_case_in_session).testSteps.all()
            
            step_snapshots = {}
            for step_result in StepResult.objects.filter(testCase=test_case_in_session, step__in=test_steps).order_by('id'):
                
                # build logs from json string
                try:
                    details = json.loads(step_result.stacktrace)
                except:
                    details = {}
                step_result.details = details
                
                try:
                    step_snapshots[step_result] = list(Snapshot.objects.filter(stepResult = step_result))
                except:
                    step_snapshots[step_result] = None
            
            return step_snapshots
                
        except:
            return []
        
    def get_context_data(self, **kwargs):
        context = super(TestResultView, self).get_context_data(**kwargs)
        current_test = get_object_or_404(TestCaseInSession, pk=self.kwargs['test_case_in_session_id'])
        context['currentTest'] = current_test
        context['testCaseId'] = self.kwargs['test_case_in_session_id']
        context['snasphotComparisonResult'] = current_test.isOkWithSnapshots()
        context['status'] = current_test.status
        
        # in case of computing error, do not display a step dedicated to it
        if context['snasphotComparisonResult'] == None:
            context['currentTest'].session.compareSnapshot = False
            
        # change test result when requested by the test
        if current_test.session.compareSnapshot and current_test.session.compareSnapshotBehaviour == 'CHANGE_TEST_RESULT' and context['snasphotComparisonResult'] == False :
            context['status'] = 'FAILURE'
            
        context['browserOrApp'] = current_test.session.browser.split(':')[-1].capitalize()
        context['applicationType'] = current_test.session.browser.split(':')[0].capitalize()

        try:
            stack_and_logs = json.loads(context['currentTest'].stacktrace)
            context['stacktrace'] = stack_and_logs['stacktrace'].split('\n')
            context['logs'] = stack_and_logs['logs'].split('\n')
        except:
            context['stacktrace'] = []
            context['logs'] = ['no logs available']
            
        last_step = [s for s in current_test.testSteps.all() if s.name == 'Test end']
        if last_step:
            last_step_result = StepResult.objects.filter(testCase=current_test, step__in=last_step)
            try:
                context['lastStepDetails'] = json.loads(last_step_result[0].stacktrace)
            except:
                context['lastStepDetails'] = {}
                
        context['infos'] = {}
        for test_info in current_test.testInfos.all():
            try:
                context['infos'][test_info.name] = json.loads(test_info.info)
            except:
                pass
                

        return context
    
    def get_target_application(self):
        test_case_in_session = TestCaseInSession.objects.get(id=self.kwargs['test_case_in_session_id'])
        return test_case_in_session.session.version.application

        
    
# Tests
# - Standard test OK
#     . look and feel: steps must have the right color
#     . pictures displayed
#     . files downloadable
#     . timestamps present
#     . video timestamp present
#     . substeps present
# - Standart test KO
#     . last step in red
#     . failed step in red
#     . error message displayed
# - Test with snapshot comparison => info only
#     . picture for comparison displayed
# - Test OK with snapshot comparison KO => change result
#     . picture for comparison displayed
#     . result has been changed