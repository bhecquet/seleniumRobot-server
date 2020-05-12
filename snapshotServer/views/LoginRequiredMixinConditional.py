'''
Created on 11 mai 2020

@author: S047432
'''
from django.contrib.auth.mixins import AccessMixin
from django.conf import settings



class LoginRequiredMixinConditional(AccessMixin):
    """
    Class that allows to activate / deactivate security based on a flag in settings.py
    """
    
    def __init__(self, *args, **kwargs):
        
        # security is enabled by default
        self.security_enabled = bool(getattr(settings, 'SECURITY_WEB_ENABLED', True))
        
        super().__init__(*args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        
        if self.security_enabled and not request.user.is_authenticated:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)