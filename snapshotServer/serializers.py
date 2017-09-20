'''
Created on 25 janv. 2017

@author: worm
'''

from rest_framework import serializers

from snapshotServer.models import Snapshot, \
    TestCaseInSession, TestStep, TestSession, ExcludeZone, \
    StepResult
from commonsServer.models import TestEnvironment

class TestSessionSerializer(serializers.ModelSerializer):
    
    # allow creating a test case given the name of environment and application, not the private key
    environment = serializers.SlugRelatedField(slug_field='name', queryset=TestEnvironment.objects.all())
    
    class Meta:
        model = TestSession
        fields = ('id', 'sessionId', 'date', 'browser', 'environment', 'version', 'compareSnapshot')

class TestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestStep
        fields = ('id', 'name')
 
class TestCaseInSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestCaseInSession
        fields = ('id', 'session', 'testCase', 'testSteps', 'stacktrace')
        
class ExcludeZoneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ExcludeZone
        fields = ('x', 'y', 'width', 'height', 'snapshot')
        
class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = ('id', 'stepResult')
        
class StepResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepResult
        fields = ('id', 'step', 'testCase', 'result', 'duration', 'stacktrace')    