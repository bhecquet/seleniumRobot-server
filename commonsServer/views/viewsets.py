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


from commonsServer.views.serializers import ApplicationSerializer,\
    VersionSerializer, TestEnvironmentSerializer, TestCaseSerializer
from seleniumRobotServer.permissions.permissions import ApplicationPermissionChecker, APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX,\
    ApplicationSpecificPermissionsVariables

def perform_create(viewset_type, view, serializer):
    """
    Do not create an object if it already exists
    """
    objects = view.serializer_class.Meta.model.objects.all()
    for key, value in serializer.validated_data.items():
        if type(value) == list:
            objects = objects.annotate(Count(key)).filter(**{key + '__count': len(value)})
            if len(value) > 0:
                for v in value:
                    objects = objects.filter(**{key: v})
        else:
            objects = objects.filter(**{key: value})

    if not objects:
        super(viewset_type, view).perform_create(serializer)
    else:
        serializer.data.serializer._data.update({'id': objects[0].id})

class BaseViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        """
        Do not create an object if it already exists
        """
        perform_create(BaseViewSet, self, serializer)

class ApplicationSpecificViewSet(BaseViewSet):
    """
    View that applies restrictions on values returned by viewset, base on the application linked to the object
    Applies filtering on GET request when a single object is requested
    """
 
       
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
    
class RetrieveByNameViewSet(CreateAPIView, RetrieveAPIView):
    permission_classes = [ApplicationSpecificPermissionsVariables]
    filter_backends = [ApplicationSpecificFilter]

    def perform_create(self, serializer):
        """
        Do not create an object if it already exists
        """
        perform_create(RetrieveByNameViewSet, self, serializer)

    def get_object(self, model):
        name = self.request.query_params.get('name', None)
        if not name:
            raise ValidationError("name parameter is mandatory")
        
        obj = get_object_or_404(model, name=name)
#        self.check_object_permissions(self.request, obj)
        
        return obj

class ApplicationPermission(ApplicationSpecificPermissionsVariables):

    def get_application(self, request, view):
        try:
            return Application.objects.get(name=request.query_params.get('name', ''))
        except:
            return ''

class ApplicationViewSet(RetrieveByNameViewSet):
    queryset = Application.objects.none()
    serializer_class = ApplicationSerializer
    permission_classes = [ApplicationPermission]
    http_method_names = ['get', 'post']

    def get_object(self):
        return super().get_object(Application)

class VersionPermission(ApplicationSpecificPermissionsVariables):

    def get_application(self, request, view):
        try:
            return Application.objects.get(pk=request.POST['application'])
        except:
            return ''

class VersionViewSet(RetrieveByNameViewSet):
    queryset = Version.objects.none()
    serializer_class = VersionSerializer
    permission_classes = [VersionPermission]
    http_method_names = ['post']

class EnvironmentPermission(ApplicationSpecificPermissionsVariables):
    """
    Allow any user that has right on at least an application, to get environment
    Create environment is only allowed to user having "add_testenvironment" permission
    """

    def get_application(self, request, view):
        if request.method == 'GET':
            allowed_applications = ApplicationPermissionChecker.get_allowed_applications(request, self.prefix)
            if allowed_applications:
                return Application.objects.get(name=allowed_applications[0])
            else:
                return ''
        else:
            return ''

class TestEnvironmentViewSet(RetrieveByNameViewSet):
    queryset = TestEnvironment.objects.none()
    serializer_class = TestEnvironmentSerializer
    http_method_names = ['get', 'post']
    permission_classes = [EnvironmentPermission]
    
    def get_object(self):
        return super().get_object(TestEnvironment)

class TestCasePermission(ApplicationSpecificPermissionsVariables):

    def get_application(self, request, view):
        try:
            if request.method == 'POST':
                return Application.objects.get(pk=request.POST['application'])
            else:
                return Application.objects.get(pk=request.query_params.get('application', ''))
        except:
            return ''

class TestCaseViewSet(RetrieveByNameViewSet):
    queryset = TestCase.objects.none()
    serializer_class = TestCaseSerializer
    http_method_names = ['get', 'post']
    permission_classes = [TestCasePermission]
    
    def get_object(self):
        return super().get_object(TestCase)
    
    