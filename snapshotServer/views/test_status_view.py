'''
Created on 26 juil. 2017

@author: worm
'''
import json
import pickle

from django.http.response import HttpResponse

from snapshotServer.models import TestCaseInSession, Snapshot
from commonsServer.views.viewsets import ApplicationSpecificViewSet
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from rest_framework.generics import RetrieveAPIView


class TestStatusPermission(ApplicationSpecificPermissionsResultRecording):
    
    def get_object_application(self, test_case_in_session):
        if test_case_in_session:
            return test_case_in_session.session.version.application
        else:
            return ''
        
    def get_application(self, request, view):
        if view.kwargs.get('testCaseId', ''): # GET
            return self.get_object_application(TestCaseInSession.objects.get(pk=view.kwargs['testCaseId']))
        return ''

class TestStatusView(RetrieveAPIView):
    
    
    queryset = TestCaseInSession.objects.none()
    permission_classes = [TestStatusPermission]
    
    """
    API to get the test session status according to comparison results
    If only session and test are passed, the test is marked as KO when at least one step has a difference
    If moreover, test step is given, returns the comparison result of the step only
    @return: dict {<snapshotId>: <differences_or_not>}
    """
        
    def get(self, request, testCaseId, testStepId=None):
        try:

            testCase = TestCaseInSession.objects.get(pk=testCaseId)
            
            if testStepId:
                snapshots = Snapshot.objects.filter(stepResult__testCase=testCase, stepResult__step=testStepId)
            else:
                snapshots = Snapshot.objects.filter(stepResult__testCase=testCase)
            
            results = {} 
            for snapshot in snapshots:
                if snapshot.refSnapshot is None:
                    results[snapshot.id] = True
                    continue
                if snapshot.pixelsDiff is None:
                    continue
                pixels = pickle.loads(snapshot.pixelsDiff)
                results[snapshot.id] = not bool(pixels)
                
            return HttpResponse(json.dumps(results), content_type='application/json')
            
        except:
            return HttpResponse(status=404, reason="Could not find one or more objects")

        