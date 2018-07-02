'''
Created on 25 janv. 2017

@author: worm
'''

from rest_framework import serializers

from commonsServer.models import Application, TestEnvironment, Version, TestCase

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

class TestCaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestCase
        fields = ('id', 'name', 'application')
        