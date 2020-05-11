'''
Created on 11 sept. 2018

@author: s047432
'''
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import Group

import logging

class CommonLDAPBackend(LDAPBackend):
    """
    Specific backend to grant all connected users to be allowed to variables operations
    """
    
    def authenticate_ldap_user(self, ldap_user, password):
        user = super(CommonLDAPBackend, self).authenticate_ldap_user(ldap_user, password)
        
        
        if user:
            try:
                variables_group = Group.objects.get(name='Variable Users')
                variables_group.user_set.add(user)
                logging.info("User %s added to group 'Variable Users'" % user.username)
            except:
                logging.warn("Group 'Variable Users' should be created ")
                
            try:
                snapshot_group = Group.objects.get(name='Snapshot Users')
                snapshot_group.user_set.add(user)
                logging.info("User %s added to group 'Snapshot Users'" % user.username)
            except:
                logging.warn("Group 'Snapshot Users' should be created ")
        
        return user

class LDAPBackend1(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_1_"
    
class LDAPBackend2(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_2_"
    
class LDAPBackend3(CommonLDAPBackend):
    settings_prefix = "AUTH_LDAP_3_"