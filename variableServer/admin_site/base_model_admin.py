'''
Created on 12 déc. 2024

'''
from django.contrib import admin
from django.conf import settings
from variableServer.models import Application, TestEnvironment
from seleniumRobotServer.permissions.permissions import ContextPermissionChecker, \
    APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX, ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX


def bypass_context_permissions(request, global_permission_code_name):
    """
    check if we need to apply or bypass application specific permissions
    
    we bypass in case
    - application / environment permissions are disabled
    - application / environment permissions are enabled and user has global permission
    
    Returns false if application permissions should be checked
    """

    return not settings.RESTRICT_ACCESS_TO_APPLICATION_OR_ENVIRONMENT_IN_ADMIN or request.user.has_perm(global_permission_code_name)

class BaseServerModelAdmin(admin.ModelAdmin):
    """
    Base class to restrict access to application objects the user has rights to see
    If model has 'environment' field, then restriction will also be based on environment
    """
    
    def _has_context_permission(self, global_permission, request, obj=None):
        """
        Whether user has rights on this application or environment
        """
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_OR_ENVIRONMENT_IN_ADMIN:
            return global_permission

        has_application_permission = None
        has_environment_permission = None

        # submiting a new variable with no application will lead to an empty string application
        # in this case, we do not allow adding this
        if request.method == 'POST' and request.POST.get('application') == '' and request.POST.get('environment') == '':
            return False

        if request.method == 'POST' and request.POST.get('application'):
            application = Application.objects.get(pk=int(request.POST['application']))
            has_application_permission = request.user.has_perm(APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + application.name)

        elif obj and obj.application:
            has_application_permission = request.user.has_perm(APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + obj.application.name)

        # if user has at least a permission on any application OR environment, let him see models and do actions (delete action / modify / ...)
        elif not obj and ContextPermissionChecker.get_allowed_applications(request):
            has_application_permission = True

        if request.method == 'POST' and request.POST.get('environment'):
            environment = TestEnvironment.objects.get(pk=int(request.POST['environment']))
            has_environment_permission = request.user.has_perm(ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + environment.name)

        elif obj and hasattr(obj, 'environment') and obj.environment:
            has_environment_permission = request.user.has_perm(ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + obj.environment.name)

        # if user has at least a permission on any application OR environment, let him see models and do actions (delete action / modify / ...)
        elif not obj and ContextPermissionChecker.get_allowed_environments(request):
            has_environment_permission = True

        return global_permission or has_application_permission or has_environment_permission
    
    def get_queryset(self, request, requested_permission):
        """
        Returns the queryset, filtered with only values that the user has rights to see
        """
        queryset = super().get_queryset(request)
        queryset, forbidden_applications, forbidden_environments = self._filter_queryset(request, queryset, requested_permission)
                 
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
        forbidden_environments = []
        
        if bypass_context_permissions(request, global_permission_code_name):
            
            # in case we are here and we have not global permissions, do not return any data
            if request.user.has_perm(global_permission_code_name):
                return queryset, forbidden_applications, forbidden_environments
            else:                        
                return queryset.none(), forbidden_applications, forbidden_environments

        application_queryset = queryset.all()

        for application_id, application_name in application_queryset.values_list('application', 'application__name').distinct().exclude(application=None):
            if not request.user.has_perm(APP_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + application_name):
                application_queryset = application_queryset.exclude(application__name=application_name)
                forbidden_applications.append(application_name)

        application_queryset = application_queryset.exclude(application=None)

        if hasattr(self.model, 'environment'):
            environment_queryset = queryset.all()
            for environment_id, environment_name in environment_queryset.values_list('environment', 'environment__name').distinct().exclude(environment=None):
                if not request.user.has_perm(ENV_SPECIFIC_VARIABLE_HANDLING_PERMISSION_PREFIX + environment_name):
                    environment_queryset = environment_queryset.exclude(environment__name=environment_name)
                    forbidden_environments.append(environment_name)

            environment_queryset = environment_queryset.exclude(environment=None)
            application_queryset.union(environment_queryset)


            
        return application_queryset, forbidden_applications, forbidden_environments
    
   
    
    def has_add_permission(self, request):
        """
        Returns True if the given request has permission to add an object.
        """
        perm = super(BaseServerModelAdmin, self).has_add_permission(request)

        return perm or self._has_context_permission(perm, request)
        
    def has_view_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to view an object.
        """
        perm = super(BaseServerModelAdmin, self).has_view_permission(request, obj)

        return perm or self._has_context_permission(perm, request, obj)

    def has_change_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.
        """
        perm = super(BaseServerModelAdmin, self).has_change_permission(request, obj)
        
        return perm or self._has_context_permission(perm, request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.
        """
        perm = super(BaseServerModelAdmin, self).has_delete_permission(request, obj)
                
        return perm or self._has_context_permission(perm, request, obj)
    
