from rest_framework.test import APITestCase
from django.contrib.auth.models import User, Group


class TestApi(APITestCase):
    fixtures = ['varServer.yaml']
    
    def _create_and_authenticate_user_with_permissions(self, permissions):
        """
        @param permissions: example: Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable'), content_type=ct)
        """
        
        user = User.objects.create_user(username='userApi', email='user@email.org', password='pass')
        self.client.force_authenticate(user=user)
        
        variable_users_group, created = Group.objects.get_or_create(name='Users')
        
        variable_users_group.permissions.add(*permissions)
        variable_users_group.user_set.add(user)
        
        user.is_staff = True
        user.save()
        
        return user, self.client