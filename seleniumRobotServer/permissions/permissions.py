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
        if not settings.SECURITY_API_ENABLED:
            return True
        
        has_model_permission = super().has_permission(request, view)
        
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            return has_model_permission

        return len([p for p in request.user.get_all_permissions() if p.startswith(APP_SPECIFIC_PERMISSION_PREFIX)]) > 0 \
                or has_model_permission

class ApplicationPermissionChecker:
    """
    This class provides helper methods for permission checking and is mostly intended to be used in viewset / django rest framework
    """

    @staticmethod
    def get_allowed_applications(request):
        """
        Returns the list of applications a user has rights on
        """
        return [p.replace(APP_SPECIFIC_PERMISSION_PREFIX, '') for p in request.user.get_all_permissions() if APP_SPECIFIC_PERMISSION_PREFIX in p]
   