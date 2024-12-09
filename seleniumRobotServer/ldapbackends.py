'''
Created on 11 sept. 2018

@author: s047432
'''
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import Group
from seleniumRobotServer.CommonBackend import CommonBackend
from django.contrib.auth.backends import ModelBackend

class CommonLDAPBackend(LDAPBackend, CommonBackend, ModelBackend):
    """
    Specific backend to grant all connected users to be allowed to variables operations
    """
    
    def authenticate_ldap_user(self, ldap_user, password):
        user = super(CommonLDAPBackend, self).authenticate_ldap_user(ldap_user, password)
        
        # add groups only of users which are staff members
        if user is not None:
            self._add_user_to_groups(user)
        
        return user
    
    def has_perm(self, user, perm, obj=None):
        
        # use django permission model instead of LDAP group permissions as we want permissions per application
        return ModelBackend.has_perm(self, user, perm, obj=obj)
    
    def get_all_permissions(self, user, obj=None):
        return ModelBackend.get_all_permissions(self, user, obj=obj)
    
    def get_group_permissions(self, user, obj=None):
        return ModelBackend.get_group_permissions(self, user, obj=obj)
    
    def get_user_permissions(self, user_obj, obj=None):
        return ModelBackend.get_user_permissions(self, user_obj, obj=obj)

class LDAPBackend1(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_1_"
    
class LDAPBackend2(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_2_"
    
class LDAPBackend3(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_3_"