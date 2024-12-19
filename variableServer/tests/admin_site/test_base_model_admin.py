
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.test.client import Client

import variableServer
from variableServer.admin_site.base_model_admin import BaseServerModelAdmin,\
    is_user_authorized
from variableServer.models import Variable, Application
from variableServer.tests.test_admin import MockRequestWithApplication,\
    MockRequest, TestAdmin, MockRequestEmptyApplication

class TestBaseModelAdmin(TestAdmin):
    
    def setUp(self)->None:
        TestAdmin.setUp(self)
        
        Application.objects.get(pk=1).save()
        
    def test_has_add_permission_superuser(self):
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
        
    def test_has_add_permission_allowed_and_authenticated(self):
        """
        Add variable on application
        user:
        - is authenticated
        - has add variable permission
        
        User can add variable
        """

        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_not_add_permission_allowed_and_authenticated(self):
        """
        Add variable on application
        user:
        - is authenticated
        - has NOT add variable permission
        
        User can NOT add variable
        """

        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        self.assertFalse(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))        
            
    def test_has_add_permission_with_add_variable_permission_and_restriction_on_application(self):
        """
        Add variable on application
        user:
        - is authenticated
        - has add variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can add variable as 'add_variable' permission is less restrictive
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
            self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_add_permission_with_add_variable_permission_and_app_permission_and_restriction_on_application(self):
        """
        Add variable on application without being allowed to add variable
        user:
        - is authenticated
        - has add variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can add variable for that application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable') | Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_add_permission_allowed_and_restriction_on_application(self):
        """
        Add variable on application without being allowed to add variable
        user:
        - is authenticated
        - has NOT add variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can add variable for that application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_add_permission_allowed_and_restriction_on_application_variable_not_linked_to_application(self):
        """
        Add variable not linked to application without being allowed to add variable
        user:
        - is authenticated
        - has NOT add variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can add NOT variable without application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_add_permission(request=MockRequestEmptyApplication(user=user)))
              
    def test_has_add_permission_not_allowed_and_restriction_on_application(self):
        """
        Add variable on application without being allowed on that application
        user:
        - is authenticated
        - has NOT add variable permission
        - has view/edit permission on 'app2'
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can NOT add variable for that application as it has no rights on it
        """
        Application.objects.get(pk=2).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self.assertFalse(base_admin.has_add_permission(request=MockRequestWithApplication(user=user)))
            

    def test_has_change_permission_superuser(self):
        """
        Super user can change data
        """
        
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
   
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
            self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_change_permission_allowed_and_authenticated(self):
        """
        change variable on application
        user:
        - is authenticated
        - has change variable permission
        
        User can change variable
        """
  
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_change_permission_not_allowed_and_authenticated(self):
        """
        change variable on application
        user:
        - is authenticated
        - has add variable permission
        
        User can NOT change variable
        """

        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        self.assertFalse(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_change_permission_allowed_and_authenticated_with_restrictions(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has change variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can change variable
        """
   
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has change variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can change variable
        """
      
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_change_permission_with_application_permission_and_authenticated(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has NOT change variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can change variable
        """
   
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user)))
            
    def test_has_change_permission_with_other_application_permission_and_authenticated(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has NOT change variable permission
        - has view/edit permission on 'app2'
        - restriction per application is set
        
        User can NOT change variable
        """
       
        Application.objects.get(pk=2).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_change_permission_and_authenticated_with_restrictions_variable_without_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has NOT change variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can NOT change variable
        variable does NOT reference application
        method is not POST
        """
 
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_change_permission_and_authenticated_with_restrictions_variable_with_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has NOT change variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can change variable
        variable reference application
        method is not POST
        """
  
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_change_permission_and_authenticated_with_restrictions_variable_with_application2(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has NOT change variable permission
        - has view/edit permission on 'app2'
        - restriction per application is set
        
        User can NOT change variable
        variable reference application
        method is not POST
        """
    
        Application.objects.get(pk=2).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_change_permission_and_authenticated_with_restrictions_variable_without_application2(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has change variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can change variable
        variable do not reference application
        method is not POST
        """
     
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
                     
    def test_has_change_permission_allowed_and_restriction_on_application_variable_not_linked_to_application(self):
        """
        Change variable not linked to application without being allowed to change variable
        user:
        - is authenticated
        - has NOT add variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can NOT change variable without application
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_change_permission(request=MockRequestEmptyApplication(user=user))) 
            
    def test_has_change_permission_not_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        Change variable on application
        user:
        - is authenticated
        - has change variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can change variable
        variable reference application
        method is not POST
        """
 
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
              
    def test_has_change_permission_not_allowed_and_authenticated_none_variable(self):
        """
        Change variable on application without being allowed to change variable
        user:
        - is authenticated
        - has change variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can change variable
        variable is NONE
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
            self.assertTrue(base_admin.has_change_permission(request=MockRequest(user=user)))
            
    def test_has_view_permission_superuser(self):
        """
        Test superuser can view
        """
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_view_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=1)))
        
    def test_has_view_permission_superuser_with_application(self):
        """
        view permission on variable with application
        """
        
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
        self.assertTrue(base_admin.has_view_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_view_permission_superuser_with_application_and_restrictions(self):
        """
        view permission on variable with application, when restrictions are applied
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
            self.assertTrue(base_admin.has_view_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_view_permission_allowed_and_authenticated(self):
        """
        view variable on application
        user:
        - is authenticated
        - has view variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is NOT set
        
        User can view
        """
   
        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
        self.assertTrue(base_admin.has_view_permission(request=MockRequestWithApplication(user=user)))   
             
    def test_has_view_permission_not_allowed_and_authenticated(self):
        """
        view variable on application
        user:
        - is authenticated
        - has NOT view variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is NOT set
        
        User can view
        """

        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
        self.assertFalse(base_admin.has_view_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_view_permission_allowed_and_authenticated_with_restrictions(self):
        """
        view variable on application
        user:
        - is authenticated
        - has view variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can view
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='view_variable')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_view_permission_and_authenticated_with_restrictions(self):
        """
        view variable on application
        user:
        - is authenticated
        - has view variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can view
        """
      
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_view_permission_and_authenticated_and_application_permissions(self):
        """
        view variable on application
        user:
        - is authenticated
        - has NOT view variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can view
        """
   
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequest(user=user)))
              
    def test_has_view_permission_and_authenticated_and_other_application_permissions(self):
        """
        view variable on application
        user:
        - is authenticated
        - has NOT view variable permission
        - has view/edit permission on 'app2'
        - restriction per application is set
        
        User can view
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self.assertFalse(base_admin.has_view_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_view_permission_with_application_permission_and_variable_without_application(self):
        """
        view variable on application
        user:
        - is authenticated
        - has NOT view variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User cannot view variable
        variable do not reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_view_permission_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        view variable on application
        user:
        - is authenticated
        - has view variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can view variable
        variable do not reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_view_permission_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        view variable on application
        user:
        - is authenticated
        - has NOT view variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can view application
        variable reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_view_permission_and_authenticated_with_restrictions_variable_with_application2(self):
        """
        view variable on application
        user:
        - is authenticated
        - has view variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can view application
        variable reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='view_variable')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
              
    def test_has_view_permission_and_authenticated_none_variable(self):
        """
        view variable on application
        user:
        - is authenticated
        - has view variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can view variable
        variable is NONE
        method is not POST
        """
   
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_variable')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequest(user=user)))
            
    def test_has_view_permission_and_authenticated_none_variable_and_application_permission(self):
        """
        view variable on application
        user:
        - is authenticated
        - has NOT view variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can view variable
        variable is NONE
        method is not POST
        """
  
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_view_permission(request=MockRequest(user=user)))

    def test_has_delete_permission_superuser(self):
        """
        Test superuser can delete
        """
        
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

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user), obj=Variable.objects.get(pk=3)))
        
    def test_has_delete_permission_allowed_and_authenticated(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has delete variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is NOT set
        
        User can delete
        """

        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
        self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))   
             
    def test_has_delete_permission_not_allowed_and_authenticated(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has NOT delete variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is NOT set
        
        User can delete
        """

        base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        self.assertFalse(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))        
        
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_delete_permission_and_authenticated_with_restrictions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has delete variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete
        Request is POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_delete_permission_on_post_and_authenticated_with_restrictions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has NOT delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete
        Request is POST
        """
  
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
              
    def test_has_delete_permission_and_authenticated_and_application_permissions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has NOT delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user)))
              
    def test_has_delete_permission_and_authenticated_and_other_application_permissions(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has NOT delete variable permission
        - has view/edit permission on 'app2'
        - restriction per application is set
        
        User can delete
        """

        Application.objects.get(pk=2).save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequestWithApplication(user=user)))
            
    def test_has_delete_permission_with_application_permission_and_variable_without_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has NOT delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User cannot delete variable
        variable do not reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_delete_permission_allowed_and_restriction_on_application_variable_not_linked_to_application(self):
        """
        Delete variable not linked to application without being allowed to delete variable
        user:
        - is authenticated
        - has NOT delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can NOT delet variable without application
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertFalse(base_admin.has_delete_permission(request=MockRequestEmptyApplication(user=user))) 
            
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions_variable_without_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has delete variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete variable
        variable do not reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=1)))
            
    def test_has_delete_permission_allowed_and_authenticated_with_restrictions_variable_with_application(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has NOT delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete application
        variable reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
            
    def test_has_delete_permission_and_authenticated_with_restrictions_variable_with_application2(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete application
        variable reference application
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user), obj=Variable.objects.get(pk=3)))
              
    def test_has_delete_permission_and_authenticated_none_variable(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has delete variable permission
        - has NOT view/edit permission on 'app1'
        - restriction per application is set
        
        User can delete variable
        variable is NONE
        method is not POST
        """
   
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='delete_variable')))
            self.assertTrue(base_admin.has_delete_permission(request=MockRequest(user=user)))
            
    def test_has_delete_permission_on_get_and_authenticated_none_variable_and_application_permission(self):
        """
        delete variable on application
        user:
        - is authenticated
        - has NOT delete variable permission
        - has view/edit permission on 'app1'
        - restriction per application is set
        
        User can see 'delete' on variable
        variable is NONE
        method is not POST
        """

        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            base_admin = BaseServerModelAdmin(model=Variable, admin_site=AdminSite())
            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
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
        Check that standard user will not have right to see protected variable
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
     