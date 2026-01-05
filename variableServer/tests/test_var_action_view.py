# -*- coding: utf-8 -*-
'''
'''
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.test.client import Client
from django.urls.base import reverse

from variableServer.models import Variable, Application
from variableServer.tests.test_admin import TestAdmin


class TestVarActionView(TestAdmin):

    fixtures = ['varServer']

    def setUp(self)->None:
        TestAdmin.setUp(self)

        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
        Application.objects.get(pk=777).save()

    def _test_copy_variable(self, permissions, post_data, number_of_created_variables):

        var1 = Variable.objects.get(id=3)
        existing_variables = len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1))

        user, client = self._create_and_authenticate_user_with_permissions(permissions)
        response = client.post(reverse('copy_variables'), data=post_data)
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        # check new variable creation
        self.assertEqual(len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1)), existing_variables + number_of_created_variables)
        return response

    def _test_download_variable(self, permissions):
        user, client = self._create_and_authenticate_user_with_permissions(permissions)
        response = client.get(reverse('download_variable', kwargs={'var_id': 666}))
        return response

    def test_copy_variables_ko_no_permissions(self):
        """
        When there are no permission, user can NOT copy variables
        applications specific permissions are disabled
        """
        self._test_copy_variable(Permission.objects.none(),
                                 {'ids': '3', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                 0)

    def test_copy_variables_ok_global_add_permission(self):
        """
        Nominal case, copy one variable with global add_variable permission
        applications specific permissions are disabled
        """
        self._test_copy_variable(Permission.objects.filter(Q(codename='add_variable')),
                                 {'ids': '3', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                 1)

    def test_copy_variables_ko_application_permission(self):
        """
        Nominal case, can NOT copy variable when user has application specific permission and restriction on applications are not set
        applications specific permissions are disabled
        """
        response = self._test_copy_variable(Permission.objects.filter(Q(codename='can_view_application_app1')),
                                            {'ids': '3', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                            0)

    def test_copy_variables_ok_application_permission_and_application_restriction(self):
        """
        User:
        - has app1 permission
        - has NOT add variable permission
        applications specific permissions are enabled

        User can copy variable
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_copy_variable(Permission.objects.filter(Q(codename='can_view_application_app1')),
                                     {'ids': '3', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                     1)

    def test_copy_variables_ko_application_permission_and_application_restriction_copy_to_no_app(self):
        """
        copy variable to no application
        User:
        - has app1 permission
        - has NOT add variable permission
        applications specific permissions are enabled

        User can NOT copy variable
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_copy_variable(Permission.objects.filter(Q(codename='can_view_application_app1')),
                                     {'ids': '3', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                     0)

    def test_copy_variables_ok_global_permission_and_application_restriction(self):
        """
        User:
        - has NOT app1 permission
        - has add variable permission
        applications specific permissions are enabled

        User can copy variable
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_copy_variable(Permission.objects.filter(Q(codename='add_variable')),
                                     {'ids': '3', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                     1)

    def test_copy_variables_ko_change_global_permission_and_application_restriction(self):
        """
        User:
        - has NOT app1 permission
        - has change variable permission
        applications specific permissions are enabled

        User can NOT copy variable
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_copy_variable(Permission.objects.filter(Q(codename='change_variable')),
                                     {'ids': '3', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                     0)

    def test_copy_variables_ko_wrong_application_and_application_restriction(self):
        """
        User:
        - has app1 permission
        - has NOT add variable permission
        applications specific permissions are enabled

        User can NOT copy variable has it has no permission on app2 (destination application)
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            existing_variables = len(Variable.objects.filter(application__id=2))
            self._test_copy_variable(Permission.objects.filter(Q(codename='can_view_application_app1')),
                                     {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'},
                                     0)

            # no new variable created
            self.assertEqual(existing_variables, len(Variable.objects.filter(application__id=2)))


    def test_copy_variables_ko_wrong_application_and_application_restriction2(self):
        """
        User:
        - has app1 permission
        - has NOT add variable permission
        applications specific permissions are enabled

        User can NOT copy variable has it has no permission on app2 (destination application)
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):

            var1 = Variable.objects.get(id=301)
            existing_variables = len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1))

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = client.post(reverse('copy_variables'), data={'ids': '301', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'})
            self.assertEqual(response.status_code, 302, "server did not reply as expected")

            # check new variable creation
            self.assertEqual(len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1)), existing_variables)

    def test_copy_variables_ko_no_application_for_variable_and_application_restriction2(self):
        """
        Copy a variable that does not belong to any application
        User:
        - has app1 permission
        - has NOT add variable permission
        applications specific permissions are enabled

        User can NOT copy variable has it has no permission on initial variable
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):

            var1 = Variable.objects.get(id=1)
            existing_variables = len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1))

            user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
            response = client.post(reverse('copy_variables'), data={'ids': '1', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'})
            self.assertEqual(response.status_code, 302, "server did not reply as expected")

            # check new variable creation
            self.assertEqual(len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1)), existing_variables)

    def test_copy_variables_ok_with_tests(self):
        """
        Nominal case, copy one variable
        """
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        response = client.post(reverse('copy_variables'), data={'ids': '1', 'test': ['1', '2'], 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'})
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        # check new var has been created
        var1 = Variable.objects.get(id=1)

        self.assertEqual(len(Variable.objects.filter(name=var1.name).filter(value=var1.value).filter(application__id=1).filter(test__id=1)), 1, "new variable has not been created" )

    def test_copy_variables_ok_with_reservable(self):
        """
        Nominal case, copy one variable which is reservable
        """
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        response = client.post(reverse('copy_variables'), data={'ids': '1', 'application': '1', 'reservable': 'on', 'nexturl': '/admin/variableServer/variable/?application=1'})
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        # check new var has been created
        var1 = Variable.objects.get(id=1)

        self.assertEqual(len(Variable.objects.filter(name=var1.name, value=var1.value, application__id=1, reservable=True)), 1, "new variable has not been created" )

    def test_copy_variables_ko(self):
        """
        Try to copy a variable with an application that does not exist
        """
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable')))
        response = client.post(reverse('copy_variables'), data={'ids': '1', 'application': '120', 'nexturl': '/admin/variableServer/variable/?application=1'})
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        var1 = Variable.objects.get(id=1)

        self.assertEqual(len(Variable.objects.filter(name=var1.name).filter(value=var1.value)), 2, "new variable should have been created" )

    def test_copy_variables_ko2(self):
        """
        Try to copy a variable that does not exist
        """
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_variable') | Q(codename='view_variable')))
        response = client.post(reverse('copy_variables'), data={'ids': '550', 'nexturl': '/admin/variableServer/variable/?application=1'}, follow=True)
        self.assertEqual(response.status_code, 200, "server did not reply as expected")

        self.assertTrue(list(response.context['messages'])[0].message.find("has not been copied"))

    ### change variables ###


    def _test_change_variables(self, permisssions, post_data):
        """
        Change one variable from app1 to app2
        """
        user, client = self._create_and_authenticate_user_with_permissions(permisssions)
        response = client.post(reverse('change_variables'), data=post_data)
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

    def test_change_variables_no_permission(self):
        """
        User:
        - has NOT change permission
        - has NOT app1 / app2 permission
        applications specific permissions are disabled

        change NOT allowed
        """
        self._test_change_variables(Permission.objects.none(), {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
        var1 = Variable.objects.get(id=3)
        self.assertEqual(var1.application.name, "app1", "application for variable should have not been moved to 'app2'")

    def test_change_variables_global_change_permissioçn(self):
        """
        User:
        - has change permission
        - has NOT app1 / app2 permission
        applications specific permissions are disabled

        change allowed
        """
        self._test_change_variables(Permission.objects.filter(Q(codename='change_variable')), {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
        var1 = Variable.objects.get(id=3)
        self.assertEqual(var1.application.name, "app2", "application for variable should have been moved to 'app2'")

    def test_change_variables_application_permission(self):
        """
        User:
        - has NOT change permission
        - has app1 / app2 permission
        applications specific permissions are disabled

        change NOT allowed
        """
        self._test_change_variables(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='can_view_application_app2')), {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
        var1 = Variable.objects.get(id=3)
        self.assertEqual(var1.application.name, "app1", "application for variable should have not been moved to 'app2'")

    def test_change_variables_global_change_permission_and_permission_restrictions(self):
        """
        User:
        - has change permission
        - has NOT app1 / app2 permission
        applications specific permissions are enabled

        change allowed
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_change_variables(Permission.objects.filter(Q(codename='change_variable')), {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
            var1 = Variable.objects.get(id=3)
            self.assertEqual(var1.application.name, "app2", "application for variable should have been moved to 'app2'")

    def test_change_variables_application_permission_and_permission_restrictions(self):
        """
        User:
        - has NOT change permission
        - has app1 / app2 permission
        applications specific permissions are enabled

        change allowed
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_change_variables(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='can_view_application_app2')),
                                        {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
            var1 = Variable.objects.get(id=3)
            self.assertEqual(var1.application.name, "app2", "application for variable should have not been moved to 'app2'")

    def test_change_variables_application1_permission_and_permission_restrictions(self):
        """
        User:
        - has NOT change permission
        - has app1 permission
        - has NOT app2 permission
        applications specific permissions are enabled

        change NOT allowed because user has no right on destination application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_change_variables(Permission.objects.filter(Q(codename='can_view_application_app1')),
                                        {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
            var1 = Variable.objects.get(id=3)
            self.assertEqual(var1.application.name, "app1", "application for variable should have not been moved to 'app2'")

    def test_change_variables_application2_permission_and_permission_restrictions(self):
        """
        User:
        - has NOT change permission
        - has app1 permission
        - has NOT app2 permission
        applications specific permissions are enabled

        change NOT allowed because user has no right on source application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_change_variables(Permission.objects.filter(Q(codename='can_view_application_app2')),
                                        {'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
            var1 = Variable.objects.get(id=3)
            self.assertEqual(var1.application.name, "app1", "application for variable should have not been moved to 'app2'")

    def test_change_variables_application1_permission_and_permission_restrictions_destination_None(self):
        """
        Change applicatin to 'None'

        User:
        - has NOT change permission
        - has app1 permission
        - has NOT app2 permission
        applications specific permissions are enabled

        change NOT allowed because user has no right on variables not linked to applications
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_change_variables(Permission.objects.filter(Q(codename='can_view_application_app1')),
                                        {'ids': '3', 'nexturl': '/admin/variableServer/variable/?application=1'})
            var1 = Variable.objects.get(id=3)
            self.assertEqual(var1.application.name, "app1", "application for variable should have not been moved to 'app2'")

    def test_change_variables_application1_permission_and_permission_restrictions_no_app_in_variable(self):
        """
        Check user cannot change a variable not linked to application

        User:
        - has NOT change permission
        - has app1 permission
        applications specific permissions are enabled

        change NOT allowed because user has no right on destination application
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._test_change_variables(Permission.objects.filter(Q(codename='can_view_application_app1')),
                                        {'ids': '1', 'application': '1', 'nexturl': '/admin/variableServer/variable/?application=1'})
            var1 = Variable.objects.get(id=1)
            self.assertIsNone(var1.application, "application for variable should have not been moved to 'app2'")


    def test_change_variables_ok(self):
        """
        Change one variable from app1 to app2
        """
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        response = client.post(reverse('change_variables'), data={'ids': '3', 'application': '2', 'nexturl': '/admin/variableServer/variable/?application=1'})
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        var1 = Variable.objects.get(id=3)
        self.assertEqual(var1.application.name, "app2", "application for variable should have been moved to 'app2'")

    def test_change_variables_ok_with_tests(self):
        """
        Add tests to a variable
        """
        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        response = client.post(reverse('change_variables'), data={'ids': '3', 'test': ['1', '2'], 'nexturl': '/admin/variableServer/variable/?application=1'})
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        var1 = Variable.objects.get(id=3)
        self.assertEqual(len(var1.test.all()), 2, "2 tests should have been added")

    def test_change_variables_ok_with_reservable(self):
        """
        Change 'reservable'
        """

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        response = client.post(reverse('change_variables'), data={'ids': '3', 'reservable': 'on', 'nexturl': '/admin/variableServer/variable/?application=1'})
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        var1 = Variable.objects.get(id=3)
        self.assertTrue(var1.reservable, "variable should become reservable")

        # change state of variable to 'not reservable'
        response = client.post(reverse('change_variables'), data={'ids': '3', 'nexturl': '/admin/variableServer/variable/?application=1'})
        self.assertEqual(response.status_code, 302, "server did not reply as expected")

        var1 = Variable.objects.get(id=3)
        self.assertFalse(var1.reservable, "variable should become unreservable")

    def test_change_variables_ko(self):
        """
        Check we cannot change a variable that does not exist
        """

        user, client = self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_variable')))
        response = client.post(reverse('change_variables'), data={'ids': '550', 'nexturl': '/admin/variableServer/variable/?application=1'}, follow=True)
        self.assertEqual(response.status_code, 200, "server did not reply as expected")
        self.assertTrue(list(response.context['messages'])[0].message.find("has not been modified") > -1)


    #DOWNLOAD VAR FILE
    def test_download_var_file_no_security_not_authenticated(self):
        """
        Check that even with security disabled, we can't access var file without authentication
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            testfile = Client().get(reverse('download_variable', kwargs={'var_id': 666}))
            self.assertEqual(401, testfile.status_code)

    def test_download_var_file_security_not_authenticated(self):
        """
        Check that with security enabled, we cannot access var file without authentication
        """
        testfile = Client().get(reverse('download_variable', kwargs={'var_id': 666}))
        self.assertEqual(401, testfile.status_code)

    def test_download_var_file_security_authenticated_no_permission(self):
        """
        Check that with
        - security enabled
        - no permission on requested application
        We cannot download var file
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            testfile = self._test_download_variable(Permission.objects.filter(Q(codename='can_view_application_app2')))
            self.assertEqual(401, testfile.status_code)

    def test_download_var_file_security_authenticated_with_permission(self):
        """
        Check that with
        - security enabled
        - permission on requested application
        We can download var file
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            testfile = self._test_download_variable(Permission.objects.filter(Q(codename='can_view_application_test')))
            self.assertEqual(200, testfile.status_code)

    def test_download_variable_file_ko_no_permissions(self):
        """
        When there are no permission, user can NOT download variable file
        applications specific permissions are disabled
        """
        testfile = self._test_download_variable(Permission.objects.none())
        self.assertEqual(testfile.status_code, 401)

    def test_download_variable_file_ok(self):
        """
        With permission on the application, user CAN download variable file
        """
        testfile = self._test_download_variable(Permission.objects.filter(Q(codename='view_variable')))
        self.assertEqual(testfile.status_code, 200)

    def test_download_variable_file_ok_app_perm(self):
        """
        With permission on the application, user CAN download variable file
        """
        testfile = self._test_download_variable(Permission.objects.filter(Q(codename='can_view_application_test')))
        self.assertEqual(testfile.status_code, 200)

    def test_download_variable_file_ko_wrong_permission(self):
        """
        With permission on another application, user can NOT download variable file
        """
        testfile = self._test_download_variable(Permission.objects.filter(Q(codename='can_view_application_app1') | Q(codename='view_variable')))
        self.assertEqual(testfile.status_code, 401)

    def test_download_variable_file_ok_global_permission_and_application_restriction(self):
        """
        User:
        - has NOT test permission
        - has view variable permission
        applications specific permissions are enabled

        User can download variable
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            testfile = self._test_download_variable(Permission.objects.filter(Q(codename='view_variable')))
            self.assertEqual(testfile.status_code, 200)
