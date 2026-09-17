from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

from snapshotServer.controllers.error_cause.knowledge_base_analyzer import (
    find_probable_cause,
)
from snapshotServer.models import ErrorCauseFromUser, StepResult


# Permet de distinguer :
# - une valeur non fournie ;
# - la valeur None fournie volontairement.
NOT_PROVIDED = object()


class TestKnowledgeBaseAnalyzer(TestCase):

    fixtures = [
        "error_cause_finder/error_cause_finder_commons.yaml",
        "error_cause_finder/error_cause_finder_test_ok.yaml",
        "error_cause_finder/error_cause_finder_test_ko.yaml",
    ]

    def setUp(self):
        self.step_result = StepResult.objects.get(pk=13)
        self.test_case = self.step_result.testCase.testCase
        self.test_step = self.step_result.step

        self.exception = (
            "org.openqa.selenium.NoSuchElementException"
        )

    def create_error_cause(
            self,
            exception=NOT_PROVIDED,
            test_case=NOT_PROVIDED,
            test_step=NOT_PROVIDED,
            commentaire="Le locator du bouton est obsolète",
            cause_type="Script",
    ):
        """
        Crée une connaissance utilisée par les tests.

        Lorsqu'un paramètre n'est pas fourni, le contexte défini
        dans setUp est utilisé. La valeur None peut être transmise
        volontairement pour tester un contexte incomplet.
        """

        if exception is NOT_PROVIDED:
            exception = self.exception

        if test_case is NOT_PROVIDED:
            test_case = self.test_case

        if test_step is NOT_PROVIDED:
            test_step = self.test_step

        return ErrorCauseFromUser.objects.create(
            testCase=test_case,
            testStep=test_step,
            exception=exception,
            action="Cliquer sur le bouton",
            errorMessage="Element not found",
            commentaire=commentaire,
            type=cause_type,
        )

    def test_returns_none_when_no_cause_exists(self):
        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_registered_cause(self):
        entry = self.create_error_cause()

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            "Le locator du bouton est obsolète",
            result["cause"],
        )
        self.assertEqual("Script", result["type"])
        self.assertEqual(entry.id, result["knowledgeId"])
        self.assertEqual(1, result["count"])
        self.assertEqual(1, result["total"])

    def test_returns_none_for_different_exception(self):
        self.create_error_cause(
            exception="org.openqa.selenium.TimeoutException"
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_none_for_missing_test_step(self):
        self.create_error_cause(
            test_step=None
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_none_for_missing_test_case(self):
        self.create_error_cause(
            test_case=None
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_none_when_exception_is_none(self):
        result = find_probable_cause(
            exception=None,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_none_when_exception_is_empty(self):
        result = find_probable_cause(
            exception="",
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_none_when_exception_contains_only_spaces(self):
        result = find_probable_cause(
            exception="   ",
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_none_when_test_case_parameter_is_none(self):
        self.create_error_cause()

        result = find_probable_cause(
            exception=self.exception,
            testCase=None,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_none_when_test_step_parameter_is_none(self):
        self.create_error_cause()

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=None,
        )

        self.assertIsNone(result)

    def test_ignores_empty_comment(self):
        self.create_error_cause(
            commentaire=""
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_ignores_comment_containing_only_spaces(self):
        self.create_error_cause(
            commentaire="   "
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_returns_updated_cause_type(self):
        entry = self.create_error_cause(
            cause_type="Application"
        )

        entry.type = "Configuration"
        entry.save(update_fields=["type"])

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            "Configuration",
            result["type"],
        )
        self.assertEqual(
            entry.id,
            result["knowledgeId"],
        )

    def test_selects_most_recent_cause_when_duplicates_exist(self):
        first_entry = self.create_error_cause(
            commentaire="Première cause",
            cause_type="Application",
        )

        second_entry = self.create_error_cause(
            commentaire="Cause la plus récente",
            cause_type="Configuration",
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNotNone(result)

        # L'analyzer utilise order_by("-id").
        self.assertEqual(
            second_entry.id,
            result["knowledgeId"],
        )
        self.assertNotEqual(
            first_entry.id,
            result["knowledgeId"],
        )
        self.assertEqual(
            "Cause la plus récente",
            result["cause"],
        )
        self.assertEqual(
            "Configuration",
            result["type"],
        )
        self.assertEqual(2, result["total"])

    @patch(
        "snapshotServer.controllers.error_cause."
        "knowledge_base_analyzer."
        "ErrorCauseFromUser.objects.filter"
    )
    def test_returns_none_when_database_error_occurs(
            self,
            mocked_filter,
    ):
        mocked_filter.side_effect = DatabaseError(
            "Database unavailable"
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)
        mocked_filter.assert_called_once()