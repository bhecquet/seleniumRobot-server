'''
Created on 19 sept. 2017

@author: worm
'''
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView

from variableServer.models import TestEnvironment
from commonsServer.views.serializers import TestEnvironmentSerializer


class EnvironmentView(RetrieveAPIView):
    
    serializer_class = TestEnvironmentSerializer
    
    def get_object(self):
        environmentName = self.request.query_params.get('name', None)
        if not environmentName:
            raise ValidationError("name parameter is mandatory")
        
        environment = TestEnvironment.objects.get(name=environmentName)
        return environment
        