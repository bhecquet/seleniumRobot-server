'''
Created on 28 mars 2018

@author: s047432
'''

import re

from django.contrib.auth.models import User, Group

from django.test.client import Client
from django.test.testcases import TestCase



# tests we should add to check admin view behavior
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
    """
    Mimic POST request when user add / change / delete a variable (for example) linked to an application
    """
    def __init__(self, user=None):
        self.user = user
        self.POST = {'application': '1'}
        self.method = 'POST'
        
class MockRequestEmptyApplication(object):
    """
    Mimic POST request when adding a variable (for example) not linked to any application
    """
    def __init__(self, user=None):
        self.user = user
        self.POST = {'application': ''}
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

    