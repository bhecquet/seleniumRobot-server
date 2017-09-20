'''
Created on 19 sept. 2017

@author: worm
'''
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView

from snapshotServer.serializers import ApplicationSerializer
from variableServer.models import Application


class ApplicationView(RetrieveAPIView):
    
    serializer_class = ApplicationSerializer
    
    def get_object(self):
        applicationName = self.request.query_params.get('name', None)
        if not applicationName:
            raise ValidationError("name parameter is mandatory")
        
        application = Application.objects.get(name=applicationName)
        return application
        