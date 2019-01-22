'''
Created on 11 sept. 2018

@author: s047432
'''
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import Group

import logging

class CommonLDAPBackend(LDAPBackend):
    
    def authenticate_ldap_user(self, ldap_user, password):
        user = super(CommonLDAPBackend, self).authenticate_ldap_user(ldap_user, password)
        
        
        if user:
            try:
                variablesGroup = Group.objects.get(name='Variable Users')
                variablesGroup.user_set.add(user)
                logging.info("User %s added to group 'Variable Users'" % user.username)
            except:
                logging.warn("Group 'Variable Users' should be created ")
        
        return user

class LDAPBackend1(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_1_"
    
class LDAPBackend2(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_2_"
    
class LDAPBackend3(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_3_"