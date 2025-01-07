'''
Created on 12 déc. 2024

'''
from django.contrib import admin
from django.conf import settings
from variableServer.models import Application
from seleniumRobotServer.permissions.permissions import ApplicationPermissionChecker,\
    APP_SPECIFIC_PERMISSION_PREFIX


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
    
def bypass_application_permissions(request, global_permission_code_name):
    """
    check if we need to apply or bypass application specific permissions
    
    we bypass in case
    - application permissions are disabled
    - application permissions are enabled and user has global permission
    
    Returns false if application permissions should be checked
    """

    return not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN or request.user.has_perm(global_permission_code_name)

class BaseServerModelAdmin(admin.ModelAdmin):
    """
    Base class to restrict access to application objects the user has rights to see
    """
    
    def _has_app_permission(self, global_permission, request, obj=None):
        """
        Whether user has rights on this application
        """
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            return global_permission
        
        if request.method == 'POST' and request.POST.get('application'):
            application = Application.objects.get(pk=int(request.POST['application']))
            return request.user.has_perm(APP_SPECIFIC_PERMISSION_PREFIX + application.name)  
        
        # submiting a new variable with no application will lead to and empty string application
        # in this case, we do not allow adding this
        elif request.method == 'POST' and request.POST.get('application') == '':
            return False             
            
        elif obj and obj.application:
            return request.user.has_perm(APP_SPECIFIC_PERMISSION_PREFIX + obj.application.name)
             
        # if user has at least a permission on any application, let him see models and do actions (delete action / modify / ...)
        # TODO: not filtering on method verb allow a user with any application specific permission to add a variable not linked to application
        elif not obj and ApplicationPermissionChecker.get_allowed_applications(request):
            return True 
            
        return global_permission
    
    def get_queryset(self, request, requested_permission):
        """
        Returns the queryset, filtered with only values that the user has rights to see
        """
        queryset = super().get_queryset(request)
        queryset, forbidden_applications = self._filter_queryset(request, queryset, requested_permission)
                 
        return queryset 
    
    def _filter_queryset(self, request, queryset, global_permission_code_name):
        """
        filter the input queryset based on application specific permissions
        if application restrictions are disabled, queryset is filtered based on global permissions
        
        @param request: the request sent by user
        @param queryset: initial queryset
        @param global_permission_code_name: name of the permission to check on the user. If user has this permission, the queryset won't be filtered
        """
        
        forbidden_applications = []
        
        if bypass_application_permissions(request, global_permission_code_name):
            
            # in case we are here and we have not global permissions, do not return any data
            if request.user.has_perm(global_permission_code_name):
                return queryset, forbidden_applications
            else:                        
                return queryset.none(), forbidden_applications
        
        for application in Application.objects.all():
            if not request.user.has_perm(APP_SPECIFIC_PERMISSION_PREFIX + application.name):
                queryset = queryset.exclude(application__name=application.name)
                forbidden_applications.append(application.name)
                
        queryset = queryset.exclude(application=None)
            
        return queryset, forbidden_applications 
    
   
    
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
    
