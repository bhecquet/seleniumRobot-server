import json
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase

from snapshotServer.views.error_cause_view import SaveErrorCauseView


class TestSaveErrorCauseView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.test_case = Mock()
        self.test_case.id = 1

        self.test_step = Mock()
        self.test_step.id = 2

        self.post_data = {
            "exception": (
                "org.openqa.selenium.NoSuchElementException"
            ),
            "errorMessage": "Element not found",
            "stepName": "Click on the button",
            "comment": "The button locator is outdated.",
            "cause": "Script",
            "testStepId": "2",
            "testCaseId": "1",
        }

    def create_post_request(self):
        return self.factory.post(
            "/snapshot/api/save-error-cause/",
            data=self.post_data,
        )

    def create_valid_form(self):
        form = Mock()
        form.is_valid.return_value = True
        form.cleaned_data = {
            "exception": (
                "org.openqa.selenium.NoSuchElementException"
            ),
            "errorMessage": "Element not found",
            "stepName": "Click on the button",
            "comment": "The button locator is outdated.",
            "cause": "Script",
            "testCaseId": self.test_case,
            "testStepId": self.test_step,
        }
        return form

    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseForm"
    )
    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseFromUser"
    )
    def test_create_new_error_cause(
            self,
            error_cause_model,
            form_class,
    ):
        form_class.return_value = self.create_valid_form()

        (
            error_cause_model.objects
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = None

        response = SaveErrorCauseView.as_view()(
            self.create_post_request()
        )

        error_cause_model.objects.create.assert_called_once_with(
            testCase=self.test_case,
            testStep=self.test_step,
            exception=(
                "org.openqa.selenium.NoSuchElementException"
            ),
            action="Click on the button",
            errorMessage="Element not found",
            comment="The button locator is outdated.",
            type="Script",
        )

        self.assertEqual(201, response.status_code)

        response_data = json.loads(response.content)

        self.assertTrue(response_data["success"])
        self.assertEqual(
            "La nouvelle cause a été enregistrée.",
            response_data["message"],
        )

    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseForm"
    )
    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseFromUser"
    )
    def test_update_existing_error_cause(
            self,
            error_cause_model,
            form_class,
    ):
        form_class.return_value = self.create_valid_form()

        existing_cause = Mock()
        existing_cause.comment = "Old comment"
        existing_cause.type = "Application"
        existing_cause.errorMessage = "Old error message"
        existing_cause.action = "Old action"

        (
            error_cause_model.objects
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = existing_cause

        response = SaveErrorCauseView.as_view()(
            self.create_post_request()
        )

        self.assertEqual(
            "The button locator is outdated.",
            existing_cause.comment,
        )
        self.assertEqual(
            "Element not found",
            existing_cause.errorMessage,
        )
        self.assertEqual(
            "Click on the button",
            existing_cause.action,
        )
        self.assertEqual("Script", existing_cause.type)

        existing_cause.save.assert_called_once()
        error_cause_model.objects.create.assert_not_called()

        self.assertEqual(200, response.status_code)

        response_data = json.loads(response.content)

        self.assertTrue(response_data["success"])
        self.assertEqual(
            "La cause existante a été mise à jour.",
            response_data["message"],
        )

    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseForm"
    )
    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseFromUser"
    )
    def test_existing_identical_cause_is_not_duplicated(
            self,
            error_cause_model,
            form_class,
    ):
        form_class.return_value = self.create_valid_form()

        existing_cause = Mock()
        existing_cause.comment = (
            "The button locator is outdated."
        )
        existing_cause.type = "Script"
        existing_cause.errorMessage = "Element not found"
        existing_cause.action = "Click on the button"

        (
            error_cause_model.objects
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = existing_cause

        response = SaveErrorCauseView.as_view()(
            self.create_post_request()
        )

        existing_cause.save.assert_called_once()
        error_cause_model.objects.create.assert_not_called()

        self.assertEqual(200, response.status_code)

    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseFromUser"
    )
    def test_get_request_does_not_create_error_cause(
            self,
            error_cause_model,
    ):
        request = self.factory.get(
            "/snapshot/api/save-error-cause/"
        )

        response = SaveErrorCauseView.as_view()(request)

        error_cause_model.objects.create.assert_not_called()
        self.assertEqual(405, response.status_code)

    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseForm"
    )
    @patch(
        "snapshotServer.views.error_cause_view.ErrorCauseFromUser"
    )
    def test_invalid_form_returns_bad_request(
            self,
            error_cause_model,
            form_class,
    ):
        invalid_form = Mock()
        invalid_form.is_valid.return_value = False
        invalid_form.errors.get_json_data.return_value = {
            "comment": [
                {
                    "message": "This field is required.",
                    "code": "required",
                }
            ]
        }
        form_class.return_value = invalid_form

        response = SaveErrorCauseView.as_view()(
            self.create_post_request()
        )

        error_cause_model.objects.create.assert_not_called()

        self.assertEqual(400, response.status_code)

        response_data = json.loads(response.content)

        self.assertFalse(response_data["success"])
        self.assertIn("errors", response_data)