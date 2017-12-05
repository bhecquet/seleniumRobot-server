'''
Created on 25 janv. 2017

@author: worm
'''

from django.contrib.auth.models import User, Group
from rest_framework import serializers

from variableServer.models import Variable
        
class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variable
        fields = ('id', 'name', 'value', 'environment', 'version', 'test', 'releaseDate', 'internal', 'protected', 'description', 'application')
