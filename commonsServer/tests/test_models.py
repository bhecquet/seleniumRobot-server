from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from variableServer.models import Application, TestEnvironment, Version


class TestModelPermissionsCreation(TestCase):

    def _assert_application_permissions_exist(self, application_name):
        content_type = ContentType.objects.get_for_model(Application, for_concrete_model=False)
        self.assertTrue(
            Permission.objects.filter(
                codename=Application.app_variable_permission_code + application_name,
                content_type=content_type,
            ).exists()
        )
        self.assertTrue(
            Permission.objects.filter(
                codename=Application.app_result_permission_code + application_name,
                content_type=content_type,
            ).exists()
        )

    def _assert_environment_permissions_exist(self, environment_name):
        content_type = ContentType.objects.get_for_model(TestEnvironment, for_concrete_model=False)
        self.assertTrue(
            Permission.objects.filter(
                codename=TestEnvironment.env_variable_permission_code + environment_name,
                content_type=content_type,
            ).exists()
        )
        self.assertTrue(
            Permission.objects.filter(
                codename=TestEnvironment.env_result_permission_code + environment_name,
                content_type=content_type,
            ).exists()
        )

    def test_application_permissions_created_on_create(self):
        application_name = "app_permission_create"
        Application.objects.create(name=application_name)

        self._assert_application_permissions_exist(application_name)

    def test_application_permissions_created_on_update(self):
        application = Application.objects.create(name="app_permission_before_update")
        application.name = "app_permission_after_update"
        application.save()

        self._assert_application_permissions_exist("app_permission_after_update")

    def test_environment_permissions_created_on_create(self):
        environment_name = "ENV_PERMISSION_CREATE"
        TestEnvironment.objects.create(name=environment_name)

        self._assert_environment_permissions_exist(environment_name)

    def test_environment_permissions_created_on_update(self):
        environment = TestEnvironment.objects.create(name="ENV_PERMISSION_BEFORE_UPDATE")
        environment.name = "ENV_PERMISSION_AFTER_UPDATE"
        environment.save()

        self._assert_environment_permissions_exist("ENV_PERMISSION_AFTER_UPDATE")


class TestVersionModel(TestCase):

    def test_version_str(self):
        application = Application.objects.create(name="my-app")
        version = Version.objects.create(application=application, name="1.2.3")

        self.assertEqual("my-app-1.2.3", str(version))

    def test_previous_versions_returns_only_same_application_sorted(self):
        app1 = Application.objects.create(name="app-v1")
        app2 = Application.objects.create(name="app-v2")
        Version.objects.create(application=app1, name="1.0")
        Version.objects.create(application=app1, name="10.0")
        current = Version.objects.create(application=app1, name="2.0")
        Version.objects.create(application=app1, name="1.5")
        Version.objects.create(application=app1, name="3.0")
        Version.objects.create(application=app2, name="0.9")

        previous_versions = current.previous_versions()

        self.assertEqual(["1.0", "1.5"], [v.name for v in previous_versions])

    def test_next_versions_returns_only_same_application_sorted_and_includes_current(self):
        app1 = Application.objects.create(name="app-v3")
        app2 = Application.objects.create(name="app-v4")
        Version.objects.create(application=app1, name="1.0")
        current = Version.objects.create(application=app1, name="2.0")
        Version.objects.create(application=app1, name="2.1")
        Version.objects.create(application=app1, name="13.0")
        Version.objects.create(application=app2, name="9.9")

        next_versions = current.next_versions()

        self.assertEqual(["2.0", "2.1", "13.0"], [v.name for v in next_versions])


class TestEnvironmentModel(TestCase):

    def test_get_parent_environments_without_parent_returns_empty_list(self):
        environment = TestEnvironment.objects.create(name="ENV_NO_PARENT")

        self.assertEqual([], environment.get_parent_environments())

    def test_get_parent_environments_with_direct_parent(self):
        parent = TestEnvironment.objects.create(name="ENV_PARENT")
        environment = TestEnvironment.objects.create(name="ENV_CHILD", genericEnvironment=parent)

        self.assertEqual([parent], environment.get_parent_environments())

    def test_get_parent_environments_with_parent_chain(self):
        root = TestEnvironment.objects.create(name="ENV_ROOT")
        parent = TestEnvironment.objects.create(name="ENV_PARENT_CHAIN", genericEnvironment=root)
        environment = TestEnvironment.objects.create(name="ENV_CHILD_CHAIN", genericEnvironment=parent)

        self.assertEqual([parent, root], environment.get_parent_environments())

    def test_get_parent_environments_ignores_self_reference(self):
        environment = TestEnvironment.objects.create(name="ENV_SELF")
        environment.genericEnvironment = environment
        environment.save()

        self.assertEqual([], environment.get_parent_environments())
