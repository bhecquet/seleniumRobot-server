'''
Created on 11 sept. 2018

@author: s047432
'''
from django_auth_ldap.backend import LDAPBackend

class LDAPBackend1(LDAPBackend):
    settings_prefix = "AUTH_LDAP_1_"
    
class LDAPBackend2(LDAPBackend):
    settings_prefix = "AUTH_LDAP_2_"
    
class LDAPBackend3(LDAPBackend):
    settings_prefix = "AUTH_LDAP_3_"