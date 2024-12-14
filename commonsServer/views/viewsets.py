'''
Created on 4 mai 2017

@author: bhecquet
'''

from rest_framework import viewsets, filters
from commonsServer.models import Application, TestEnvironment, \
    TestCase, Version
from django.db.models.aggregates import Count
from commonsServer.views.serializers import ApplicationSerializer,\
    VersionSerializer, TestEnvironmentSerializer, TestCaseSerializer
from rest_framework.exceptions import ValidationError
from django.conf import settings
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissions
from django.contrib.auth.models import Permission


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
            super().perform_create(serializer)
        else:
            serializer.data.serializer._data.update({'id': objects[0].id})
            
class ApplicationSpecificViewSet(BaseViewSet):
    """
    View that applies restrictions on values returned by viewset, base on the application linked to the object
    Applies filtering on GET request when a single object is requested
    """
    
    def perform_create(self, serializer):
        """
        Prevent creating / updating objects on restricted applications
        """
        if (not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN 
            or self.request.user.has_perm('variableServer.add_%s' % self.serializer_class.Meta.model.model_name)
            or self.request.user.has_perm('variableServer.change_%s' % self.serializer_class.Meta.model.model_name)):
            super().perform_create(serializer)
        
        allowed_aplications = [p.replace(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX, '') for p in self.request.user.get_all_permissions() if BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX in p]
        
        if serializer.validated_data['application'].name in allowed_aplications:
            super().perform_create(serializer)
        else:
            self.permission_denied(
                    self.request,
                    message="You don't have rights for application %s" % serializer.validated_data['application'],
                    code=None
                )
            
    def get_object(self):
        """
        check object permission
        """
        obj = super().get_object()

        self.check_object_permissions(self.request, obj)

        return obj
        
    def check_object_permissions(self, request, obj):
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            viewsets.ModelViewSet.check_object_permissions(self, request, obj)
        
        if obj and obj.application:
            permission = BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX + obj.application.name
            if not self.request.user.has_perm(permission):
                self.permission_denied(
                    request,
                    message="You don't have rights for application %s" % obj.application,
                    code=None
                )
        else:
            viewsets.ModelViewSet.check_object_permissions(self, request, obj)
            
class ApplicationSpecificFilter(filters.BaseFilterBackend):
    """
    This filter only applies to models that have an 'application' field
    Applies filter on GET request when list of objects is requested
    """
    
    def filter_queryset(self, request, queryset, view):
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN or request.user.has_perm('variableServer.view_%s' % queryset.model._meta.model_name):
            return queryset
        
        allowed_aplications = [p.replace(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX, '') for p in request.user.get_all_permissions() if BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX in p]
        
        return queryset.filter(application__name__in=allowed_aplications)

class ApplicationViewSet(BaseViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    
class VersionViewSet(BaseViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    
class TestEnvironmentViewSet(BaseViewSet):
    queryset = TestEnvironment.objects.all()
    serializer_class = TestEnvironmentSerializer

class TestCaseViewSet(ApplicationSpecificViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [ApplicationSpecificPermissions]
    filter_backends = [ApplicationSpecificFilter]
    
    