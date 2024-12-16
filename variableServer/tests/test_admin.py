'''
Created on 28 mars 2018

@author: s047432
'''

import re

from django.contrib.auth.models import User, Group

from django.test.client import Client
from django.test.testcases import TestCase



# tests we should add to check admin view behavior
# - when permissions are set for application, 
#   - cannot delete Variable of application whose user does not have right for
#   - cannot delete TestCase of application whose user does not have right for
#   - cannot delete Version of application whose user does not have right for
#   - variable belonging to restricted application are not shown
#   - test case belonging to restricted application are not shown
#   - version belonging to restricted application are not shown
#   - cannot change several variable at once to/from restricted application
#   - cannot copy several variable to/from restricted application
#   - cannot add variable to a restricted application
#   - cannot add testcase to a restricted application
#   - cannot add version to a restricted application
#   - for unrestricted applications, check the above behavior are not active
# - change multiple variables at once
# - copy multiple variables
# - copy several variables, one with tests, other without and check that resulting test is none
# - copy several variables, all with tests and check that resulting tests are the same as from variables
# - check filtering of tests and version when modifying a variable
class MockRequest(object):
    def __init__(self, user=None):
        self.user = user
        self.method = 'GET'
        self.GET = {}
        
class MockRequestWithApplication(object):
    def __init__(self, user=None):
        self.user = user
        self.POST = {'application': '1'}
        self.method = 'POST'

class MockSuperUser:
    def has_perm(self, perm, obj=None):
        return True


request = MockRequest()
request.user = MockSuperUser()

# https://stackoverflow.com/questions/6498488/testing-admin-modeladmin-in-django
class TestAdmin(TestCase):
    
    fixtures = ['varServer']
    
    def _create_and_authenticate_user_with_permissions(self, permissions):
        """
        @param permissions: example: Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable'), content_type=ct)
        """
        
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        client = Client()
        client.login(username='user', password='pass')
        
        variable_users_group, created = Group.objects.get_or_create(name='Variable Users')
        
        variable_users_group.permissions.add(*permissions)
        variable_users_group.user_set.add(user)
        
        user.is_staff = True
        user.save()
        
        return user, client
    
    def _format_content(self, content):
        return re.sub('>\s+<', '><', str(content).replace('\\n', ''))
        
    
### is_user_authorized ###    
    

    
### Environment Filter ###
    
    
        
### TestCaseAdmin ###

   
    