'''
Created on 4 sept. 2017

@author: worm
'''
from django.views.generic.list import ListView
from snapshotServer.models import TestCaseInSession, StepResult, Snapshot
import json
from snapshotServer.views.LoginRequiredMixinConditional import LoginRequiredMixinConditional

class TestResultView(LoginRequiredMixinConditional, ListView):
    """
    View displaying a single test result
    """
    
    template_name = "snapshotServer/testResult.html"
    
    @classmethod
    def buildLogStringFromJson(cls, jsonString):
        """
        {"name":"Login","type":"step","actions":[
            {"messageType":"INFO","name":"everything OK","type":"message"},
            {"name":"action2","failed":false,"type":"action"},
            {"name":"subStep","type":"step","actions":[
                {"messageType":"WARNING","name":"everything in subStep almost OK","type":"message"},
                {"name":"action1","failed":false,"type":"action"}
            ]}
        ]}

        to 
        
        <ul>
            <li>everything OK</li>
            <li>action2</li>
            <ul>
                <li>everything in subStep almost OK</li>
                <li>action1</li>
            </ul>
        </ul>
        """
        logStr = ""
        
        def parseStep(step, firstCall=False):
            
            nonlocal logStr
            
            # do not reprint the main step name as test report will print it
            if not firstCall:
                logStr += "<li>%s</li>\n" % step['name']
                
            logStr += "<ul>\n"
            for action in step['actions']:
                if action['type'] == 'message':
                    logStr += "<div class='message-%s'>%s: %s</div>\n" % (action['messageType'].lower(), action['messageType'], action['name'])
                elif action['type'] == 'action':
                    if action['failed']:
                        logStr += "<li class='action-failed'>%s</li>\n" % (action['name'],)
                    else:
                        logStr += "<li class='action-success'>%s</li>\n" % (action['name'],)
                elif action['type'] == 'step':
                    parseStep(action)
                    
            logStr += "</ul>\n"
            

        logsDict = json.loads(jsonString)
        
        parseStep(logsDict, True)
        
        return logStr
        
        
    
    def get_queryset(self):
        try:
            test_case_in_session = self.kwargs['testCaseInSessionId']
            test_steps = TestCaseInSession.objects.get(id=test_case_in_session).testSteps.all()
            
            stepSnapshots = {}
            for step_result in StepResult.objects.filter(testCase=test_case_in_session, step__in=test_steps).order_by('id'):
                
                # build logs from json string
                try:
                    details = json.loads(step_result.stacktrace)
                except:
                    details = {}
                step_result.details = details
                
                try:
                    stepSnapshots[step_result] = Snapshot.objects.get(stepResult = step_result)
                except:
                    stepSnapshots[step_result] = None
            
            return stepSnapshots
                
        except:
            return []
        
    def get_context_data(self, **kwargs):
        context = super(TestResultView, self).get_context_data(**kwargs)
        current_test = TestCaseInSession.objects.get(pk=self.kwargs['testCaseInSessionId'])
        context['currentTest'] = current_test
        context['testCaseId'] = self.kwargs['testCaseInSessionId']
        context['snasphotComparisonResult'] = current_test.isOkWithSnapshots()
        context['status'] = current_test.status
        if current_test.session.compareSnapshot and current_test.session.compareSnapshotBehaviour == 'CHANGE_TEST_RESULT' and not current_test.isOkWithSnapshots() :
            context['status'] = 'FAILURE'
            
        context['browserOrApp'] = current_test.session.browser.split(':')[-1].capitalize()
        context['applicationType'] = current_test.session.browser.split(':')[0].capitalize()

        try:
            stack_and_logs = json.loads(context['current_test'].stacktrace)
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

        return context
    
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