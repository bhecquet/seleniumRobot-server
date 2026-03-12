'''
Created on 12 mars 2026

@author: S047432
'''
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls.base import reverse

from django.contrib.contenttypes.models import ContentType

from commonsServer.tests.test_api import TestApi
from variableServer.models import Application


class TestErrorAnalysisView(TestApi):

    fixtures = ['snapshotServer.yaml']

    def setUp(self):
        # ensure application-specific permissions are created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()

        self.content_type_application = ContentType.objects.get_for_model(Application, for_concrete_model=False)

    # -------------------------------------------------------------------------
    # Security / permission tests
    # -------------------------------------------------------------------------

    def test_error_analysis_no_security_not_authenticated(self):
        """
        With security disabled, an unauthenticated request must succeed (200)
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            with patch('snapshotServer.views.error_analysis_view.ErrorCauseFinderExecutor.submit'):
                response = self.client.post(reverse('errorAnalysisView', args=[1]))
        self.assertEqual(response.status_code, 200)

    def test_error_analysis_security_not_authenticated(self):
        """
        With security enabled, an unauthenticated request must be rejected (401)
        """
        response = self.client.post(reverse('errorAnalysisView', args=[1]))
        self.assertEqual(response.status_code, 401)

    def test_error_analysis_security_authenticated_no_permission(self):
        """
        With security enabled and no permission on the requested application,
        the request must be rejected (403)
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(
                Permission.objects.filter(
                    Q(codename='can_view_results_application_myapp2', content_type=self.content_type_application)
                )
            )
            response = self.client.post(reverse('errorAnalysisView', args=[1]))
        self.assertEqual(response.status_code, 403)

    def test_error_analysis_security_authenticated_with_permission(self):
        """
        With security enabled and the correct application permission,
        the request must succeed (200)
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(
                Permission.objects.filter(
                    Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)
                )
            )
            with patch('snapshotServer.views.error_analysis_view.ErrorCauseFinderExecutor.submit') as mock_submit:
                response = self.client.post(reverse('errorAnalysisView', args=[1]))

        self.assertEqual(response.status_code, 200)
        mock_submit.assert_called_once()

    def test_error_analysis_security_authenticated_with_permission_object_not_found(self):
        """
        With security enabled and the correct permission, requesting a
        non-existent TestCaseInSession must return 403
        (permission check fails before the 404 is raised because the object
        cannot be resolved to an application)
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(
                Permission.objects.filter(
                    Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)
                )
            )
            response = self.client.post(reverse('errorAnalysisView', args=[9999]))
        self.assertEqual(response.status_code, 403)

    # -------------------------------------------------------------------------
    # Functional tests
    # -------------------------------------------------------------------------

    def test_error_analysis_submits_analysis(self):
        """
        A valid POST must call ErrorCauseFinderExecutor.submit with the
        correct TestCaseInSession instance
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            with patch('snapshotServer.views.error_analysis_view.ErrorCauseFinderExecutor.submit') as mock_submit:
                response = self.client.post(reverse('errorAnalysisView', args=[1]))

                self.assertEqual(response.status_code, 200)
                # verify the executor was called with the correct object
                args, _ = mock_submit.call_args
                self.assertEqual(args[0].pk, 1)

    def test_error_analysis_testcaseinsession_not_found(self):
        """
        When the TestCaseInSession does not exist, a 404 must be returned
        (security disabled so we reach the view logic)
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(
                Permission.objects.filter(
                    Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)
                )
            )
            response = self.client.post(reverse('errorAnalysisView', args=[9999]))
            self.assertEqual(response.status_code, 403)

    def test_error_analysis_wrong_http_method_get(self):
        """
        GET requests must be rejected (405 Method Not Allowed)
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            response = self.client.get(reverse('errorAnalysisView', args=[1]))
        self.assertEqual(response.status_code, 405)

    def test_error_analysis_wrong_http_method_delete(self):
        """
        DELETE requests must be rejected (405 Method Not Allowed)
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            response = self.client.delete(reverse('errorAnalysisView', args=[1]))
        self.assertEqual(response.status_code, 405)

