'''
Created on 25 janv. 2017

@author: worm
'''

from django.contrib.auth.models import User, Group
from rest_framework import serializers

from snapshotServer.models import Snapshot, Application, TestEnvironment, \
    TestCase, TestStep, Version, TestSession


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
        fields = ('name',)

class TestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSession
        fields = ('sessionId', 'date', 'testCases')

class TestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestStep
        fields = ('name', 'testCase')

class TestCaseSerializer(serializers.ModelSerializer):
    
    # allow creating a test case given the name of environment and application, not the private key
    environment = serializers.SlugRelatedField(slug_field='name', queryset=TestEnvironment.objects.all())
    version = serializers.SlugRelatedField(slug_field='name', queryset=Version.objects.all())
    
    class Meta:
        model = TestCase
        fields = ('name', 'environment', 'version')
        
class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = ('step', 'browser', 'session')