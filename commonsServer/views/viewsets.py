'''
Created on 4 mai 2017

@author: bhecquet
'''

from rest_framework import viewsets, filters
from variableServer.models import Application, TestEnvironment, \
    TestCase, Version
from django.db.models.aggregates import Count
from commonsServer.views.serializers import ApplicationSerializer,\
    VersionSerializer, TestEnvironmentSerializer, TestCaseSerializer
from rest_framework.exceptions import ValidationError
from django.conf import settings
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissions
from rest_framework.generics import get_object_or_404, CreateAPIView,\
    RetrieveAPIView


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
        model_name = self.queryset.model._meta.model_name
        
        if (not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN 
            or self.request.user.has_perm('variableServer.add_%s' % model_name)
            or self.request.user.has_perm('variableServer.change_%s' % model_name)):
            super().perform_create(serializer)
            return
        
        allowed_aplications = [p.replace(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX, '') for p in self.request.user.get_all_permissions() if BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX in p]
        
        if 'application' not in serializer.validated_data:
            self.permission_denied(
                    self.request,
                    message="You don't have rights on %s" % model_name,
                    code=None
                )
        elif serializer.validated_data['application'].name in allowed_aplications:
            super().perform_create(serializer)
        else:
            self.permission_denied(
                    self.request,
                    message="You don't have rights for application %s" % serializer.validated_data['application'],
                    code=None
                )
        
    def check_object_permissions(self, request, obj):
        """
        Check user has permission on object
        It has permission if:
        - it has permission on model
        - it has permission on application, if application restriction is set
        """
        
        model_permissions = []
        for permission in self.get_permissions():
            model_permissions += permission.get_required_permissions(request.method, obj.__class__)
            
        has_model_permission = any([self.request.user.has_perm(model_permission) for model_permission in model_permissions])
            
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN or has_model_permission:
            return viewsets.ModelViewSet.check_object_permissions(self, request, obj)
        
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
    
class RetrieveByNameViewSet(CreateAPIView, RetrieveAPIView, ApplicationSpecificViewSet):
    permission_classes = [ApplicationSpecificPermissions]
    filter_backends = [ApplicationSpecificFilter]
    
    def get_object(self, model):
        name = self.request.query_params.get('name', None)
        if not name:
            raise ValidationError("name parameter is mandatory")
        
        obj = get_object_or_404(model, name=name)
        self.check_object_permissions(self.request, obj)
        
        return obj

class ApplicationViewSet(RetrieveByNameViewSet):
    queryset = Application.objects.none()
    serializer_class = ApplicationSerializer
    
    def get_object(self):
        return super().get_object(Application)
    
class VersionViewSet(RetrieveByNameViewSet):
    queryset = Version.objects.none()
    serializer_class = VersionSerializer
    
    def get_object(self):
        return super().get_object(Version)
    
class TestEnvironmentViewSet(RetrieveByNameViewSet):
    queryset = TestEnvironment.objects.none()
    serializer_class = TestEnvironmentSerializer
    
    def get_object(self):
        return super().get_object(TestEnvironment)

class TestCaseViewSet(RetrieveByNameViewSet):
    queryset = TestCase.objects.none()
    serializer_class = TestCaseSerializer
    
    def get_object(self):
        return super().get_object(TestCase)
    
    