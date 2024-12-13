'''
Created on 4 mai 2017

@author: bhecquet
'''

from rest_framework import viewsets
from commonsServer.models import Application, TestEnvironment, \
    TestCase, Version
from django.db.models.aggregates import Count
from commonsServer.views.serializers import ApplicationSerializer,\
    VersionSerializer, TestEnvironmentSerializer, TestCaseSerializer
from rest_framework.exceptions import ValidationError
from django.conf import settings
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin


class BaseViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        """
        Do not create an object if it already exists
        """
        objects = self.serializer_class.Meta.model.objects.all()
        for key, value in serializer.validated_data.items():
            if type(value) == list:
                objects = objects.annotate(Count(key)).filter(**{key + '__count': len(value)})
                if len(value) > 0:
                    for v in value:
                        objects = objects.filter(**{key: v})
            else:
                objects = objects.filter(**{key: value})
    
        if not objects:
            super(BaseViewSet, self).perform_create(serializer)
        else:
            serializer.data.serializer._data.update({'id': objects[0].id})
            
    def get_object(self):
        """
        check object permission
        """
        obj = super().get_object()

        self.check_object_permissions(self.request, obj)

        return obj
        
    def check_object_permissions(self, request, obj):
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            return viewsets.ModelViewSet.check_object_permissions(self, request, obj)
        
        if obj and obj.application:
            return self.request.user.has_perm(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX + obj.application.name)
        else:
            return viewsets.ModelViewSet.check_object_permissions(self, request, obj)

class ApplicationViewSet(BaseViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    
class VersionViewSet(BaseViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    
class TestEnvironmentViewSet(BaseViewSet):
    queryset = TestEnvironment.objects.all()
    serializer_class = TestEnvironmentSerializer

class TestCaseViewSet(BaseViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    