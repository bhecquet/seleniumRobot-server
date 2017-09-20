'''
Created on 19 sept. 2017

@author: worm
'''
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView

from variableServer.models import Version
from commonsServer.views.serializers import VersionSerializer


class VersionView(RetrieveAPIView):
    
    serializer_class = VersionSerializer
    
    def get_object(self):
        versionName = self.request.query_params.get('name', None)
        if not versionName:
            raise ValidationError("name parameter is mandatory")
        
        version = Version.objects.get(name=versionName)
        return version
        