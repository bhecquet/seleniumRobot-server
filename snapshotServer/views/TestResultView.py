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
    
    def buildLogStringFromJson(self, jsonString):
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
        logsDict = json.loads(jsonString)
        logStr = ""
        parseStep(logsDict)
        
        
        def parseStep(step):
            logStr += "<ul>"
            logStr += "<li>%s</li>" % step['name']
            logStr += "<ul>"
            for action in step['actions']:
                if action['type'] == 'message':
                    logStr += "<li>%s %s</li>" % (action['messageType'], action['name'])
                elif action['type'] == 'action':
                    if action['failed']:
                        logStr += "<li class='failed'>%s %s</li>" % (action['name'],)
                    else:
                        logStr += "<li class='success'>%s %s</li>" % (action['name'],)
                elif action['type'] == 'step':
                    parseStep(action)
                    
            logStr += "</ul>"
            logStr += "</ul>"
        
    
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
                    logs = ""
                
                
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