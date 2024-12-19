'''
Created on 12 déc. 2024

'''
from django.contrib import admin
from django.conf import settings
from variableServer.models import Application


def is_user_authorized(user):
    """
    Returns True if user can view protected variables
    @param user: user for which rights are checked
    """
    if not user:
        return False
    if (user 
        and user.is_authenticated 
        and (user.is_superuser 
             or user.has_perm('variableServer.see_protected_var'))):
        return True
    else:
        return False

class BaseServerModelAdmin(admin.ModelAdmin):
    """
    Base class to restrict access to application objects the user has rights to see
    
    TODO: unit tests not created!!!
    """
    
    APP_SPECIFIC_PERMISSION_PREFIX = 'variableServer.can_view_application_'
    
    def _has_app_permission(self, global_permission, request, obj=None):
        """
        Whether user has rights on this application
        """
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            return global_permission
        
        if request.method == 'POST' and request.POST.get('application'):
            application = Application.objects.get(pk=int(request.POST['application']))
            return request.user.has_perm(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX + application.name)                        
            
        elif obj and obj.application:
            return request.user.has_perm(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX + obj.application.name)
             
        # if user has at least a permission on any application, let him see models and do actions (delete action / modify / ...)
        elif not obj and [p for p in request.user.get_all_permissions() if p.startswith(BaseServerModelAdmin.APP_SPECIFIC_PERMISSION_PREFIX)]:
            return True 
            
        return global_permission
    
    def has_add_permission(self, request):
        """
        Returns True if the given request has permission to add an object.
        """
        perm = super(BaseServerModelAdmin, self).has_add_permission(request)

        return perm or self._has_app_permission(perm, request)
        
    def has_view_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to view an object.
        """
        perm = super(BaseServerModelAdmin, self).has_view_permission(request, obj)

        return perm or self._has_app_permission(perm, request, obj)

    def has_change_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.
        """
        perm = super(BaseServerModelAdmin, self).has_change_permission(request, obj)
        
        return perm or self._has_app_permission(perm, request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.
        """
        perm = super(BaseServerModelAdmin, self).has_delete_permission(request, obj)
                
        return perm or self._has_app_permission(perm, request, obj)
    
