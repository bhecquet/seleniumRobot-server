'''
Created on 25 janv. 2017

@author: worm
'''

from django.contrib.auth.models import User, Group
from rest_framework import serializers

from snapshotServer.models import Snapshot, Application, TestEnvironment, \
    TestCaseInSession, TestStep, Version, TestSession, ExcludeZone, TestCase


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('id', 'name',)

class VersionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Version
        fields = ('id', 'name', 'application')

class TestEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestEnvironment
        fields = ('id', 'name',)

class TestSessionSerializer(serializers.ModelSerializer):
    
    # allow creating a test case given the name of environment and application, not the private key
    environment = serializers.SlugRelatedField(slug_field='name', queryset=TestEnvironment.objects.all())
    
    class Meta:
        model = TestSession
        fields = ('id', 'sessionId', 'date', 'browser', 'environment', 'version')

class TestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestStep
        fields = ('id', 'name', 'testCase')

class TestCaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestCase
        fields = ('id', 'name', 'application')
        
class TestCaseInSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestCaseInSession
        fields = ('id', 'session', 'testCase', 'testSteps')
        
class ExcludeZoneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ExcludeZone
        fields = ('x', 'y', 'width', 'height', 'snapshot')
        
class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = ('id', 'step', 'testCase', 'session')