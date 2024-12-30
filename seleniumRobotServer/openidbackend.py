'''
Created on 3 juin 2020

@author: S047432
'''
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from seleniumRobotServer.CommonBackend import CommonBackend
from django.contrib.auth.backends import ModelBackend

class NameOIDCAB(OIDCAuthenticationBackend, CommonBackend):
    """
    Class tweaking behaviour of OpenId connect
    Users are searched by name, not email, in case of LDAP connection behind the scene
    """
    
    def filter_users_by_claims(self, claims):
        name = claims.get('sub')
        if not name:
            return self.UserModel.objects.none()
        
        return self.UserModel.objects.filter(username__iexact=name)
    
    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed."""

        scopes = self.get_settings('OIDC_RP_SCOPES', 'sub')
        if 'sub' in scopes.split():
            return 'sub' in claims

        return True
    
    
    def create_user(self, claims):
        """Return object for a newly created user account."""
        username = claims['sub']
        member_of = claims.get('acr', {}).get('values', [])
        
        is_staff = len(list(set(member_of).intersection(self.get_settings('OIDC_IS_STAFF_GROUP_NAMES', [])))) > 0
        is_superuser = len(list(set(member_of).intersection(self.get_settings('OIDC_IS_SUPERUSER_GROUP_NAMES', [])))) > 0
        
        user = self.UserModel.objects.create_user(username, is_staff=is_staff, is_superuser=is_superuser)
        
        return user

    def update_user(self, user, claims):
        """
        Update user permissions
        """
        member_of = claims.get('acr', {}).get('values', [])
        
        is_staff = len(list(set(member_of).intersection(self.get_settings('OIDC_IS_STAFF_GROUP_NAMES', [])))) > 0
        is_superuser = len(list(set(member_of).intersection(self.get_settings('OIDC_IS_SUPERUSER_GROUP_NAMES', [])))) > 0
        
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        
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
    
