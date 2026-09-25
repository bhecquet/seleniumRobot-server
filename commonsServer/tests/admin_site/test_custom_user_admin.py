import datetime
import variableServer

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from commonsServer.admin import CustomUserAdmin
from commonsServer.tests.test_parent import TestWebAndAdmin
from variableServer.models import Application, TestEnvironment
from commonsServer.tests.test_api import TestApi

User = get_user_model()


class MockRequest:
    """Objet Request minimal utilisé par Django Admin."""
    pass


class TestCustomUserAdmin(TestWebAndAdmin):

    fixtures = ['commons_server']

    def setUp(self):
        super().setUp()

        self.user = User.objects.create(username="bob")
        Application.objects.get(pk=1).save()
        TestEnvironment.objects.get(pk=1).save()

        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)
        self.content_type_environment = ContentType.objects.get_for_model(variableServer.models.TestEnvironment, for_concrete_model=False)

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
        client.force_login(admin_user)
        response = client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(3, len(user_permissions))
        self.assertTrue('variableServer.can_view_application_app1' in user_permissions)
        self.assertTrue('variableServer.can_view_results_application_app1' in user_permissions)
        self.assertTrue('snapshotServer.view_testsession' in user_permissions)

    def test_view_session_permission_given(self):
        """
        Check the view session permission is given if user has permission on application results
        """

        can_edit_variable_permission = Permission.objects.get(codename='can_view_results_application_app1', content_type=self.content_type_application)

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
        client.force_login(admin_user)
        response = client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(2, len(user_permissions))
        self.assertFalse('variableServer.can_view_application_app1' in user_permissions)
        self.assertTrue('variableServer.can_view_results_application_app1' in user_permissions)
        self.assertTrue('snapshotServer.view_testsession' in user_permissions)

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
        client.force_login(admin_user)
        response = client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(0, len(user_permissions))

    def test_view_result_for_environment_permission_given(self):
        """
        Check the view result permission is given if user has permission on environment variables
        """

        can_edit_variable_permission = Permission.objects.get(codename='can_view_environment_DEV', content_type=self.content_type_environment)

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

        admin_user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_user', content_type=self.content_type_environment)))
        admin_user.is_superuser = True
        admin_user.save()
        client.force_login(admin_user)
        response = client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(3, len(user_permissions))
        self.assertTrue('variableServer.can_view_environment_DEV' in user_permissions)
        self.assertTrue('variableServer.can_view_results_environment_DEV' in user_permissions)
        self.assertTrue('snapshotServer.view_testsession' in user_permissions)

    def test_view_session_for_environment_permission_given(self):
        """
        Check the view session permission is given if user has permission on environment results
        """

        can_edit_variable_permission = Permission.objects.get(codename='can_view_results_environment_DEV', content_type=self.content_type_environment)

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

        admin_user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_user', content_type=self.content_type_environment)))
        admin_user.is_superuser = True
        admin_user.save()
        client.force_login(admin_user)
        response = client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(2, len(user_permissions))
        self.assertFalse('variableServer.can_view_environment_DEV' in user_permissions)
        self.assertTrue('variableServer.can_view_results_environment_DEV' in user_permissions)
        self.assertTrue('snapshotServer.view_testsession' in user_permissions)

    def test_view_result_for_environment_permission_not_given(self):
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
        client.force_login(admin_user)
        response = client.post(f'/admin/auth/user/{self.user.id}/change/', data=form_data)
        self.assertEqual(302, response.status_code)
        user_permissions = self.user.get_all_permissions()
        self.assertEqual(0, len(user_permissions))


