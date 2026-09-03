from datetime import timedelta

from django.utils import timezone

from commonsServer.tests.test_api import TestApi
from django.contrib.auth.models import Permission
from django.db.models import Q

from django.contrib.auth.models import User

class TestUserView(TestApi):

    def test_user_is_active_not_authenticated(self):
        """
        Requesting user is not authenticated => 401 is returned
        """
        User(username="user1", last_login=timezone.now() - timedelta(days=1)).save()

        response = self.client.get('/commons/api/inactiveUsers')
        self.assertEqual(401, response.status_code)

    def test_user_is_active_no_permission(self):
        """
        Requesting user is authenticated but has no permission on 'view_user' => 403 is returned
        """
        User(username="user1", last_login=timezone.now() - timedelta(days=1)).save()

        self._create_and_authenticate_user_with_permissions(Permission.objects.none())

        response = self.client.get('/commons/api/inactiveUsers')
        self.assertEqual(403, response.status_code)

    def test_user_is_active_wrong_permission(self):
        """
        Requesting user is authenticated but has a permission that is not 'view_user' => 403 is returned
        """
        User(username="user1", last_login=timezone.now() - timedelta(days=1)).save()

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_user')))

        response = self.client.get('/commons/api/inactiveUsers')
        self.assertEqual(403, response.status_code)

    def test_user_is_active_superuser_without_permission(self):
        """
        Requesting user is a superuser without explicit 'view_user' permission => access is granted
        """
        User(username="user1", last_login=timezone.now() - timedelta(days=1)).save()

        user, _ = self._create_and_authenticate_user_with_permissions(Permission.objects.none())
        user.is_superuser = True
        user.save()

        response = self.client.get('/commons/api/inactiveUsers')
        self.assertEqual(200, response.status_code)

    def test_user_is_active(self):
        """
        Nominal case
        Requesting user has permissions, no user is inactive
        :return:
        """
        User(username="user1", last_login=timezone.now() - timedelta(days=1)).save()

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_user')))

        response = self.client.get('/commons/api/inactiveUsers')
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())

    def test_user_is_not_active(self):
        """
        Nominal case
        Requesting user has permissions, a user is inactive
        :return:
        """
        User(username="user1", last_login=timezone.now() - timedelta(days=120)).save()

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_user')))

        response = self.client.get('/commons/api/inactiveUsers')
        self.assertEqual(200, response.status_code)
        user_list = response.json()
        self.assertEqual(len(user_list), 1)
        self.assertEqual(user_list[0]['username'], 'user1')

    def test_user_other_verbs_forbidden(self):
        """
        Only GET is implemented on this view, other verbs should return 405, even with all permissions granted
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_user')
                                                                                        | Q(codename='add_user')
                                                                                        | Q(codename='change_user')
                                                                                        | Q(codename='delete_user')))

        response = self.client.post('/commons/api/inactiveUsers')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/commons/api/inactiveUsers')
        self.assertEqual(405, response.status_code)
        response = self.client.patch('/commons/api/inactiveUsers')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/commons/api/inactiveUsers')
        self.assertEqual(405, response.status_code)
