'''
Created on 11 mai 2020

@author: S047432
'''
from django.contrib.auth.mixins import AccessMixin
from django.conf import settings
from seleniumRobotServer.permissions.permissions import APP_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX, \
    ENV_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX


class LoginRequiredMixinConditional(AccessMixin):
    """
    Class that allows to activate / deactivate security based on a flag in settings.py
    """
    
    def get_target_application(self):
        """
        Method that returns the application object related to what user wants to view
        
        """
        raise NotImplementedError("get_target_application must be overridden")

    def get_target_environment(self):
        """
        Method that returns the environment object related to what user wants to view

        """
        raise NotImplementedError("get_target_environment must be overridden")
    
    def _get_target_application(self):
        try:
            return self.get_target_application()
        except Exception as e:
            return None

    def _get_target_environment(self):
        try:
            return self.get_target_environment()
        except Exception as e:
            return None

    def dispatch(self, request, *args, **kwargs):
        
        # No permission if not authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # No permission if user is authenticated, but has no permission for requested application
        if not self._has_application_permission(self._get_target_application()) and not self._has_environment_permission(self._get_target_environment()):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
    
    def _has_application_permission(self, application):
        """
        Returns True if user has application permission or if it's not needed
        """
        if application:
            return self.request.user.has_perm(APP_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX + application.name)
        
        else:
            return True

    def _has_environment_permission(self, environment):
        """
        Returns True if user has environment permission or if it's not needed
        """
        if environment:
            return self.request.user.has_perm(ENV_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX + environment.name)

        else:
            return True
      