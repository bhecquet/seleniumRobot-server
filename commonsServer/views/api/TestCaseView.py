'''
Created on 19 sept. 2017

@author: worm
'''
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView

from variableServer.models import TestCase
from commonsServer.views.serializers import TestCaseSerializer


class TestCaseView(RetrieveAPIView):
    
    serializer_class = TestCaseSerializer
    
    def get_object(self):
        testCaseName = self.request.query_params.get('name', None)
        if not testCaseName:
            raise ValidationError("name parameter is mandatory")
        
        testCase = TestCase.objects.get(name=testCaseName)
        return testCase
        