class TestCustomUserAdminEffectivePermissions(TestWebAndAdmin):
    """
    Tests for the 'effective_permissions' read-only field added to the User admin change view
    """

    fixtures = ['commons_server']

    def setUp(self):
        super().setUp()

        self.user = User.objects.create(username="bob")
        Application.objects.get(pk=1).save()
        TestEnvironment.objects.get(pk=1).save()

        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)
        self.admin = CustomUserAdmin(User, AdminSite())

    def test_effective_permissions_field_is_readonly(self):
        """
        Check the field is exposed as read-only so it cannot be edited from the form
        """
        self.assertIn('effective_permissions', self.admin.readonly_fields)

    def test_effective_permissions_in_fieldsets(self):
        """
        Check the field is added to the fieldsets so it is displayed on the change page
        """
        fieldsets = self.admin.get_fieldsets(MockRequest(), self.user)
        permission_fields = fieldsets[2][1]['fields']
        self.assertIn('effective_permissions', permission_fields)

    def test_effective_permissions_returns_empty_string_for_unsaved_user(self):
        """
        Check no error occurs and an empty value is returned when there is no user instance (add view)
        """
        self.assertEqual('', self.admin.effective_permissions(None))
        self.assertEqual('', self.admin.effective_permissions(User(username='new_user')))

    def test_effective_permissions_returns_no_permission(self):
        """
        Check the field is empty when the user has no permission
        """
        self.assertEqual('', self.admin.effective_permissions(self.user))

    def test_effective_permissions_returns_direct_permissions(self):
        """
        Check the field lists the permissions directly granted to the user
        """
        permission = Permission.objects.get(codename='can_view_application_app1', content_type=self.content_type_application)
        self.user.user_permissions.add(permission)

        content = self.admin.effective_permissions(self.user)
        self.assertIn('variableServer.can_view_application_app1', content)

    def test_effective_permissions_returns_permissions_from_group(self):
        """
        Check the field also lists permissions inherited from a group the user belongs to
        """
        from django.contrib.auth.models import Group

        permission = Permission.objects.get(codename='can_view_application_app1', content_type=self.content_type_application)
        group = Group.objects.create(name='group1')
        group.permissions.add(permission)
        self.user.groups.add(group)

        content = self.admin.effective_permissions(self.user)
        self.assertIn('variableServer.can_view_application_app1', content)

    def test_effective_permissions_displayed_in_change_view(self):
        """
        Check the permissions are actually rendered on the User change page
        """
        permission = Permission.objects.get(codename='can_view_application_app1', content_type=self.content_type_application)
        self.user.user_permissions.add(permission)

        admin_user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_user', content_type=self.content_type_application)))
        admin_user.is_superuser = True
        admin_user.save()
        client.force_login(admin_user)

        response = client.get(f'/admin/auth/user/{self.user.id}/change/')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'variableServer.can_view_application_app1')


