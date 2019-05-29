'''
Created on 19 sept. 2017

@author: worm
'''
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView, get_object_or_404

from commonsServer.views.serializers import VersionSerializer
from variableServer.models import Version


class VersionView(RetrieveAPIView):
    
    serializer_class = VersionSerializer
    queryset = Version.objects.none()
    
    def get_object(self):
        versionName = self.request.query_params.get('name', None)
        if not versionName:
            raise ValidationError("name parameter is mandatory")
        
        version = get_object_or_404(Version, name=versionName)
        return version
        