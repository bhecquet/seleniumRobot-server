'''
Created on 25 janv. 2017

@author: worm
'''

from rest_framework import serializers

from snapshotServer.models import Snapshot, \
    TestCaseInSession, TestStep, TestSession, ExcludeZone, \
    StepResult, TestStepsThroughTestCaseInSession, File, ExecutionLogs, TestInfo
from commonsServer.models import TestEnvironment

class TestSessionSerializer(serializers.ModelSerializer):
    
    # allow creating a test case given the name of environment and application, not the private key
    environment = serializers.SlugRelatedField(slug_field='name', queryset=TestEnvironment.objects.all())
    
    class Meta:
        model = TestSession
        fields = ('id', 'sessionId', 'date', 'browser', 'environment', 'version', 'compareSnapshot', 'compareSnapshotBehaviour', 'name', 'ttl', 'startedBy')

class TestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestStep
        fields = ('id', 'name')

class TestStepsThroughTestCaseInSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestStepsThroughTestCaseInSession
        fields = ('testStep', 'order')
        

class TestCaseInSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestCaseInSession
        fields = ('id', 'session', 'testCase', 'testSteps', 'stacktrace', 'isOkWithSnapshots', 'computed', 'name', 'computingError', 'status', 'gridNode', 'description')
        
    def create(self, validated_data):
        
        # do not create if it exists
        tcss = TestCaseInSession.objects.filter(**validated_data)
        if len(tcss) > 0:
            test_case_in_sesssion = tcss[0]
        else:
            test_case_in_sesssion = super(TestCaseInSessionSerializer, self).create(validated_data)
        
        # add test steps
        self._update_test_steps(test_case_in_sesssion)
        
        return test_case_in_sesssion
    
    def _update_test_steps(self, test_case_in_sesssion):
        if 'testSteps' in self.initial_data:
            
            for step_through_test_case_in_session in TestStepsThroughTestCaseInSession.objects.filter(testcaseinsession=test_case_in_sesssion):
                step_through_test_case_in_session.delete(keep_parents=True)
            
            for i, step_id in enumerate(self.initial_data.getlist('testSteps', [])):
                step_through_test_case_in_session = TestStepsThroughTestCaseInSession(order=i, teststep=TestStep.objects.get(pk=int(step_id)), testcaseinsession=test_case_in_sesssion)
                step_through_test_case_in_session.save()
        
        
    def update(self, instance, validated_data):
        
        self._update_test_steps(instance)
        
        return super(TestCaseInSessionSerializer, self).update(instance, validated_data)
        
        
        
class TestInfoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TestInfo
        fields = ('id', 'testCase', 'name', 'info')
        
        
class ExcludeZoneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ExcludeZone
        fields = ('id', 'x', 'y', 'width', 'height', 'snapshot')
        
class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = ('id', 'stepResult', 'name', 'compareOption', 'diffTolerance')
        
        
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'stepResult', 'file')
        
class ExecutionLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionLogs
        fields = ('id', 'testCase', 'file')
        
class StepReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = ('id', 'stepResult')
        
class StepResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepResult
        fields = ('id', 'step', 'testCase', 'result', 'duration', 'stacktrace')    