'''
Created on 28 mars 2018

@author: s047432
'''

import re

from django.contrib.auth.models import User, Group

from django.test.client import Client
from django.test.testcases import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
import variableServer



# tests we should add to check admin view behavior
# - change multiple variables at once
# - copy multiple variables
# - copy several variables, one with tests, other without and check that resulting test is none
# - copy several variables, all with tests and check that resulting tests are the same as from variables
# - check filtering of tests and version when modifying a variable


class Messages:
    def __init__(self):
        self.content = []
    def add(self, level, message, extraargs):
        self.content.append(message)

class MockRequest():
    def __init__(self, user=None):
        self.user = user
        self.method = 'GET'
        self.GET = {}
        self.META = {}
        self._messages = Messages()

class MockRequestWithApplication():
    """
    Mimic POST request when user add / change / delete a variable (for example) linked to an application
    """
    def __init__(self, user=None):
        self.user = user
        self.POST = {'application': '1'}
        self.method = 'POST'

class MockRequestEmptyApplicationEmptyEnvironment():
    """
    Mimic POST request when adding a variable (for example) not linked to any application or environment
    """
    def __init__(self, user=None):
        self.user = user
        self.POST = {'application': '', 'environment': ''}
        self.method = 'POST'

class MockSuperUser:
    def has_perm(self, perm, obj=None):
        return True

class TestParent:


    def create_user_with_permissions(self, permissions: 'QuerySet[Permission]') -> User:

        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        user.user_permissions.add(*permissions)

        user.is_staff = True
        user.save()

        return user

    def _format_content(self, content):
        return re.sub('>\s+<', '><', str(content).replace('\\n', ''))


# https://stackoverflow.com/questions/6498488/testing-admin-modeladmin-in-django
class TestWebAndAdmin(TestCase, TestParent):
    """
    Parent test class for all test that use django client to call services
    For API tests, use TestApi class
    """

    def _create_and_authenticate_user_without_permissions(self) -> tuple[User, Client]:
        return self._create_and_authenticate_user_with_permissions(Permission.objects.none())

    def _create_and_authenticate_user_with_permissions(self, permissions: 'QuerySet[Permission]') -> tuple[User, Client]:
        """
        @param permissions: example: Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable'), content_type=ct)
        """
        user = self.create_user_with_permissions(permissions)
        client = Client()
        client.login(username='user', password='pass')

        return user, client

    def setUp(self):

        self.content_type_testcase = ContentType.objects.get_for_model(variableServer.models.TestCase, for_concrete_model=False)
        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)
        self.content_type_version = ContentType.objects.get_for_model(variableServer.models.Version, for_concrete_model=False)
        self.content_type_environment = ContentType.objects.get_for_model(variableServer.models.TestEnvironment, for_concrete_model=False)



