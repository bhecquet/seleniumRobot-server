from django.conf import settings
from rest_framework.permissions import DjangoModelPermissions

from commonsServer.models import Application, TestEnvironment

APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX = 'variableServer.' + Application.app_variable_permission_code
APP_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX = 'variableServer.' + Application.app_result_permission_code
ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX = 'variableServer.' + TestEnvironment.env_variable_permission_code
ENV_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX = 'variableServer.' + TestEnvironment.env_result_permission_code

class BYPASS_APPLICATION_CHECK:
    name = '_BYPASS_APPLICATION_CHECK_'

class GenericPermissions(DjangoModelPermissions):
    """
    Default permission that will be applied to any API
    """
    
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

class ContextSpecificPermissions(GenericPermissions):
    
    app_prefix = APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX
    env_prefix = ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX
    security_key = 'SECURITY_API_ENABLED'
    bypass_application_check = 'BYPASS_APPLICATION_CHECK'
    
    def _has_model_permission(self, request, view):
        """
        Returns True if user has the required permission on the model
        """
        if not getattr(settings, self.security_key):
            return True

        queryset = self._queryset(view)
        model_permissions = self.get_required_permissions(request.method, queryset.model)
            
        return any([request.user.has_perm(model_permission) for model_permission in model_permissions])
    
    def get_application(self, request, view):
        """
        Method to override to get Application object from child view
        It's possible to return BYPASS_APPLICATION_CHECK key so that, during "has_permission" phase, we can delegate to 'has_object_permission'
        ex: PATCH / PUT request may do 'has_permission' prior to 'has_object_permission', in this case, controlling the application two times is unecessary
        """
        try:
            if request.POST.get('application', ''):
                return Application.objects.get(id=request.data['application'])
            elif view.kwargs.get('pk', ''): # GET, needed so that we can refuse access if object is unknown
                return self.get_object_application(view.queryset.model.objects.get(pk=view.kwargs['pk']))
            else:
                return ''
        except:
            return ''

    def get_environment(self, request, view):
        """
        Method to override to get Environment object from child view
        It's possible to return BYPASS_APPLICATION_CHECK key so that, during "has_permission" phase, we can delegate to 'has_object_permission'
        ex: PATCH / PUT request may do 'has_permission' prior to 'has_object_permission', in this case, controlling the application two times is unecessary
        """
        try:
            if request.POST.get('environment', ''):
                return TestEnvironment.objects.get(id=request.data['environment'])
            elif view.kwargs.get('pk', ''): # GET, needed so that we can refuse access if object is unknown
                return self.get_object_environment(view.queryset.model.objects.get(pk=view.kwargs['pk']))
            else:
                return ''
        except:
            return ''
    

    def has_permission(self, request, view):
        """
        Allow acces to model if model permissions are set, or any application specific permission is set
        In the later case, object filtering will be done later
        """
        
        if not getattr(settings, self.security_key):
            return True
        
        has_model_permission = super().has_permission(request, view)
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_OR_ENVIRONMENT_IN_ADMIN:
            return has_model_permission
        
        try:
            application = self.get_application(request, view)
            environment = self.get_environment(request, view)
        except:
            # if we cannot check the application, stop
            return has_model_permission
        allowed_applications = ContextPermissionChecker.get_allowed_applications(request, self.prefix)
        allowed_environments = ContextPermissionChecker.get_allowed_environments(request, self.prefix)

        return ((application and application.name in allowed_applications)
                or (environment and environment.name in allowed_environments)
                or has_model_permission)
                
    def _bypass_context_permissions(self, request, view):
        """
        check if we need to apply or bypass application specific permissions
        
        we bypass in case
        - context (application / environment) permissions are disabled
        - context (application / environment) permissions are enabled and user has global permission
        - api security is disabled
        
        Returns false if application permissions should be checked
        """
        
        has_model_permission = self._has_model_permission(request, view)
        return not settings.RESTRICT_ACCESS_TO_APPLICATION_OR_ENVIRONMENT_IN_ADMIN or has_model_permission or not getattr(settings, self.security_key)
    
    def get_object_application(self, obj):
        """
        Returns the application object associated to this object
        To be overriden in subclass if access to Application object is different
        """
        if obj:
            return obj.application
        
        return None

    def get_object_environment(self, obj):
        """
        Returns the environment object associated to this object
        To be overriden in subclass if access to TestEnvironment object is different
        """
        if obj:
            return obj.environment

        return None
                
    def has_object_permission(self, request, view, obj):
        
        application = self.get_object_application(obj)
        environment = self.get_object_environment(obj)

        if self._bypass_context_permissions(request, view):
            return super().has_object_permission(request, view, obj)
        
        elif obj and application:
            permission = self.app_prefix + application.name
            return request.user.has_perm(permission)
        elif obj and environment:
            permission = self.env_prefix + environment.name
            return request.user.has_perm(permission)
        else:
            return super().has_object_permission(request, view, obj)
        
                
class ContextSpecificPermissionsResultRecording(ContextSpecificPermissions):
    """
    Permissions asssociated to result recording via API
    
    Result recording is associated to variable handling of the same application as recording is merely done by
    - CI => it must also have rights on variables
    - automation engineer => it already has right on sensible data of application
    """
    app_prefix = APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX
    env_prefix = ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX
    security_key = 'SECURITY_API_ENABLED'
                
class ContextSpecificPermissionsResultConsultation(ContextSpecificPermissions):
    """
    Permissions asssociated to result consultation via GUI
    """
    app_prefix = APP_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX
    env_prefix = ENV_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX
    security_key = 'SECURITY_WEB_ENABLED'
    
class ContextSpecificPermissionsVariables(ContextSpecificPermissions):
    """
    Permissions associated to variable handling via API
    """
    app_prefix = APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX
    env_prefix = ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX
    security_key = 'SECURITY_API_ENABLED'
    

class ContextPermissionChecker:
    """
    This class provides helper methods for permission checking and is mostly intended to be used in viewset / django rest framework
    """

    @staticmethod
    def get_allowed_applications(request, prefix=APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX):
        """
        Returns the list of applications a user has rights on
        """
        return [p.replace(prefix, '') for p in request.user.get_all_permissions() if prefix in p]

    @staticmethod
    def get_allowed_environments(request, prefix=ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX):
        """
        Returns the list of environments a user has rights on
        """
        return [p.replace(prefix, '') for p in request.user.get_all_permissions() if prefix in p]
   