from django.test import TestCase

from snapshotServer.controllers.error_cause.knowledge_base_analyzer import (
    find_probable_cause,
)
from snapshotServer.models import ErrorCauseFromUser, StepResult


class TestKnowledgeBaseAnalyzer(TestCase):

    fixtures = [
        'error_cause_finder/error_cause_finder_commons.yaml',
        'error_cause_finder/error_cause_finder_test_ok.yaml',
        'error_cause_finder/error_cause_finder_test_ko.yaml',
    ]

    def setUp(self):
        self.step_result = StepResult.objects.get(pk=13)
        self.test_case = self.step_result.testCase.testCase
        self.test_step = self.step_result.step
        self.exception = "org.openqa.selenium.NoSuchElementException"

    def create_error_cause(
            self,
            exception=None,
            test_case=None,
            test_step=None,
            commentaire="Le locator du bouton est obsolète"
    ):
        return ErrorCauseFromUser.objects.create(
            testCase=test_case if test_case is not None else self.test_case,
            testStep=test_step if test_step is not None else self.test_step,
            exception=exception if exception is not None else self.exception,
            action="Cliquer sur le bouton",
            errorMessage="Element not found",
            commentaire=commentaire,
            type="Script",
        )

    def test_find_probable_cause_returns_none_when_no_cause_exists(self):
        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_find_probable_cause_returns_registered_cause(self):
        self.create_error_cause()

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
        self.assertEqual(1, result["count"])
        self.assertEqual(1, result["total"])

    def test_find_probable_cause_returns_none_for_different_exception(self):
        self.create_error_cause(
            exception="org.openqa.selenium.TimeoutException"
        )

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_find_probable_cause_returns_none_for_different_test_step(self):
        self.create_error_cause(test_step=None)

        ErrorCauseFromUser.objects.filter(
            exception=self.exception
        ).update(testStep=None)

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)

    def test_find_probable_cause_returns_none_for_different_test_case(self):
        self.create_error_cause(test_case=None)

        ErrorCauseFromUser.objects.filter(
            exception=self.exception
        ).update(testCase=None)

        result = find_probable_cause(
            exception=self.exception,
            testCase=self.test_case,
            testStep=self.test_step,
        )

        self.assertIsNone(result)