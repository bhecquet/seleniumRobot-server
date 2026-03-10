import datetime
import variableServer

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from commonsServer.admin import CustomUserAdmin
from variableServer.models import Application
from commonsServer.tests.test_api import TestApi

User = get_user_model()


class MockRequest:
    """Objet Request minimal utilisé par Django Admin."""
    pass


class TestAdmin(TestApi):

    fixtures = ['commons_server']

    def setUp(self):
        self.user = User.objects.create(username="bob")
        Application.objects.get(pk=1).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)

    def test_view_result_permission_given(self):
        """
        Check the view result permission is given if user has permission on application variables
        """

        can_edit_variable_permission = Permission.objects.get(codename='can_view_application_app1', content_type=self.content_type_application)

        # simulation de données venant du formulaire admin
        form_data = {
            "username": "bob",
            "first_name": "bob",
            "last_name": "bob",
            "date_joined_0": datetime.datetime.today().date().isoformat(),
            "date_joined_1": datetime.datetime.today().time().isoformat(),
            "user_permissions": [can_edit_variable_permission.id],
            "_save": "Save"
        }

        admin_user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_user', content_type=self.content_type_application)))
        admin_user.is_superuser = True
        admin_user.save()
        self.client.force_login(admin_user)
        response = self.client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(2, len(user_permissions))
        self.assertTrue('variableServer.can_view_application_app1' in user_permissions)
        self.assertTrue('variableServer.can_view_results_application_app1' in user_permissions)

    def test_view_result_permission_not_given(self):
        """
        Check view results permission is not automatically given on save
        """

        # simulation de données venant du formulaire admin
        form_data = {
            "username": "bob",
            "first_name": "bob",
            "last_name": "bob",
            "date_joined_0": datetime.datetime.today().date().isoformat(),
            "date_joined_1": datetime.datetime.today().time().isoformat(),
            "user_permissions": [],
            "_save": "Save"
        }

        admin_user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_user', content_type=self.content_type_application)))
        admin_user.is_superuser = True
        admin_user.save()
        self.client.force_login(admin_user)
        response = self.client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(0, len(user_permissions))


