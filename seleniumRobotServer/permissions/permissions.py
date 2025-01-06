from rest_framework.permissions import DjangoModelPermissions
from django.conf import settings
from commonsServer.models import Application

APP_SPECIFIC_PERMISSION_PREFIX = 'variableServer.can_view_application_'

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

class ApplicationSpecificPermissions(GenericPermissions):
    """
    Permissions to apply to any model that need the allow access to a specific application
    """
    def has_permission(self, request, view):
        """
        Allow acces to model if model permissions are set, or any application specific permission is set
        In the later case, object filtering will be done later
        """
        
        has_model_permission = super().has_permission(request, view)
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            return has_model_permission

        return len([p for p in request.user.get_all_permissions() if p.startswith(APP_SPECIFIC_PERMISSION_PREFIX)]) > 0 \
                or has_model_permission

class ApplicationPermissionChecker:
    
    
    
    @staticmethod
    def has_model_permission(request, object_class, permission_instances):
        """
        Returns True if user has the required permission on the model
        """

        model_permissions = []
        for permission in permission_instances:
            model_permissions += permission.get_required_permissions(request.method, object_class)
            
        return any([request.user.has_perm(model_permission) for model_permission in model_permissions])
    
    @staticmethod
    def get_allowed_applications(request):
        """
        Returns the list of applications a user has rights on
        """
        return [p.replace(APP_SPECIFIC_PERMISSION_PREFIX, '') for p in request.user.get_all_permissions() if APP_SPECIFIC_PERMISSION_PREFIX in p]
    
    @staticmethod
    def filter_queryset(request, queryset, global_permission_code_name):
        """
        filter the input queryset based on application specific permissions
        if application restrictions are disabled, queryset is filtered based on global permissions
        
        @param request: the request sent by user
        @param queryset: initial queryset
        @param global_permission_code_name: name of the permission to check on the user. If user has this permission, the queryset won't be filtered
        """
        
        forbidden_applications = []
        
        if ApplicationPermissionChecker.bypass_application_permissions(request, global_permission_code_name):
            
            # in case we are here and we have not global permissions, do not return any data
            if not request.user.has_perm(global_permission_code_name):
                return queryset.none(), forbidden_applications
            else:                        
                return queryset, forbidden_applications
        
        for application in Application.objects.all():
            if not request.user.has_perm(APP_SPECIFIC_PERMISSION_PREFIX + application.name):
                queryset = queryset.exclude(application__name=application.name)
                forbidden_applications.append(application.name)
                
        queryset = queryset.exclude(application=None)
            
        return queryset, forbidden_applications
    
    @staticmethod
    def bypass_application_permissions(request, global_permission_code_name):
        """
        check if we need to apply or bypass application specific permissions
        
        we bypass in case
        - application permissions are disabled
        - application permissions are enabled and user has global permission
        
        Returns false if application permissions should be checked
        """

        return not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN or request.user.has_perm(global_permission_code_name)