class TestCustomUserAdminLdapPermissions(TestWebAndAdmin):
    """
    Tests for the resolution of permissions granted through LDAP group membership.

    django-auth-ldap only resolves and caches these permissions on the transient
    'user.ldap_user' attribute when the user actually authenticates through LDAP
    in the current process. Since the admin works with a User freshly reloaded
    from the database, CustomUserAdmin._get_ldap_group_permissions() queries the
    configured LDAP backends directly (using their service account) instead.
    As there is no real LDAP server available for tests, the LDAP backend and
    the internal '_LDAPUser' helper are mocked.
    """

    fixtures = ['commons_server']

    def setUp(self):
        super().setUp()

        self.user = User.objects.create(username="bob")
        Application.objects.get(pk=1).save()

        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)
        self.admin = CustomUserAdmin(User, AdminSite())

    def test_no_ldap_permission_when_no_backend_configured(self):
        """
        Check that, without any LDAP backend registered (default test settings), no LDAP
        lookup is attempted and the field only reflects Django native permissions
        """
        from unittest.mock import patch

        with patch('commonsServer.admin._LDAPUser') as mock_ldap_user_class:
            self.assertEqual(set(), self.admin._get_ldap_group_permissions(self.user))
            mock_ldap_user_class.assert_not_called()

    def test_ldap_group_permissions_are_added_to_effective_permissions(self):
        """
        Check permissions returned by the LDAP backend for the user's LDAP groups are
        included in the computed effective permissions
        """
        from unittest.mock import MagicMock, patch
        from django_auth_ldap.backend import LDAPBackend

        ldap_backend = LDAPBackend()
        mock_ldap_user = MagicMock()
        mock_ldap_user.get_group_permissions.return_value = {'variableServer.can_view_application_app1'}

        with patch('commonsServer.admin.get_backends', return_value=[ldap_backend]), \
             patch('commonsServer.admin._LDAPUser', return_value=mock_ldap_user) as mock_ldap_user_class:

            content = self.admin.effective_permissions(self.user)

            mock_ldap_user_class.assert_called_once_with(ldap_backend, username=self.user.username)
            self.assertIn('variableServer.can_view_application_app1', content)

    def test_ldap_group_permissions_merged_with_direct_permissions(self):
        """
        Check LDAP group permissions are merged (union, no duplicates) with permissions
        directly granted to the user in Django
        """
        from unittest.mock import MagicMock, patch
        from django_auth_ldap.backend import LDAPBackend

        direct_permission = Permission.objects.get(codename='can_view_application_app1', content_type=self.content_type_application)
        self.user.user_permissions.add(direct_permission)

        ldap_backend = LDAPBackend()
        mock_ldap_user = MagicMock()
        mock_ldap_user.get_group_permissions.return_value = {
            'variableServer.can_view_application_app1',  # already granted directly, should not be duplicated
            'variableServer.can_view_results_application_app1',
        }

        with patch('commonsServer.admin.get_backends', return_value=[ldap_backend]), \
             patch('commonsServer.admin._LDAPUser', return_value=mock_ldap_user):

            content = self.admin.effective_permissions(self.user)

            self.assertEqual(1, content.count('variableServer.can_view_application_app1'))
            self.assertIn('variableServer.can_view_results_application_app1', content)

    def test_non_ldap_backends_are_ignored(self):
        """
        Check that authentication backends which are not LDAP backends are skipped and
        never queried through '_LDAPUser'
        """
        from unittest.mock import patch
        from django.contrib.auth.backends import ModelBackend

        with patch('commonsServer.admin.get_backends', return_value=[ModelBackend()]), \
             patch('commonsServer.admin._LDAPUser') as mock_ldap_user_class:

            self.assertEqual(set(), self.admin._get_ldap_group_permissions(self.user))
            mock_ldap_user_class.assert_not_called()

    def test_ldap_errors_are_handled_gracefully(self):
        """
        Check that an error while querying the LDAP server (unreachable server, unknown
        user, ...) does not break the admin page and simply results in no LDAP
        permission being added
        """
        from unittest.mock import patch
        from django_auth_ldap.backend import LDAPBackend

        ldap_backend = LDAPBackend()

        with patch('commonsServer.admin.get_backends', return_value=[ldap_backend]), \
             patch('commonsServer.admin._LDAPUser', side_effect=Exception('LDAP server unreachable')):

            permissions = self.admin._get_ldap_group_permissions(self.user)
            self.assertEqual(set(), permissions)

            # effective_permissions must not raise either and keep displaying native permissions
            content = self.admin.effective_permissions(self.user)
            self.assertEqual('', content)

    def test_multiple_ldap_backends_are_all_queried(self):
        """
        Check permissions from several configured LDAP backends (e.g. LDAPBackend1,
        LDAPBackend2) are all collected
        """
        from unittest.mock import MagicMock, patch
        from django_auth_ldap.backend import LDAPBackend

        class LDAPBackendA(LDAPBackend):
            settings_prefix = "AUTH_LDAP_1_"

        class LDAPBackendB(LDAPBackend):
            settings_prefix = "AUTH_LDAP_2_"

        backend_a = LDAPBackendA()
        backend_b = LDAPBackendB()

        mock_ldap_user_a = MagicMock()
        mock_ldap_user_a.get_group_permissions.return_value = {'variableServer.can_view_application_app1'}
        mock_ldap_user_b = MagicMock()
        mock_ldap_user_b.get_group_permissions.return_value = {'variableServer.can_view_results_application_app1'}

        def fake_ldap_user(backend, username):
            return mock_ldap_user_a if backend is backend_a else mock_ldap_user_b

        with patch('commonsServer.admin.get_backends', return_value=[backend_a, backend_b]), \
             patch('commonsServer.admin._LDAPUser', side_effect=fake_ldap_user):

            permissions = self.admin._get_ldap_group_permissions(self.user)

            self.assertEqual(
                {'variableServer.can_view_application_app1', 'variableServer.can_view_results_application_app1'},
                permissions,
            )

