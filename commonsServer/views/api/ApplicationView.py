'''
Created on 19 sept. 2017

@author: worm
'''
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView, get_object_or_404

from variableServer.models import Application
from commonsServer.views.serializers import ApplicationSerializer


class ApplicationView(RetrieveAPIView):
    
    serializer_class = ApplicationSerializer
    
    def get_object(self):
        applicationName = self.request.query_params.get('name', None)
        if not applicationName:
            raise ValidationError("name parameter is mandatory")
        
        application = get_object_or_404(Application, name=applicationName)
        return application
        