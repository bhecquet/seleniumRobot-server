from rest_framework.test import APITransactionTestCase

from commonsServer.tests.test_parent import TestParent
from hashed_auth.models import Token


class TestApi(APITransactionTestCase, TestParent):
    
    def _create_and_authenticate_user_with_permissions(self, permissions):
        """
        @param permissions: example: Permission.objects.filter(Q(codename='add_variable') | Q(codename='change_variable'), content_type=ct)
        """
        user = super().create_user_with_permissions(permissions)
        self.client.force_authenticate(user=user)

        token = Token.objects.get_or_create(user=user)[0]
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.raw_key)

        return user, self.client