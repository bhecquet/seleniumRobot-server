'''
Created on 11 sept. 2018

@author: s047432
'''
from django_auth_ldap.backend import LDAPBackend
from seleniumRobotServer.CommonBackend import CommonBackend
from django.contrib.auth.backends import ModelBackend

class CommonLDAPBackend(LDAPBackend, CommonBackend, ModelBackend):
    """
    Specific backend to grant all connected users to be allowed to variables operations
    """
    
    def authenticate_ldap_user(self, ldap_user, password):
        user = super(CommonLDAPBackend, self).authenticate_ldap_user(ldap_user, password)
        
        return user

class LDAPBackend1(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_1_"
    
class LDAPBackend2(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_2_"
    
class LDAPBackend3(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_3_"