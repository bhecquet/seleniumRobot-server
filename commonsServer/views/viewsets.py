'''
Created on 4 mai 2017

@author: bhecquet
'''

from rest_framework import viewsets, filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404, CreateAPIView,\
    RetrieveAPIView
from variableServer.models import Application, TestEnvironment, \
    TestCase, Version
from django.db.models.aggregates import Count
from django.conf import settings

from commonsServer.views.serializers import ApplicationSerializer,\
    VersionSerializer, TestEnvironmentSerializer, TestCaseSerializer
from seleniumRobotServer.permissions.permissions import ApplicationPermissionChecker, APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX,\
    ApplicationSpecificPermissionsVariables



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
            
    def has_model_permission(self):
        """
        Returns True if user has the required permission on the model
        """
        if not settings.SECURITY_API_ENABLED:
            return True

        model_permissions = []
        for permission in self.get_permissions():
            model_permissions += permission.get_required_permissions(self.request.method, self.queryset.model)
            
        return any([self.request.user.has_perm(model_permission) for model_permission in model_permissions])
            
class ApplicationSpecificViewSet(BaseViewSet):
    """
    View that applies restrictions on values returned by viewset, base on the application linked to the object
    Applies filtering on GET request when a single object is requested
    """
    
    def bypass_application_permissions(self):
        """
        check if we need to apply or bypass application specific permissions
        
        we bypass in case
        - application permissions are disabled
        - application permissions are enabled and user has global permission
        - api security is disabled
        
        Returns false if application permissions should be checked
        """
        
        has_model_permission = self.has_model_permission()
        return not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN or has_model_permission or not settings.SECURITY_API_ENABLED
    
    def perform_create(self, serializer):
        """
        Prevent creating / updating objects on restricted applications
        """
        model_name = self.queryset.model._meta.model_name

        if self.bypass_application_permissions():
            super().perform_create(serializer)
            return
        
        allowed_aplications = ApplicationPermissionChecker.get_allowed_applications(self.request)
        
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

        if self.bypass_application_permissions():
            return viewsets.ModelViewSet.check_object_permissions(self, request, obj)
        
        elif obj and obj.application:
            permission = APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + obj.application.name
            if not self.request.user.has_perm(permission):
                self.permission_denied(
                    request,
                    message="You don't have rights for application %s" % obj.application.name,
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
        
        if view.bypass_application_permissions():
            return queryset
        
        allowed_aplications = ApplicationPermissionChecker.get_allowed_applications(request)
        
        return queryset.filter(application__name__in=allowed_aplications)
    
class RetrieveByNameViewSet(CreateAPIView, RetrieveAPIView, ApplicationSpecificViewSet):
    permission_classes = [ApplicationSpecificPermissionsVariables]
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
    
    def check_object_permissions(self, request, obj):
        """
        Check user has permission on object
        It has permission if:
        - it has permission on model
        - it has permission on application, if application restriction is set
        """

        if self.bypass_application_permissions():
            return viewsets.ModelViewSet.check_object_permissions(self, request, obj)
        
        permission = APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + obj.name
        if not self.request.user.has_perm(permission):
            self.permission_denied(
                request,
                message="You don't have rights for application %s" % obj.name,
                code=None
            )
        
    
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
    
    def check_object_permissions(self, request, obj):
        """
        Check user has permission on object
        It has permission if:
        - it has permission on model
        - it has permission on application, if application restriction is set
        """

        if self.bypass_application_permissions():
            return viewsets.ModelViewSet.check_object_permissions(self, request, obj)
        
        if self.request.method != 'GET':
            self.permission_denied(
                request,
                message="You don't have rights to change environment %s" % obj.name,
                code=None
            )
        
        # when application restrictions is set, we allow to see all environments as there is no link between application and environment

class TestCaseViewSet(RetrieveByNameViewSet):
    queryset = TestCase.objects.none()
    serializer_class = TestCaseSerializer
    
    def get_object(self):
        return super().get_object(TestCase)
    
    