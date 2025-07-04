'''
Created on 11 mai 2020

@author: S047432
'''
from django.contrib.auth.mixins import AccessMixin
from django.conf import settings
from seleniumRobotServer.permissions.permissions import APP_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX



class LoginRequiredMixinConditional(AccessMixin):
    """
    Class that allows to activate / deactivate security based on a flag in settings.py
    """
    
    def get_target_application(self):
        """
        Method that returns the application object related to what user wants to view
        
        """
        raise NotImplementedError("get_target_application must be overridden")
    
    def _get_target_application(self):
        try:
            return self.get_target_application()
        except Exception as e:
            return None
    
    def __init__(self, *args, **kwargs):
        
        # security is enabled by default
        self.security_enabled = bool(getattr(settings, 'SECURITY_WEB_ENABLED', True))
        
        super().__init__(*args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        
        # No permission if not authenticated
        if self.security_enabled and not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # No permission if user is authenticated, but has not permission for requested application
        if not self._has_application_permission(self._get_target_application()):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
    
    def _has_application_permission(self, application):
        """
        Returns True if user has application permission or if it's not needed
        """
        if not settings.RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN:
            return True
        
        if application:
            return self.request.user.has_perm(APP_SPECIFIC_RESULT_VIEW_PERMISSION_PREFIX + application.name)
        
        else:
            return True
      