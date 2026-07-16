from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase

from snapshotServer.views.error_cause_view import save_error_cause


class TestSaveErrorCauseView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.post_data = {
            "exception": "org.openqa.selenium.NoSuchElementException",
            "errorMessage": "Element not found",
            "stepName": "Cliquer sur le bouton",
            "commentaire": "Le locator du bouton est obsolète",
            "cause": "Script",
            "testStepId": "2",
            "testCaseId": "1",
        }

    def create_post_request(self):
        request = self.factory.post(
            "/snapshot/api/save-error-cause/",
            data=self.post_data,
        )
        request.META["HTTP_REFERER"] = "/snapshot/testResults/result/11/"
        return request

    @patch("snapshotServer.views.error_cause_view.messages.success")
    @patch("snapshotServer.views.error_cause_view.ErrorCauseFromUser")
    @patch("snapshotServer.views.error_cause_view.TestCase")
    @patch("snapshotServer.views.error_cause_view.TestStep")
    def test_create_new_error_cause(
            self,
            test_step_model,
            test_case_model,
            error_cause_model,
            success_message
    ):
        test_step = Mock()
        test_case = Mock()

        test_step_model.objects.filter.return_value.first.return_value = (
            test_step
        )
        test_case_model.objects.filter.return_value.first.return_value = (
            test_case
        )

        error_cause_model.objects.filter.return_value.first.return_value = None

        response = save_error_cause(self.create_post_request())

        error_cause_model.objects.create.assert_called_once_with(
            testCase=test_case,
            testStep=test_step,
            exception="org.openqa.selenium.NoSuchElementException",
            action="Cliquer sur le bouton",
            errorMessage="Element not found",
            commentaire="Le locator du bouton est obsolète",
            type="Script",
        )

        success_message.assert_called_once()
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            "/snapshot/testResults/result/11/",
            response.url,
        )

    @patch("snapshotServer.views.error_cause_view.messages.success")
    @patch("snapshotServer.views.error_cause_view.ErrorCauseFromUser")
    @patch("snapshotServer.views.error_cause_view.TestCase")
    @patch("snapshotServer.views.error_cause_view.TestStep")
    def test_update_existing_error_cause(
            self,
            test_step_model,
            test_case_model,
            error_cause_model,
            success_message
    ):
        test_step = Mock()
        test_case = Mock()

        existing_cause = Mock()
        existing_cause.commentaire = "Ancien commentaire"

        test_step_model.objects.filter.return_value.first.return_value = (
            test_step
        )
        test_case_model.objects.filter.return_value.first.return_value = (
            test_case
        )
        error_cause_model.objects.filter.return_value.first.return_value = (
            existing_cause
        )

        response = save_error_cause(self.create_post_request())

        self.assertEqual(
            "Le locator du bouton est obsolète",
            existing_cause.commentaire,
        )
        self.assertEqual(
            "Element not found",
            existing_cause.errorMessage,
        )
        self.assertEqual("Script", existing_cause.type)

        existing_cause.save.assert_called_once()
        error_cause_model.objects.create.assert_not_called()
        success_message.assert_called_once()

        self.assertEqual(302, response.status_code)

    @patch("snapshotServer.views.error_cause_view.messages.info")
    @patch("snapshotServer.views.error_cause_view.ErrorCauseFromUser")
    @patch("snapshotServer.views.error_cause_view.TestCase")
    @patch("snapshotServer.views.error_cause_view.TestStep")
    def test_existing_identical_cause_is_not_duplicated(
            self,
            test_step_model,
            test_case_model,
            error_cause_model,
            info_message
    ):
        existing_cause = Mock()
        existing_cause.commentaire = (
            "Le locator du bouton est obsolète"
        )

        test_step_model.objects.filter.return_value.first.return_value = Mock()
        test_case_model.objects.filter.return_value.first.return_value = Mock()

        error_cause_model.objects.filter.return_value.first.return_value = (
            existing_cause
        )

        response = save_error_cause(self.create_post_request())

        existing_cause.save.assert_not_called()
        error_cause_model.objects.create.assert_not_called()
        info_message.assert_called_once()

        self.assertEqual(302, response.status_code)

    @patch("snapshotServer.views.error_cause_view.ErrorCauseFromUser")
    def test_get_request_does_not_create_error_cause(
            self,
            error_cause_model
    ):
        request = self.factory.get(
            "/snapshot/api/save-error-cause/"
        )

        response = save_error_cause(request)

        error_cause_model.objects.create.assert_not_called()
        self.assertEqual(302, response.status_code)
        self.assertEqual("/", response.url)