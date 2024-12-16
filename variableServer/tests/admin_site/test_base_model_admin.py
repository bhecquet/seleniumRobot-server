import datetime
import re

from django import forms
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.test.client import Client
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone

import commonsServer
from commonsServer.models import Application, Version
import variableServer
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin,\
    is_user_authorized
from variableServer.models import Variable
from variableServer.tests.test_admin import MockRequestWithApplication,\
    MockRequest

class TestBaseModelAdmin(TestCase):
    
    def test_has_add_permission_superuser(self):
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
        
    def test_has_add_permission_allowed_and_authenticated(self):
        """
        Add variable on application
        user:
        - is authenticated
        - can add variable
        - can view app1
        
        restriction on application is not applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='add_variable')))
        self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_add_permission_allowed_and_authenticated_with_restrictions(self):
        """
        Add variable on application
        user:
        - is authenticated
        - can add variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='add_variable')))
            self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_add_permission_not_allowed_and_authenticated_with_restrictions(self):
        """
        Add variable on application
        user:
        - is authenticated
        - can add variable
        - can NOT view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
            self.assertFalse(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_add_permission_not_allowed_and_authenticated(self):
        """
        Add variable on application without being allowed to add variable
        user:
        - is authenticated
        - can NOT add variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_add_permission(request=MockRequest(user=user)))
            

    def test_has_change_permission_superuser(self):
        
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=1)))
        
    def test_has_change_permission_superuser_with_application(self):
        """
        Change permission on variable with application
        """
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_change_permission_superuser_with_application_and_restrictions(self):
        """
        Change permission on variable with application, when restrictions are applied
        """
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
            self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_change_permission_allowed_and_authenticated(self):
        """
        change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is not applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
        self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_change_permission_allowed_and_authenticated_with_restrictions(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_change_permission_not_allowed_and_authenticated(self):
        """
        Change variable on application without being allowed to change variable
        user:
        - is authenticated
        - can NOT change variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequest(user=user)))
            
    def test_has_change_permission_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_change_permission_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
              
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
              
    def test_has_change_permission_not_allowed_and_authenticated_none_variable(self):
        """
        Change variable on application without being allowed to change variable
        user:
        - is authenticated
        - can change variable
        - can NOT view app1
        
        restriction on application is applied
        variable is NONE
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user)))
            

    def test_has_delete_permission_superuser(self):
        
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=1)))
        
    def test_has_delete_permission_superuser_with_application(self):
        """
        delete permission on variable with application
        """
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_delete_permission_superuser_with_application_and_restrictions(self):
        """
        delete permission on variable with application, when restrictions are applied
        """
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_delete_permission_allowed_and_authenticated(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is not applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
        self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_delete_permission_not_allowed_and_authenticated_with_restrictions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_delete_permission_not_allowed_and_authenticated(self):
        """
        delete variable on application without being allowed to delete variable
        user:
        - is authenticated
        - can NOT delete variable
        - can view app1
        
        restriction on application is applied
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequest(user=user)))
            
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_delete_permission_not_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        variable do not reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
              
            
    def test_has_delete_permission_not_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        variable reference application
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
              
    def test_has_delete_permission_not_allowed_and_authenticated_none_variable(self):
        """
        delete variable on application without being allowed to delete variable
        user:
        - is authenticated
        - can delete variable
        - can NOT view app1
        
        restriction on application is applied
        variable is NONE
        method is not POST
        """
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user)))
            
    def test_is_user_authorized_standard_user(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        self.assertFalse(is_user_authorized(user))
       
    def test_is_user_authorized_authenticated_user_no_permission(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        client = Client()
        client.login(username='user', password='pass')
        
        self.assertFalse(is_user_authorized(user))
       
    def test_is_user_authorized_authenticated_user_with_permission(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        user = User.objects.create_user(username='user', email='user@email.org', password='pass')
        client = Client()
        client.login(username='user', password='pass')
        
        variable_users_group, created = Group.objects.get_or_create(name='Variable Users')
        ct = ContentType.objects.get_for_model(variableServer.models.Variable, for_concrete_model=False)
        variable_users_group.permissions.add(*Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable') | Q(codename='delete_variable') | Q(codename='see_protected_var') , content_type=ct))
        variable_users_group.user_set.add(user)
        
        self.assertTrue(is_user_authorized(user))
       
    def test_is_user_authorized_none_user(self):
        """
        Check that standard user will not have right to see protected variabls
        """
        self.assertFalse(is_user_authorized(None))
     
    def test_is_user_authorized_super_user(self):
        """
        Check that super user will have right to see protected variabls
        """
        user = User.objects.create_superuser(username='user', email='user@email.org', password='pass')
        self.assertTrue(is_user_authorized(user))
     