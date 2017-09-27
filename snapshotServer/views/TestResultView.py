'''
Created on 4 sept. 2017

@author: worm
'''
from django.views.generic.list import ListView
from snapshotServer.models import TestCaseInSession, StepResult, Snapshot
import json

class TestResultView(ListView):
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
            testCaseInSession = self.kwargs['testCaseInSessionId']
            testSteps = TestCaseInSession.objects.get(id=testCaseInSession).testSteps.all()
            
            stepSnapshots = {}
            for stepResult in StepResult.objects.filter(testCase=testCaseInSession, step__in=testSteps).order_by('id'):
                
                # build logs from json string
                if stepResult.stacktrace:
                    logs = self.buildLogStringFromJson(stepResult.stacktrace)
                else:
                    logs = None
                stepResult.formattedLogs = logs
                
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